"""Pure-numpy fallback implementations for Binary Waterfall acceleration.

These functions mirror the Rust bridge API and are used when the Rust
library is not available.
"""

from collections.abc import Callable
from typing import Any, Literal

import numpy as np
import numpy.typing as npt
from pathlib import Path

# Global state for file data
_file_data = None
_file_size = 0


def is_available():
    """Always available (pure Python fallback)."""
    return True


def load_file(file_path: str):
    """Load a binary file into memory (numpy array).

    Args:
        file_path: Path to the binary file

    Returns:
        File size in bytes
    """
    global _file_data, _file_size

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, 'rb') as f:
        raw = f.read()

    _file_data = np.frombuffer(raw, dtype=np.uint8)
    _file_size = len(_file_data)
    return _file_size


def get_file_size():
    """Get the size of the currently loaded file.

    Returns:
        File size in bytes
    """
    if _file_data is None:
        raise RuntimeError("No file loaded")
    return _file_size


def unload_file():
    """Unload the currently loaded file."""
    global _file_data, _file_size
    _file_data = None
    _file_size = 0


def generate_frame(width: int, height: int, frame_number: int, bit_depth: Literal[8, 16, 24, 32]):
    """Generate an RGBA frame from the loaded file using numpy.

    Args:
        width: Frame width in pixels
        height: Frame height in pixels
        frame_number: Absolute frame number
        bit_depth: Bits per pixel (8, 16, 24, or 32)

    Returns:
        numpy array of shape (height, width, 4) with dtype uint8 (RGBA)
    """
    if _file_data is None:
        raise RuntimeError("No file loaded")

    bytes_per_sample = bit_depth // 8
    pixels_per_frame = width * height
    bytes_per_frame = pixels_per_frame * bytes_per_sample

    offset = int(frame_number) * bytes_per_frame
    if offset + bytes_per_frame > _file_size:
        raise ValueError(f"Frame {frame_number} out of range")

    frame_bytes = _file_data[offset:offset + bytes_per_frame]

    if bit_depth == 8:
        gray = frame_bytes.reshape((height, width))
        rgba = np.zeros((height, width, 4), dtype=np.uint8)
        rgba[:, :, 0] = gray
        rgba[:, :, 1] = gray
        rgba[:, :, 2] = gray
        rgba[:, :, 3] = 255
    elif bit_depth == 16:
        frames16 = frame_bytes.reshape((height, width, 2))
        gray = (frames16[:, :, 0].astype(np.uint16) << 8 | frames16[:, :, 1].astype(np.uint16)).astype(np.uint8)
        rgba = np.zeros((height, width, 4), dtype=np.uint8)
        rgba[:, :, 0] = gray
        rgba[:, :, 1] = gray
        rgba[:, :, 2] = gray
        rgba[:, :, 3] = 255
    elif bit_depth == 24:
        frames24 = frame_bytes.reshape((height, width, 3))
        rgba = np.zeros((height, width, 4), dtype=np.uint8)
        rgba[:, :, :3] = frames24
        rgba[:, :, 3] = 255
    elif bit_depth == 32:
        rgba = frame_bytes.reshape((height, width, 4)).copy()
    else:
        raise ValueError(f"Unsupported bit depth: {bit_depth}")

    return rgba


def compute_audio(num_samples: int, sample_rate: int=44100):
    """Compute audio samples from the loaded file using numpy.

    Args:
        num_samples: Number of samples to generate
        sample_rate: Sample rate in Hz (default 44100)

    Returns:
        numpy array of shape (num_samples,) with dtype float32
    """
    if _file_data is None:
        raise RuntimeError("No file loaded")

    data_len = len(_file_data)
    if data_len == 0:
        raise RuntimeError("File is empty")

    indices = np.arange(num_samples, dtype=np.int64)
    byte_positions = (indices * 2) % data_len
    byte_vals = _file_data[byte_positions].astype(np.float64)
    freqs = 200.0 + (byte_vals / 255.0) * 800.0

    t = indices.astype(np.float64) / sample_rate
    samples = np.sin(2.0 * np.pi * freqs * t).astype(np.float32) * 0.5

    return samples


