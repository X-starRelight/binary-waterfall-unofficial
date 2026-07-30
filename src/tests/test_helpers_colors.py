import os
import sys


# Ensure src is in path before importing
if "src" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from binary_waterfall_unofficial.helpers.colors import (
    filter_rgb_bytes,
    average_rgb_bytes,
    get_luminance,
    pick_shade_from_luminance,
    desaturate,
    invert,
    average,
)


class TestFilterRgbBytes:
    def test_invert_filter(self):
        """Test invert filter produces correct output."""
        input_data = bytes([10, 20, 30, 40, 50, 60])
        result = filter_rgb_bytes(input_data, invert)
        assert result == bytes([245, 235, 225, 215, 205, 195])
    
    def test_identity_filter(self):
        """Test identity filter returns same values."""
        input_data = bytes([100, 150, 200])
        result = filter_rgb_bytes(input_data, lambda r, g, b: (r, g, b))
        assert result == input_data
    
    def test_empty_input(self):
        """Test filter with empty input."""
        result = filter_rgb_bytes(b"", invert)
        assert result == b""
    
    def test_single_pixel(self):
        """Test filter with single pixel."""
        input_data = bytes([255, 128, 0])
        result = filter_rgb_bytes(input_data, invert)
        assert result == bytes([0, 127, 255])
    
    def test_desaturate_filter(self):
        """Test desaturate filter."""
        input_data = bytes([100, 150, 200])
        result = filter_rgb_bytes(input_data, desaturate)
        # desaturate returns (min+max)/2 for each pixel
        expected = bytes([150, 150, 150])
        assert result == expected


class TestAverageRgbBytes:
    def test_average_same_values(self):
        """Test averaging identical values."""
        a = bytes([100, 100, 100])
        b = bytes([100, 100, 100])
        result = average_rgb_bytes(a, b)
        assert result == bytes([100, 100, 100])
    
    def test_average_different_values(self):
        """Test averaging different values."""
        a = bytes([100, 100, 100])
        b = bytes([200, 200, 200])
        result = average_rgb_bytes(a, b)
        assert result == bytes([150, 150, 150])
    
    def test_average_multiple_pixels(self):
        """Test averaging multiple pixels."""
        a = bytes([100, 150, 200, 50, 100, 150])
        b = bytes([200, 100, 50, 150, 200, 100])
        result = average_rgb_bytes(a, b)
        assert result == bytes([150, 125, 125, 100, 150, 125])


class TestLuminance:
    def test_white_luminance(self):
        """Test luminance of white."""
        assert get_luminance(255, 255, 255) == 1.0
    
    def test_black_luminance(self):
        """Test luminance of black."""
        assert get_luminance(0, 0, 0) == 0.0
    
    def test_mid_gray_luminance(self):
        """Test luminance of mid-gray."""
        result = get_luminance(128, 128, 128)
        assert 0.4 < result < 0.6


class TestPickShadeFromLuminance:
    def test_dark_returns_light(self):
        """Test dark pixels return light shade."""
        r, g, b = pick_shade_from_luminance(0, 0, 0)
        assert r == 0xFF
        assert g == 0xFF
        assert b == 0xFF
    
    def test_light_returns_dark(self):
        """Test light pixels return dark shade."""
        r, g, b = pick_shade_from_luminance(255, 255, 255)
        assert r == 0x00
        assert g == 0x00
        assert b == 0x00


class TestDesaturate:
    def test_desaturate_colors(self):
        """Test desaturate converts to gray."""
        r, g, b = desaturate(100, 150, 200)
        assert r == g == b == 150  # (100+200)/2


class TestInvert:
    def test_invert_black(self):
        """Test inverting black gives white."""
        r, g, b = invert(0, 0, 0)
        assert r == 255
        assert g == 255
        assert b == 255
    
    def test_invert_white(self):
        """Test inverting white gives black."""
        r, g, b = invert(255, 255, 255)
        assert r == 0
        assert g == 0
        assert b == 0


class TestAverage:
    def test_average_same(self):
        """Test averaging same values."""
        r, g, b = average(100, 100, 100, 100, 100, 100)
        assert r == 100
        assert g == 100
        assert b == 100
    
    def test_average_different(self):
        """Test averaging different values."""
        r, g, b = average(100, 150, 200, 200, 100, 50)
        assert r == 150
        assert g == 125
        assert b == 125
