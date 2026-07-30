import os
import sys
import tempfile
import pytest
import numpy as np

# Ensure src is in path before importing
if "src" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import binary_waterfall_unofficial.ngen as ngen
from binary_waterfall_unofficial.constants.enums import ColorFmtCode


@pytest.fixture
def test_file():
    """Create a temporary test file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
        f.write(bytes(range(256)) * 100)
        test_file = f.name
    
    yield test_file
    
    ngen.unload_file()
    if os.path.exists(test_file):
        os.unlink(test_file)


class TestNgenLoadFile:
    def test_load_file_success(self, test_file: str):
        """Test loading a file."""
        size = ngen.load_file(test_file)
        assert size == 256 * 100
        assert ngen._file_data is not None # pyright: ignore[reportPrivateUsage]
        assert ngen._file_size == 256 * 100 # pyright: ignore[reportPrivateUsage]
    
    def test_load_file_nonexistent(self):
        """Test loading a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            ngen.load_file("/nonexistent/file.bin")
    
    def test_unload_file(self, test_file: str):
        """Test unloading a file."""
        ngen.load_file(test_file)
        assert ngen._file_data is not None # pyright: ignore[reportPrivateUsage]
        
        ngen.unload_file()
        assert ngen._file_data is None # pyright: ignore[reportPrivateUsage]
        assert ngen._file_size == 0 # pyright: ignore[reportPrivateUsage]


class TestNgenGetFileSize:
    def test_get_file_size(self, test_file: str):
        """Test getting file size."""
        ngen.load_file(test_file)
        size = ngen.get_file_size()
        assert size == 256 * 100
    
    def test_get_file_size_no_file(self):
        """Test getting file size when no file loaded."""
        ngen.unload_file()
        with pytest.raises(RuntimeError):
            ngen.get_file_size()


class TestNgenGetFileBytes:
    def test_get_file_bytes(self, test_file: str):
        """Test getting bytes from file."""
        ngen.load_file(test_file)
        data = ngen.get_file_bytes(0, 10)
        assert len(data) == 10
        assert data == bytes(range(10))
    
    def test_get_file_bytes_offset(self, test_file: str):
        """Test getting bytes with offset."""
        ngen.load_file(test_file)
        data = ngen.get_file_bytes(100, 10)
        assert len(data) == 10
        assert data == bytes(range(100, 110))
    
    def test_get_file_bytes_beyond_end(self, test_file: str):
        """Test getting bytes beyond file end returns partial or empty data."""
        ngen.load_file(test_file)
        data = ngen.get_file_bytes(10000, 100)
        # Should return empty or partial data (not crash)
        assert isinstance(data, bytes)


class TestNgenGenerateFrame:
    def test_generate_frame_8bit(self, test_file: str):
        """Test generating frame with 8-bit depth."""
        ngen.load_file(test_file)
        frame = ngen.generate_frame(8, 8, 0, 8)
        assert frame.shape == (8, 8, 4)  # RGBA
        assert frame.dtype == np.uint8
    
    def test_generate_frame_24bit(self, test_file: str):
        """Test generating frame with 24-bit depth."""
        ngen.load_file(test_file)
        frame = ngen.generate_frame(8, 8, 0, 24)
        assert frame.shape == (8, 8, 4)  # RGBA
        assert frame.dtype == np.uint8
    
    def test_generate_frame_out_of_range(self, test_file: str):
        """Test generating frame out of range."""
        ngen.load_file(test_file)
        with pytest.raises(ValueError):
            ngen.generate_frame(8, 8, 99999, 8)


class TestNgenGenerateFrameWithColorFormat:
    def test_generate_frame_rgb(self, test_file: str):
        """Test generating frame with RGB color format."""
        ngen.load_file(test_file)
        
        # Get frame bytes
        frame_bytes = ngen.get_file_bytes(0, 8 * 8 * 3)
        
        # Generate frame with RGB format
        color_format = [ColorFmtCode.RED.value, ColorFmtCode.GREEN.value, ColorFmtCode.BLUE.value]
        frame = ngen.generate_frame_with_color_format(
            8, 8, frame_bytes, color_format, 1 # pyright: ignore[reportArgumentType]
        )
        
        assert frame.shape == (8, 8, 3)  # RGB
        assert frame.dtype == np.uint8
    
    def test_generate_frame_inverted(self, test_file: str):
        """Test generating frame with inverted colors."""
        ngen.load_file(test_file)
        
        # Use smaller frame size to ensure we have enough data
        width, height = 4, 4
        frame_bytes = ngen.get_file_bytes(0, width * height * 3)
        
        # Generate frame with inverted RGB format
        color_format = [ColorFmtCode.RED_INV.value, ColorFmtCode.GREEN_INV.value, ColorFmtCode.BLUE_INV.value]
        frame = ngen.generate_frame_with_color_format(
            width, height, frame_bytes, color_format, 1 # pyright: ignore[reportArgumentType]
        )
        
        assert frame.shape == (height, width, 3)
        # For inverted format, each output byte should be 255 - input byte
        # The first pixel's R channel should be 255 - frame_bytes[0]
        # (since RED_INV takes every color_bytes-th byte starting at index 0)
        assert frame[0, 0, 0] == 255 - frame_bytes[0]
    
    def test_generate_frame_white(self, test_file: str):
        """Test generating frame with white (grayscale) format."""
        ngen.load_file(test_file)
        
        frame_bytes = ngen.get_file_bytes(0, 8 * 8 * 3)
        
        # Generate frame with white format
        color_format = [ColorFmtCode.WHITE.value]
        frame = ngen.generate_frame_with_color_format(
            8, 8, frame_bytes, color_format, 1 # pyright: ignore[reportArgumentType]
        )
        
        assert frame.shape == (8, 8, 3)
        # All channels should be the same for grayscale
        assert frame[0, 0, 0] == frame[0, 0, 1] == frame[0, 0, 2]


class TestNgenComputeAudio:
    def test_compute_audio(self, test_file: str):
        """Test computing audio samples."""
        ngen.load_file(test_file)
        
        samples = ngen.compute_audio(1000, 44100)
        assert len(samples) == 1000
        assert samples.dtype == np.float32
        # Audio samples should be in range [-1, 1]
        assert np.all(samples >= -1.0)
        assert np.all(samples <= 1.0)


class TestNgenFilterRgbBatch:
    def test_filter_no_change(self):
        """Test filter with no change (filter_type=0)."""
        rgb_data = np.array([[100, 150, 200], [50, 100, 150]], dtype=np.uint8)
        result = ngen.filter_rgb_batch(rgb_data, 0)
        np.testing.assert_array_equal(result, rgb_data)
    
    def test_filter_invert(self):
        """Test invert filter."""
        rgb_data = np.array([[0, 0, 0], [255, 255, 255]], dtype=np.uint8)
        result = ngen.filter_rgb_batch(rgb_data, 1)
        expected = np.array([[255, 255, 255], [0, 0, 0]], dtype=np.uint8)
        np.testing.assert_array_equal(result, expected)
    
    def test_filter_grayscale(self):
        """Test grayscale filter."""
        rgb_data = np.array([[100, 150, 200]], dtype=np.uint8)
        result = ngen.filter_rgb_batch(rgb_data, 2)
        # Grayscale should have same value for all channels
        assert result[0, 0] == result[0, 1] == result[0, 2]