def filter_rgb_batch(rgb_data: npt.NDArray[np.uint8], filter_type: int=0, value: float=0.5):
    """Apply color filter to RGB pixel data using numpy.

    Args:
        rgb_data: numpy array of shape (N, 3) or (N,) with packed RGB, dtype uint8
        filter_type: 0=None, 1=Invert, 2=Grayscale, 3=Sepia, 4=Threshold
        value: Filter parameter (used for Threshold, 0.0-1.0)

    Returns:
        numpy array of filtered RGB data, same shape as input
    """
    original_shape = rgb_data.shape
    if rgb_data.ndim == 2 and rgb_data.shape[1] == 3:
        flat = rgb_data.reshape(-1, 3).astype(np.float64)
    elif rgb_data.ndim == 1:
        flat = rgb_data.reshape(-1, 3).astype(np.float64)
    else:
        raise ValueError(f"Invalid input shape: {rgb_data.shape}")

    r, g, b = flat[:, 0], flat[:, 1], flat[:, 2]

    if filter_type == 0:
        out = flat
    elif filter_type == 1:
        out = 255.0 - flat
    elif filter_type == 2:
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        out = np.column_stack([gray, gray, gray])
    elif filter_type == 3:
        tr = 0.393 * r + 0.769 * g + 0.189 * b
        tg = 0.349 * r + 0.686 * g + 0.168 * b
        tb = 0.272 * r + 0.534 * g + 0.131 * b
        out = np.column_stack([tr, tg, tb])
        out = np.clip(out, 0, 255)
    elif filter_type == 4:
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        v = np.where(gray >= value * 255.0, 255.0, 0.0)
        out = np.column_stack([v, v, v])
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")

    result = np.clip(out, 0, 255).astype(np.uint8)

    if len(original_shape) == 1:
        return result.flatten()
    return result.reshape(original_shape)


def export_video(file_path: str, width: int, height: int, frame_rate: int, total_frames: int,
                 bit_depth: Literal[8, 16, 24, 32], filter_type: int=0, filter_value: float=0.5, progress_callback: Callable[[float], Any] | None=None):
    """Export frames as video using subprocess ffmpeg pipe.

    Args:
        file_path: Output video file path
        width: Frame width
        height: Frame height
        frame_rate: Frames per second
        total_frames: Total number of frames
        bit_depth: Bits per pixel in source
        filter_type: Color filter type (0=None)
        filter_value: Filter parameter
        progress_callback: Optional callable(progress_float) for progress updates

    Returns:
        Number of frames exported
    """
    import subprocess

    cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-pix_fmt', 'rgba',
        '-s', f'{width}x{height}',
        '-r', f'{frame_rate:.2f}',
        '-i', '-',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',
        str(file_path),
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert proc.stdin is not None

    try:
        for frame_num in range(total_frames):
            rgba = generate_frame(width, height, frame_num, bit_depth)

            if filter_type != 0:
                _pixels = width * height
                rgb_flat = rgba[:, :, :3].reshape(-1, 3)
                filtered = filter_rgb_batch(rgb_flat, filter_type, filter_value)
                rgba[:, :, :3] = filtered.reshape((height, width, 3))

            proc.stdin.write(rgba.tobytes())

            if progress_callback is not None:
                progress_callback((frame_num + 1) / total_frames)
    finally:
        proc.stdin.close()
        proc.wait()

    return total_frames


def export_sequence(dir_path: str, width: int, height: int, bit_depth: Literal[8, 16, 24, 32], filter_type: int=0,
                    filter_value: float=0.5, start_frame: int=0, end_frame: int=0,
                    progress_callback: Callable[[float], Any] | None=None):
    """Export frames as PNG image sequence using PIL/pillow.

    Args:
        dir_path: Output directory path
        width: Frame width
        height: Frame height
        bit_depth: Bits per pixel in source
        filter_type: Color filter type (0=None)
        filter_value: Filter parameter
        start_frame: First frame number (inclusive)
        end_frame: Last frame number (exclusive)
        progress_callback: Optional callable(progress_float) for progress updates

    Returns:
        Number of frames exported
    """
    from PIL import Image

    out_dir = Path(dir_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    total = end_frame - start_frame
    for idx in range(total):
        frame_num = start_frame + idx
        rgba = generate_frame(width, height, frame_num, bit_depth)

        if filter_type != 0:
            _pixels = width * height
            rgb_flat = rgba[:, :, :3].reshape(-1, 3)
            filtered = filter_rgb_batch(rgb_flat, filter_type, filter_value)
            rgba[:, :, :3] = filtered.reshape((height, width, 3))

        img = Image.fromarray(rgba, 'RGBA')
        img.save(out_dir / f'{frame_num:08d}.png')

        if progress_callback is not None:
            progress_callback((idx + 1) / total)

    return total
