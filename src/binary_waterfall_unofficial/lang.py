from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, fields
from typing import Any

from .constants import DATA_DIR


_CUSTOM_LANGS_DIR: str = os.path.join(DATA_DIR, "custom_langs")
_SETTINGS_FILE: str = os.path.join(DATA_DIR, "settings.json")
_BUILTIN_LANGS_DIR: str = os.path.join(os.path.dirname(__file__), "langs")


def _nested_get(data: dict[str, Any], dotted_key: str, default: str = "") -> str: # pyright: ignore[reportUnusedFunction]
    """从嵌套字典获取值"""
    parts = dotted_key.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part] # pyright: ignore[reportUnknownVariableType]
        else:
            return default
    return str(current) if not isinstance(current, str) else current # pyright: ignore[reportUnknownArgumentType]


def _merge_lang(current: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    """递归合并，当前语言缺失的 key 用 fallback 补全"""
    merged: dict[str, Any] = fallback.copy()
    for k, v in current.items():
        if k in merged and isinstance(v, dict) and isinstance(merged[k], dict):
            merged[k] = _merge_lang(v, merged[k]) # pyright: ignore[reportUnknownArgumentType]
        else:
            merged[k] = v
    return merged


# ==================== 静态 dataclass 定义（字段名固定，值从 JSON 加载） ====================

@dataclass(frozen=True)
class MenuLang:
    file: str
    settings: str
    export: str
    help: str
    language: str
    title: str


@dataclass(frozen=True)
class MenuFileLang:
    open: str
    close: str


@dataclass(frozen=True)
class MenuSettingsLang:
    audio: str
    video: str
    player: str


@dataclass(frozen=True)
class MenuExportLang:
    audio: str
    image: str
    image_sequence: str
    video: str


@dataclass(frozen=True)
class MenuHelpLang:
    hotkeys: str
    about: str


@dataclass(frozen=True)
class DialogLang:
    audio_settings: str
    video_settings: str
    player_settings: str
    export_image: str
    export_sequence: str
    export_video: str
    encoder_settings: str
    hotkey_info: str
    error: str
    warning: str
    invalid_color_format: str
    exporting_images: str
    exporting_video: str
    export_image_as: str
    export_audio_as: str
    export_video_as: str
    export_image_sequence_to: str
    open_file: str
    no_file_error: str
    no_file_error_detail: str
    export_error: str
    export_error_frame: str
    export_error_audio: str
    export_error_sequence: str
    export_error_video: str
    export_complete: str
    export_complete_frame: str
    export_complete_audio: str
    export_complete_sequence: str
    export_complete_video: str
    export_aborted: str
    export_aborted_frame: str
    export_aborted_sequence: str
    export_aborted_video: str
    rendering_frames: str
    exporting_image_sequence: str
    all_binary_files: str
    png_files: str
    jpeg_files: str
    bmp_files: str
    mp3_files: str
    wav_files: str
    flac_files: str
    ogg_files: str
    m4a_files: str
    mkv_files: str
    mov_files: str
    mp4_files: str
    avi_files: str
    abort: str
    language_restart_title: str
    language_restart_message: str
    language_restart_ok: str
    language_restart_restart_now: str
    export_width: str
    export_height: str
    aspect_ratio: str
    force: str
    image_format: str
    fps: str
    video_codec: str
    audio_codec: str
    encoder_preset: str
    file_is_empty: str
    file_is_small: str
    feat_disabled: str
    can_use_feat: str
    import_language: str
    import_language_title: str
    import_language_filter: str
    import_language_success: str
    import_language_error: str
    import_language_invalid: str
    remove_language: str
    remove_language_confirm: str
    remove_language_success: str
    fallback_language: str
    fallback_language_title: str
    fallback_language_desc: str
    fallback_language_current: str
    is_custom: str
    ffmpeg_not_found: str
    audio_export_error: str
    file_is_very_small: str


@dataclass(frozen=True)
class AudioLang:
    channels: str
    mono: str
    stereo: str
    sample_size: str
    sample_rate: str
    file_volume: str
    endianness: str
    little_endian: str
    big_endian: str


@dataclass(frozen=True)
class VideoLang:
    width: str
    height: str
    color_format: str
    audio_alignment: str
    frame_start: str
    frame_center: str
    frame_end: str
    playhead: str
    visible: str
    flip_vertical: str
    flip_horizontal: str
    flip: str


@dataclass(frozen=True)
class PlayerLang:
    max_dimension: str
    fps: str


@dataclass(frozen=True)
class HotkeysLang:
    play_pause: str
    forward: str
    back: str
    frame_forward: str
    frame_back: str
    restart: str
    volume_up: str
    volume_down: str
    mute: str
    key_spacebar: str
    key_right: str
    key_left: str
    key_up: str
    key_down: str


@dataclass(frozen=True)
class AboutLang:
    o_project_home: str
    m_project_home: str
    o_donate: str


@dataclass(frozen=True)
class Lang:
    """完整的语言 dataclass，字段名静态定义，值全部从 JSON 加载"""
    menu: MenuLang
    menu_file: MenuFileLang
    menu_settings: MenuSettingsLang
    menu_export: MenuExportLang
    menu_help: MenuHelpLang
    dialog: DialogLang
    audio: AudioLang
    video: VideoLang
    player: PlayerLang
    hotkeys: HotkeysLang
    about: AboutLang


# ==================== dataclass 构建辅助 ====================

def _build_from_dict(cls: type, data: dict[str, Any]) -> Any:
    """从字典构建 dataclass，只传入存在的字段"""
    field_names = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in data.items() if k in field_names}
    return cls(**filtered)


