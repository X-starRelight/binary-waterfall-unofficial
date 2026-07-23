use crate::mmap;

pub fn compute_audio(
    num_samples: u32,
    sample_rate: u32,
    out_ptr: *mut f32,
) -> Result<i64, String> {
    let out = unsafe { std::slice::from_raw_parts_mut(out_ptr, num_samples as usize) };

    mmap::with_mmap(|data| {
        let data_len = data.len();
        if data_len == 0 {
            return Err("File is empty".to_string());
        }

        for i in 0..num_samples as usize {
            let byte_pos = (i * 2) % data_len;
            let byte_val = data[byte_pos] as f32;
            let freq = 200.0f64 + (byte_val as f64 / 255.0) * 800.0;
            let t = i as f64 / sample_rate as f64;
            let sample = (2.0 * std::f64::consts::PI * freq * t).sin() as f32;
            out[i] = sample * 0.5;
        }

        Ok(num_samples as i64)
    })
}
