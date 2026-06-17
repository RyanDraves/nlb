// Minimal WebSocket plugin for the wasm client. Implements the brm_ws_* imports
// declared in client/src/main.rs by talking to the browser WebSocket and copying
// bytes straight through `wasm_memory` (a global the macroquad loader exposes).
// Self-contained on purpose: it avoids sapp_jsutils, whose JS API has drifted
// across macroquad versions and broke the abandoned quad-net plugin.
(function () {
    let sock = null;
    let open = 0;
    const queue = []; // Array<Uint8Array> of received binary messages
    let recvCount = 0;

    // Lightweight introspection for debugging from the devtools console.
    window.__brm_net = function () {
        return { url: sock && sock.url, ready: sock && sock.readyState, open, queued: queue.length, received: recvCount };
    };

    function bytes(ptr, len) {
        // Re-read .buffer each call: wasm memory growth detaches old buffers.
        return new Uint8Array(wasm_memory.buffer, ptr, len);
    }

    const register_plugin = function (importObject) {
        importObject.env.brm_ws_connect = function (ptr, len) {
            let url = new TextDecoder().decode(bytes(ptr, len).slice());
            if (url.charAt(0) === "/") {
                url = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + url;
            }
            sock = new WebSocket(url);
            sock.binaryType = "arraybuffer";
            open = 0;
            queue.length = 0;
            sock.onopen = function () { open = 1; };
            sock.onclose = function () { open = 0; };
            sock.onmessage = function (e) {
                if (e.data instanceof ArrayBuffer) { queue.push(new Uint8Array(e.data)); recvCount++; }
            };
        };
        importObject.env.brm_ws_connected = function () { return open; };
        importObject.env.brm_ws_send = function (ptr, len) {
            if (sock && open) sock.send(bytes(ptr, len).slice());
        };
        importObject.env.brm_ws_recv_len = function () {
            return queue.length ? queue[0].length : -1;
        };
        importObject.env.brm_ws_recv_into = function (ptr) {
            const msg = queue.shift();
            bytes(ptr, msg.length).set(msg);
        };

        // --- Touch device + soft-keyboard name entry -----------------------
        // The wasm client (client/src/web.rs) asks whether this is a touch
        // device (to switch to the on-screen joystick) and drives a hidden HTML
        // <input> for name entry — a real input the user taps, so the mobile
        // soft keyboard appears from a genuine gesture.
        const touch = ("ontouchstart" in window) || (navigator.maxTouchPoints > 0);
        const nameEl = function () { return document.getElementById("brm_name"); };

        importObject.env.brm_is_touch = function () { return touch ? 1 : 0; };
        importObject.env.brm_name_show = function () {
            const el = nameEl();
            if (el) el.style.display = "block";
        };
        importObject.env.brm_name_hide = function () {
            const el = nameEl();
            if (el) { el.blur(); el.style.display = "none"; }
        };
        importObject.env.brm_name_get = function (ptr, max) {
            const el = nameEl();
            if (!el) return -1;
            let out = new TextEncoder().encode(el.value);
            if (out.length > max) out = out.subarray(0, max);
            bytes(ptr, out.length).set(out);
            return out.length;
        };

        // --- Gamepad (browser Gamepad API) ---------------------------------
        // Mirrors the native gilrs path (client/src/gamepad.rs): left stick or
        // D-pad for movement, the South button (A / Cross, standard-mapping
        // index 0) for bomb/ready, edge-triggered. We drive the single web
        // player from the first connected pad.
        const PAD_DEADZONE = 0.35;
        let padBombPrev = false;
        function firstPad() {
            const pads = navigator.getGamepads ? navigator.getGamepads() : [];
            for (let i = 0; i < pads.length; i++) if (pads[i]) return pads[i];
            return null;
        }
        function padPressed(p, i) { return p.buttons[i] && p.buttons[i].pressed; }

        importObject.env.brm_gamepad_present = function () { return firstPad() ? 1 : 0; };
        importObject.env.brm_gamepad_x = function () {
            const p = firstPad();
            if (!p) return 0;
            let x = p.axes[0] || 0;
            if (Math.abs(x) < PAD_DEADZONE) x = 0;
            if (padPressed(p, 14)) x = -1; // D-pad left
            if (padPressed(p, 15)) x = 1;  // D-pad right
            return x;
        };
        importObject.env.brm_gamepad_y = function () {
            const p = firstPad();
            if (!p) return 0;
            let y = p.axes[1] || 0; // browser stick is already +Y down
            if (Math.abs(y) < PAD_DEADZONE) y = 0;
            if (padPressed(p, 12)) y = -1; // D-pad up
            if (padPressed(p, 13)) y = 1;  // D-pad down
            return y;
        };
        importObject.env.brm_gamepad_bomb = function () {
            const p = firstPad();
            const now = !!(p && padPressed(p, 0));
            const edge = now && !padBombPrev;
            padBombPrev = now;
            return edge ? 1 : 0;
        };
    };

    miniquad_add_plugin({ register_plugin, name: "brm_net", version: 1 });
})();
