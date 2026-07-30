import os
import sys
import tempfile
import threading
import pytest

# Ensure src is in path before importing
if "src" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from binary_waterfall_unofficial.generators import BinaryWaterfall


@pytest.fixture
def test_file():
    """Create a temporary test file with enough data for frame generation."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
        # Create a file large enough for 8x8 frames with various color formats
        f.write(bytes(range(256)) * 1000)
        test_file = f.name
    
    yield test_file
    
    if os.path.exists(test_file):
        try:
            os.unlink(test_file)
        except PermissionError:
            pass  # File might still be in use


class TestBinaryWaterfallContextManager:
    def test_context_manager_enter_exit(self, test_file: str):
        """Test context manager properly enters and exits."""
        with BinaryWaterfall(filename=test_file) as bw:
            assert bw.filename is not None
            assert bw.file is not None
        
        # After context exit, file should be closed
        assert bw.file is None
        assert bw.filename is None
    
    def test_context_manager_cleanup_temp_dir(self, test_file: str):
        """Test context manager cleans up temporary directory."""
        temp_dir: str = ""
        with BinaryWaterfall(filename=test_file) as bw:
            temp_dir = bw.temp_dir
            assert os.path.exists(temp_dir)
        
        # After context exit, temp dir should be cleaned up
        assert not os.path.exists(temp_dir)
    
    def test_context_manager_exception_handling(self, test_file: str):
        """Test context manager handles exceptions properly."""
        temp_dir: str = ""
        try:
            with BinaryWaterfall(filename=test_file) as bw:
                temp_dir = bw.temp_dir
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Temp dir should still be cleaned up
        assert not os.path.exists(temp_dir)


class TestBinaryWaterfallSetFilename:
    def test_set_filename_closes_old_file(self, test_file: str):
        """Test that opening a new file closes the old one."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(bytes(range(256)) * 10)
            second_file = f.name
        
        try:
            bw = BinaryWaterfall(filename=test_file)
            assert bw.file is not None
            old_file = bw.file
            
            bw.set_filename(second_file)
            # Old file should be closed
            assert old_file.closed
            assert bw.file is not None
            assert bw.file is not old_file
            
            bw.cleanup()
        finally:
            if os.path.exists(second_file):
                os.unlink(second_file)
    
    def test_set_filename_none_closes_file(self, test_file: str):
        """Test that setting filename to None closes the file."""
        bw = BinaryWaterfall(filename=test_file)
        assert bw.file is not None
        
        bw.set_filename(None)
        assert bw.file is None
        assert bw.filename is None
        
        bw.cleanup()
    
    def test_set_filename_nonexistent_raises(self, test_file: str):
        """Test that setting nonexistent file raises FileNotFoundError."""
        bw = BinaryWaterfall()
        
        with pytest.raises(FileNotFoundError):
            bw.set_filename("/nonexistent/file.bin")
        
        bw.cleanup()


class TestBinaryWaterfallThreadSafety:
    def test_concurrent_file_access(self, test_file: str):
        """Test that concurrent file access doesn't corrupt state."""
        bw = BinaryWaterfall(filename=test_file)
        
        errors: list[str] = []
        
        def read_file():
            try:
                for _ in range(50):
                    data = bw.get_file_bytes(0, 100)
                    if len(data) != 100:
                        errors.append("Invalid data length")
            except Exception as e:
                errors.append(str(e))
        
        def modify_state():
            try:
                for _ in range(50):
                    bw.width = 8
                    bw.height = 8
            except Exception as e:
                errors.append(str(e))
        
        threads = [
            threading.Thread(target=read_file),
            threading.Thread(target=modify_state),
            threading.Thread(target=read_file),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        bw.cleanup()


class TestBinaryWaterfallFrameGeneration:
    def test_frame_generation_basic(self, test_file: str):
        """Test that frame generation produces correct output size."""
        bw = BinaryWaterfall(
            filename=test_file,
            width=8,
            height=8,
            color_format_string="rgb",
            num_channels=1,
            sample_bytes=1,
            sample_rate=44100
        )
        
        frame = bw.get_frame_bytestring(0)
        expected_size = 8 * 8 * 3  # width * height * 3 bytes RGB
        assert len(frame) == expected_size
        bw.cleanup()
    
    def test_frame_generation_with_playhead(self, test_file: str):
        """Test frame generation with playhead visible."""
        bw = BinaryWaterfall(
            filename=test_file,
            width=8,
            height=8,
            color_format_string="rgb",
            playhead_visible=True
        )
        
        frame = bw.get_frame_bytestring(0)
        assert len(frame) == 8 * 8 * 3
        bw.cleanup()
    
    def test_frame_generation_different_formats(self, test_file: str):
        """Test frame generation with different color formats."""
        formats = ["rgb", "bgr", "w", "RGx", "rGx"]  # Valid color format strings
        
        for fmt in formats:
            bw = BinaryWaterfall(
                filename=test_file,
                width=4,
                height=4,
                color_format_string=fmt
            )
            
            frame = bw.get_frame_bytestring(0)
            assert len(frame) == 4 * 4 * 3  # Always RGB output
            bw.cleanup()
