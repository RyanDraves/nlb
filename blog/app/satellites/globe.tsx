"use client";

import { missions, splitBlurb, type Mission } from "@/app/satellites/data/missions";
import tleData from "@/app/satellites/data/tles.json";
import * as satellite from "satellite.js";
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

// --- Scene scale --------------------------------------------------------------
const EARTH_RADIUS_KM = 6371;
const SCENE_EARTH_RADIUS = 1; // Earth drawn as a unit sphere
const KM_TO_SCENE = SCENE_EARTH_RADIUS / EARTH_RADIUS_KM;

// Number of samples used to draw a full orbit loop.
const ORBIT_SAMPLES = 256;

// The Earth texture's prime-meridian is not perfectly aligned to the ECI frame
// we draw orbits in. This offset (radians, about the polar axis) nudges the
// texture so markers sit over roughly the right longitudes. Tweak if needed.
const EARTH_TEXTURE_OFFSET = -Math.PI / 2;

// Colors for active vs. deorbited orbits/markers.
const ACTIVE_COLOR = 0x4fd1c5; // teal
const DEORBITED_COLOR = 0xf6993f; // amber

interface TleEntry {
  name: string;
  tle1: string;
  tle2: string;
}

interface PreparedSat {
  noradId: string;
  satrec: satellite.SatRec;
  mission?: Mission;
  status: "active" | "deorbited";
  color: number;
}

/** Map a satellite.js ECI position (km) into three.js scene space (Y-up). */
function eciToScene(p: satellite.EciVec3<number>): THREE.Vector3 {
  // ECI: x -> vernal equinox, z -> north pole. three.js is Y-up.
  return new THREE.Vector3(p.x, p.z, -p.y).multiplyScalar(KM_TO_SCENE);
}

/** Julian date stored on a satrec -> JS Date. */
function epochOf(satrec: satellite.SatRec): Date {
  // jdsatepochF (sub-day fraction) exists in satellite.js v5 but isn't in every
  // version of the types; read it defensively without `any`.
  const frac = (satrec as { jdsatepochF?: number }).jdsatepochF ?? 0;
  const jd = satrec.jdsatepoch + frac;
  return new Date((jd - 2440587.5) * 86400000);
}

/** Propagate to a single scene-space position, or null if SGP4 fails. */
function positionAt(satrec: satellite.SatRec, when: Date): THREE.Vector3 | null {
  const pv = satellite.propagate(satrec, when);
  if (!pv || typeof pv.position === "boolean" || !pv.position) return null;
  return eciToScene(pv.position as satellite.EciVec3<number>);
}

/** Sample one full orbital period into a list of scene-space points. */
function orbitPoints(satrec: satellite.SatRec, base: Date): THREE.Vector3[] {
  const periodMin = (2 * Math.PI) / satrec.no; // satrec.no is radians/minute
  const pts: THREE.Vector3[] = [];
  for (let i = 0; i <= ORBIT_SAMPLES; i++) {
    const t = new Date(base.getTime() + (i / ORBIT_SAMPLES) * periodMin * 60000);
    const p = positionAt(satrec, t);
    if (p) pts.push(p);
  }
  return pts;
}

function prepareSatellites(): PreparedSat[] {
  const entries = tleData.satellites as Record<string, TleEntry>;
  const prepared: PreparedSat[] = [];
  for (const [noradId, entry] of Object.entries(entries)) {
    if (!entry.tle1 || !entry.tle2) continue;
    const satrec = satellite.twoline2satrec(entry.tle1, entry.tle2);
    const mission = missions[noradId];
    const status = mission?.status ?? "active";
    prepared.push({
      noradId,
      satrec,
      mission,
      status,
      color: status === "deorbited" ? DEORBITED_COLOR : ACTIVE_COLOR,
    });
  }
  return prepared;
}

interface Tooltip {
  noradId: string;
  x: number;
  y: number;
  pinned: boolean;
}

