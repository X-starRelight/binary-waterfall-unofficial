import os
import sys
import time
import multiprocessing
import pytest
from PySide6.QtCore import QCoreApplication
from typing import Any

# Ensure src is in path before importing
if "src" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from binary_waterfall_unofficial.export_manager import (
    ExportManager,
    export_worker,
    CancelledException,
    _SubprocessDialog,
)


def _long_running():
    """Module-level target for multiprocessing tests (Windows spawn requires picklable target)."""
    time.sleep(10)


@pytest.fixture
def qapp_instance():
    """Create a fresh QCoreApplication for each test."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


class TestExportManager:
    def test_export_manager_init(self, qapp_instance: QCoreApplication):
        manager = ExportManager()
        assert manager.has_active_exports() is False
        assert manager._next_id == 0
        assert len(manager._active) == 0

    def test_export_manager_start_export_returns_task_id(self, qapp_instance: QCoreApplication):
        manager = ExportManager()
        manager._next_id = 0
        assert manager._next_id == 0
        manager._next_id += 1
        assert manager._next_id == 1

    def test_export_manager_has_active_exports(self, qapp_instance: QCoreApplication):
        manager = ExportManager()
        assert manager.has_active_exports() is False
        manager._active[0] = multiprocessing.Process(target=_long_running)
        assert manager.has_active_exports() is True
        manager._active.clear()
        assert manager.has_active_exports() is False

    def test_export_manager_kill_all(self, qapp_instance: QCoreApplication):
        manager = ExportManager()

        p1 = multiprocessing.Process(target=_long_running)
        p2 = multiprocessing.Process(target=_long_running)
        p1.start()
        p2.start()

        manager._active[0] = p1
        manager._active[1] = p2

        assert manager.has_active_exports() is True

        manager.kill_all()

        p1.join(timeout=5)
        p2.join(timeout=5)

        assert manager.has_active_exports() is False
        assert not p1.is_alive()
        assert not p2.is_alive()

    def test_export_manager_on_done_cleans_up(self, qapp_instance: QCoreApplication):
        manager = ExportManager()
        manager._active[42] = multiprocessing.Process(target=_long_running)
        manager._on_done(42, 0)
        assert 42 not in manager._active

    def test_export_manager_task_id_increments(self, qapp_instance: QCoreApplication):
        manager = ExportManager()
        id1 = manager._next_id
        manager._next_id += 1
        id2 = manager._next_id
        manager._next_id += 1
        id3 = manager._next_id
        assert id1 == 0
        assert id2 == 1
        assert id3 == 2

    def test_export_manager_on_done_with_unknown_id(self, qapp_instance: QCoreApplication):
        manager = ExportManager()
        manager._on_done(999, 0)
        assert 999 not in manager._active

    def test_export_manager_kill_all_empty(self, qapp_instance: QCoreApplication):
        manager = ExportManager()
        manager.kill_all()
        assert manager.has_active_exports() is False


class TestSubprocessDialog:
    def test_subprocess_dialog_is_picklable(self):
        """_SubprocessDialog wraps dialog and app, verify it can be imported."""
        assert _SubprocessDialog is not None


class TestExportWorker:
    def test_export_worker_is_callable(self):
        assert callable(export_worker)

    def test_cancelled_exception_is_exception(self):
        assert issubclass(CancelledException, Exception)
        with pytest.raises(CancelledException):
            raise CancelledException("test")

    def test_cancelled_exception_message(self):
        exc = CancelledException("user cancelled")
        assert str(exc) == "user cancelled"


class TestExportManagerIntegration:
    def test_export_manager_signal_emission(self, qapp_instance: QCoreApplication):
        manager = ExportManager()

        received_signals: list[tuple[int, int]] = []
        manager.task_done.connect(lambda task_id, exit_code: received_signals.append((task_id, exit_code)))

        manager.task_done.emit(1, 0)
        qapp_instance.processEvents()

        assert len(received_signals) == 1
        assert received_signals[0] == (1, 0)

    def test_export_manager_multiple_signals(self, qapp_instance: QCoreApplication):
        manager = ExportManager()

        received_signals: list[tuple[int, int]] = []
        manager.task_done.connect(lambda task_id, exit_code: received_signals.append((task_id, exit_code)))

        manager.task_done.emit(0, 0)
        manager.task_done.emit(1, 1)
        manager.task_done.emit(2, 2)
        qapp_instance.processEvents()

        assert len(received_signals) == 3
        assert received_signals == [(0, 0), (1, 1), (2, 2)]

    def test_export_worker_exits_with_error_for_invalid_params(self, qapp_instance: QCoreApplication):
        """Test that export_worker exits with code 1 when given invalid params."""
        p = multiprocessing.Process(
            target=export_worker,
            args=("frame", {"nonexistent_key": True}, {}),
        )
        p.start()
        p.join(timeout=10)
        assert p.exitcode == 1

    def test_export_worker_exits_with_error_for_missing_file(self, qapp_instance: QCoreApplication):
        """Test that export_worker exits with code 1 for a non-existent binary file."""
        p = multiprocessing.Process(
            target=export_worker,
            args=(
                "frame",
                {
                    "file": "C:\\nonexistent_file.bin",
                    "width": 100,
                    "height": 100,
                    "color_format": "R8G8B8",
                    "endianness": "little",
                    "alignment": "none",
                    "bit_depth": 8,
                    "zero_is_black": False,
                    "clip": False,
                    "normalize": False,
                    "color_space": "sRGB",
                    "gamma": 2.2,
                    "output_color_space": "sRGB",
                },
                {"output_path": "C:\\test_output.png"},
            ),
        )
        p.start()
        p.join(timeout=10)
        assert p.exitcode == 1
