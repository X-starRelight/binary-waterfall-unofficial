from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import QProgressDialog
from proglog import ProgressBarLogger # pyright: ignore[reportMissingTypeStubs]


# Custom proglog class for QProgressDialogs
#   Handles updating the progress in a QProgressDialog
#   Designed to work with moviepy's export option
class QtBarLoggerMoviepy(ProgressBarLogger):
    def __init__(self, progress_dialog: QProgressDialog, init_state: dict[str, Any] | None = None, bars: dict[str, Any] | None = None, ignored_bars: list[str] | None = None,
                 logged_bars: str = 'all', min_time_interval: int = 0, ignore_bars_under: int = 0):
        super().__init__(init_state, bars, ignored_bars, logged_bars, min_time_interval, ignore_bars_under) # pyright: ignore[reportUnknownMemberType]
        self.progress_dialog = progress_dialog
        self.progress_dialog.setMaximum(100)
        self.set_progress(0)

    def set_progress(self, value: int) -> None:
        self.progress_dialog.setValue(value)

    def callback(self, **changes: Any) -> None:
        if "message" in changes:
            message: str = changes["message"].strip("Moviepy - ")

            if "Building video" in message:
                self.progress_dialog.setLabelText("(1/3) Building video...")
            elif "Writing audio" in message:
                self.progress_dialog.setLabelText("(2/3) Writing audio...")
            elif "Done." in message:
                self.progress_dialog.setLabelText("Done writing audio!")
            elif "Writing video" in message:
                self.progress_dialog.setLabelText("(3/3) Writing video...")
            elif "Done !" in message:
                self.progress_dialog.setLabelText("Done writing video!")
            elif "video ready" in message:
                self.progress_dialog.setLabelText("Video is ready!")
            else:
                self.progress_dialog.setLabelText(message)

    def bars_callback(self, bar: str, attr: str, value: int, old_value: int | None = None) -> None:
        self.progress_dialog.setMaximum(self.bars[bar]["total"]) # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        self.set_progress(value)
