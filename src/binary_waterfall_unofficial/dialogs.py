from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout, QLabel, QDialog, QDialogButtonBox, QComboBox, QLineEdit, QCheckBox, QSpinBox,
    QDoubleSpinBox, QMessageBox, QWidget
)
from PyQt6.QtGui import QPixmap, QIcon

from .constants.enums import AlignmentCode, AudioCodecCode, EncoderPresetCode, ImageFormatCode, VideoCodecCode
from . import constants
from .lang import L


# Audio settings input window
#   User interface to set the audio settings (for computation)
class AudioSettings(QDialog):
    def __init__(self,
                 num_channels: int,
                 sample_bytes: int,
                 sample_rate: int,
                 volume: int,
                 endianness: constants.EndiannessCode = constants.EndiannessCode.LITTLE,
                 parent: QWidget | None = None
                 ) -> None:
        super().__init__(parent=parent)
        
        self.setWindowTitle(L.dialog.audio_settings)
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)

        self.num_channels = num_channels
        self.sample_bytes = sample_bytes
        self.sample_rate = sample_rate
        self.volume = volume
        self.endianness = endianness

        self.channels_label = QLabel(L.audio.channels)
        self.channels_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.channels_entry = QComboBox()
        self.channels_entry.addItems([L.audio.mono, L.audio.stereo]) # pyright: ignore[reportUnknownMemberType]
        if self.num_channels == 1:
            self.channels_entry.setCurrentIndex(0)
        elif self.num_channels == 2:
            self.channels_entry.setCurrentIndex(1)
        self.channels_entry.currentIndexChanged.connect(self.channel_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.sample_size_label = QLabel(L.audio.sample_size)
        self.sample_size_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.sample_size_entry = QComboBox()
        self.sample_size_entry.addItems(["8-bit", "16-bit", "24-bit", "32-bit"]) # pyright: ignore[reportUnknownMemberType]
        if self.sample_bytes == 1:
            self.sample_size_entry.setCurrentIndex(0)
        elif self.sample_bytes == 2:
            self.sample_size_entry.setCurrentIndex(1)
        elif self.sample_bytes == 3:
            self.sample_size_entry.setCurrentIndex(2)
        elif self.sample_bytes == 4:
            self.sample_size_entry.setCurrentIndex(3)
        self.sample_size_entry.currentIndexChanged.connect(self.sample_size_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.sample_rate_label = QLabel(L.audio.sample_rate)
        self.sample_rate_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.sample_rate_entry = QSpinBox()
        self.sample_rate_entry.setMinimum(1)
        self.sample_rate_entry.setMaximum(192000)
        self.sample_rate_entry.setSingleStep(1000)
        self.sample_rate_entry.setSuffix("Hz")
        self.sample_rate_entry.setValue(self.sample_rate)
        self.sample_rate_entry.valueChanged.connect(self.sample_rate_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.volume_label = QLabel(L.audio.file_volume)
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.volume_entry = QSpinBox()
        self.volume_entry.setMinimum(0)
        self.volume_entry.setMaximum(100)
        self.volume_entry.setSingleStep(5)
        self.volume_entry.setSuffix("%")
        self.volume_entry.setValue(self.volume)
        self.volume_entry.valueChanged.connect(self.volume_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.endianness_label = QLabel(L.audio.endianness)
        self.endianness_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.endianness_entry = QComboBox()
        self.endianness_entry.addItems([L.audio.little_endian, L.audio.big_endian]) # pyright: ignore[reportUnknownMemberType]
        if self.endianness == constants.EndiannessCode.LITTLE:
            self.endianness_entry.setCurrentIndex(0)
        elif self.endianness == constants.EndiannessCode.BIG:
            self.endianness_entry.setCurrentIndex(1)
        self.endianness_entry.currentIndexChanged.connect(self.endianness_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.confirm_buttons.accepted.connect(self.accept) # pyright: ignore[reportUnknownMemberType]
        self.confirm_buttons.rejected.connect(self.reject) # pyright: ignore[reportUnknownMemberType]

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.channels_label, 0, 0)
        self.main_layout.addWidget(self.channels_entry, 0, 1)
        self.main_layout.addWidget(self.sample_size_label, 1, 0)
        self.main_layout.addWidget(self.sample_size_entry, 1, 1)
        self.main_layout.addWidget(self.sample_rate_label, 2, 0)
        self.main_layout.addWidget(self.sample_rate_entry, 2, 1)
        self.main_layout.addWidget(self.volume_label, 3, 0)
        self.main_layout.addWidget(self.volume_entry, 3, 1)
        self.main_layout.addWidget(self.endianness_label, 4, 0)
        self.main_layout.addWidget(self.endianness_entry, 4, 1)
        self.main_layout.addWidget(self.confirm_buttons, 5, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def get_audio_settings(self) -> dict[str, int | constants.EndiannessCode]:
        result: dict[str, int | constants.EndiannessCode] = dict()
        result["num_channels"] = self.num_channels
        result["sample_bytes"] = self.sample_bytes
        result["sample_rate"] = self.sample_rate
        result["volume"] = self.volume
        result["endianness"] = self.endianness

        return result

    def channel_entry_changed(self, idx: int) -> None:
        if idx == 0:
            self.num_channels = 1
        elif idx == 1:
            self.num_channels = 2

    def sample_size_entry_changed(self, idx: int) -> None:
        if idx == 0:
            self.sample_bytes = 1
        elif idx == 1:
            self.sample_bytes = 2
        elif idx == 2:
            self.sample_bytes = 3
        elif idx == 3:
            self.sample_bytes = 4

    def sample_rate_entry_changed(self, value: int) -> None:
        self.sample_rate = value

    def volume_entry_changed(self, value: int) -> None:
        self.volume = value

    def endianness_entry_changed(self, idx: int) -> None:
        if idx == 0:
            self.endianness = constants.EndiannessCode.LITTLE
        elif idx == 1:
            self.endianness = constants.EndiannessCode.BIG

    def resize_window(self) -> None:
        self.setFixedSize(self.sizeHint())


# Video settings input window
#   User interface to set the video settings (for computation)
class VideoSettings(QDialog):
    def __init__(self,
                 bw: Any,
                 width: int,
                 height: int,
                 color_format: str,
                 flip_v: bool,
                 flip_h: bool,
                 alignment: constants.AlignmentCode,
                 playhead_visible: bool,
                 parent: QWidget | None = None
                 ) -> None:
        super().__init__(parent=parent)
        
        self.setWindowTitle(L.dialog.video_settings)
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)

        self.bw = bw

        self.entry_width = width
        self.entry_height = height
        self.color_format = color_format
        self.flip_v = flip_v
        self.flip_h = flip_h
        self.alignment = alignment
        self.playhead_visible = playhead_visible

        self.width_label = QLabel(L.video.width)
        self.width_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.width_entry = QSpinBox()
        self.width_entry.setMinimum(4)
        self.width_entry.setMaximum(1024)
        self.width_entry.setSingleStep(4)
        self.width_entry.setSuffix("px")
        self.width_entry.setValue(self.entry_width)
        self.width_entry.valueChanged.connect(self.width_entry_changed)# pyright: ignore[reportUnknownMemberType]

        self.height_label = QLabel(L.video.height)
        self.height_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.height_entry = QSpinBox()
        self.height_entry.setMinimum(4)
        self.height_entry.setMaximum(1024)
        self.height_entry.setSingleStep(4)
        self.height_entry.setSuffix("px")
        self.height_entry.setValue(self.entry_height)
        self.height_entry.valueChanged.connect(self.height_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.color_format_label = QLabel(L.video.color_format)
        self.color_format_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.color_format_entry = QLineEdit()
        self.color_format_entry.setMaxLength(64)
        self.color_format_entry.setText(self.color_format)
        self.color_format_entry.editingFinished.connect(self.color_format_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.alignment_label = QLabel(L.video.audio_alignment)
        self.alignment_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.alignment_entry = QComboBox()
        self.alignment_entry.addItems([L.video.frame_start, L.video.frame_center, L.video.frame_end]) # pyright: ignore[reportUnknownMemberType]
        if self.alignment == constants.AlignmentCode.START:
            self.alignment_entry.setCurrentIndex(0)
        elif self.alignment == constants.AlignmentCode.MIDDLE:
            self.alignment_entry.setCurrentIndex(1)
        elif self.alignment == constants.AlignmentCode.END:
            self.alignment_entry.setCurrentIndex(2)
        self.alignment_entry.currentIndexChanged.connect(self.alignment_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.playhead_entry_label = QLabel(L.video.playhead)
        self.playhead_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.playhead_entry = QCheckBox(L.video.visible)
        self.playhead_entry.setChecked(self.playhead_visible)
        self.playhead_entry.stateChanged.connect(self.playhead_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.flip_v_entry_label = QLabel(L.video.flip_vertical)
        self.flip_v_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.flip_v_entry = QCheckBox(L.video.flip)
        self.flip_v_entry.setChecked(self.flip_v)
        self.flip_v_entry.stateChanged.connect(self.flip_v_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.flip_h_entry_label = QLabel(L.video.flip_horizontal)
        self.flip_h_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.flip_h_entry = QCheckBox(L.video.flip)
        self.flip_h_entry.setChecked(self.flip_h)
        self.flip_h_entry.stateChanged.connect(self.flip_h_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.confirm_buttons.accepted.connect(self.accept) # pyright: ignore[reportUnknownMemberType]
        self.confirm_buttons.rejected.connect(self.reject) # pyright: ignore[reportUnknownMemberType]

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.width_label, 0, 0)
        self.main_layout.addWidget(self.width_entry, 0, 1)
        self.main_layout.addWidget(self.height_label, 1, 0)
        self.main_layout.addWidget(self.height_entry, 1, 1)
        self.main_layout.addWidget(self.color_format_label, 2, 0)
        self.main_layout.addWidget(self.color_format_entry, 2, 1)
        self.main_layout.addWidget(self.alignment_label, 3, 0)
        self.main_layout.addWidget(self.alignment_entry, 3, 1)
        self.main_layout.addWidget(self.playhead_entry_label, 4, 0)
        self.main_layout.addWidget(self.playhead_entry, 4, 1)
        self.main_layout.addWidget(self.flip_v_entry_label, 5, 0)
        self.main_layout.addWidget(self.flip_v_entry, 5, 1)
        self.main_layout.addWidget(self.flip_h_entry_label, 6, 0)
        self.main_layout.addWidget(self.flip_h_entry, 6, 1)
        self.main_layout.addWidget(self.confirm_buttons, 7, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def get_video_settings(self) -> dict[str, int | str | bool | AlignmentCode]:
        result: dict[str, int | str | bool | AlignmentCode] = dict()
        result["width"] = self.entry_width
        result["height"] = self.entry_height
        result["color_format"] = self.color_format
        result["flip_v"] = self.flip_v
        result["flip_h"] = self.flip_h
        result["alignment"] = self.alignment
        result["playhead_visible"] = self.playhead_visible

        return result

    def width_entry_changed(self, value: int) -> None:
        self.entry_width = value

    def height_entry_changed(self, value: int) -> None:
        self.entry_height = value

    def color_format_entry_changed(self) -> None:
        color_format = self.color_format_entry.text()
        parsed = self.bw.parse_color_format(color_format)
        if parsed["is_valid"]:
            self.color_format = color_format
        else:
            self.color_format_entry.setText(self.color_format)
            self.color_format_entry.setFocus()

            
            error_popup = QMessageBox(parent=self)
            error_popup.setIcon(QMessageBox.Icon.Critical)
            error_popup.setText(L.dialog.invalid_color_format)
            error_popup.setInformativeText(parsed["message"])
            error_popup.setWindowTitle(L.dialog.error)
            error_popup.exec()

    def playhead_entry_changed(self, value: int) -> None:
        if value == 0:
            self.playhead_visible = False
        else:
            self.playhead_visible = True

    def flip_v_entry_changed(self, value: int) -> None:
        if value == 0:
            self.flip_v = False
        else:
            self.flip_v = True

    def flip_h_entry_changed(self, value: int) -> None:
        if value == 0:
            self.flip_h = False
        else:
            self.flip_h = True

    def alignment_entry_changed(self, idx: int) -> None:
        if idx == 0:
            self.alignment = constants.AlignmentCode.START
        elif idx == 1:
            self.alignment = constants.AlignmentCode.MIDDLE
        elif idx == 2:
            self.alignment = constants.AlignmentCode.END

    def resize_window(self) -> None:
        self.setFixedSize(self.sizeHint())


# Player settings input window
#   User interface to set the player settings (for playback)
class PlayerSettings(QDialog):
    def __init__(self,
                 max_view_dim: int,
                 fps: int,
                 parent: QWidget | None = None
                 ) -> None:
        super().__init__(parent=parent)
        
        self.setWindowTitle(L.dialog.player_settings)
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)

        self.max_view_dim = max_view_dim
        self.fps = fps

        self.max_dim_label = QLabel(L.player.max_dimension)
        self.max_dim_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.max_dim_entry = QSpinBox()
        self.max_dim_entry.setMinimum(256)
        self.max_dim_entry.setMaximum(7680)
        self.max_dim_entry.setSingleStep(64)
        self.max_dim_entry.setSuffix("px")
        self.max_dim_entry.setValue(self.max_view_dim)
        self.max_dim_entry.valueChanged.connect(self.max_dim_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.fps_label = QLabel(L.player.fps)
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.fps_entry = QSpinBox()
        self.fps_entry.setMinimum(1)
        self.fps_entry.setMaximum(120)
        self.fps_entry.setSingleStep(1)
        self.fps_entry.setSuffix("fps")
        self.fps_entry.setValue(self.fps)
        self.fps_entry.valueChanged.connect(self.fps_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.confirm_buttons.accepted.connect(self.accept) # pyright: ignore[reportUnknownMemberType]
        self.confirm_buttons.rejected.connect(self.reject) # pyright: ignore[reportUnknownMemberType]

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.max_dim_label, 0, 0)
        self.main_layout.addWidget(self.max_dim_entry, 0, 1)
        self.main_layout.addWidget(self.fps_label, 1, 0)
        self.main_layout.addWidget(self.fps_entry, 1, 1)
        self.main_layout.addWidget(self.confirm_buttons, 2, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def get_player_settings(self) -> dict[str, int]:
        result: dict[str, int] = dict()
        result["max_view_dim"] = self.max_view_dim
        result["fps"] = self.fps

        return result

    def max_dim_entry_changed(self, value: int) -> None:
        self.max_view_dim = value

    def fps_entry_changed(self, value: int) -> None:
        self.fps = value

    def resize_window(self) -> None:
        self.setFixedSize(self.sizeHint())


# Export image dialog
#   User interface to export a single frame
class ExportFrame(QDialog):
    def __init__(self,
                 width: int,
                 height: int,
                 parent: QWidget | None = None
                 ) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle(L.dialog.export_image)
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)

        self.entry_width = width
        self.entry_height = height
        self.keep_aspect = False

        self.width_label = QLabel(L.dialog.export_width)
        self.width_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.width_entry = QSpinBox()
        self.width_entry.setMinimum(64)
        self.width_entry.setMaximum(7680)
        self.width_entry.setSingleStep(64)
        self.width_entry.setSuffix("px")
        self.width_entry.setValue(self.entry_width)
        self.width_entry.valueChanged.connect(self.width_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.height_label = QLabel(L.dialog.export_height)
        self.height_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.height_entry = QSpinBox()
        self.height_entry.setMinimum(64)
        self.height_entry.setMaximum(7680)
        self.height_entry.setSingleStep(64)
        self.height_entry.setSuffix("px")
        self.height_entry.setValue(self.entry_height)
        self.height_entry.valueChanged.connect(self.height_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.aspect_label = QLabel(L.dialog.aspect_ratio)
        self.aspect_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.aspect_entry = QCheckBox(L.dialog.force)
        self.aspect_entry.setChecked(self.keep_aspect)
        self.aspect_entry.stateChanged.connect(self.aspect_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.confirm_buttons.accepted.connect(self.accept) # pyright: ignore[reportUnknownMemberType]
        self.confirm_buttons.rejected.connect(self.reject) # pyright: ignore[reportUnknownMemberType]

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.width_label, 0, 0)
        self.main_layout.addWidget(self.width_entry, 0, 1)
        self.main_layout.addWidget(self.height_label, 1, 0)
        self.main_layout.addWidget(self.height_entry, 1, 1)
        self.main_layout.addWidget(self.aspect_label, 2, 0)
        self.main_layout.addWidget(self.aspect_entry, 2, 1)
        self.main_layout.addWidget(self.confirm_buttons, 3, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self) -> None:
        self.setFixedSize(self.sizeHint())

    def get_settings(self) -> dict[str, int | bool]:
        result: dict[str, int | bool] = dict()
        result["width"] = self.entry_width
        result["height"] = self.entry_height
        result["keep_aspect"] = self.keep_aspect

        return result

    def width_entry_changed(self, value: int) -> None:
        self.entry_width = value

    def height_entry_changed(self, value: int) -> None:
        self.entry_height = value

    def aspect_entry_changed(self, value: int) -> None:
        if value == 0:
            self.keep_aspect = False
        else:
            self.keep_aspect = True


# Export image sequence dialog
#   User interface to export an image sequence
class ExportSequence(QDialog):
    def __init__(self,
                 width: int,
                 height: int,
                 parent: QWidget | None = None
                 ) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle(L.dialog.export_sequence)
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)

        self.entry_width = width
        self.entry_height = height
        self.fps = 60.0
        self.keep_aspect = False
        self.format = constants.ImageFormatCode.PNG

        self.fps_label = QLabel(L.dialog.fps)
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.fps_entry = QDoubleSpinBox()
        self.fps_entry.setMinimum(1.0)
        self.fps_entry.setMaximum(120.0)
        self.fps_entry.setSingleStep(1.0)
        self.fps_entry.setSuffix("fps")
        self.fps_entry.setValue(self.fps)
        self.fps_entry.valueChanged.connect(self.fps_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.width_label = QLabel(L.dialog.export_width)
        self.width_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.width_entry = QSpinBox()
        self.width_entry.setMinimum(64)
        self.width_entry.setMaximum(7680)
        self.width_entry.setSingleStep(64)
        self.width_entry.setSuffix("px")
        self.width_entry.setValue(self.entry_width)
        self.width_entry.valueChanged.connect(self.width_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.height_label = QLabel(L.dialog.export_height)
        self.height_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.height_entry = QSpinBox()
        self.height_entry.setMinimum(64)
        self.height_entry.setMaximum(7680)
        self.height_entry.setSingleStep(64)
        self.height_entry.setSuffix("px")
        self.height_entry.setValue(self.entry_height)
        self.height_entry.valueChanged.connect(self.height_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.aspect_label = QLabel(L.dialog.aspect_ratio)
        self.aspect_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.aspect_entry = QCheckBox(L.dialog.force)
        self.aspect_entry.setChecked(self.keep_aspect)
        self.aspect_entry.stateChanged.connect(self.aspect_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.format_label = QLabel(L.dialog.image_format)
        self.format_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.format_entry = QComboBox()
        self.format_entry.addItems(["PNG (.png)", "JPEG (.jpg)", "BMP (.bmp)"]) # pyright: ignore[reportUnknownMemberType]
        if self.format == constants.ImageFormatCode.PNG:
            self.format_entry.setCurrentIndex(0)
        elif self.format == constants.ImageFormatCode.JPEG:
            self.format_entry.setCurrentIndex(1)
        elif self.format == constants.ImageFormatCode.BITMAP:
            self.format_entry.setCurrentIndex(2)
        self.format_entry.currentIndexChanged.connect(self.format_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.confirm_buttons.accepted.connect(self.accept) # pyright: ignore[reportUnknownMemberType]
        self.confirm_buttons.rejected.connect(self.reject) # pyright: ignore[reportUnknownMemberType]

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.fps_label, 0, 0)
        self.main_layout.addWidget(self.fps_entry, 0, 1)
        self.main_layout.addWidget(self.width_label, 1, 0)
        self.main_layout.addWidget(self.width_entry, 1, 1)
        self.main_layout.addWidget(self.height_label, 2, 0)
        self.main_layout.addWidget(self.height_entry, 2, 1)
        self.main_layout.addWidget(self.aspect_label, 3, 0)
        self.main_layout.addWidget(self.aspect_entry, 3, 1)
        self.main_layout.addWidget(self.format_label, 4, 0)
        self.main_layout.addWidget(self.format_entry, 4, 1)
        self.main_layout.addWidget(self.confirm_buttons, 5, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self) -> None:
        self.setFixedSize(self.sizeHint())

    def get_settings(self) -> dict[str, int | float | bool | ImageFormatCode]:
        result: dict[str, int | float | bool | ImageFormatCode] = dict()
        result["width"] = self.entry_width
        result["height"] = self.entry_height
        result["fps"] = self.fps
        result["keep_aspect"] = self.keep_aspect
        result["format"] = self.format

        return result

    def width_entry_changed(self, value: int) -> None:
        self.entry_width = value

    def height_entry_changed(self, value: int) -> None:
        self.entry_height = value

    def aspect_entry_changed(self, value: int) -> None:
        if value == 0:
            self.keep_aspect = False
        else:
            self.keep_aspect = True

    def fps_entry_changed(self, value: float) -> None:
        self.fps = value

    def format_entry_changed(self, value: int) -> None:
        if value == 0:
            self.format = constants.ImageFormatCode.PNG
        elif value == 1:
            self.format = constants.ImageFormatCode.JPEG
        elif value == 2:
            self.format = constants.ImageFormatCode.BITMAP


# Export video dialog
#   User interface to export a video
class ExportVideo(QDialog):
    def __init__(self,
                 width: int,
                 height: int,
                 parent: QWidget | None = None
                 ) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle(L.dialog.export_video)
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)

        self.entry_width = width
        self.entry_height = height
        self.fps = 60.0
        self.keep_aspect = False

        self.fps_label = QLabel(L.dialog.fps)
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.fps_entry = QDoubleSpinBox()
        self.fps_entry.setMinimum(1.0)
        self.fps_entry.setMaximum(120.0)
        self.fps_entry.setSingleStep(1.0)
        self.fps_entry.setSuffix("fps")
        self.fps_entry.setValue(self.fps)
        self.fps_entry.valueChanged.connect(self.fps_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.width_label = QLabel(L.dialog.export_width)
        self.width_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.width_entry = QSpinBox()
        self.width_entry.setMinimum(64)
        self.width_entry.setMaximum(7680)
        self.width_entry.setSingleStep(64)
        self.width_entry.setSuffix("px")
        self.width_entry.setValue(self.entry_width)
        self.width_entry.valueChanged.connect(self.width_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.height_label = QLabel(L.dialog.export_height)
        self.height_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.height_entry = QSpinBox()
        self.height_entry.setMinimum(64)
        self.height_entry.setMaximum(7680)
        self.height_entry.setSingleStep(64)
        self.height_entry.setSuffix("px")
        self.height_entry.setValue(self.entry_height)
        self.height_entry.valueChanged.connect(self.height_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.aspect_label = QLabel(L.dialog.aspect_ratio)
        self.aspect_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.aspect_entry = QCheckBox(L.dialog.force)
        self.aspect_entry.setChecked(self.keep_aspect)
        self.aspect_entry.stateChanged.connect(self.aspect_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.confirm_buttons.accepted.connect(self.accept) # pyright: ignore[reportUnknownMemberType]
        self.confirm_buttons.rejected.connect(self.reject) # pyright: ignore[reportUnknownMemberType]

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.fps_label, 0, 0)
        self.main_layout.addWidget(self.fps_entry, 0, 1)
        self.main_layout.addWidget(self.width_label, 1, 0)
        self.main_layout.addWidget(self.width_entry, 1, 1)
        self.main_layout.addWidget(self.height_label, 2, 0)
        self.main_layout.addWidget(self.height_entry, 2, 1)
        self.main_layout.addWidget(self.aspect_label, 3, 0)
        self.main_layout.addWidget(self.aspect_entry, 3, 1)
        self.main_layout.addWidget(self.confirm_buttons, 4, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self) -> None:
        self.setFixedSize(self.sizeHint())

    def get_settings(self) -> dict[str, int | float | bool]:
        result: dict[str, int | float | bool] = dict()
        result["width"] = self.entry_width
        result["height"] = self.entry_height
        result["fps"] = self.fps
        result["keep_aspect"] = self.keep_aspect

        return result

    def width_entry_changed(self, value: int) -> None:
        self.entry_width = value

    def height_entry_changed(self, value: int) -> None:
        self.entry_height = value

    def aspect_entry_changed(self, value: int) -> None:
        if value == 0:
            self.keep_aspect = False
        else:
            self.keep_aspect = True

    def fps_entry_changed(self, value: float) -> None:
        self.fps = value


# Export video encoder settings dialog
#   User interface to set encoder settings when exporting a video
class VideoEncoderSettings(QDialog):
    def __init__(self,
                 video_format: constants.VideoFormatCode,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle(L.dialog.encoder_settings)
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)

        self.video_format = video_format

        # Set defaults
        if self.video_format == constants.VideoFormatCode.MP4:
            self.codec = constants.VideoCodecCode.LIBX264
        elif self.video_format == constants.VideoFormatCode.AVI:
            self.codec = constants.VideoCodecCode.PNG
        elif self.video_format == constants.VideoFormatCode.MKV:
            self.codec = constants.VideoCodecCode.LIBX265
        elif self.video_format == constants.VideoFormatCode.MOV:
            self.codec = constants.VideoCodecCode.PRORES
        self.audio_codec = constants.AudioCodecCode.MP3
        self.preset = constants.EncoderPresetCode.ULTRAFAST

        self.codec_entry_label = QLabel(L.dialog.video_codec)
        self.codec_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.codec_entry = QComboBox()
        if self.video_format == constants.VideoFormatCode.MP4:
            self.codec_entry.addItems(["LIBX264", "MPEG4"]) # pyright: ignore[reportUnknownMemberType]
            if self.codec == constants.VideoCodecCode.LIBX264:
                self.codec_entry.setCurrentIndex(0)
            elif self.codec == constants.VideoCodecCode.MPEG4:
                self.codec_entry.setCurrentIndex(1)
        elif self.video_format == constants.VideoFormatCode.AVI:
            self.codec_entry.addItems(["PNG", "Raw"]) # pyright: ignore[reportUnknownMemberType]
            if self.codec == constants.VideoCodecCode.PNG:
                self.codec_entry.setCurrentIndex(0)
            elif self.codec == constants.VideoCodecCode.RAW:
                self.codec_entry.setCurrentIndex(1)
        elif self.video_format == constants.VideoFormatCode.MKV:
            self.codec_entry.addItems(["LIBX265", "LIBX264"]) # pyright: ignore[reportUnknownMemberType]
            if self.codec == constants.VideoCodecCode.LIBX265:
                self.codec_entry.setCurrentIndex(0)
            elif self.codec == constants.VideoCodecCode.LIBX264:
                self.codec_entry.setCurrentIndex(1)
        elif self.video_format == constants.VideoFormatCode.MOV:
            self.codec_entry.addItems(["ProRes"]) # pyright: ignore[reportUnknownMemberType]
            self.codec_entry.setCurrentIndex(0)
        self.codec_entry.currentIndexChanged.connect(self.codec_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.audio_codec_entry_label = QLabel(L.dialog.audio_codec)
        self.audio_codec_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.audio_codec_entry = QComboBox()
        self.audio_codec_entry.addItems(["MP3", "M4A (AAC)", "FLAC", "OGG (Vorbis)", "WAV 16-bit", "WAV 32-bit"]) # pyright: ignore[reportUnknownMemberType]
        if self.audio_codec == constants.AudioCodecCode.MP3:
            self.audio_codec_entry.setCurrentIndex(0)
        elif self.audio_codec == constants.AudioCodecCode.M4A:
            self.audio_codec_entry.setCurrentIndex(1)
        elif self.audio_codec == constants.AudioCodecCode.FLAC:
            self.audio_codec_entry.setCurrentIndex(2)
        elif self.audio_codec == constants.AudioCodecCode.VORBIS:
            self.audio_codec_entry.setCurrentIndex(3)
        elif self.audio_codec == constants.AudioCodecCode.WAV16:
            self.audio_codec_entry.setCurrentIndex(4)
        elif self.audio_codec == constants.AudioCodecCode.WAV32:
            self.audio_codec_entry.setCurrentIndex(5)
        self.audio_codec_entry.currentIndexChanged.connect(self.audio_codec_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.preset_entry_label = QLabel(L.dialog.encoder_preset)
        self.preset_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.preset_entry = QComboBox()
        self.preset_entry.addItems([ # pyright: ignore[reportUnknownMemberType]
            "Ultra Fast",
            "Super Fast",
            "Very Fast",
            "Faster",
            "Fast",
            "Medium",
            "Slow",
            "Slower",
            "Very Slow",
            "Placebo"
        ])
        if self.preset == constants.EncoderPresetCode.ULTRAFAST:
            self.preset_entry.setCurrentIndex(0)
        elif self.preset == constants.EncoderPresetCode.SUPERFAST:
            self.preset_entry.setCurrentIndex(1)
        elif self.preset == constants.EncoderPresetCode.VERYFAST:
            self.preset_entry.setCurrentIndex(2)
        elif self.preset == constants.EncoderPresetCode.FASTER:
            self.preset_entry.setCurrentIndex(3)
        elif self.preset == constants.EncoderPresetCode.FAST:
            self.preset_entry.setCurrentIndex(4)
        elif self.preset == constants.EncoderPresetCode.MEDIUM:
            self.preset_entry.setCurrentIndex(5)
        elif self.preset == constants.EncoderPresetCode.SLOW:
            self.preset_entry.setCurrentIndex(6)
        elif self.preset == constants.EncoderPresetCode.SLOWER:
            self.preset_entry.setCurrentIndex(7)
        elif self.preset == constants.EncoderPresetCode.VERYSLOW:
            self.preset_entry.setCurrentIndex(8)
        elif self.preset == constants.EncoderPresetCode.PLACEBO:
            self.preset_entry.setCurrentIndex(9)
        self.preset_entry.currentIndexChanged.connect(self.preset_entry_changed) # pyright: ignore[reportUnknownMemberType]

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.confirm_buttons.accepted.connect(self.accept) # pyright: ignore[reportUnknownMemberType]
        self.confirm_buttons.rejected.connect(self.reject) # pyright: ignore[reportUnknownMemberType]

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.codec_entry_label, 0, 0)
        self.main_layout.addWidget(self.codec_entry, 0, 1)
        self.main_layout.addWidget(self.audio_codec_entry_label, 1, 0)
        self.main_layout.addWidget(self.audio_codec_entry, 1, 1)
        self.main_layout.addWidget(self.preset_entry_label, 2, 0)
        self.main_layout.addWidget(self.preset_entry, 2, 1)
        self.main_layout.addWidget(self.confirm_buttons, 3, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self) -> None:
        self.setFixedSize(self.sizeHint())

    def get_settings(self) -> dict[str, VideoCodecCode | AudioCodecCode | EncoderPresetCode]:
        result: dict[str, VideoCodecCode | AudioCodecCode | EncoderPresetCode] = dict()
        result["codec"] = self.codec
        result["audio_codec"] = self.audio_codec
        result["preset"] = self.preset

        return result

    def codec_entry_changed(self, value: int) -> None:
        if self.video_format == constants.VideoFormatCode.MP4:
            if value == 0:
                self.codec = constants.VideoCodecCode.LIBX264
            elif value == 1:
                self.codec = constants.VideoCodecCode.MPEG4
        elif self.video_format == constants.VideoFormatCode.AVI:
            if value == 0:
                self.codec = constants.VideoCodecCode.PNG
            elif value == 1:
                self.codec = constants.VideoCodecCode.RAW
        elif self.video_format == constants.VideoFormatCode.MKV:
            if value == 0:
                self.codec = constants.VideoCodecCode.LIBX265
            elif value == 1:
                self.codec = constants.VideoCodecCode.LIBX264
        elif self.video_format == constants.VideoFormatCode.MOV:
            self.codec = constants.VideoCodecCode.PRORES

    def audio_codec_entry_changed(self, value: int) -> None:
        if value == 0:
            self.audio_codec = constants.AudioCodecCode.MP3
        elif value == 1:
            self.audio_codec = constants.AudioCodecCode.M4A
        elif value == 2:
            self.audio_codec = constants.AudioCodecCode.FLAC
        elif value == 3:
            self.audio_codec = constants.AudioCodecCode.VORBIS
        elif value == 4:
            self.audio_codec = constants.AudioCodecCode.WAV16
        elif value == 5:
            self.audio_codec = constants.AudioCodecCode.WAV32

    def preset_entry_changed(self, value: int) -> None:
        if value == 0:
            self.preset = constants.EncoderPresetCode.ULTRAFAST
        elif value == 1:
            self.preset = constants.EncoderPresetCode.SUPERFAST
        elif value == 2:
            self.preset = constants.EncoderPresetCode.VERYFAST
        elif value == 3:
            self.preset = constants.EncoderPresetCode.FASTER
        elif value == 4:
            self.preset = constants.EncoderPresetCode.FAST
        elif value == 5:
            self.preset = constants.EncoderPresetCode.MEDIUM
        elif value == 6:
            self.preset = constants.EncoderPresetCode.SLOW
        elif value == 7:
            self.preset = constants.EncoderPresetCode.SLOWER
        elif value == 8:
            self.preset = constants.EncoderPresetCode.VERYSLOW
        elif value == 9:
            self.preset = constants.EncoderPresetCode.PLACEBO


# Hotkey info dialog
#   Lists the program hotkeys
class HotkeysInfo(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        
        self.setWindowTitle(L.dialog.hotkey_info)
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)

        self.play_label = QLabel(L.hotkeys.play_pause)
        self.play_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.play_key_label = QLabel(L.hotkeys.key_spacebar)
        self.play_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.forward_label = QLabel(L.hotkeys.forward)
        self.forward_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.forward_key_label = QLabel(L.hotkeys.key_right)
        self.forward_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.back_label = QLabel(L.hotkeys.back)
        self.back_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.back_key_label = QLabel(L.hotkeys.key_left)
        self.back_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.frame_forward_label = QLabel(L.hotkeys.frame_forward)
        self.frame_forward_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.frame_forward_key_label = QLabel(">")
        self.frame_forward_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.frame_back_label = QLabel(L.hotkeys.frame_back)
        self.frame_back_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.frame_back_key_label = QLabel("<")
        self.frame_back_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.restart_label = QLabel(L.hotkeys.restart)
        self.restart_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.restart_key_label = QLabel("R")
        self.restart_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.volume_up_label = QLabel(L.hotkeys.volume_up)
        self.volume_up_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.volume_up_key_label = QLabel(L.hotkeys.key_up)
        self.volume_up_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.volume_down_label = QLabel(L.hotkeys.volume_down)
        self.volume_down_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.volume_down_key_label = QLabel(L.hotkeys.key_down)
        self.volume_down_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.mute_label = QLabel(L.hotkeys.mute)
        self.mute_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.mute_key_label = QLabel("M")
        self.mute_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.confirm_buttons.accepted.connect(self.accept) # pyright: ignore[reportUnknownMemberType]

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.play_label, 0, 0)
        self.main_layout.addWidget(self.play_key_label, 0, 1)
        self.main_layout.addWidget(self.back_label, 1, 0)
        self.main_layout.addWidget(self.back_key_label, 1, 1)
        self.main_layout.addWidget(self.forward_label, 2, 0)
        self.main_layout.addWidget(self.forward_key_label, 2, 1)
        self.main_layout.addWidget(self.frame_back_label, 3, 0)
        self.main_layout.addWidget(self.frame_back_key_label, 3, 1)
        self.main_layout.addWidget(self.frame_forward_label, 4, 0)
        self.main_layout.addWidget(self.frame_forward_key_label, 4, 1)
        self.main_layout.addWidget(self.restart_label, 5, 0)
        self.main_layout.addWidget(self.restart_key_label, 5, 1)
        self.main_layout.addWidget(self.volume_up_label, 6, 0)
        self.main_layout.addWidget(self.volume_up_key_label, 6, 1)
        self.main_layout.addWidget(self.volume_down_label, 7, 0)
        self.main_layout.addWidget(self.volume_down_key_label, 7, 1)
        self.main_layout.addWidget(self.mute_label, 8, 0)
        self.main_layout.addWidget(self.mute_key_label, 8, 1)
        self.main_layout.addWidget(self.confirm_buttons, 9, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self) -> None:
        self.setFixedSize(self.sizeHint())


# About dialog
#   Gives info about the program
class About(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        
        self.setWindowTitle(f"{L.menu_help.about} {constants.TITLE}")
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)

        self.icon_size = 200

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(QPixmap(constants.ICON_PATHS["program"]))
        self.icon_label.setScaledContents(True)
        self.icon_label.setFixedSize(self.icon_size, self.icon_size)

        self.about_text = QLabel(
            f"{constants.TITLE} v{constants.VERSION}\n{constants.COPYRIGHT}\n© Copyright 2026\n\n"
            f"{constants.DESCRIPTION}\n\n"
            f"{L.about.o_project_home}\n{constants.O_PROJECT_URL}\n\n"
            f"{L.about.m_project_home}\n{constants.M_PROJECT_URL}\n\n"
            f"{L.about.o_donate}\n{constants.O_DONATE_URL}")
        self.about_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.confirm_buttons.accepted.connect(self.accept) # pyright: ignore[reportUnknownMemberType]

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.icon_label, 0, 0, 2, 1)
        self.main_layout.addWidget(self.about_text, 0, 1)
        self.main_layout.addWidget(self.confirm_buttons, 1, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self) -> None:
        self.setFixedSize(self.sizeHint())
