use std::process::{Command, Stdio};
use std::io::Write;
use crate::mmap;
use crate::filter;

pub fn export_video(
    path: *const u8,
    path_len: usize,
    width: u32,
    height: u32,
    frame_rate: f64,
    total_frames: u64,
    bit_depth: u32,
    filter_type: u8,
    filter_value: f64,
    progress_ptr: *mut f64,
) -> Result<i64, String> {
    let path_str = unsafe {
        let slice = std::slice::from_raw_parts(path, path_len);
        String::from_utf8_lossy(slice).to_string()
    };

    let bytes_per_frame = (width as usize) * (height as usize) * (bit_depth as usize / 8);
    let rgba_size = (width as usize) * (height as usize) * 4;

    let mut child = Command::new("ffmpeg")
        .args(&[
            "-y",
            "-f", "rawvideo",
            "-pix_fmt", "rgba",
            "-s", &format!("{}x{}", width, height),
            "-r", &format!("{:.2}", frame_rate),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            &path_str,
        ])
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to spawn ffmpeg: {}", e))?;

    let stdin = child.stdin.as_mut().ok_or("Failed to open ffmpeg stdin")?;
    let mut frame_buf: Vec<u8> = vec![0u8; rgba_size];

    for frame_num in 0..total_frames {
        let offset = (frame_num as usize) * bytes_per_frame;
        let raw_frame = mmap::with_mmap(|data| {
            if offset + bytes_per_frame > data.len() {
                return Err(format!("Frame {} out of range", frame_num));
            }
            Ok(data[offset..offset + bytes_per_frame].to_vec())
        })?;

        let pixels = (width as usize) * (height as usize);
        match bit_depth {
            8 => {
                for i in 0..pixels {
                    let val = raw_frame[i];
                    let base = i * 4;
                    frame_buf[base] = val;
                    frame_buf[base + 1] = val;
                    frame_buf[base + 2] = val;
                    frame_buf[base + 3] = 255;
                }
            }
            16 => {
                for i in 0..pixels {
                    let hi = raw_frame[i * 2] as u16;
                    let lo = raw_frame[i * 2 + 1] as u16;
                    let val = ((hi << 8) | lo) as u8;
                    let base = i * 4;
                    frame_buf[base] = val;
                    frame_buf[base + 1] = val;
                    frame_buf[base + 2] = val;
                    frame_buf[base + 3] = 255;
                }
            }
            24 => {
                for i in 0..pixels {
                    let base = i * 4;
                    let src = i * 3;
                    frame_buf[base] = raw_frame[src];
                    frame_buf[base + 1] = raw_frame[src + 1];
                    frame_buf[base + 2] = raw_frame[src + 2];
                    frame_buf[base + 3] = 255;
                }
            }
            32 => {
                frame_buf.copy_from_slice(&raw_frame);
            }
            _ => return Err(format!("Unsupported bit depth: {}", bit_depth)),
        }

        if filter_type != 0 {
            let mut filtered = vec![0u8; rgba_size];
            let mut rgb_in = vec![0u8; pixels * 3];
            let mut rgb_out = vec![0u8; pixels * 3];
            for i in 0..pixels {
                rgb_in[i * 3] = frame_buf[i * 4];
                rgb_in[i * 3 + 1] = frame_buf[i * 4 + 1];
                rgb_in[i * 3 + 2] = frame_buf[i * 4 + 2];
            }
            filter::filter_rgb_batch(
                rgb_in.as_ptr(),
                pixels,
                filter_type,
                filter_value,
                rgb_out.as_mut_ptr(),
            )?;
            for i in 0..pixels {
                filtered[i * 4] = rgb_out[i * 3];
                filtered[i * 4 + 1] = rgb_out[i * 3 + 1];
                filtered[i * 4 + 2] = rgb_out[i * 3 + 2];
                filtered[i * 4 + 3] = 255;
            }
            frame_buf = filtered;
        }

        stdin.write_all(&frame_buf)
            .map_err(|e| format!("Failed to write frame: {}", e))?;

        if !progress_ptr.is_null() {
            unsafe {
                *progress_ptr = (frame_num + 1) as f64 / total_frames as f64;
            }
        }
    }

    let _ = stdin;
    child.wait().map_err(|e| format!("ffmpeg wait failed: {}", e))?;

    Ok(total_frames as i64)
}
