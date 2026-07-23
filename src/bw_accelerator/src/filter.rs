/// Apply color filter to a batch of RGB pixels.
/// filter_type: 0=None, 1=Invert, 2=Grayscale, 3=Sepia, 4=Threshold
pub fn filter_rgb_batch(
    in_ptr: *const u8,
    num_pixels: usize,
    filter_type: u8,
    value: f64,
    out_ptr: *mut u8,
) -> Result<i64, String> {
    let in_slice = unsafe { std::slice::from_raw_parts(in_ptr, num_pixels * 3) };
    let out_slice = unsafe { std::slice::from_raw_parts_mut(out_ptr, num_pixels * 3) };

    for i in 0..num_pixels {
        let base = i * 3;
        let r = in_slice[base] as f64;
        let g = in_slice[base + 1] as f64;
        let b = in_slice[base + 2] as f64;

        let (nr, ng, nb) = match filter_type {
            0 => (r, g, b),
            1 => (255.0 - r, 255.0 - g, 255.0 - b),
            2 => {
                let gray = 0.299 * r + 0.587 * g + 0.114 * b;
                (gray, gray, gray)
            }
            3 => {
                let tr = 0.393 * r + 0.769 * g + 0.189 * b;
                let tg = 0.349 * r + 0.686 * g + 0.168 * b;
                let tb = 0.272 * r + 0.534 * g + 0.131 * b;
                (tr.min(255.0), tg.min(255.0), tb.min(255.0))
            }
            4 => {
                let gray = 0.299 * r + 0.587 * g + 0.114 * b;
                let v = if gray >= value * 255.0 { 255.0 } else { 0.0 };
                (v, v, v)
            }
            _ => return Err(format!("Unknown filter type: {}", filter_type)),
        };

        out_slice[base] = nr.clamp(0.0, 255.0) as u8;
        out_slice[base + 1] = ng.clamp(0.0, 255.0) as u8;
        out_slice[base + 2] = nb.clamp(0.0, 255.0) as u8;
    }

    Ok((num_pixels * 3) as i64)
}
