//! WebSocket transport, abstracted over native and wasm.
//!
//! Native runs the `ws` crate's event loop on a background thread (one per
//! connection); wasm uses our own tiny plugin (web/brm_net.js) that talks to the
//! browser WebSocket via raw wasm memory. We don't use quad-net: its wasm side
//! depends on an old sapp_jsutils JS API current macroquad dropped, and its
//! native handler `unwrap()`s the channel send in `on_message`, so dropping a
//! socket (e.g. a controller unplugging) panics its still-running thread.

#[cfg(not(target_arch = "wasm32"))]
pub use native::WebSocket;

#[cfg(target_arch = "wasm32")]
pub use wasm::WebSocket;

#[cfg(not(target_arch = "wasm32"))]
mod native {
    use std::sync::atomic::{AtomicBool, Ordering};
    use std::sync::{mpsc, Arc};

    /// A WebSocket client backed by the `ws` crate. Each connection owns a
    /// background thread running its event loop; the main thread pushes outbound
    /// frames through `out` and drains inbound frames from `rx`.
    pub struct WebSocket {
        out: ws::Sender,
        rx: mpsc::Receiver<Vec<u8>>,
        connected: Arc<AtomicBool>,
    }

    /// ws-rs handler. Unlike quad-net's, it never panics on a dropped receiver
    /// and just tracks the open/closed state.
    struct Handler {
        tx: mpsc::Sender<Vec<u8>>,
        connected: Arc<AtomicBool>,
    }

    impl ws::Handler for Handler {
        fn on_open(&mut self, _: ws::Handshake) -> ws::Result<()> {
            self.connected.store(true, Ordering::SeqCst);
            Ok(())
        }
        fn on_message(&mut self, msg: ws::Message) -> ws::Result<()> {
            // Ignore a closed receiver (the WebSocket was dropped) — never panic.
            let _ = self.tx.send(msg.into_data());
            Ok(())
        }
        fn on_close(&mut self, _: ws::CloseCode, _: &str) {
            self.connected.store(false, Ordering::SeqCst);
        }
        fn on_error(&mut self, _: ws::Error) {
            self.connected.store(false, Ordering::SeqCst);
        }
    }

    impl WebSocket {
        pub fn connect(url: &str) -> Result<WebSocket, ()> {
            let (msg_tx, msg_rx) = mpsc::channel::<Vec<u8>>();
            let (out_tx, out_rx) = mpsc::channel::<ws::Sender>();
            let connected = Arc::new(AtomicBool::new(false));
            let url = url.to_owned();
            let conn = connected.clone();
            std::thread::spawn(move || {
                let _ = ws::connect(url, |out| {
                    // Hand the Sender back to connect(), then build the handler.
                    let _ = out_tx.send(out);
                    Handler { tx: msg_tx.clone(), connected: conn.clone() }
                });
            });
            // The factory runs as soon as the connection object is created (well
            // before the handshake), so this returns promptly; `connected` flips
            // true only once the socket actually opens. A closed channel means
            // the worker died first — i.e. connect failed.
            match out_rx.recv() {
                Ok(out) => Ok(WebSocket { out, rx: msg_rx, connected }),
                Err(_) => Err(()),
            }
        }

        pub fn connected(&self) -> bool {
            self.connected.load(Ordering::SeqCst)
        }

        pub fn send_bytes(&self, data: &[u8]) {
            // Ignore send errors: a closed socket is handled by the server
            // dropping the player; never panic the game over a dead connection.
            let _ = self.out.send(ws::Message::Binary(data.to_vec()));
        }

        pub fn try_recv(&mut self) -> Option<Vec<u8>> {
            self.rx.try_recv().ok()
        }
    }

    impl Drop for WebSocket {
        fn drop(&mut self) {
            // Stop this connection's event loop so its thread exits cleanly
            // instead of delivering to a now-dropped receiver.
            let _ = self.out.shutdown();
        }
    }
}

#[cfg(target_arch = "wasm32")]
mod wasm {
    extern "C" {
        fn brm_ws_connect(ptr: *const u8, len: usize);
        fn brm_ws_connected() -> i32;
        fn brm_ws_send(ptr: *const u8, len: usize);
        /// Length of the next queued message, or -1 if the queue is empty.
        fn brm_ws_recv_len() -> i32;
        /// Copy the next queued message into `ptr` (must hold `brm_ws_recv_len`
        /// bytes) and pop it.
        fn brm_ws_recv_into(ptr: *mut u8);
    }

    pub struct WebSocket;

    impl WebSocket {
        pub fn connect(url: &str) -> Result<WebSocket, ()> {
            unsafe { brm_ws_connect(url.as_ptr(), url.len()) };
            Ok(WebSocket)
        }
        pub fn connected(&self) -> bool {
            unsafe { brm_ws_connected() == 1 }
        }
        pub fn send_bytes(&self, data: &[u8]) {
            unsafe { brm_ws_send(data.as_ptr(), data.len()) };
        }
        pub fn try_recv(&mut self) -> Option<Vec<u8>> {
            let n = unsafe { brm_ws_recv_len() };
            if n < 0 {
                return None;
            }
            let mut buf = vec![0u8; n as usize];
            unsafe { brm_ws_recv_into(buf.as_mut_ptr()) };
            Some(buf)
        }
    }
}
