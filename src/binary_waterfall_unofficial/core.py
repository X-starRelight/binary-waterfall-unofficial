import os
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from . import window, constants


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