def _build_lang(data: dict[str, Any]) -> Lang:
    """从嵌套字典构建完整的 Lang dataclass"""
    return Lang(
        menu=_build_from_dict(MenuLang, data.get("menu", {})),
        menu_file=_build_from_dict(MenuFileLang, data.get("menu_file", {})),
        menu_settings=_build_from_dict(MenuSettingsLang, data.get("menu_settings", {})),
        menu_export=_build_from_dict(MenuExportLang, data.get("menu_export", {})),
        menu_help=_build_from_dict(MenuHelpLang, data.get("menu_help", {})),
        dialog=_build_from_dict(DialogLang, data.get("dialog", {})),
        audio=_build_from_dict(AudioLang, data.get("audio", {})),
        video=_build_from_dict(VideoLang, data.get("video", {})),
        player=_build_from_dict(PlayerLang, data.get("player", {})),
        hotkeys=_build_from_dict(HotkeysLang, data.get("hotkeys", {})),
        about=_build_from_dict(AboutLang, data.get("about", {})),
    )


# ==================== 状态管理 ====================

@dataclass
class _LangState:
    current: str = "en_us"
    fallback: str = "en_us"


class LangManager:
    def __init__(self) -> None:
        self._builtin: dict[str, dict[str, Any]] = {}
        self._custom: dict[str, dict[str, Any]] = {}
        self._state = _LangState()
        self._lang: Lang | None = None

    def init(self) -> None:
        """初始化：加载内置语言、用户语言、设置"""
        os.makedirs(_CUSTOM_LANGS_DIR, exist_ok=True)
        self._load_builtin()
        self._load_custom()
        self._load_settings()
        self._rebuild()

    def _load_builtin(self) -> None:
        for fname in os.listdir(_BUILTIN_LANGS_DIR):
            if fname.endswith(".json"):
                code = fname[:-5]
                with open(os.path.join(_BUILTIN_LANGS_DIR, fname), encoding="utf-8") as f:
                    self._builtin[code] = json.load(f)

    def _load_custom(self) -> None:
        if not os.path.isdir(_CUSTOM_LANGS_DIR):
            return
        for fname in os.listdir(_CUSTOM_LANGS_DIR):
            if fname.endswith(".json"):
                code = fname[:-5]
                with open(os.path.join(_CUSTOM_LANGS_DIR, fname), encoding="utf-8") as f:
                    self._custom[code] = json.load(f)

    def _load_settings(self) -> None:
        if not os.path.isfile(_SETTINGS_FILE):
            return
        try:
            with open(_SETTINGS_FILE, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
            self._state.current = data.get("language", "en_us")
            self._state.fallback = data.get("fallback_language", "en_us")
        except (json.JSONDecodeError, OSError):
            pass

    def save_settings(self) -> None:
        os.makedirs(os.path.dirname(_SETTINGS_FILE), exist_ok=True)
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "language": self._state.current,
                "fallback_language": self._state.fallback,
            }, f, indent=2, ensure_ascii=False)

    def _rebuild(self) -> None:
        """根据当前语言和回退语言重建 Lang dataclass"""
        fallback_data: dict[str, Any] = self._get_lang_data(self._state.fallback)
        current_data: dict[str, Any] = self._get_lang_data(self._state.current)
        merged: dict[str, Any] = _merge_lang(current_data, fallback_data)
        self._lang = _build_lang(merged)

    def _get_lang_data(self, code: str) -> dict[str, Any]:
        """获取语言数据，优先自定义，再内置"""
        if code in self._custom:
            return self._custom[code]
        if code in self._builtin:
            return self._builtin[code]
        return {}

    def available_languages(self) -> dict[str, str]:
        """返回所有可用语言 {code: display_name}"""
        result: dict[str, str] = {}
        for code in self._builtin:
            result[code] = self._get_display_name(code, self._builtin[code])
        for code in self._custom:
            if code not in result:
                result[code] = self._get_display_name(code, self._custom[code])
        return result

    def _get_display_name(self, code: str, data: dict[str, Any]) -> str:
        """从语言数据中获取显示名称"""
        meta: dict[str, str] = data.get("_meta", {})
        return meta.get("name", code)

    def set_language(self, code: str) -> None:
        """切换当前语言"""
        self._state.current = code
        self._rebuild()
        self.save_settings()

    def set_fallback(self, code: str) -> None:
        """设置回退语言"""
        self._state.fallback = code
        self._rebuild()
        self.save_settings()

    def import_language(self, src_path: str, code: str | None = None) -> str:
        """导入自定义语言文件，返回语言代码"""
        if code is None:
            code = os.path.splitext(os.path.basename(src_path))[0]
        dst = os.path.join(_CUSTOM_LANGS_DIR, f"{code}.json")
        shutil.copy2(src_path, dst)
        with open(dst, encoding="utf-8") as f:
            self._custom[code] = json.load(f)
        self._rebuild()
        return code

    def remove_language(self, code: str) -> bool:
        """删除自定义语言"""
        if code not in self._custom:
            return False
        path = os.path.join(_CUSTOM_LANGS_DIR, f"{code}.json")
        if os.path.isfile(path):
            os.remove(path)
        del self._custom[code]
        if self._state.current == code:
            self.set_language("en_us")
        else:
            self._rebuild()
        return True

    @property
    def current_code(self) -> str:
        return self._state.current

    @property
    def fallback_code(self) -> str:
        return self._state.fallback

    @property
    def custom_codes(self) -> list[str]:
        """返回所有自定义语言代码"""
        return list(self._custom.keys())

    @property
    def builtin_codes(self) -> list[str]:
        """返回所有内置语言代码"""
        return list(self._builtin.keys())

    @property
    def lang(self) -> Lang:
        """直接访问 Lang dataclass，支持 lang.menu.file 形式"""
        if self._lang is None:
            raise RuntimeError("LangManager not initialized. Call init() first.")
        return self._lang

    def save_app_settings(self, settings: dict[str, Any]) -> None:
        """Save application settings to settings.json"""
        os.makedirs(os.path.dirname(_SETTINGS_FILE), exist_ok=True)
        # Load existing settings first
        existing: dict[str, Any] = {}
        if os.path.isfile(_SETTINGS_FILE):
            try:
                with open(_SETTINGS_FILE, encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        # Merge with new settings
        existing.update(settings)
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    def load_app_settings(self) -> dict[str, Any]:
        """Load application settings from settings.json"""
        if not os.path.isfile(_SETTINGS_FILE):
            return {}
        try:
            with open(_SETTINGS_FILE, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
            # Remove language-only keys
            data.pop("language", None)
            data.pop("fallback_language", None)
            return data
        except (json.JSONDecodeError, OSError):
            return {}


# ==================== 全局单例 ====================

_manager = LangManager()


def get_manager() -> LangManager:
    return _manager


def __getattr__(name: str) -> Any:
    """支持 lang.menu.file 形式的直接属性访问"""
    if name in ("menu", "menu_file", "menu_settings", "menu_export", "menu_help",
                "dialog", "audio", "video", "player", "hotkeys", "about"):
        return getattr(_manager.lang, name)
    raise AttributeError(f"module 'lang' has no attribute {name!r}")

get_manager().init()
L = get_manager().lang # pyright: ignore[reportConstantRedefinition]
