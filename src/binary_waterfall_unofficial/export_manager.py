from __future__ import annotations

import sys
import multiprocessing
import threading
from typing import Any

from PySide6.QtCore import QObject, QTimer, Qt, Signal
from PySide6.QtWidgets import QApplication, QProgressDialog, QMessageBox


class CancelledException(Exception):
    pass


class _SubprocessDialog:
    """QProgressDialog 的鸭子类型包装器。

    每次更新后调用 app.processEvents()，
    使子进程 UI 保持响应，无需专门的事件循环线程。
    """

    def __init__(self, dialog: QProgressDialog, app: QApplication) -> None:
        self._d = dialog
        self._app = app

    def setValue(self, value: int) -> None:
        self._d.setValue(value)
        self._app.processEvents()

    def setLabelText(self, text: str) -> None:
        self._d.setLabelText(text)
        self._app.processEvents()

    def setMaximum(self, maximum: int) -> None:
        self._d.setMaximum(maximum)
        self._app.processEvents()

    def setAutoReset(self, enable: bool) -> None:
        self._d.setAutoReset(enable)

    def wasCanceled(self) -> bool:
        return self._d.wasCanceled()


def export_worker(
    export_type: str,
    bw_params: dict[str, Any],
    export_params: dict[str, Any],
) -> None:
    """每个导出子进程的入口函数。

    退出码：
        0 = 成功
        1 = 错误（子进程内部已弹出错误对话框）
        2 = 用户取消
    """
    app = QApplication.instance() or QApplication(sys.argv)

    from . import generators
    bw = generators.BinaryWaterfall(**bw_params)

    from .outputs import Renderer
    renderer = Renderer(bw)

    from .lang import L
    progress = QProgressDialog(L.export.export_preparing, L.dialog.cancel, 0, 100)
    progress.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress.setWindowFlags(
        progress.windowFlags()
        | Qt.WindowType.WindowStaysOnTopHint
        | Qt.WindowType.WindowContextHelpButtonHint
    )
    progress.setWindowTitle(L.dialog.export_progress_title.format(type=export_type))
    progress.setMinimumWidth(350)
    progress.show()
    app.processEvents()

    dialog = _SubprocessDialog(progress, app) # pyright: ignore[reportArgumentType]

    try:
        if export_type == "frame":
            renderer.export_frame(**export_params)
        elif export_type == "audio":
            renderer.export_audio(**export_params)
        elif export_type == "sequence":
            renderer.export_sequence(**export_params, progress_dialog=dialog) # pyright: ignore[reportArgumentType]
        elif export_type == "video":
            renderer.export_video(**export_params, progress_dialog=dialog) # pyright: ignore[reportArgumentType]

        progress.close()

        if not dialog.wasCanceled():
            _map = {
                "frame": L.dialog.export_complete_frame,
                "audio": L.dialog.export_complete_audio,
                "sequence": L.dialog.export_complete_sequence,
                "video": L.dialog.export_complete_video,
            }
            QMessageBox.information(
                None,
                L.dialog.export_complete,
                _map.get(export_type, L.dialog.export_complete),
            )
            sys.exit(0)
        else:
            _abort_map = {
                "frame": getattr(L.dialog, "export_aborted_frame", L.dialog.export_aborted),
                "audio": getattr(L.dialog, "export_aborted_frame", L.dialog.export_aborted),
                "sequence": getattr(L.dialog, "export_aborted_sequence", L.dialog.export_aborted),
                "video": getattr(L.dialog, "export_aborted_video", L.dialog.export_aborted),
            }
            QMessageBox.warning(
                None,
                L.dialog.export_aborted,
                _abort_map.get(export_type, L.dialog.export_aborted),
            )
            sys.exit(2)

    except CancelledException:
        progress.close()
        QMessageBox.warning(
            None,
            L.dialog.export_aborted,
            L.dialog.export_aborted,
        )
        sys.exit(2)

    except Exception as e:
        progress.close()
        _err_map = {
            "frame": L.dialog.export_error_frame,
            "audio": L.dialog.export_error_audio,
            "sequence": L.dialog.export_error_sequence,
            "video": L.dialog.export_error_video,
        }
        msg = _err_map.get(export_type, L.dialog.export_error)
        if "{error}" in msg:
            msg = msg.format(error=str(e))
        QMessageBox.critical(
            None,
            L.dialog.export_error,
            msg,
        )
        sys.exit(1)


class ExportManager(QObject):
    """在主进程中管理并发导出子进程。"""

    task_done = Signal(int, int)  # (task_id, exit_code)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._next_id: int = 0
        self._active: dict[int, multiprocessing.Process] = {}

    def start_export(
        self,
        export_type: str,
        bw_params: dict[str, Any],
        export_params: dict[str, Any],
    ) -> int:
        """启动一个子进程导出任务，返回 task_id。"""
        task_id = self._next_id
        self._next_id += 1

        p = multiprocessing.Process(
            target=export_worker,
            args=(export_type, bw_params, export_params),
            daemon=True,
        )
        p.start()
        self._active[task_id] = p

        t = threading.Thread(target=self._wait, args=(task_id, p), daemon=True)
        t.start()

        return task_id

    def _wait(self, task_id: int, process: multiprocessing.Process) -> None:
        process.join()
        QTimer.singleShot(0, lambda: self._on_done(task_id, process.exitcode or 0))

    def _on_done(self, task_id: int, exit_code: int) -> None:
        self._active.pop(task_id, None)
        self.task_done.emit(task_id, exit_code)

    def has_active_exports(self) -> bool:
        return len(self._active) > 0

    def kill_all(self) -> None:
        for p in self._active.values():
            p.terminate()
        self._active.clear()
