import os
import json
import sys
from typing import Any
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QWidget, QGridLayout, QHBoxLayout, QLabel,
    QFileDialog, QMessageBox, QSlider, QProgressDialog
)
from PyQt6.QtGui import QPixmap, QIcon, QAction, QKeyEvent, QMouseEvent

from . import constants, generators, outputs, widgets, dialogs
from .lang import L, get_manager


def _restart_run():
    from . import core
    core.main(sys.argv)


def show_cannotuse_feat(parent: QWidget | None = None):
    QMessageBox.information(
        parent,
        L.dialog.feat_disabled,
        L.dialog.can_use_feat,
        QMessageBox.StandardButton.Ok
    )

# My QMainWindow class
#   Used to customize the main window.
#   The actual object used to programmatically reference
#   the "main window" is MainWindow
class MyQMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.file_savename: str = ""
        self.muted: bool = False

        
        self.setWindowTitle(L.menu.title)
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        self.bw = generators.BinaryWaterfall()

        self.last_save_location = constants.USER_DIR
        self.last_load_location = constants.USER_DIR

        self.renderer = outputs.Renderer(
            binary_waterfall=self.bw
        )

        self.padding_px = 10

        self.seek_bar = widgets.SeekBar()
        self.seek_bar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.seek_bar.setOrientation(Qt.Orientation.Horizontal)
        self.seek_bar.setMinimum(0)
        self.update_seekbar()
        self.seek_bar.sliderMoved.connect(self.seekbar_moved) # pyright: ignore[reportUnknownMemberType]

        self.player_label = QLabel()
        self.player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.player = outputs.Player(
            binary_waterfall=self.bw,
            display=self.player_label,
            set_playbutton_function=self.set_play_button,
            set_seekbar_function=self.seek_bar.setValue
        )

        self.current_volume = self.player.volume

        # Setup seek bar to correctly change player location
        self.seek_bar.set_position_changed_function(self.seekbar_moved)

        self.set_file_savename()

        # Save the pixmaps for later
        self.play_icons: dict[str, dict[str, QPixmap]] = {
            "play": {
                "base": QPixmap(constants.ICON_PATHS["button"]["play"]["base"]), # pyright: ignore[reportArgumentType]
                "hover": QPixmap(constants.ICON_PATHS["button"]["play"]["hover"]), # pyright: ignore[reportArgumentType]
                "clicked": QPixmap(constants.ICON_PATHS["button"]["play"]["clicked"]) # pyright: ignore[reportArgumentType]
            },
            "pause": {
                "base": QPixmap(constants.ICON_PATHS["button"]["pause"]["base"]), # pyright: ignore[reportArgumentType]
                "hover": QPixmap(constants.ICON_PATHS["button"]["pause"]["hover"]), # pyright: ignore[reportArgumentType]
                "clicked": QPixmap(constants.ICON_PATHS["button"]["pause"]["clicked"]) # pyright: ignore[reportArgumentType]
            }
        }

        self.transport_play = widgets.ImageButton(
            pixmap=self.play_icons["play"]["base"],
            pixmap_hover=self.play_icons["play"]["hover"],
            pixmap_pressed=self.play_icons["play"]["clicked"],
            scale=1.0,
            parent=self
        )
        self.transport_play.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.transport_play.setFixedSize(self.transport_play.img_width, self.transport_play.img_height)
        self.transport_play.clicked.connect(self.play_clicked) # pyright: ignore[reportUnknownMemberType]

        self.transport_forward = widgets.ImageButton(
            pixmap=QPixmap(constants.ICON_PATHS["button"]["forward"]["base"]), # pyright: ignore[reportArgumentType]
            pixmap_hover=QPixmap(constants.ICON_PATHS["button"]["forward"]["hover"]), # pyright: ignore[reportArgumentType]
            pixmap_pressed=QPixmap(constants.ICON_PATHS["button"]["forward"]["clicked"]), # pyright: ignore[reportArgumentType]
            scale=0.75,
            parent=self
        )
        self.transport_forward.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.transport_forward.setFixedSize(self.transport_forward.img_width, self.transport_forward.img_height)
        self.transport_forward.clicked.connect(self.forward_clicked) # pyright: ignore[reportUnknownMemberType]

        self.transport_back = widgets.ImageButton(
            pixmap=QPixmap(constants.ICON_PATHS["button"]["back"]["base"]), # pyright: ignore[reportArgumentType]
            pixmap_hover=QPixmap(constants.ICON_PATHS["button"]["back"]["hover"]), # pyright: ignore[reportArgumentType]
            pixmap_pressed=QPixmap(constants.ICON_PATHS["button"]["back"]["clicked"]), # pyright: ignore[reportArgumentType]
            scale=0.75,
            parent=self
        )
        self.transport_back.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.transport_back.setFixedSize(self.transport_back.img_width, self.transport_back.img_height)
        self.transport_back.clicked.connect(self.back_clicked) # pyright: ignore[reportUnknownMemberType]

        self.transport_restart = widgets.ImageButton(
            pixmap=QPixmap(constants.ICON_PATHS["button"]["restart"]["base"]), # pyright: ignore[reportArgumentType]
            pixmap_hover=QPixmap(constants.ICON_PATHS["button"]["restart"]["hover"]), # pyright: ignore[reportArgumentType]
            pixmap_pressed=QPixmap(constants.ICON_PATHS["button"]["restart"]["clicked"]), # pyright: ignore[reportArgumentType]
            scale=0.5,
            parent=self
        )
        self.transport_restart.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.transport_restart.setFixedSize(self.transport_restart.img_width, self.transport_restart.img_height)
        self.transport_restart.clicked.connect(self.restart_clicked) # pyright: ignore[reportUnknownMemberType]

        self.volume_icons: dict[str, QPixmap] = {
            "base": QPixmap(constants.ICON_PATHS["volume"]["base"]), # pyright: ignore[reportArgumentType]
            "mute": QPixmap(constants.ICON_PATHS["volume"]["mute"]), # pyright: ignore[reportArgumentType]
        }

        self.volume_icon = QLabel()
        self.volume_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_icon.setScaledContents(True)
        self.volume_icon.setFixedSize(20, 20)
        self.set_volume_icon(mute=self.is_player_muted())
        self.unmute_volume = self.current_volume
        self.volume_icon.mousePressEvent = self.volume_icon_clicked # pyright: ignore[reportAttributeAccessIssue]

        self.volume_label = QLabel()
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_label.setFixedWidth(30)
        self.set_volume_label_value(self.current_volume)

        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.volume_slider.setFixedSize(20, 50)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.valueChanged.connect(self.volume_slider_changed) # pyright: ignore[reportUnknownMemberType]

        self.transport_left_layout = QHBoxLayout()
        self.transport_left_layout.setSpacing(self.padding_px)
        self.transport_left_layout.addWidget(self.transport_restart)
        self.transport_left_layout.addWidget(self.transport_back)

        self.restart_counterpad = QLabel()

        self.transport_right_layout = QHBoxLayout()
        self.transport_right_layout.setSpacing(self.padding_px)
        self.transport_right_layout.addWidget(self.transport_forward)
        self.transport_right_layout.addWidget(self.restart_counterpad)

        self.voume_layout = QGridLayout()
        self.voume_layout.setContentsMargins(0, 0, self.padding_px, 0)

        self.voume_layout.addWidget(self.volume_icon, 0, 0,
                                    alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        self.voume_layout.addWidget(self.volume_label, 1, 0,
                                    alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.voume_layout.addWidget(self.volume_slider, 0, 1, 2, 1,
                                    alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.main_layout = QGridLayout()
        self.main_layout.setContentsMargins(0, 0, 0, self.padding_px)
        self.main_layout.setSpacing(self.padding_px)

        self.main_layout.addWidget(self.player_label, 0, 0, 1, 5, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.seek_bar, 1, 0, 1, 5, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(self.transport_left_layout, 2, 1,
                                   alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(self.transport_play, 2, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(self.transport_right_layout, 2, 3,
                                   alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addLayout(self.voume_layout, 2, 4, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.main_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.main_widget.setStyleSheet("background-color: {};".format(constants.COLORS["controls_background"]))
        self.setCentralWidget(self.main_widget)

        self.main_menu: QMenuBar = self.menuBar() # pyright: ignore[reportAttributeAccessIssue]
        self.setStyleSheet("QMenuBar {{ background-color: {bg}; }}".format(
            bg=constants.COLORS["status_background"]
        ))

        

        self.file_menu: QMenu = self.main_menu.addMenu(L.menu.file) # pyright: ignore[reportAttributeAccessIssue]

        self.file_menu_open = QAction(L.menu_file.open, self)
        self.file_menu_open.triggered.connect(self.open_file_clicked) # pyright: ignore[reportUnknownMemberType]
        self.file_menu.addAction(self.file_menu_open) # pyright: ignore[reportUnknownMemberType]

        self.file_menu_close = QAction(L.menu_file.close, self)
        self.file_menu_close.setEnabled(False)
        self.file_menu_close.triggered.connect(self.close_file_clicked) # pyright: ignore[reportUnknownMemberType]
        self.file_menu.addAction(self.file_menu_close) # pyright: ignore[reportUnknownMemberType]

        self.settings_menu: QMenu = self.main_menu.addMenu(L.menu.settings) # pyright: ignore[reportAttributeAccessIssue]

        self.settings_menu_audio = QAction(L.menu_settings.audio, self)
        self.settings_menu_audio.triggered.connect(self.audio_settings_clicked) # pyright: ignore[reportUnknownMemberType]
        self.settings_menu.addAction(self.settings_menu_audio) # pyright: ignore[reportUnknownMemberType]

        self.settings_menu_video = QAction(L.menu_settings.video, self)
        self.settings_menu_video.triggered.connect(self.video_settings_clicked) # pyright: ignore[reportUnknownMemberType]
        self.settings_menu.addAction(self.settings_menu_video) # pyright: ignore[reportUnknownMemberType]

        self.settings_menu_player = QAction(L.menu_settings.player, self)
        self.settings_menu_player.triggered.connect(self.player_settings_clicked) # pyright: ignore[reportUnknownMemberType]
        self.settings_menu.addAction(self.settings_menu_player) # pyright: ignore[reportUnknownMemberType]

        self.language_menu: QMenu = self.settings_menu.addMenu(L.menu.language) # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        self._build_language_menu()

        self.export_menu: QMenu = self.main_menu.addMenu(L.menu.export) # pyright: ignore[reportAttributeAccessIssue]
        self.export_menu.setEnabled(False) # pyright: ignore[reportUnknownMemberType]

        self.export_menu_audio = QAction(L.menu_export.audio, self)
        # self.export_menu_audio.triggered.connect(lambda : show_cannotuse_feat(self)) # pyright: ignore[reportUnknownMemberType]
        self.export_menu_audio.triggered.connect(self.export_audio_clicked) # pyright: ignore[reportUnknownMemberType]
        self.export_menu.addAction(self.export_menu_audio) # pyright: ignore[reportUnknownMemberType]

        self.export_menu_image = QAction(L.menu_export.image, self)
        # self.export_menu_image.triggered.connect(lambda : show_cannotuse_feat(self)) # pyright: ignore[reportUnknownMemberType]
        self.export_menu_image.triggered.connect(self.export_image_clicked) # pyright: ignore[reportUnknownMemberType]
        self.export_menu.addAction(self.export_menu_image) # pyright: ignore[reportUnknownMemberType]

        self.export_menu_sequence = QAction(L.menu_export.image_sequence, self)
        # self.export_menu_sequence.triggered.connect(lambda : show_cannotuse_feat(self)) # pyright: ignore[reportUnknownMemberType]
        self.export_menu_sequence.triggered.connect(self.export_sequence_clicked) # pyright: ignore[reportUnknownMemberType]
        self.export_menu.addAction(self.export_menu_sequence) # pyright: ignore[reportUnknownMemberType]

        self.export_menu_video = QAction(L.menu_export.video, self)
        # self.export_menu_video.triggered.connect(lambda : show_cannotuse_feat(self)) # pyright: ignore[reportUnknownMemberType]
        self.export_menu_video.triggered.connect(self.export_video_clicked) # pyright: ignore[reportUnknownMemberType]
        self.export_menu.addAction(self.export_menu_video) # pyright: ignore[reportUnknownMemberType]

        self.help_menu: QMenu = self.main_menu.addMenu(L.menu.help) # pyright: ignore[reportAttributeAccessIssue]

        self.help_menu_hotkeys = QAction(L.menu_help.hotkeys, self)
        self.help_menu_hotkeys.triggered.connect(self.hotkeys_clicked) # pyright: ignore[reportUnknownMemberType]
        self.help_menu.addAction(self.help_menu_hotkeys) # pyright: ignore[reportUnknownMemberType]

        self.help_menu_about = QAction(L.menu_help.about, self)
        self.help_menu_about.triggered.connect(self.about_clicked) # pyright: ignore[reportUnknownMemberType]
        self.help_menu.addAction(self.help_menu_about) # pyright: ignore[reportUnknownMemberType]

        self.set_volume(self.current_volume)

        # Load saved settings
        self._load_app_settings()

        # Set window to content size
        self.resize_window()

    def _build_language_menu(self) -> None:
        """构建语言子菜单"""
        self.language_menu.clear()
        available = get_manager().available_languages()
        current = get_manager().current_code
        custom_codes = get_manager().custom_codes

        for code, name in sorted(available.items()):
            display_name = f"{name} ({code})"
            if code in custom_codes:
                display_name += L.dialog.is_custom
            action = QAction(display_name, self)
            action.setCheckable(True)
            action.setChecked(code == current)
            action.triggered.connect(lambda checked, c=code: self._switch_language(c)) # pyright: ignore[reportUnknownLambdaType, reportUnknownMemberType]
            self.language_menu.addAction(action) # pyright: ignore[reportUnknownMemberType]

        self.language_menu.addSeparator() # pyright: ignore[reportUnknownMemberType]

        import_action = QAction(L.dialog.import_language, self)
        import_action.triggered.connect(self._import_language) # pyright: ignore[reportUnknownMemberType]
        self.language_menu.addAction(import_action) # pyright: ignore[reportUnknownMemberType]

        if custom_codes:
            remove_action = QAction(L.dialog.remove_language, self)
            remove_action.triggered.connect(self._remove_language) # pyright: ignore[reportUnknownMemberType]
            self.language_menu.addAction(remove_action) # pyright: ignore[reportUnknownMemberType]

        self.language_menu.addSeparator() # pyright: ignore[reportUnknownMemberType]

        fallback_action = QAction(L.dialog.fallback_language, self)
        fallback_action.triggered.connect(self._set_fallback_language) # pyright: ignore[reportUnknownMemberType]
        self.language_menu.addAction(fallback_action) # pyright: ignore[reportUnknownMemberType]

    def _import_language(self) -> None:
        """导入自定义语言文件"""
        filename, _filetype = QFileDialog.getOpenFileName(
            self,
            L.dialog.import_language_title,
            "",
            L.dialog.import_language_filter
        )

        if filename == "":
            return

        try:
            with open(filename, encoding="utf-8") as f:
                data = json.load(f)

            # Validate it's a dict
            if not isinstance(data, dict):
                raise ValueError("File must contain a JSON object")

            # Validate it has _meta with name
            if "_meta" not in data or "name" not in data["_meta"]:
                raise ValueError("File must have '_meta.name' field")

            code: str = get_manager().import_language(filename) # pyright: ignore[reportUnusedVariable]
            name: str = data["_meta"]["name"] # pyright: ignore[reportUnknownVariableType]

            QMessageBox.information(
                self,
                L.dialog.import_language_title,
                L.dialog.import_language_success.format(code=name), # pyright: ignore[reportUnknownArgumentType]
                QMessageBox.StandardButton.Ok
            )

            self._rebuild_menus()
            self._show_restart_prompt()

        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self,
                L.dialog.error,
                L.dialog.import_language_invalid.format(error=str(e)),
                QMessageBox.StandardButton.Ok
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                L.dialog.error,
                L.dialog.import_language_error.format(error=str(e)),
                QMessageBox.StandardButton.Ok
            )

    def _remove_language(self) -> None:
        """移除自定义语言"""
        custom_codes = get_manager().custom_codes
        if not custom_codes:
            return

        # Build list of custom languages with display names
        items: list[tuple[str, str]] = []
        for code in sorted(custom_codes):
            name = get_manager().available_languages().get(code, code)
            items.append((code, name))

        # Show selection dialog
        from PyQt6.QtWidgets import QInputDialog
        names = [f"{name} ({code})" for code, name in items]
        selected, ok = QInputDialog.getItem( # pyright: ignore[reportUnknownMemberType]
            self,
            L.dialog.remove_language,
            L.dialog.remove_language,
            names,
            0,
            False
        )

        if not ok:
            return

        # Find the code
        idx = names.index(selected)
        code, name = items[idx]

        # Confirm
        result = QMessageBox.question(
            self,
            L.dialog.remove_language,
            L.dialog.remove_language_confirm.format(name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            get_manager().remove_language(code)
            self._rebuild_menus()
            self._show_restart_prompt()

    def _set_fallback_language(self) -> None:
        """设置回退语言"""
        from PyQt6.QtWidgets import QInputDialog

        available = get_manager().available_languages()
        builtin = get_manager().builtin_codes
        current_fallback = get_manager().fallback_code

        # Build list of available fallback languages (only built-in)
        items: list[tuple[str, str]] = []
        for code in sorted(builtin):
            name = available.get(code, code)
            items.append((code, name))

        names = [f"{name} ({code})" for code, name in items]
        current_idx = 0
        for i, (code, _) in enumerate(items):
            if code == current_fallback:
                current_idx = i
                break

        selected, ok = QInputDialog.getItem( # pyright: ignore[reportUnknownMemberType]
            self,
            L.dialog.fallback_language_title,
            L.dialog.fallback_language_desc,
            names,
            current_idx,
            False
        )

        if not ok:
            return

        # Find the code
        idx = names.index(selected)
        code, name = items[idx]

        get_manager().set_fallback(code)
        self._rebuild_menus()
        self._show_restart_prompt()

    def _switch_language(self, code: str) -> None:
        """切换语言"""
        get_manager().set_language(code)
        self._rebuild_menus()
        self._show_restart_prompt()

    def _rebuild_menus(self) -> None:
        """重建所有菜单文本（但不是全部）"""
        L = get_manager().lang
        
        self.file_menu.setTitle(L.menu.file)
        self.file_menu_open.setText(L.menu_file.open)
        self.file_menu_close.setText(L.menu_file.close)

        self.settings_menu.setTitle(L.menu.settings)
        self.settings_menu_audio.setText(L.menu_settings.audio)
        self.settings_menu_video.setText(L.menu_settings.video)
        self.settings_menu_player.setText(L.menu_settings.player)
        self.language_menu.setTitle(L.menu.language)

        self.export_menu.setTitle(L.menu.export)
        self.export_menu_audio.setText(L.menu_export.audio)
        self.export_menu_image.setText(L.menu_export.image)
        self.export_menu_sequence.setText(L.menu_export.image_sequence)
        self.export_menu_video.setText(L.menu_export.video)

        self.help_menu.setTitle(L.menu.help)
        self.help_menu_hotkeys.setText(L.menu_help.hotkeys)
        self.help_menu_about.setText(L.menu_help.about)

        self._build_language_menu()

    def _show_restart_prompt(self) -> None:
        """显示语言切换重启提示框"""
        L = get_manager().lang
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(L.dialog.language_restart_title)
        msg_box.setText(L.dialog.language_restart_message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.addButton(QMessageBox.StandardButton.Ok)
        restart_button = msg_box.addButton(
            L.dialog.language_restart_restart_now,
            QMessageBox.ButtonRole.AcceptRole
        )
        msg_box.exec()
        if msg_box.clickedButton() == restart_button:
            self._restart_application()

    def _restart_application(self) -> None:
        """完全重启应用进程"""
        self.destroy()
        from multiprocessing import Process
        t = Process(target=_restart_run)
        t.daemon = False
        t.start()
        sys.exit(0)

    def _load_app_settings(self) -> None:
        """Load saved application settings"""
        settings = get_manager().load_app_settings()
        if not settings:
            return

        # Apply audio settings
        if "num_channels" in settings:
            self.bw.num_channels = settings["num_channels"]
        if "sample_bytes" in settings:
            self.bw.sample_bytes = settings["sample_bytes"]
        if "sample_rate" in settings:
            self.bw.sample_rate = settings["sample_rate"]
        if "file_volume" in settings:
            self.bw.volume = settings["file_volume"]
        if "endianness" in settings:
            from .constants.enums import EndiannessCode
            self.bw.endianness = EndiannessCode(settings["endianness"])

        # Apply video settings
        if "width" in settings and "height" in settings:
            self.bw.set_dims(width=settings["width"], height=settings["height"])
        if "color_format_string" in settings:
            self.bw.set_color_format(settings["color_format_string"])
        if "flip_v" in settings or "flip_h" in settings:
            self.bw.set_flip(
                flip_v=settings.get("flip_v", constants.DEFAULTS["flip_v"]),
                flip_h=settings.get("flip_h", constants.DEFAULTS["flip_h"])
            )
        if "alignment" in settings:
            from .constants.enums import AlignmentCode
            self.bw.set_alignment(alignment=AlignmentCode(settings["alignment"]))
        if "playhead_visible" in settings:
            self.bw.set_playhead_visible(playhead_visible=settings["playhead_visible"])

        # Apply player settings
        if "max_dim" in settings:
            self.player.update_dims(max_dim=settings["max_dim"])
        if "player_fps" in settings:
            self.player.set_fps(fps=settings["player_fps"])

        # Apply volume
        if "file_volume" in settings:
            self.current_volume = settings["file_volume"]
            self.set_volume(settings["file_volume"])

        # Re-compute audio with loaded settings
        if self.bw.filename is not None:
            self.bw.compute_audio()
            self.player.set_audio_file(self.bw.audio_filename)
            self.player.update_image()

    def _save_app_settings(self) -> None:
        """Save current application settings"""
        settings: dict[str, Any] = {}

        # Audio settings
        if self.bw.num_channels is not None:
            settings["num_channels"] = self.bw.num_channels
        if self.bw.sample_bytes is not None:
            settings["sample_bytes"] = self.bw.sample_bytes
        if self.bw.sample_rate is not None:
            settings["sample_rate"] = self.bw.sample_rate
        if self.bw.volume is not None:
            settings["file_volume"] = self.bw.volume
        if self.bw.endianness is not None:
            settings["endianness"] = self.bw.endianness.value

        # Video settings
        if self.bw.width is not None:
            settings["width"] = self.bw.width
        if self.bw.height is not None:
            settings["height"] = self.bw.height
        if self.bw.get_color_format_string():
            settings["color_format_string"] = self.bw.get_color_format_string()
        if self.bw.flip_v is not None:
            settings["flip_v"] = self.bw.flip_v
        if self.bw.flip_h is not None:
            settings["flip_h"] = self.bw.flip_h
        if self.bw.alignment is not None:
            settings["alignment"] = self.bw.alignment.value
        if self.bw.playhead_visible is not None:
            settings["playhead_visible"] = self.bw.playhead_visible

        # Player settings
        settings["max_dim"] = self.player.max_dim
        settings["player_fps"] = self.player.fps

        get_manager().save_app_settings(settings)

    def keyPressEvent(self, a0: QKeyEvent) -> None: # pyright: ignore[reportIncompatibleMethodOverride]
        key = a0.key()

        if key == Qt.Key.Key_Space:
            self.play_clicked()
        elif key == Qt.Key.Key_Left:
            self.back_clicked()
        elif key == Qt.Key.Key_Right:
            self.forward_clicked()
        elif key == Qt.Key.Key_Up:
            new_volume = min(self.current_volume + 5, 100)
            self.set_volume(new_volume)
        elif key == Qt.Key.Key_Down:
            new_volume = max(self.current_volume - 5, 0)
            self.set_volume(new_volume)
        elif key == Qt.Key.Key_M:
            self.toggle_mute()
        elif key == Qt.Key.Key_R:
            self.restart_clicked()
        elif key == Qt.Key.Key_Comma:
            self.player.frame_back()
        elif key == Qt.Key.Key_Period:
            self.player.frame_forward()

    def resize_window(self) -> None:
        # First, make largest elements smaller
        self.seek_bar.setFixedWidth(20)

        # Next, we update counterpadding
        self.update_counterpad_size()

        # We need to wait a sec for the sizeHint to recompute
        QTimer.singleShot(10, self.resize_window_helper) # pyright: ignore[reportUnknownMemberType]

    def resize_window_helper(self) -> None:
        size_hint = self.sizeHint()
        self.setFixedSize(size_hint)

        self.seek_bar.setFixedWidth(size_hint.width() - (self.padding_px * 2))

    def update_counterpad_size(self) -> None:
        self.restart_counterpad.setFixedSize(self.transport_restart.sizeHint())

    def set_play_button(self, play: bool) -> None:
        if play:
            self.transport_play.change_pixmaps(
                pixmap=self.play_icons["play"]["base"],
                pixmap_hover=self.play_icons["play"]["hover"],
                pixmap_pressed=self.play_icons["play"]["clicked"]
            )
        else:
            self.transport_play.change_pixmaps(
                pixmap=self.play_icons["pause"]["base"],
                pixmap_hover=self.play_icons["pause"]["hover"],
                pixmap_pressed=self.play_icons["pause"]["clicked"]
            )

    def is_player_muted(self) -> bool:
        if self.player.volume == 0:
            return True
        else:
            return False

    def set_volume_icon(self, mute: bool) -> None:
        if mute:
            self.volume_icon.setPixmap(self.volume_icons["mute"])
        else:
            self.volume_icon.setPixmap(self.volume_icons["base"])

    def set_volume_label_value(self, value: int) -> None:
        self.volume_label.setText(f"{value}%")

    def set_volume(self, value: int) -> None:
        self.current_volume = value

        self.player.set_volume(self.current_volume)
        self.set_volume_label_value(self.current_volume)
        self.volume_slider.setValue(self.player.volume)

        if self.current_volume > 0:
            self.unmute_volume = self.current_volume

        if self.current_volume == 0:
            self.set_volume_icon(mute=True)
        else:
            self.set_volume_icon(mute=False)

    def update_seekbar(self) -> None:
        if self.bw.filename is None:
            self.seek_bar.setEnabled(False)
            self.seek_bar.setValue(0)
        else:
            assert self.bw.audio_length_ms is not None
            self.seek_bar.setMaximum(self.bw.audio_length_ms)
            self.seek_bar.setEnabled(True)

    def seekbar_moved(self, position: int) -> None:
        self.player.set_position(position)

    def pause_player(self) -> None:
        self.player.pause()

    def play_player(self) -> None:
        self.player.play()

    def play_clicked(self) -> None:
        if self.player.is_playing():
            # Already playing, pause
            self.pause_player()
        else:
            # Paused, start playing
            self.play_player()

    def forward_clicked(self) -> None:
        self.player.forward()

    def back_clicked(self) -> None:
        self.player.back()

    def restart_clicked(self) -> None:
        self.player.restart()

    def toggle_mute(self) -> None:
        if self.is_player_muted():
            self.muted = False
            self.volume_slider.setValue(self.unmute_volume)
        else:
            self.muted = True
            self.volume_slider.setValue(0)

    def volume_icon_clicked(self, ev: QMouseEvent) -> None:
        self.toggle_mute()

    def volume_slider_changed(self, value: int) -> None:
        self.set_volume(value)

    def set_file_savename(self, name: str | None = None) -> None:
        if name is None:
            self.file_savename = "Untitled"
        else:
            self.file_savename = name

    def open_file_clicked(self) -> None:
        self.pause_player()

        filename, _filetype = QFileDialog.getOpenFileName(
            self,
            L.dialog.open_file,
            self.last_load_location,
            L.dialog.all_binary_files
        )

        if filename != "":
            file_size = os.path.getsize(filename)
            if file_size == 0:
                QMessageBox.critical(
                    self,
                    L.dialog.error,
                    L.dialog.file_is_empty.format(filename=filename),
                    QMessageBox.StandardButton.Ok
                )
                return
            elif file_size < 1024:
                QMessageBox.warning(
                    self,
                    L.dialog.warning,
                    L.dialog.file_is_small.format(filename=filename, size=file_size),
                    QMessageBox.StandardButton.Ok
                )

            self.player.open_file(filename=filename)

            _file_path, file_title = os.path.split(filename)
            file_savename, _file_ext = os.path.splitext(file_title)
            self.set_file_savename(file_savename)
            self.setWindowTitle(f"{L.menu.title} | {file_title}")

            self.last_load_location = filename

            self.update_seekbar()

            self.export_menu.setEnabled(True)
            self.file_menu_close.setEnabled(True)

    def close_file_clicked(self) -> None:
        self.pause_player()

        self.player.close_file()

        self.set_file_savename()
        
        self.setWindowTitle(L.menu.title)

        self.update_seekbar()

        self.export_menu.setEnabled(False)
        self.file_menu_close.setEnabled(False)

    def audio_settings_clicked(self) -> None:
        assert self.bw.num_channels is not None
        assert self.bw.sample_bytes is not None
        assert self.bw.sample_rate is not None
        assert self.bw.endianness is not None
        popup = dialogs.AudioSettings(
            num_channels=self.bw.num_channels,
            sample_bytes=self.bw.sample_bytes,
            sample_rate=self.bw.sample_rate,
            volume=self.bw.volume, # pyright: ignore[reportArgumentType]
            endianness=self.bw.endianness,
            parent=self
        )

        result = popup.exec()

        if result:
            audio_settings = popup.get_audio_settings()
            self.player.set_audio_settings(
                num_channels=audio_settings["num_channels"], # pyright: ignore[reportArgumentType]
                sample_bytes=audio_settings["sample_bytes"], # pyright: ignore[reportArgumentType]
                sample_rate=audio_settings["sample_rate"], # pyright: ignore[reportArgumentType]
                volume=audio_settings["volume"], # pyright: ignore[reportArgumentType]
                endianness=audio_settings["endianness"] # pyright: ignore[reportArgumentType]
            )

            self.update_seekbar()
            self._save_app_settings()

    def video_settings_clicked(self) -> None:
        assert self.bw.width is not None
        assert self.bw.height is not None
        assert self.bw.flip_v is not None
        assert self.bw.flip_h is not None
        assert self.bw.alignment is not None
        assert self.bw.playhead_visible is not None
        popup = dialogs.VideoSettings(
            bw=self.bw,
            width=self.bw.width,
            height=self.bw.height,
            color_format=self.bw.get_color_format_string(),
            flip_v=self.bw.flip_v,
            flip_h=self.bw.flip_h,
            alignment=self.bw.alignment,
            playhead_visible=self.bw.playhead_visible,
            parent=self
        )

        result = popup.exec()

        if result:
            video_settings = popup.get_video_settings()
            self.bw.set_dims(
                width=video_settings["width"], # pyright: ignore[reportArgumentType]
                height=video_settings["height"] # pyright: ignore[reportArgumentType]
            )
            self.bw.set_color_format(video_settings["color_format"]) # pyright: ignore[reportArgumentType]
            self.bw.set_flip(
                flip_v=video_settings["flip_v"], # pyright: ignore[reportArgumentType]
                flip_h=video_settings["flip_h"] # pyright: ignore[reportArgumentType]
            )
            self.bw.set_alignment(
                alignment=video_settings["alignment"] # pyright: ignore[reportArgumentType]
            )
            self.bw.set_playhead_visible(
                playhead_visible=video_settings["playhead_visible"] # pyright: ignore[reportArgumentType]
            )
            self.player.refresh_dims()
            self.player.update_image()
            self._save_app_settings()
            # We need to wait a moment for the size hint to be computed
            QTimer.singleShot(10, self.resize_window) # pyright: ignore[reportUnknownMemberType]

    def player_settings_clicked(self) -> None:
        popup = dialogs.PlayerSettings(
            max_view_dim=self.player.max_dim,
            fps=self.player.fps, # pyright: ignore[reportArgumentType]
            parent=self
        )

        result = popup.exec()

        if result:
            player_settings = popup.get_player_settings()
            self.player.set_fps(fps=player_settings["fps"])
            self.player.update_dims(max_dim=player_settings["max_view_dim"])
            self._save_app_settings()
            # We need to wait a moment for the size hint to be computed
            QTimer.singleShot(10, self.resize_window) # pyright: ignore[reportUnknownMemberType]

    def export_image_clicked(self) -> None:
        
        if self.bw.audio_filename is None:
            QMessageBox.critical(
                self,
                L.dialog.no_file_error,
                L.dialog.no_file_error_detail,
                QMessageBox.StandardButton.Cancel
            )
            return

        popup = dialogs.ExportFrame(
            width=self.player.width,
            height=self.player.height,
            parent=self
        )

        result = popup.exec()

        if result:
            settings = popup.get_settings()

            filename, _filetype = QFileDialog.getSaveFileName(
                self,
                L.dialog.export_image_as,
                os.path.join(self.last_save_location, f"{self.file_savename}{constants.ImageFormatCode.PNG.value}"),
                f"{L.dialog.png_files} (*{constants.ImageFormatCode.PNG.value});;"
                f"{L.dialog.jpeg_files} (*{constants.ImageFormatCode.JPEG.value});;"
                f"{L.dialog.bmp_files} (*{constants.ImageFormatCode.BITMAP.value})"
            )

            if filename != "":
                _file_path, _file_title = os.path.split(filename)
                self.last_save_location = _file_path
                try:
                    self.renderer.export_frame(
                        ms=self.player.get_position(),
                        filename=filename,
                        size=(settings["width"], settings["height"]),
                        keep_aspect=settings["keep_aspect"] # pyright: ignore[reportArgumentType]
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        L.dialog.export_error,
                        L.dialog.export_error_frame.format(error=str(e)),
                        QMessageBox.StandardButton.Ok
                    )
                else:
                    QMessageBox.information(
                        self,
                        L.dialog.export_complete,
                        L.dialog.export_complete_frame,
                        QMessageBox.StandardButton.Ok
                    )

    def export_audio_clicked(self) -> None:
        
        if self.bw.audio_filename is None:
            QMessageBox.critical(
                self,
                L.dialog.no_file_error,
                L.dialog.no_file_error_detail,
                QMessageBox.StandardButton.Cancel
            )
            return

        filename, _filetype = QFileDialog.getSaveFileName(
            self,
            L.dialog.export_audio_as,
            os.path.join(self.last_save_location, f"{self.file_savename}{constants.AudioFormatCode.MP3.value}"),
            f"{L.dialog.mp3_files} (*{constants.AudioFormatCode.MP3.value});;"
            f"{L.dialog.wav_files} (*{constants.AudioFormatCode.WAVE.value});;"
            f"{L.dialog.flac_files} (*{constants.AudioFormatCode.FLAC.value});;"
            f"{L.dialog.ogg_files} (*{constants.AudioFormatCode.OGG.value});;"
            f"{L.dialog.m4a_files} (*{constants.AudioFormatCode.M4A.value})"
        )

        if filename != "":
            _file_path, _file_title = os.path.split(filename)
            self.last_save_location = _file_path
            try:
                self.renderer.export_audio(
                    filename=filename
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    L.dialog.export_error,
                    L.dialog.export_error_audio.format(error=str(e)),
                    QMessageBox.StandardButton.Ok
                )
            else:
                QMessageBox.information(
                    self,
                    L.dialog.export_complete,
                    L.dialog.export_complete_audio,
                    QMessageBox.StandardButton.Ok
                )

    def export_sequence_clicked(self) -> None:
        
        if self.bw.audio_filename is None:
            QMessageBox.critical(
                self,
                L.dialog.no_file_error,
                L.dialog.no_file_error_detail,
                QMessageBox.StandardButton.Cancel
            )
            return

        popup = dialogs.ExportSequence(
            width=self.player.width,
            height=self.player.height,
            parent=self
        )

        result = popup.exec()

        if result:
            settings = popup.get_settings()

            file_dir = QFileDialog.getExistingDirectory(
                self,
                L.dialog.export_image_sequence_to,
                self.last_save_location
            )

            if file_dir != "":
                _file_dir_parent, _file_dir_title = os.path.split(file_dir)
                self.last_save_location = _file_dir_parent
                frame_count = self.renderer.get_frame_count(
                    fps=settings["fps"] # pyright: ignore[reportArgumentType]
                )
                progress_popup = QProgressDialog(L.dialog.exporting_image_sequence, L.dialog.export_aborted, 0, frame_count, self)
                progress_popup.setWindowModality(Qt.WindowModality.WindowModal)
                progress_popup.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)
                progress_popup.setWindowTitle(L.dialog.exporting_images)
                progress_popup.setFixedSize(300, 100)

                try:
                    self.renderer.export_sequence(
                        directory=file_dir,
                        size=(settings["width"], settings["height"]), # pyright: ignore[reportArgumentType]
                        fps=settings["fps"], # pyright: ignore[reportArgumentType]
                        keep_aspect=settings["keep_aspect"], # pyright: ignore[reportArgumentType]
                        image_format=settings["format"], # pyright: ignore[reportArgumentType]
                        progress_dialog=progress_popup
                    )
                except Exception as e:
                    progress_popup.cancel()
                    QMessageBox.critical(
                        self,
                        L.dialog.export_error,
                        L.dialog.export_error_sequence.format(error=str(e)),
                        QMessageBox.StandardButton.Ok
                    )
                else:
                    if progress_popup.wasCanceled():
                        # shutil.rmtree(file_dir) # Dangerous! May delete user data
                        QMessageBox.warning(
                            self,
                            L.dialog.export_aborted,
                            L.dialog.export_aborted_sequence,
                            QMessageBox.StandardButton.Ok
                        )
                    else:
                        QMessageBox.information(
                            self,
                            L.dialog.export_complete,
                            L.dialog.export_complete_sequence,
                            QMessageBox.StandardButton.Ok
                        )

    def export_video_clicked(self) -> None:

        if self.bw.audio_filename is None:
            QMessageBox.critical(
                self,
                L.dialog.no_file_error,
                L.dialog.no_file_error_detail,
                QMessageBox.StandardButton.Cancel
            )
            return

        popup = dialogs.ExportVideo(
            width=self.player.width,
            height=self.player.height,
            parent=self
        )

        result = popup.exec()

        if result:
            settings = popup.get_settings()

            filename, _filetype = QFileDialog.getSaveFileName(
                self,
                L.dialog.export_video_as,
                os.path.join(self.last_save_location, f"{self.file_savename}{constants.VideoFormatCode.MP4.value}"),
                f"{L.dialog.mp4_files} (*{constants.VideoFormatCode.MP4.value});;"
                f"{L.dialog.avi_files} (*{constants.VideoFormatCode.AVI.value});;"
                f"{L.dialog.mkv_files} (*{constants.VideoFormatCode.MKV.value});;"
                f"{L.dialog.mov_files} (*{constants.VideoFormatCode.MOV.value})"
            )

            if filename != "":
                _file_path, _file_title = os.path.split(filename)
                self.last_save_location = _file_path

                _file_main_name, file_ext = os.path.splitext(_file_title)
                file_ext = file_ext.lower()

                encoder_popup = dialogs.VideoEncoderSettings(
                    video_format=constants.VideoFormatCode(file_ext),
                    parent=self
                )

                encoder_result = encoder_popup.exec()

                if encoder_result:
                    encoder_settings = encoder_popup.get_settings()

                    frame_count = self.renderer.get_frame_count(
                        fps=settings["fps"]
                    )
                    progress_popup = QProgressDialog(L.dialog.rendering_frames, L.dialog.export_aborted, 0, frame_count, self)
                    progress_popup.setWindowModality(Qt.WindowModality.WindowModal)
                    progress_popup.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowContextHelpButtonHint)
                    progress_popup.setWindowTitle(L.dialog.exporting_video)
                    progress_popup.setFixedSize(300, 100)

                    try:
                        self.renderer.export_video(
                            filename=filename,
                            size=(settings["width"], settings["height"]), # pyright: ignore[reportArgumentType]
                            fps=settings["fps"],
                            keep_aspect=settings["keep_aspect"], # pyright: ignore[reportArgumentType]
                            progress_dialog=progress_popup,
                            codec=encoder_settings["codec"].value,
                            audio_codec=encoder_settings["audio_codec"].value,
                            bitrate=None,
                            audio_bitrate=None,
                            preset=encoder_settings["preset"].value
                        )
                    except Exception as e:
                        progress_popup.cancel()
                        QMessageBox.critical(
                            self,
                            L.dialog.export_error,
                            L.dialog.export_error_video.format(error=str(e)),
                            QMessageBox.StandardButton.Ok
                        )
                    else:
                        if progress_popup.wasCanceled():
                            QMessageBox.warning(
                                self,
                                L.dialog.export_aborted,
                                L.dialog.export_aborted_video,
                                QMessageBox.StandardButton.Ok
                            )
                        else:
                            QMessageBox.information(
                                self,
                                L.dialog.export_complete,
                                L.dialog.export_complete_video,
                                QMessageBox.StandardButton.Ok
                            )

    def hotkeys_clicked(self) -> None:
        popup = dialogs.HotkeysInfo(parent=self)

        popup.exec()

    def about_clicked(self) -> None:
        popup = dialogs.About(parent=self)

        popup.exec()
