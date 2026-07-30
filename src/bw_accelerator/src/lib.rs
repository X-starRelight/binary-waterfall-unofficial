mod mmap;
mod frame;
mod audio;
mod filter;
mod export_video;
mod export_sequence;

#[no_mangle]
pub extern "C" fn load_file_mmap(path: *const u8, path_len: usize) -> i64 {
    let path_str = unsafe {
        let slice = std::slice::from_raw_parts(path, path_len);
        String::from_utf8_lossy(slice).to_string()
    };
    match mmap::load_file(&path_str) {
        Ok(size) => size,
        Err(_) => -1,
    }
}

#[no_mangle]
pub extern "C" fn get_file_size() -> i64 {
    match mmap::get_file_size() {
        Ok(size) => size,
        Err(_) => -1,
    }
}

#[no_mangle]
pub extern "C" fn unload_file() {
    let _ = mmap::unload_file();
}

#[no_mangle]
pub extern "C" fn generate_frame(
    width: u32,
    height: u32,
    frame_number: u64,
    bit_depth: u32,
    out_ptr: *mut u8,
    out_len: usize,
) -> i64 {
    match frame::generate_frame(width, height, frame_number, bit_depth, out_ptr, out_len) {
        Ok(n) => n,
        Err(_) => -1,
    }
}

#[no_mangle]
pub extern "C" fn compute_audio(
    num_samples: u32,
    sample_rate: u32,
    out_ptr: *mut f32,
) -> i64 {
    match audio::compute_audio(num_samples, sample_rate, out_ptr) {
        Ok(n) => n,
        Err(_) => -1,
    }
}

#[no_mangle]
pub extern "C" fn filter_rgb_batch(
    in_ptr: *const u8,
    num_pixels: usize,
    filter: u8,
    value: f64,
    out_ptr: *mut u8,
) -> i64 {
    match filter::filter_rgb_batch(in_ptr, num_pixels, filter, value, out_ptr) {
        Ok(n) => n,
        Err(_) => -1,
    }
}

#[no_mangle]
pub extern "C" fn export_video(
    path: *const u8,
    path_len: usize,
    width: u32,
    height: u32,
    frame_rate: f64,
    total_frames: u64,
    bit_depth: u32,
    filter: u8,
    filter_value: f64,
    progress_ptr: *mut f64,
) -> i64 {
    match export_video::export_video(
        path, path_len, width, height, frame_rate,
        total_frames, bit_depth, filter, filter_value, progress_ptr,
    ) {
        Ok(n) => n,
        Err(_) => -1,
    }
}

#[no_mangle]
pub extern "C" fn export_sequence(
    path: *const u8,
    path_len: usize,
    width: u32,
    height: u32,
    bit_depth: u32,
    filter: u8,
    filter_value: f64,
    start_frame: u64,
    end_frame: u64,
    progress_ptr: *mut f64,
) -> i64 {
    match export_sequence::export_sequence(
        path, path_len, width, height, bit_depth,
        filter, filter_value, start_frame, end_frame, progress_ptr,
    ) {
        Ok(n) => n,
        Err(_) => -1,
    }
}

/// Generate an RGB frame using color format string.
/// 
/// # Arguments
/// * `frame_bytes_ptr` - Pointer to frame data
/// * `frame_bytes_len` - Length of frame data
/// * `color_format_ptr` - Pointer to color format codes (u8 array)
/// * `color_format_len` - Length of color format array
/// * `width` - Frame width
/// * `height` - Frame height
/// * `color_bytes` - Bytes per color component (default 1)
/// * `out_ptr` - Output buffer (RGB, width * height * 3 bytes)
/// * `out_len` - Output buffer length
#[no_mangle]
pub extern "C" fn generate_frame_with_color_format(
    frame_bytes_ptr: *const u8,
    frame_bytes_len: usize,
    color_format_ptr: *const u8,
    color_format_len: usize,
    width: u32,
    height: u32,
    color_bytes: u32,
    out_ptr: *mut u8,
    out_len: usize,
) -> i64 {
    let frame_bytes = unsafe { std::slice::from_raw_parts(frame_bytes_ptr, frame_bytes_len) };
    let color_format = unsafe { std::slice::from_raw_parts(color_format_ptr, color_format_len) };
    
    match frame::generate_frame_with_color_format(
        width, height, frame_bytes, color_format, color_bytes, out_ptr, out_len,
    ) {
        Ok(n) => n,
        Err(_) => -1,
    }
}
