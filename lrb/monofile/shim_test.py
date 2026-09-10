"""Browser coverage for the `window.__monofile` shim inside `shell.html`.

The shim is the one part of monofile that no `rust_test` can reach, and it is
where the only real bug so far got in: adding an object store without bumping
the IndexedDB version made every draft call hang forever instead of failing.
Catching that class of bug needs a real IndexedDB, so this drives real Chrome.

`rust_wasm_bindgen_test` would be the idiomatic route, but it is broken in this
environment — it points Chrome's `--user-data-dir` at Bazel's `test.outputs`,
and the `SingletonLock` symlink Chrome creates there fails Bazel's output-tree
validation. Verified against the rules' own `hello_world_web_wasm_bindgen_test`,
which fails the same way with no first-party code involved.

The shim source is extracted from the real `shell.html` rather than duplicated,
so this cannot drift from what actually ships.

Served over http rather than `file://` because the assertions need to come back
out of the browser. That means it does not exercise the shared `file__0` origin;
the keying logic it checks is origin-independent.
"""

import http.server
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import threading
import unittest

SHELL = pathlib.Path(os.environ['MONOFILE_SHELL'])

# The assertions, run inside the page. Each returns a list of [name, ok, detail].
HARNESS_JS = r"""
const results = [];
const check = (name, ok, detail) => results.push([name, !!ok, detail || ""]);
const withTimeout = (p, ms, label) => Promise.race([
  p,
  new Promise((_, rej) => setTimeout(() => rej(new Error("timed out: " + label)), ms)),
]);
const idbDelete = (name) => new Promise((res) => {
  const r = indexedDB.deleteDatabase(name);
  r.onsuccess = r.onerror = r.onblocked = () => res();
});

async function run() {
  const M = window.__monofile;

  // 1. The shim exposes the contract web.rs binds to. A rename here is
  //    otherwise only discovered at runtime, in a browser, on save.
  for (const fn of ["canSaveInPlace", "acquire", "commit", "open", "toast",
                    "setDirty", "configure", "newDocId",
                    "saveDraft", "loadDraft", "clearDraft"]) {
    check("exports " + fn, typeof M[fn] === "function");
  }

  // 2. THE REGRESSION TEST. Pre-create the database at version 1 holding only
  //    `handles`, exactly as a monofile shipped before `drafts` existed would
  //    have left it. saveDraft must still work. Before the schema was
  //    versioned, the transaction threw inside the success handler and the
  //    promise never settled — every draft call hung, silently, forever.
  await idbDelete("legacy-monofile");
  await new Promise((res, rej) => {
    const r = indexedDB.open("legacy-monofile", 1);
    r.onupgradeneeded = () => r.result.createObjectStore("handles");
    r.onsuccess = () => { r.result.close(); res(); };
    r.onerror = () => rej(r.error);
  });
  M.configure({ appId: "legacy", docId: "doc-legacy" });
  try {
    await withTimeout(M.saveDraft("LEGACY-OK"), 4000, "saveDraft over a v1 database");
    const got = await withTimeout(M.loadDraft(), 4000, "loadDraft over a v1 database");
    check("upgrades a database created before the drafts store existed",
          got && got.payload === "LEGACY-OK");
  } catch (e) {
    check("upgrades a database created before the drafts store existed", false, e.message);
  }

  // 3. Databases are scoped per app: one app's drafts are invisible to another.
  //    Sharing a database is what makes a version bump in one app break every
  //    other app's already-distributed files.
  await idbDelete("appa-monofile");
  await idbDelete("appb-monofile");
  M.configure({ appId: "appa", docId: "shared-doc" });
  await M.saveDraft("FROM-APP-A");
  M.configure({ appId: "appb", docId: "shared-doc" });
  check("a second app does not see the first app's drafts",
        (await M.loadDraft()) === null);
  M.configure({ appId: "appa" });
  const backA = await M.loadDraft();
  check("the first app still sees its own draft", backA && backA.payload === "FROM-APP-A");

  // 4. Drafts follow the document id, so renaming or moving a file keeps them.
  M.configure({ appId: "keys", docId: "doc-one" });
  await M.saveDraft("ONE");
  M.configure({ appId: "keys", docId: "doc-two" });
  check("a different document does not see the first document's draft",
        (await M.loadDraft()) === null);
  await M.saveDraft("TWO");
  M.configure({ appId: "keys", docId: "doc-one" });
  const one = await M.loadDraft();
  check("each document keeps its own draft", one && one.payload === "ONE");

  // 5. clearDraft actually clears, and only the current document's.
  await M.clearDraft();
  check("clearDraft removes the current document's draft",
        (await M.loadDraft()) === null);
  M.configure({ appId: "keys", docId: "doc-two" });
  const two = await M.loadDraft();
  check("clearDraft leaves other documents alone", two && two.payload === "TWO");

  // 6. Ids are unique; drafts keyed by a repeated id would collide.
  const ids = new Set(Array.from({ length: 64 }, () => M.newDocId()));
  check("newDocId is unique", ids.size === 64, `${ids.size}/64 distinct`);

  // 7. Nothing may touch storage before configure() supplies the app id.
  //    An eager lookup at load time opens the default-named database, which
  //    both misses the real data and leaves a stray database behind.
  const names = (await indexedDB.databases()).map((d) => d.name);
  check("no storage is opened before configure() names the app",
        !names.includes("monofile-monofile"), names.join(", "));

  // 8. A missing draft is null, not a throw — boot must survive a fresh file.
  M.configure({ appId: "keys", docId: "never-saved" });
  check("an absent draft reads back as null", (await M.loadDraft()) === null);
}

run().then(
  () => { document.title = "DONE"; report(); },
  (e) => { check("harness", false, String(e && e.stack || e)); document.title = "DONE"; report(); },
);
function report() {
  navigator.sendBeacon("/result", JSON.stringify(results));
}
"""


