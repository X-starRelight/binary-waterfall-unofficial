import os
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

from . import window, constants


# Main window class
#   Handles variables related to the main window.
#   Any actual program functionality or additional dialogs are
#   handled using different classes
class MainWindow:
    def __init__(self, qt_args: list[str]):
        # Apply dark mode on Windows systems
        if constants.PLATFORM == constants.PlatformCode.WINDOWS: # pyright: ignore[reportUnnecessaryComparison]
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"

        # Make main objects
        self.app = QApplication(qt_args)
        self.window = window.MyQMainWindow()

        # Setup colors
        self.app.setStyle("fusion")
        self.palette = QPalette()
        self.palette.setColor(QPalette.ColorRole.Window, QColor(constants.COLORS["background"]))
        self.palette.setColor(QPalette.ColorRole.WindowText, QColor(constants.COLORS["text"]))
        self.palette.setColor(QPalette.ColorRole.Base, QColor(constants.COLORS["foreground"]))
        self.palette.setColor(QPalette.ColorRole.AlternateBase, QColor(constants.COLORS["foreground"]))
        self.palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.black)
        self.palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        self.palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        self.palette.setColor(QPalette.ColorRole.Button, QColor(constants.COLORS["foreground"]))
        self.palette.setColor(QPalette.ColorRole.ButtonText, QColor(constants.COLORS["button_text"]))
        self.palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        self.palette.setColor(QPalette.ColorRole.Link, QColor(constants.COLORS["link"]))
        self.palette.setColor(QPalette.ColorRole.Highlight, QColor(constants.COLORS["link"]))
        self.palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

        self.palette.setColorGroup(
            QPalette.ColorGroup.Disabled,
            self.palette.windowText(),
            QColor(constants.COLORS["disabled"]),
            self.palette.light(),
            self.palette.dark(),
            self.palette.mid(),
            QColor(constants.COLORS["disabled_text"]),
            self.palette.brightText(),
            QColor(constants.COLORS["disabled"]),
            self.palette.window()
        )

        self.app.setPalette(self.palette)

    def run(self):
        self.window.show()
        self.app.exec()


def main(args: list[str]):
    if constants.HAS_SPLASH:
        import pyi_splash # pyright: ignore[reportMissingModuleSource]
        pyi_splash.close()

    main_window = MainWindow(args)
    main_window.run()


def run():
    main(sys.argv)
