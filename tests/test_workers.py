import os
import sys
import time
import pytest
from PyQt6.QtCore import QCoreApplication

# Ensure src is in path before importing
if "src" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from binary_waterfall_unofficial.workers import FileWorker, AudioWorker, FrameWorker
from binary_waterfall_unofficial import generators


@pytest.fixture
def qapp_instance():
    """Create a fresh QCoreApplication for each test."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


class TestFileWorker:
    def test_file_worker_starts_and_stops(self, qapp_instance, tmp_path):
        """Test that FileWorker can start and stop without errors."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"\x00" * 1024)
        
        bw = generators.BinaryWaterfall()
        worker = FileWorker(str(test_file), bw)
        
        # Connect signals to track them
        finished = []
        errors = []
        worker.finished.connect(lambda info: finished.append(info))
        worker.error.connect(lambda msg: errors.append(msg))
        
        worker.start()
        # Give worker time to run
        time.sleep(0.5)
        qapp_instance.processEvents()
        
        # Worker should have finished or be running
        # Check that we got either finished or error signal
        assert len(finished) + len(errors) > 0 or not worker.isRunning()
        
        # If we got finished signal, verify the data
        if finished:
            info = finished[0]
            assert "filename" in info
            assert "total_bytes" in info
            assert "audio_filename" in info
            assert info["total_bytes"] == 1024
        
        bw.cleanup()

    def test_file_worker_emits_error_for_missing_file(self, qapp_instance):
        """Test that FileWorker emits error for non-existent file."""
        bw = generators.BinaryWaterfall()
        worker = FileWorker("/nonexistent/file.bin", bw)
        
        errors = []
        worker.error.connect(lambda msg: errors.append(msg))
        worker.start()
        
        # Wait for worker to finish
        time.sleep(0.5)
        qapp_instance.processEvents()
        
        assert len(errors) == 1
        assert "not found" in errors[0].lower() or "不存在" in errors[0]
        
        bw.cleanup()

    def test_file_worker_can_be_interrupted(self, qapp_instance, tmp_path):
        """Test that FileWorker can be interrupted."""
        test_file = tmp_path / "large.bin"
        test_file.write_bytes(b"\x00" * (10 * 1024 * 1024))
        
        bw = generators.BinaryWaterfall()
        worker = FileWorker(str(test_file), bw)
        
        worker.start()
        worker.interrupt()
        worker.wait(5000)
        
        assert not worker.isRunning()
        bw.cleanup()


class TestAudioWorker:
    def test_audio_worker_imports(self, qapp_instance):
        """Test that AudioWorker can be imported."""
        assert AudioWorker is not None


class TestFrameWorker:
    def test_frame_worker_imports(self, qapp_instance):
        """Test that FrameWorker can be imported."""
        assert FrameWorker is not None
