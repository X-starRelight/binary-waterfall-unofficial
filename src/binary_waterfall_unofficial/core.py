import os
import sys
import multiprocessing
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from . import window, constants


def attach_console() -> None:
    """Attach to a parent console when launched from one, create none otherwise.

    - Windows: GUI subsystem binaries never own a console; attach to the parent
      console (cmd/PowerShell) when present, otherwise leave stdout/stderr as-is.
    - macOS/Linux: launching from a terminal already inherits the terminal's
      stdout/stderr, and launching from the desktop simply has no console, so
      nothing needs to be done.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        if kernel32.AttachConsole(-1):  # ATTACH_PARENT_PROCESS
            if sys.stdout is None:
                sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            if sys.stderr is None:
                sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            if sys.stdin is None:
                sys.stdin = open("CONIN$", "r", encoding="utf-8")
    except OSError:
        pass


def _setup_app(app: QApplication) -> None:
    """配置应用样式和调色板"""
    app.setStyle("fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(constants.COLORS["background"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(constants.COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(constants.COLORS["foreground"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(constants.COLORS["foreground"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(constants.COLORS["foreground"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(constants.COLORS["button_text"]))
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(constants.COLORS["link"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(constants.COLORS["link"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

    palette.setColorGroup(
        QPalette.ColorGroup.Disabled,
        palette.windowText(),
        QColor(constants.COLORS["disabled"]),
        palette.light(),
        palette.dark(),
        palette.mid(),
        QColor(constants.COLORS["disabled_text"]),
        palette.brightText(),
        QColor(constants.COLORS["disabled"]),
        palette.window()
    )

    app.setPalette(palette)


def main(args: list[str]):
    multiprocessing.freeze_support()
    attach_console()

    if constants.HAS_SPLASH:
        import pyi_splash # pyright: ignore[reportMissingModuleSource]
        pyi_splash.close()

    # Apply dark mode on Windows systems
    if constants.PLATFORM == constants.PlatformCode.WINDOWS: # pyright: ignore[reportUnnecessaryComparison]
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"

    # QApplication 只能创建一次
    app = QApplication(args)
    _setup_app(app)

    win = window.MyQMainWindow()
    win.show()
    app.exec()


def run():
    main(sys.argv)
