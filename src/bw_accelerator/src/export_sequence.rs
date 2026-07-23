use std::fs::File;
use std::path::Path;
use png::Encoder;
use crate::mmap;
use crate::filter;

pub fn export_sequence(
    path: *const u8,
    path_len: usize,
    width: u32,
    height: u32,
    bit_depth: u32,
    filter_type: u8,
    filter_value: f64,
    start_frame: u64,
    end_frame: u64,
    progress_ptr: *mut f64,
) -> Result<i64, String> {
    let base_path = unsafe {
        let slice = std::slice::from_raw_parts(path, path_len);
        String::from_utf8_lossy(slice).to_string()
    };

    let bytes_per_frame = (width as usize) * (height as usize) * (bit_depth as usize / 8);
    let pixels = (width as usize) * (height as usize);
    let total_frames = end_frame - start_frame;

    let dir = Path::new(&base_path);
    if !dir.exists() {
        std::fs::create_dir_all(dir).map_err(|e| format!("Failed to create directory: {}", e))?;
    }

    for idx in 0..total_frames {
        let frame_num = start_frame + idx;
        let offset = (frame_num as usize) * bytes_per_frame;

        let raw_frame = mmap::with_mmap(|data| {
            if offset + bytes_per_frame > data.len() {
                return Err(format!("Frame {} out of range", frame_num));
            }
            Ok(data[offset..offset + bytes_per_frame].to_vec())
        })?;

        let mut rgba_buf: Vec<u8> = vec![0u8; pixels * 4];
        match bit_depth {
            8 => {
                for i in 0..pixels {
                    let val = raw_frame[i];
                    let base = i * 4;
                    rgba_buf[base] = val;
                    rgba_buf[base + 1] = val;
                    rgba_buf[base + 2] = val;
                    rgba_buf[base + 3] = 255;
                }
            }
            16 => {
                for i in 0..pixels {
                    let hi = raw_frame[i * 2] as u16;
                    let lo = raw_frame[i * 2 + 1] as u16;
                    let val = ((hi << 8) | lo) as u8;
                    let base = i * 4;
                    rgba_buf[base] = val;
                    rgba_buf[base + 1] = val;
                    rgba_buf[base + 2] = val;
                    rgba_buf[base + 3] = 255;
                }
            }
            24 => {
                for i in 0..pixels {
                    let base = i * 4;
                    let src = i * 3;
                    rgba_buf[base] = raw_frame[src];
                    rgba_buf[base + 1] = raw_frame[src + 1];
                    rgba_buf[base + 2] = raw_frame[src + 2];
                    rgba_buf[base + 3] = 255;
                }
            }
            32 => {
                rgba_buf.copy_from_slice(&raw_frame);
            }
            _ => return Err(format!("Unsupported bit depth: {}", bit_depth)),
        }

        if filter_type != 0 {
            let mut rgb_in = vec![0u8; pixels * 3];
            let mut rgb_out = vec![0u8; pixels * 3];
            for i in 0..pixels {
                rgb_in[i * 3] = rgba_buf[i * 4];
                rgb_in[i * 3 + 1] = rgba_buf[i * 4 + 1];
                rgb_in[i * 3 + 2] = rgba_buf[i * 4 + 2];
            }
            filter::filter_rgb_batch(
                rgb_in.as_ptr(),
                pixels,
                filter_type,
                filter_value,
                rgb_out.as_mut_ptr(),
            )?;
            for i in 0..pixels {
                rgba_buf[i * 4] = rgb_out[i * 3];
                rgba_buf[i * 4 + 1] = rgb_out[i * 3 + 1];
                rgba_buf[i * 4 + 2] = rgb_out[i * 3 + 2];
                rgba_buf[i * 4 + 3] = 255;
            }
        }

        let file_name = format!("{:08}.png", frame_num);
        let file_path = dir.join(&file_name);
        let file = File::create(&file_path)
            .map_err(|e| format!("Failed to create {}: {}", file_path.display(), e))?;

        let mut encoder = Encoder::new(file, width, height);
        encoder.set_color(png::ColorType::Rgba);
        encoder.set_depth(png::BitDepth::Eight);

        let mut writer = encoder.write_header()
            .map_err(|e| format!("PNG header write failed: {}", e))?;

        writer.write_image_data(&rgba_buf)
            .map_err(|e| format!("PNG data write failed: {}", e))?;

        if !progress_ptr.is_null() {
            unsafe {
                *progress_ptr = (idx + 1) as f64 / total_frames as f64;
            }
        }
    }

    Ok(total_frames as i64)
}
