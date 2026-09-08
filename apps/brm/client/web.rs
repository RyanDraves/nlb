//! Browser-only hooks implemented in `web/brm_net.js`: touch-device detection
//! and soft-keyboard name entry via a hidden HTML `<input>`. All no-ops on
//! native (where there's a real keyboard and no touch).

#[cfg(target_arch = "wasm32")]
mod imp {
    use brm_shared::PlayerInput;

    extern "C" {
        fn brm_is_touch() -> i32;
        fn brm_name_show();
        fn brm_name_hide();
        fn brm_name_get(ptr: *mut u8, max: usize) -> i32;
        fn brm_gamepad_present() -> i32;
        fn brm_gamepad_x() -> f32;
        fn brm_gamepad_y() -> f32;
        fn brm_gamepad_bomb() -> i32;
    }

    pub fn is_touch() -> bool {
        unsafe { brm_is_touch() == 1 }
    }
    pub fn name_show() {
        unsafe { brm_name_show() }
    }
    pub fn name_hide() {
        unsafe { brm_name_hide() }
    }
    /// The current text in the hidden name input, if any.
    pub fn name_value() -> Option<String> {
        let mut buf = [0u8; 64];
        let n = unsafe { brm_name_get(buf.as_mut_ptr(), buf.len()) };
        if n < 0 {
            return None;
        }
        String::from_utf8(buf[..n as usize].to_vec()).ok()
    }

    /// Whether a browser gamepad is connected (so we drive the player with it).
    pub fn gamepad_present() -> bool {
        unsafe { brm_gamepad_present() == 1 }
    }
    /// Sample the browser gamepad. `brm_gamepad_bomb` is edge-triggered, so call
    /// this exactly once per frame.
    pub fn gamepad_input() -> PlayerInput {
        unsafe {
            PlayerInput {
                dx: brm_gamepad_x(),
                dy: brm_gamepad_y(),
                place_bomb: brm_gamepad_bomb() == 1,
            }
        }
    }
}

#[cfg(not(target_arch = "wasm32"))]
mod imp {
    use brm_shared::PlayerInput;

    pub fn is_touch() -> bool {
        false
    }
    pub fn name_show() {}
    pub fn name_hide() {}
    pub fn name_value() -> Option<String> {
        None
    }
    // Only referenced from the wasm input path; native uses gilrs (gamepad.rs).
    #[allow(dead_code)]
    pub fn gamepad_present() -> bool {
        false
    }
    #[allow(dead_code)]
    pub fn gamepad_input() -> PlayerInput {
        PlayerInput::default()
    }
}

pub use imp::*;
