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

/// Color format codes (matching Python ColorFmtCode enum)
#[repr(u8)]
#[derive(Clone, Copy)]
pub enum ColorFmtCode {
    Red = 0,      // 'r'
    RedInv = 1,   // 'R'
    Green = 2,    // 'g'
    GreenInv = 3, // 'G'
    Blue = 4,     // 'b'
    BlueInv = 5,  // 'B'
    White = 6,    // 'w'
    WhiteInv = 7, // 'W'
    Unused = 8,   // 'x'
}

impl ColorFmtCode {
    pub fn from_u8(val: u8) -> Option<Self> {
        match val {
            0 => Some(Self::Red),
            1 => Some(Self::RedInv),
            2 => Some(Self::Green),
            3 => Some(Self::GreenInv),
            4 => Some(Self::Blue),
            5 => Some(Self::BlueInv),
            6 => Some(Self::White),
            7 => Some(Self::WhiteInv),
            8 => Some(Self::Unused),
            _ => None,
        }
    }
}

/// Generate an RGB frame using color format string (fastest path).
/// 
/// # Arguments
/// * `width` - Frame width in pixels
/// * `height` - Frame height in pixels
/// * `frame_bytes` - Raw binary data for the frame
/// * `color_format` - Slice of ColorFmtCode values describing the color mapping
/// * `color_bytes` - Number of bytes per color component (default 1)
/// * `out_ptr` - Output buffer pointer (must be at least width * height * 3 bytes)
/// * `out_len` - Output buffer length
/// 
/// # Returns
/// Number of bytes written to output buffer, or error message
pub fn generate_frame_with_color_format(
    width: u32,
    height: u32,
    frame_bytes: &[u8],
    color_format: &[u8],
    color_bytes: u32,
    out_ptr: *mut u8,
    out_len: usize,
) -> Result<i64, String> {
    let pixels = (width as usize) * (height as usize);
    let expected_out = pixels * 3; // RGB output
    
    if out_len < expected_out {
        return Err(format!("Output buffer too small: {} < {}", out_len, expected_out));
    }
    
    let out = unsafe { std::slice::from_raw_parts_mut(out_ptr, out_len) };
    let color_bytes = color_bytes as usize;
    
    // Initialize output to black
    for i in 0..expected_out {
        out[i] = 0;
    }
    
    // Process each color format code
    let mut source_idx = 0;
    for &fmt_byte in color_format {
        let fmt = ColorFmtCode::from_u8(fmt_byte)
            .ok_or_else(|| format!("Invalid color format code: {}", fmt_byte))?;
        
        if source_idx >= frame_bytes.len() {
            break;
        }
        
        match fmt {
            ColorFmtCode::Red => {
                for i in 0..pixels {
                    if source_idx + i * color_bytes < frame_bytes.len() {
                        out[i * 3] = frame_bytes[source_idx + i * color_bytes];
                    }
                }
            }
            ColorFmtCode::RedInv => {
                for i in 0..pixels {
                    if source_idx + i * color_bytes < frame_bytes.len() {
                        out[i * 3] = 255 - frame_bytes[source_idx + i * color_bytes];
                    }
                }
            }
            ColorFmtCode::Green => {
                for i in 0..pixels {
                    if source_idx + i * color_bytes < frame_bytes.len() {
                        out[i * 3 + 1] = frame_bytes[source_idx + i * color_bytes];
                    }
                }
            }
            ColorFmtCode::GreenInv => {
                for i in 0..pixels {
                    if source_idx + i * color_bytes < frame_bytes.len() {
                        out[i * 3 + 1] = 255 - frame_bytes[source_idx + i * color_bytes];
                    }
                }
            }
            ColorFmtCode::Blue => {
                for i in 0..pixels {
                    if source_idx + i * color_bytes < frame_bytes.len() {
                        out[i * 3 + 2] = frame_bytes[source_idx + i * color_bytes];
                    }
                }
            }
            ColorFmtCode::BlueInv => {
                for i in 0..pixels {
                    if source_idx + i * color_bytes < frame_bytes.len() {
                        out[i * 3 + 2] = 255 - frame_bytes[source_idx + i * color_bytes];
                    }
                }
            }
            ColorFmtCode::White => {
                for i in 0..pixels {
                    if source_idx + i * color_bytes < frame_bytes.len() {
                        let val = frame_bytes[source_idx + i * color_bytes];
                        out[i * 3] = val;
                        out[i * 3 + 1] = val;
                        out[i * 3 + 2] = val;
                    }
                }
            }
            ColorFmtCode::WhiteInv => {
                for i in 0..pixels {
                    if source_idx + i * color_bytes < frame_bytes.len() {
                        let val = 255 - frame_bytes[source_idx + i * color_bytes];
                        out[i * 3] = val;
                        out[i * 3 + 1] = val;
                        out[i * 3 + 2] = val;
                    }
                }
            }
            ColorFmtCode::Unused => {
                // Skip unused bytes
            }
        }
        
        source_idx += 1;
    }
    
    Ok(expected_out as i64)
}
