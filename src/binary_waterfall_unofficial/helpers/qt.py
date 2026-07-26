from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import QProgressDialog
from proglog import ProgressBarLogger # pyright: ignore[reportMissingTypeStubs]
from ..lang import L


# Custom proglog class for QProgressDialogs
#   Handles updating the progress in a QProgressDialog
#   Designed to work with moviepy's export option
class QtBarLoggerMoviepy(ProgressBarLogger):
    def __init__(self, progress_dialog: QProgressDialog, init_state: dict[str, Any] | None = None, bars: dict[str, Any] | None = None, ignored_bars: list[str] | None = None,
                 logged_bars: str = 'all', min_time_interval: int = 0, ignore_bars_under: int = 0):
        super().__init__(init_state, bars, ignored_bars, logged_bars, min_time_interval, ignore_bars_under) # pyright: ignore[reportUnknownMemberType]
        if progress_dialog is None: # pyright: ignore[reportUnnecessaryComparison]
            raise RuntimeError('progress_dialog 参数不应该传入 None ')

        self.progress_dialog: QProgressDialog | None = progress_dialog
        self.progress_dialog.setMaximum(100)
        self.set_progress(0)

    def _safe_set_label(self, text: str) -> None:
        try:
            if self.progress_dialog is not None:
                self.progress_dialog.setLabelText(text)
        except RuntimeError:
            self.progress_dialog = None

    def _safe_set_value(self, value: int) -> None:
        try:
            if self.progress_dialog is not None:
                self.progress_dialog.setValue(value)
        except RuntimeError:
            self.progress_dialog = None

    def _safe_set_maximum(self, max_val: int) -> None:
        try:
            if self.progress_dialog is not None:
                self.progress_dialog.setMaximum(max_val)
        except RuntimeError:
            self.progress_dialog = None

    def set_progress(self, value: int) -> None:
        self._safe_set_value(value)

    def callback(self, **changes: Any) -> None:
        if "message" in changes:
            message: str = changes["message"]

            if "Building video" in message:
                self._safe_set_label(L.export.building_video)
            elif "Writing audio" in message:
                self._safe_set_label(L.export.writing_audio)
            elif "Done." in message:
                self._safe_set_label(L.export.done_writing_audio)
            elif "Writing video" in message:
                self._safe_set_label(L.export.writing_video)
            elif "Done !" in message:
                self._safe_set_label(L.export.done_writing_video)
            elif "video ready" in message:
                self._safe_set_label(L.export.video_is_ready)
            else:
                self._safe_set_label(message)

    def bars_callback(self, bar: str, attr: str, value: int, old_value: int | None = None) -> None:
        self._safe_set_maximum(self.bars[bar]["total"]) # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        self.set_progress(value)
