use crate::mmap;

pub fn generate_frame(
    width: u32,
    height: u32,
    frame_number: u64,
    bit_depth: u32,
    out_ptr: *mut u8,
    out_len: usize,
) -> Result<i64, String> {
    let bytes_per_frame = (width as usize) * (height as usize) * (bit_depth as usize / 8);
    let expected_out = (width as usize) * (height as usize) * 4; // RGBA
    if out_len < expected_out {
        return Err(format!("Output buffer too small: {} < {}", out_len, expected_out));
    }

    mmap::with_mmap(|data| {
        let offset = (frame_number as usize) * bytes_per_frame;
        if offset + bytes_per_frame > data.len() {
            return Err(format!(
                "Frame {} out of range (file size={}, bytes_per_frame={})",
                frame_number,
                data.len(),
                bytes_per_frame
            ));
        }
        let frame_data = &data[offset..offset + bytes_per_frame];
        let out = unsafe { std::slice::from_raw_parts_mut(out_ptr, out_len) };

        let pixels = (width as usize) * (height as usize);

        match bit_depth {
            8 => {
                for i in 0..pixels {
                    let val = frame_data[i];
                    let base = i * 4;
                    out[base] = val;
                    out[base + 1] = val;
                    out[base + 2] = val;
                    out[base + 3] = 255;
                }
            }
            16 => {
                for i in 0..pixels {
                    let hi = frame_data[i * 2] as u16;
                    let lo = frame_data[i * 2 + 1] as u16;
                    let val = ((hi << 8) | lo) as u8;
                    let base = i * 4;
                    out[base] = val;
                    out[base + 1] = val;
                    out[base + 2] = val;
                    out[base + 3] = 255;
                }
            }
            24 => {
                for i in 0..pixels {
                    let base = i * 4;
                    let src = i * 3;
                    out[base] = frame_data[src];
                    out[base + 1] = frame_data[src + 1];
                    out[base + 2] = frame_data[src + 2];
                    out[base + 3] = 255;
                }
            }
            32 => {
                for i in 0..pixels {
                    let base = i * 4;
                    let src = i * 4;
                    out[base] = frame_data[src];
                    out[base + 1] = frame_data[src + 1];
                    out[base + 2] = frame_data[src + 2];
                    out[base + 3] = frame_data[src + 3];
                }
            }
            _ => return Err(format!("Unsupported bit depth: {}", bit_depth)),
        }

        Ok(expected_out as i64)
    })
}
