//! WebSocket transport, abstracted over native and wasm.
//!
//! Native uses quad-net (tungstenite under the hood); wasm uses our own tiny
//! plugin (web/brm_net.js) that talks to the browser WebSocket via raw wasm
//! memory — quad-net's wasm side depends on an old sapp_jsutils JS API that
//! current macroquad no longer ships.

#[cfg(not(target_arch = "wasm32"))]
pub use quad_net::web_socket::WebSocket;

#[cfg(target_arch = "wasm32")]
pub use wasm::WebSocket;

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
