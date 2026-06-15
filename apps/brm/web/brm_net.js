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
    };

    miniquad_add_plugin({ register_plugin, name: "brm_net", version: 1 });
})();
