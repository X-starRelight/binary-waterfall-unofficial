"""Python FFI bridge to the bw_accelerator Rust library using SenRi FFI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from collections.abc import Callable

import numpy as np

# Try to load the Rust library
RUST_AVAILABLE: bool = False
_lib: Any = None
_load_file: Any = None
_get_file_size: Any = None
_unload_file: Any = None
_generate_frame: Any = None
_compute_audio: Any = None
_filter_rgb_batch: Any = None
_export_video: Any = None
_export_sequence: Any = None
address_of: Callable[..., Any] | None = None

try:
    from senri_ffi import Library, types, address_of as _address_of, pointer  # type: ignore[reportUnknownMemberType]

    address_of = _address_of

    # Determine library path
    if sys.platform == 'win32':
        lib_name = 'bw_accelerator.dll'
    elif sys.platform == 'darwin':
        lib_name = 'libbw_accelerator.dylib'
    else:
        lib_name = 'libbw_accelerator.so'

    # Search paths: target/release first, then alongside this file
    search_paths = [
        # Path(__file__).parent.parent.parent / 'bw_accelerator' / 'target' / 'release' / lib_name,
        Path(__file__).parent / 'bw_accelerator' / lib_name,
        Path(__file__).parent / lib_name,
        Path(__file__).parent / 'lib' / lib_name,
    ]

    lib_path = None
    for p in search_paths:
        if p.exists():
            lib_path = p
            break

    if lib_path is not None:
        _lib = Library.load(str(lib_path))

        # Bind function signatures
        _load_file = _lib.func("load_file_mmap", types.int64, [types.cstring, types.uint64])  # type: ignore[reportUnknownMemberType]
        _get_file_size = _lib.func("get_file_size", types.int64, [])  # type: ignore[reportUnknownMemberType]
        _unload_file = _lib.func("unload_file", types.void, [])  # type: ignore[reportUnknownMemberType]
        _generate_frame = _lib.func("generate_frame", types.int64, [  # type: ignore[reportUnknownMemberType]
            types.uint32, types.uint32, types.uint64, types.uint32,  # type: ignore[reportUnknownMemberType]
            pointer(types.uint8), types.uint64,  # type: ignore[reportUnknownMemberType]
        ])
        _compute_audio = _lib.func("compute_audio", types.int64, [  # type: ignore[reportUnknownMemberType]
            types.uint32, types.uint32, pointer(types.float32),  # type: ignore[reportUnknownMemberType]
        ])
        _filter_rgb_batch = _lib.func("filter_rgb_batch", types.int64, [  # type: ignore[reportUnknownMemberType]
            pointer(types.uint8), types.uint64, types.uint8, types.float64,  # type: ignore[reportUnknownMemberType]
            pointer(types.uint8),  # type: ignore[reportUnknownMemberType]
        ])
        _export_video = _lib.func("export_video", types.int64, [  # type: ignore[reportUnknownMemberType]
            types.cstring, types.uint64, types.uint32, types.uint32,  # type: ignore[reportUnknownMemberType]
            types.float64, types.uint64, types.uint32, types.uint8,  # type: ignore[reportUnknownMemberType]
            types.float64, pointer(types.float64),  # type: ignore[reportUnknownMemberType]
        ])
        _export_sequence = _lib.func("export_sequence", types.int64, [  # type: ignore[reportUnknownMemberType]
            types.cstring, types.uint64, types.uint32, types.uint32,  # type: ignore[reportUnknownMemberType]
            types.uint32, types.uint8, types.float64, types.uint64,  # type: ignore[reportUnknownMemberType]
            types.uint64, pointer(types.float64),  # type: ignore[reportUnknownMemberType]
        ])

        RUST_AVAILABLE: bool = True # pyright: ignore[reportConstantRedefinition]
except Exception:
    RUST_AVAILABLE: bool = False # pyright: ignore[reportConstantRedefinition]
    _lib = None


def is_available() -> bool:
    """Check if Rust acceleration is available."""
    return RUST_AVAILABLE


def load_file(file_path: str | Path) -> int:
    """Load a binary file into mmap.

    Args:
        file_path: Path to the binary file

    Returns:
        File size in bytes

    Raises:
        RuntimeError: If Rust library not available or load fails
    """
    if not RUST_AVAILABLE:
        raise RuntimeError("Rust accelerator not available")

    path_bytes = str(file_path).encode('utf-8')
    result = _load_file(path_bytes, len(path_bytes))
    if result < 0:
        raise RuntimeError(f"Failed to load file: error code {result}")
    return result


def get_file_size() -> int:
    """Get the size of the currently loaded file.

    Returns:
        File size in bytes

    Raises:
        RuntimeError: If no file loaded or library not available
    """
    if not RUST_AVAILABLE:
        raise RuntimeError("Rust accelerator not available")

    result = _get_file_size()
    if result < 0:
        raise RuntimeError("No file loaded")
    return result


def unload_file() -> None:
    """Unload the currently loaded file from mmap.

    Raises:
        RuntimeError: If library not available
    """
    if not RUST_AVAILABLE:
        raise RuntimeError("Rust accelerator not available")

    _unload_file()


def generate_frame(width: int, height: int, frame_number: int, bit_depth: int) -> np.ndarray:
    """Generate an RGBA frame from the loaded file.

    Args:
        width: Frame width in pixels
        height: Frame height in pixels
        frame_number: Absolute frame number
        bit_depth: Bits per pixel (8, 16, 24, or 32)

    Returns:
        numpy array of shape (height, width, 4) with dtype uint8 (RGBA)

    Raises:
        RuntimeError: If generation fails
    """
    if not RUST_AVAILABLE:
        raise RuntimeError("Rust accelerator not available")

    pixels = width * height
    out_len = pixels * 4  # RGBA
    out_buf = bytearray(out_len)
    out_addr = address_of(out_buf)  # type: ignore[misc]

    result = _generate_frame(
        width, height, frame_number, bit_depth,
        out_addr, out_len
    )

    if result < 0:
        raise RuntimeError(f"Frame generation failed: error code {result}")

    return np.frombuffer(out_buf, dtype=np.uint8).reshape((height, width, 4)).copy()


def compute_audio(num_samples: int, sample_rate: int = 44100) -> np.ndarray:
    """Compute audio samples from the loaded file.

    Args:
        num_samples: Number of samples to generate
        sample_rate: Sample rate in Hz (default 44100)

    Returns:
        numpy array of shape (num_samples,) with dtype float32

    Raises:
        RuntimeError: If computation fails
    """
    if not RUST_AVAILABLE:
        raise RuntimeError("Rust accelerator not available")

    out_buf = bytearray(num_samples * 4)  # 4 bytes per float32
    out_addr = address_of(out_buf)  # type: ignore[misc]

    result = _compute_audio(num_samples, sample_rate, out_addr)

    if result < 0:
        raise RuntimeError(f"Audio computation failed: error code {result}")

    return np.frombuffer(out_buf, dtype=np.float32).copy()


def filter_rgb_batch(
    rgb_data: np.ndarray,
    filter_type: int = 0,
    value: float = 0.5,
) -> np.ndarray:
    """Apply color filter to RGB pixel data.

    Args:
        rgb_data: numpy array of shape (N, 3) or (N,) with packed RGB, dtype uint8
        filter_type: 0=None, 1=Invert, 2=Grayscale, 3=Sepia, 4=Threshold
        value: Filter parameter (used for Threshold, 0.0-1.0)

    Returns:
        numpy array of filtered RGB data, same shape as input

    Raises:
        RuntimeError: If filtering fails
    """
    if not RUST_AVAILABLE:
        raise RuntimeError("Rust accelerator not available")

    original_shape = rgb_data.shape
    if rgb_data.ndim == 2 and rgb_data.shape[1] == 3:
        flat = rgb_data.flatten()
    elif rgb_data.ndim == 1:
        flat = rgb_data
    else:
        raise ValueError(f"Invalid input shape: {rgb_data.shape}")

    num_pixels = len(flat) // 3
    in_buf = bytearray(np.ascontiguousarray(flat, dtype=np.uint8).tobytes())
    in_addr = address_of(in_buf)  # type: ignore[misc]
    out_buf = bytearray(num_pixels * 3)
    out_addr = address_of(out_buf)  # type: ignore[misc]

    result = _filter_rgb_batch(in_addr, num_pixels, filter_type, value, out_addr)

    if result < 0:
        raise RuntimeError(f"Filter failed: error code {result}")

    out_arr = np.frombuffer(out_buf, dtype=np.uint8).copy()
    if len(original_shape) == 2:
        return out_arr.reshape(original_shape)
    return out_arr


def export_video(
    file_path: str | Path,
    width: int,
    height: int,
    frame_rate: float,
    total_frames: int,
    bit_depth: int,
    filter_type: int = 0,
    filter_value: float = 0.5,
    progress_callback: Callable[[float], None] | None = None,
) -> int:
    """Export frames as video using ffmpeg pipe.

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

    Raises:
        RuntimeError: If export fails
    """
    if not RUST_AVAILABLE:
        raise RuntimeError("Rust accelerator not available")

    path_bytes = str(file_path).encode('utf-8')

    # Progress pointer
    progress_buf = bytearray(8)  # 8 bytes for f64
    progress_addr = address_of(progress_buf)  # type: ignore[misc]

    result = _export_video(
        path_bytes, len(path_bytes),
        width, height, frame_rate,
        total_frames, bit_depth,
        filter_type, filter_value,
        progress_addr
    )

    if progress_callback is not None:
        progress_callback(1.0)

    if result < 0:
        raise RuntimeError(f"Video export failed: error code {result}")

    return result


def export_sequence(
    dir_path: str | Path,
    width: int,
    height: int,
    bit_depth: int,
    filter_type: int = 0,
    filter_value: float = 0.5,
    start_frame: int = 0,
    end_frame: int = 0,
    progress_callback: Callable[[float], None] | None = None,
) -> int:
    """Export frames as PNG image sequence.

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

    Raises:
        RuntimeError: If export fails
    """
    if not RUST_AVAILABLE:
        raise RuntimeError("Rust accelerator not available")

    path_bytes = str(dir_path).encode('utf-8')

    # Progress pointer
    progress_buf = bytearray(8)
    progress_addr = address_of(progress_buf)  # type: ignore[misc]

    result = _export_sequence(
        path_bytes, len(path_bytes),
        width, height, bit_depth,
        filter_type, filter_value,
        start_frame, end_frame,
        progress_addr
    )

    if progress_callback is not None:
        progress_callback(1.0)

    if result < 0:
        raise RuntimeError(f"Sequence export failed: error code {result}")

    return result