const Globe = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<Tooltip | null>(null);
  // Keep the latest tooltip in a ref so the (single-run) effect can read it.
  const tooltipRef = useRef<Tooltip | null>(null);
  tooltipRef.current = tooltip;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const isDark = () =>
      document.documentElement.classList.contains("dark");

    const scene = new THREE.Scene();
    const setBackground = () =>
      scene.background = new THREE.Color(isDark() ? 0x05070d : 0x0b1020);
    setBackground();

    const camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.01,
      1000,
    );
    camera.position.set(0, 4, 9);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 1.5;
    controls.maxDistance = 40;

    // --- Lights ---
    scene.add(new THREE.AmbientLight(0xffffff, 0.35));
    const sun = new THREE.DirectionalLight(0xffffff, 1.1);
    sun.position.set(5, 3, 5);
    scene.add(sun);

    // --- Earth ---
    const earth = new THREE.Mesh(
      new THREE.SphereGeometry(SCENE_EARTH_RADIUS, 64, 64),
      new THREE.MeshPhongMaterial({ shininess: 8 }),
    );
    scene.add(earth);
    new THREE.TextureLoader().load("/assets/satellites/earth.jpg", (tex) => {
      tex.colorSpace = THREE.SRGBColorSpace;
      (earth.material as THREE.MeshPhongMaterial).map = tex;
      (earth.material as THREE.MeshPhongMaterial).needsUpdate = true;
    });
    // Orient the Earth's inertial spin so markers sit over the right longitudes.
    earth.rotation.y = satellite.gstime(new Date()) + EARTH_TEXTURE_OFFSET;

    // --- Starfield (cheap, no texture) ---
    const starGeo = new THREE.BufferGeometry();
    const starCount = 800;
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i++) {
      const r = 60 + Math.random() * 40;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      starPos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      starPos[i * 3 + 1] = r * Math.cos(phi);
      starPos[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
    }
    starGeo.setAttribute("position", new THREE.BufferAttribute(starPos, 3));
    scene.add(
      new THREE.Points(
        starGeo,
        new THREE.PointsMaterial({ color: 0xffffff, size: 0.15, sizeAttenuation: true }),
      ),
    );

    // --- Satellites: orbits + markers ---
    const sats = prepareSatellites();
    const markerMeshes: THREE.Mesh[] = [];
    const disposables: { dispose(): void }[] = [];

    const markerData: { sat: PreparedSat; pos: THREE.Vector3 }[] = [];

    for (const sat of sats) {
      const base = sat.status === "deorbited" ? epochOf(sat.satrec) : new Date();

      const pts = orbitPoints(sat.satrec, base);
      if (pts.length > 1) {
        const geom = new THREE.BufferGeometry().setFromPoints(pts);
        const mat =
          sat.status === "deorbited"
            ? new THREE.LineDashedMaterial({
                color: sat.color,
                dashSize: 0.12,
                gapSize: 0.08,
                transparent: true,
                opacity: 0.7,
              })
            : new THREE.LineBasicMaterial({ color: sat.color });
        const line = new THREE.Line(geom, mat);
        if (sat.status === "deorbited") line.computeLineDistances();
        scene.add(line);
        disposables.push(geom, mat);
      }

      const pos = positionAt(sat.satrec, base);
      if (pos) markerData.push({ sat, pos });
    }

    // Co-located satellites (e.g. two birds in the same GEO slot) would stack
    // into a single un-hoverable dot. Cluster markers that land within
    // CLUSTER_DIST and fan each cluster out along its radial (altitude) axis so
    // every satellite is a distinct, pickable marker.
    const CLUSTER_DIST = 0.2;
    // Separation between adjacent markers in a cluster; keep > marker diameter
    // (0.18) so co-located satellites read as distinct, individually pickable dots.
    const SPREAD = 0.3;
    const groups: number[][] = [];
    markerData.forEach((m, i) => {
      const group = groups.find((g) =>
        g.some((j) => markerData[j].pos.distanceTo(m.pos) < CLUSTER_DIST),
      );
      if (group) group.push(i);
      else groups.push([i]);
    });
    for (const group of groups) {
      if (group.length < 2) continue;
      group.forEach((idx, k) => {
        const m = markerData[idx];
        const radial = m.pos.clone().normalize();
        m.pos.addScaledVector(radial, (k - (group.length - 1) / 2) * SPREAD);
      });
    }

    for (const { sat, pos } of markerData) {
      const markerGeo = new THREE.SphereGeometry(0.09, 16, 16);
      const markerMat = new THREE.MeshBasicMaterial({ color: sat.color });
      const marker = new THREE.Mesh(markerGeo, markerMat);
      marker.position.copy(pos);
      marker.userData.noradId = sat.noradId;
      scene.add(marker);
      markerMeshes.push(marker);
      disposables.push(markerGeo, markerMat);
    }

    // --- Picking ---
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();

    const pickAt = (clientX: number, clientY: number) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(markerMeshes, false);
      return hits.length ? hits[0].object : null;
    };

    const onPointerMove = (e: PointerEvent) => {
      if (tooltipRef.current?.pinned) return;
      const hit = pickAt(e.clientX, e.clientY);
      const rect = renderer.domElement.getBoundingClientRect();
      if (hit) {
        renderer.domElement.style.cursor = "pointer";
        setTooltip({
          noradId: hit.userData.noradId,
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
          pinned: false,
        });
      } else {
        renderer.domElement.style.cursor = "grab";
        // Only clear (and re-render) if a hover tooltip is currently showing.
        if (tooltipRef.current && !tooltipRef.current.pinned) setTooltip(null);
      }
    };

    const onClick = (e: MouseEvent) => {
      const hit = pickAt(e.clientX, e.clientY);
      const rect = renderer.domElement.getBoundingClientRect();
      if (hit) {
        setTooltip({
          noradId: hit.userData.noradId,
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
          pinned: true,
        });
      } else {
        setTooltip(null);
      }
    };

    renderer.domElement.addEventListener("pointermove", onPointerMove);
    renderer.domElement.addEventListener("click", onClick);

    // --- Resize ---
    const onResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    const resizeObserver = new ResizeObserver(onResize);
    resizeObserver.observe(container);

    // React to theme changes.
    const themeObserver = new MutationObserver(setBackground);
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });

    // --- Render loop ---
    let frameId = 0;
    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
      themeObserver.disconnect();
      renderer.domElement.removeEventListener("pointermove", onPointerMove);
      renderer.domElement.removeEventListener("click", onClick);
      controls.dispose();
      earth.geometry.dispose();
      (earth.material as THREE.Material).dispose();
      starGeo.dispose();
      for (const d of disposables) d.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  const activeMission: Mission | undefined = tooltip
    ? missions[tooltip.noradId]
    : undefined;
  const blurb = activeMission ? splitBlurb(activeMission.blurb) : undefined;

  return (
    <div ref={containerRef} className="relative h-full w-full">
      {tooltip && (
        <div
          className={`${
            tooltip.pinned ? "pointer-events-auto" : "pointer-events-none"
          } absolute z-10 max-w-xs rounded-lg border border-gray-200 bg-white/95 p-3 text-sm shadow-md dark:border-gray-700 dark:bg-gray-800/95`}
          style={{
            left: Math.round(tooltip.x) + 12,
            top: Math.round(tooltip.y) + 12,
          }}
        >
          <div className="font-bold text-gray-900 dark:text-white">
            {activeMission?.name || `NORAD ${tooltip.noradId}`}
          </div>
          <div className="mb-1 text-xs text-gray-500 dark:text-gray-400">
            {[
              activeMission?.orbit,
              activeMission?.launched && `launched ${activeMission.launched}`,
              activeMission?.status,
            ]
              .filter(Boolean)
              .join(" · ")}
          </div>
          {activeMission?.role && (
            <div className="text-gray-700 dark:text-gray-300">
              <span className="font-semibold">Role:</span> {activeMission.role}
            </div>
          )}
          {blurb?.text && (
            <p className="mt-1 text-gray-700 dark:text-gray-300">{blurb.text}</p>
          )}
          {blurb?.url && (
            <a
              href={blurb.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 inline-block text-teal-600 hover:underline dark:text-teal-400"
            >
              Learn more →
            </a>
          )}
          {!tooltip.pinned && (
            <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">
              click to pin
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Globe;