def extract_shim(html: str) -> str:
    """The shim exactly as it ships, so this test cannot drift from reality."""
    m = re.search(r'<script id="monofile-shim">(.*?)</script>', html, re.S)
    assert m, 'shell.html has no <script id="monofile-shim">'
    return m.group(1)


def find_chrome() -> str | None:
    for name in ('google-chrome', 'chromium', 'chromium-browser'):
        path = shutil.which(name)
        if path:
            return path
    return None


class ShimTest(unittest.TestCase):
    def test_shim_behaviour_in_a_real_browser(self):
        chrome = find_chrome()
        if not chrome:
            self.skipTest('no Chrome on PATH; skipping browser coverage of the shim')

        shim = extract_shim(SHELL.read_text())
        page = (
            "<!DOCTYPE html><meta charset='utf-8'><title>shim</title>"
            f'<script>{shim}</script>'
            f'<script>{HARNESS_JS}</script>'
        )

        received: list = []
        done = threading.Event()

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                body = page.encode()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):  # noqa: N802
                n = int(self.headers.get('Content-Length', 0))
                received.append(self.rfile.read(n).decode())
                self.send_response(204)
                self.end_headers()
                done.set()

            def log_message(self, *_args, **_kwargs):
                pass

        server = http.server.HTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]

        with tempfile.TemporaryDirectory() as profile:
            proc = subprocess.Popen(
                [
                    chrome,
                    '--headless=new',
                    '--disable-gpu',
                    '--no-sandbox',
                    f'--user-data-dir={profile}',
                    f'http://127.0.0.1:{port}/',
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                # No --virtual-time-budget: it stops IndexedDB callbacks from
                # ever firing, which silently turns every assertion below into a
                # timeout. Real time, real timeout.
                ok = done.wait(timeout=90)
            finally:
                proc.kill()
                proc.wait(timeout=30)
                server.shutdown()

        self.assertTrue(ok, 'browser never reported results (see the harness timeout)')

        results = json.loads(received[0])
        failures = [r for r in results if not r[1]]
        self.assertTrue(results, 'harness produced no assertions')
        self.assertFalse(
            failures,
            'shim assertions failed:\n'
            + '\n'.join(f'  {name}: {detail}' for name, _, detail in failures),
        )


if __name__ == '__main__':
    unittest.main()
