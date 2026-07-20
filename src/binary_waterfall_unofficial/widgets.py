from __future__ import annotations
from collections.abc import Callable
from PyQt6.QtCore import QEvent, QSize
from PyQt6.QtWidgets import QAbstractButton, QSlider, QWidget, QStyle
from PyQt6.QtGui import QEnterEvent, QMouseEvent, QPainter, QPaintEvent, QPixmap


# Custom image-based button
#   Allows for very fancy custom buttons
class ImageButton(QAbstractButton):
    def __init__(self,
                 pixmap: QPixmap,
                 pixmap_hover: QPixmap,
                 pixmap_pressed: QPixmap,
                 scale: float = 1.0,
                 parent: QWidget | None = None
                 ) -> None:
        super(ImageButton, self).__init__(parent)
        self.scale = scale
        self.img_height: int = 0
        self.img_width: int = 0
        self.pixmap_pressed: QPixmap | None = None
        self.pixmap_hover: QPixmap | None = None
        self.pixmap: QPixmap | None = None

        self.change_pixmaps(
            pixmap=pixmap,
            pixmap_hover=pixmap_hover,
            pixmap_pressed=pixmap_pressed
        )

        self.pressed.connect(self.update) # pyright: ignore[reportUnknownMemberType]
        self.released.connect(self.update) # pyright: ignore[reportUnknownMemberType]

    def change_pixmaps(self,
                       pixmap: QPixmap,
                       pixmap_hover: QPixmap,
                       pixmap_pressed: QPixmap
                       ) -> None:
        self.pixmap = pixmap
        self.pixmap_hover = pixmap_hover
        self.pixmap_pressed = pixmap_pressed

        self.img_width = round(self.pixmap.width() * self.scale)
        self.img_height = round(self.pixmap.height() * self.scale)

        self.update()

    def paintEvent(self, e: QPaintEvent) -> None: # pyright: ignore[reportIncompatibleMethodOverride]
        if self.isDown():
            pix = self.pixmap_pressed
        elif self.underMouse():
            pix = self.pixmap_hover
        else:
            pix = self.pixmap

        if pix is None:
            return

        painter = QPainter(self)
        painter.drawPixmap(e.rect(), pix)

    def enterEvent(self, e: QEnterEvent | None) -> None: # pyright: ignore[reportIncompatibleMethodOverride]
        self.update()

    def leaveEvent(self, e: QEvent) -> None: # pyright: ignore[reportIncompatibleMethodOverride]
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(self.img_width, self.img_height)


# Custom seekbar class
#   A customized slider
class SeekBar(QSlider):
    def __init__(self,
                 position_changed_function: Callable[[int], None] | None = None,
                 parent: QWidget | None = None
                 ) -> None:
        super(SeekBar, self).__init__(parent)

        self.position_changed_function = position_changed_function

    def set_position_changed_function(self, position_changed_function: Callable[[int], None] | None) -> None:
        self.position_changed_function = position_changed_function

    def set_position_if_set(self, value: int) -> None:
        if self.position_changed_function is None:
            self.setValue(value)
        else:
            self.position_changed_function(value)

    def mousePressEvent(self, ev: QMouseEvent) -> None: # pyright: ignore[reportIncompatibleMethodOverride]
        value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), int(ev.position().x()), self.width())
        self.set_position_if_set(value)

    def mouseMoveEvent(self, ev: QMouseEvent) -> None: # type: ignore
        value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), int(ev.position().x()), self.width())
        self.set_position_if_set(value)
