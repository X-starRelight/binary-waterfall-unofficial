# 子进程导出实现计划

> **对于自动化执行者：** 必须使用子技能：superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务执行本计划。使用复选框（`- [ ]`）语法跟踪进度。

**目标：** 将所有导出操作（图片、音频、图片序列、视频）放入子进程执行，主界面在导出期间永不阻塞。

**架构：** 每个导出任务运行在独立的 `multiprocessing.Process` 中，拥有自己的 `QApplication` 和 `QProgressDialog`。通信极简：主进程启动子进程，子进程通过退出码通知结果。守护线程等待进程结束，通过 `QTimer.singleShot` 将结果投递到主线程。

**技术栈：** Python multiprocessing、PySide6（QApplication、QProgressDialog、QMessageBox）、threading

---

## 文件结构

| 操作 | 文件 | 职责 |
|------|------|------|
| 新增 | `src/binary_waterfall_unofficial/export_manager.py` | `ExportManager` 类 + `export_worker` 函数 + `_SubprocessDialog` 包装器 |
| 修改 | `src/binary_waterfall_unofficial/core.py:44` | 添加 `multiprocessing.freeze_support()` |
| 修改 | `src/binary_waterfall_unofficial/window.py:33-70` | 初始化 `ExportManager`，替换 4 个导出方法中的直接 `renderer` 调用 |
| 修改 | `src/binary_waterfall_unofficial/window.py:1154-1162` | 覆写 `closeEvent` 处理导出中的关闭 |

---

## 任务 1：创建 export_manager.py 核心文件

**文件：**
- 新增：`src/binary_waterfall_unofficial/export_manager.py`

- [ ] **步骤 1：创建 export_manager.py，包含 CancelledException、_SubprocessDialog、export_worker 和 ExportManager**

```python
# src/binary_waterfall_unofficial/export_manager.py
"""基于子进程的导出管理器。

每个导出任务运行在独立的 multiprocessing.Process 中，
拥有自己的 QApplication 和 QProgressDialog。主进程保持响应。
"""
from __future__ import annotations

import sys
import multiprocessing
import threading
from typing import Any

from PySide6.QtCore import QObject, QTimer, Qt, Signal
from PySide6.QtWidgets import QApplication, QProgressDialog, QMessageBox


class CancelledException(Exception):
    """用户取消导出时抛出。"""
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

    # 在子进程中重建 BinaryWaterfall
    from . import generators
    bw = generators.BinaryWaterfall(**bw_params)

    from .outputs import Renderer
    renderer = Renderer(bw)

    # 创建进度对话框（子进程自己的）
    progress = QProgressDialog("准备中...", "取消", 0, 100)
    progress.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress.setWindowFlags(
        progress.windowFlags()
        | Qt.WindowType.WindowStaysOnTopHint
        | Qt.WindowType.WindowContextHelpButtonHint
    )
    progress.setWindowTitle(f"导出{export_type}")
    progress.setMinimumWidth(350)
    progress.show()
    app.processEvents()

    dialog = _SubprocessDialog(progress, app)

    try:
        if export_type == "frame":
            renderer.export_frame(**export_params)
        elif export_type == "audio":
            renderer.export_audio(**export_params)
        elif export_type == "sequence":
            renderer.export_sequence(**export_params, progress_dialog=dialog)
        elif export_type == "video":
            renderer.export_video(**export_params, progress_dialog=dialog)

        progress.close()

        if not dialog.wasCanceled():
            # 成功：在子进程内弹出完成对话框
            from .lang import L
            _map = {
                "frame": L.dialog.export_complete_frame,
                "audio": L.dialog.export_complete_audio,
                "sequence": L.dialog.export_complete_sequence,
                "video": L.dialog.export_complete_video,
            }
            QMessageBox.information(
                None,
                L.dialog.export_complete,
                _map.get(export_type, "导出成功"),
            )
            sys.exit(0)
        else:
            # 导出过程中用户点击了取消
            from .lang import L
            _abort_map = {
                "frame": getattr(L.dialog, "export_aborted_frame", "导出已取消"),
                "audio": getattr(L.dialog, "export_aborted_frame", "导出已取消"),
                "sequence": getattr(L.dialog, "export_aborted_sequence", "导出已取消"),
                "video": getattr(L.dialog, "export_aborted_video", "导出已取消"),
            }
            QMessageBox.warning(
                None,
                L.dialog.export_aborted,
                _abort_map.get(export_type, L.dialog.export_aborted),
            )
            sys.exit(2)

    except CancelledException:
        progress.close()
        from .lang import L
        QMessageBox.warning(
            None,
            L.dialog.export_aborted,
            L.dialog.export_aborted,
        )
        sys.exit(2)

    except Exception as e:
        progress.close()
        from .lang import L
        _err_map = {
            "frame": L.dialog.export_error_frame,
            "audio": L.dialog.export_error_audio,
            "sequence": L.dialog.export_error_sequence,
            "video": L.dialog.export_error_video,
        }
        msg = _err_map.get(export_type, "导出失败")
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

        # 守护线程：阻塞在 join() 上，完成后将结果投递到主线程
        t = threading.Thread(target=self._wait, args=(task_id, p), daemon=True)
        t.start()

        return task_id

    def _wait(self, task_id: int, process: multiprocessing.Process) -> None:
        process.join()
        # 通过 Qt 信号投递回主线程
        QTimer.singleShot(0, lambda: self._on_done(task_id, process.exitcode or 0))

    def _on_done(self, task_id: int, exit_code: int) -> None:
        self._active.pop(task_id, None)
        self.task_done.emit(task_id, exit_code)

    def has_active_exports(self) -> bool:
        """是否有正在运行的导出任务。"""
        return len(self._active) > 0

    def kill_all(self) -> None:
        """终止所有活跃的导出子进程。"""
        for p in self._active.values():
            p.terminate()
        self._active.clear()
```

- [ ] **步骤 2：验证文件创建正确**

运行：`python -c "from src.binary_waterfall_unofficial.export_manager import ExportManager, export_worker; print('OK')"`
预期输出：`OK`

---

## 任务 2：在 core.py 中添加 multiprocessing.freeze_support()

**文件：**
- 修改：`src/binary_waterfall_unofficial/core.py:44-59`

- [ ] **步骤 1：在 core.py 顶部添加 multiprocessing 导入**

将：

```python
import os
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from . import window, constants
```

改为：

```python
import os
import sys
import multiprocessing
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from . import window, constants
```

- [ ] **步骤 2：在 main() 函数第一行添加 freeze_support**

在 `core.py` 中，将 `def main(args: list[str]):` 改为：

```python
def main(args: list[str]):
    multiprocessing.freeze_support()

    if constants.HAS_SPLASH:
        # ... 后续代码不变
```

- [ ] **步骤 3：验证语法**

运行：`python -c "from src.binary_waterfall_unofficial import core; print('OK')"`
预期输出：`OK`

---

## 任务 3：在 MyQMainWindow 中添加 _get_bw_params 辅助方法

**文件：**
- 修改：`src/binary_waterfall_unofficial/window.py`（MyQMainWindow 类，约第 70 行之后）

- [ ] **步骤 1：添加 _get_bw_params 方法和 import ExportManager**

在 `window.py` 中，添加 `ExportManager` 到导入。将：

```python
from . import constants, generators, outputs, widgets, dialogs
```

改为：

```python
from . import constants, generators, outputs, widgets, dialogs
from .export_manager import ExportManager
```

然后在 `MyQMainWindow` 类中添加辅助方法（在 `set_file_savename` 之后，约第 76 行）：

```python
    def _get_bw_params(self) -> dict[str, Any]:
        """将当前 BinaryWaterfall 状态序列化，用于子进程重建。"""
        return {
            "filename": self.bw.filename,
            "width": self.bw.width,
            "height": self.bw.height,
            "color_format_string": self.bw._color_format_string,  # pyright: ignore[reportPrivateUsage]
            "num_channels": self.bw.num_channels,
            "sample_bytes": self.bw.sample_bytes,
            "sample_rate": self.bw.sample_rate,
            "volume": self.bw.volume,
            "endianness": self.bw.endianness,
            "flip_v": self.bw.flip_v,
            "flip_h": self.bw.flip_h,
            "alignment": self.bw.alignment,
            "playhead_visible": self.bw.playhead_visible,
        }
```

- [ ] **步骤 2：检查 BinaryWaterfall 是否存储了 color_format_string**

需要验证 `bw._color_format_string` 属性是否存在。运行：

`grep -n "color_format_string" src/binary_waterfall_unofficial/generators.py`

- [ ] **步骤 3：如果 color_format_string 未被存储，将其添加到 BinaryWaterfall.__init__**

在 `generators.py` 中，找到 `self.set_color_format(color_format_string=color_format_string)` 调用（约第 87 行），在其后添加：

```python
        self._color_format_string: str = color_format_string
```

- [ ] **步骤 4：验证语法**

运行：`python -c "from src.binary_waterfall_unofficial.window import MyQMainWindow; print('OK')"`
预期输出：`OK`

---

## 任务 4：在 MyQMainWindow.__init__ 中初始化 ExportManager

**文件：**
- 修改：`src/binary_waterfall_unofficial/window.py:34-69`（MyQMainWindow.__init__）

- [ ] **步骤 1：在 self.renderer 之后添加 export_manager 初始化**

在 `window.py` 的 `MyQMainWindow.__init__` 中，第 50 行（`self.renderer = outputs.Renderer(...)`）之后，添加：

```python
        self.export_manager = ExportManager(self)
        self.export_manager.task_done.connect(self._on_export_done)
```

- [ ] **步骤 2：在 MyQMainWindow 中添加 _on_export_done 回调方法**

在类中添加此方法（靠近其他导出方法）：

```python
    def _on_export_done(self, task_id: int, exit_code: int) -> None:
        """导出子进程完成时调用。"""
        # 子进程已自行弹出成功/错误/取消对话框。
        # 主进程不重复弹窗。
        # 此槽函数留作将来使用（如日志记录、状态栏更新）。
        pass
```

- [ ] **步骤 3：验证语法**

运行：`python -c "from src.binary_waterfall_unofficial.window import MyQMainWindow; print('OK')"`
预期输出：`OK`

---

## 任务 5：替换 export_image_clicked 使用子进程

**文件：**
- 修改：`src/binary_waterfall_unofficial/window.py:885-939`（export_image_clicked 方法）

- [ ] **步骤 1：替换整个 export_image_clicked 方法**

```python
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
                self.export_manager.start_export(
                    "frame",
                    bw_params=self._get_bw_params(),
                    export_params={
                        "ms": self.player.get_position(),
                        "filename": filename,
                        "size": (settings["width"], settings["height"]),
                        "keep_aspect": settings["keep_aspect"],
                    },
                )
```

- [ ] **步骤 2：验证语法**

运行：`python -c "from src.binary_waterfall_unofficial.window import MyQMainWindow; print('OK')"`
预期输出：`OK`

---

## 任务 6：替换 export_audio_clicked 使用子进程

**文件：**
- 修改：`src/binary_waterfall_unofficial/window.py:941-983`（export_audio_clicked 方法）

- [ ] **步骤 1：替换整个 export_audio_clicked 方法**

```python
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
            self.export_manager.start_export(
                "audio",
                bw_params=self._get_bw_params(),
                export_params={
                    "filename": filename,
                },
            )
```

- [ ] **步骤 2：验证语法**

运行：`python -c "from src.binary_waterfall_unofficial.window import MyQMainWindow; print('OK')"`
预期输出：`OK`

---

## 任务 7：替换 export_sequence_clicked 使用子进程

**文件：**
- 修改：`src/binary_waterfall_unofficial/window.py:985-1057`（export_sequence_clicked 方法）

- [ ] **步骤 1：替换整个 export_sequence_clicked 方法**

```python
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
                self.export_manager.start_export(
                    "sequence",
                    bw_params=self._get_bw_params(),
                    export_params={
                        "directory": file_dir,
                        "fps": settings["fps"],
                        "size": (settings["width"], settings["height"]),
                        "keep_aspect": settings["keep_aspect"],
                        "image_format": settings["format"],
                    },
                )
```

- [ ] **步骤 2：验证语法**

运行：`python -c "from src.binary_waterfall_unofficial.window import MyQMainWindow; print('OK')"`
预期输出：`OK`

---

## 任务 8：替换 export_video_clicked 使用子进程

**文件：**
- 修改：`src/binary_waterfall_unofficial/window.py:1059-1152`（export_video_clicked 方法）

- [ ] **步骤 1：替换整个 export_video_clicked 方法**

```python
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

                    self.export_manager.start_export(
                        "video",
                        bw_params=self._get_bw_params(),
                        export_params={
                            "filename": filename,
                            "fps": settings["fps"],
                            "size": (settings["width"], settings["height"]),
                            "keep_aspect": settings["keep_aspect"],
                            "codec": encoder_settings["codec"].value,
                            "audio_codec": encoder_settings["audio_codec"].value,
                            "bitrate": None,
                            "audio_bitrate": None,
                            "preset": encoder_settings["preset"].value,
                        },
                    )
```

- [ ] **步骤 2：验证语法**

运行：`python -c "from src.binary_waterfall_unofficial.window import MyQMainWindow; print('OK')"`
预期输出：`OK`

---

## 任务 9：覆写 closeEvent 处理导出中的关闭

**文件：**
- 修改：`src/binary_waterfall_unofficial/window.py`（MyQMainWindow 类，添加新方法）

- [ ] **步骤 1：在 MyQMainWindow 中添加 closeEvent 覆写**

在 `MyQMainWindow` 类末尾（`hotkeys_clicked` 之前）添加：

```python
    def closeEvent(self, event) -> None:
        if not self.export_manager.has_active_exports():
            event.accept()
            return

        reply = QMessageBox.question(
            self,
            L.dialog.export_aborted,
            "有导出任务正在执行，是否关闭？\n关闭将中止所有导出。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.export_manager.kill_all()
            event.accept()
        else:
            event.ignore()
```

- [ ] **步骤 2：验证语法**

运行：`python -c "from src.binary_waterfall_unofficial.window import MyQMainWindow; print('OK')"`
预期输出：`OK`

---

## 任务 10：验证应用能正常启动

- [ ] **步骤 1：快速导入检查**

运行：`python -c "from src.binary_waterfall_unofficial import core; print('导入成功')"`
预期输出：`导入成功`

- [ ] **步骤 2：运行现有测试**

运行：`python -m pytest tests/ -v --tb=short 2>&1 | head -50`
预期：测试通过（或至少没有与导出相关的新失败）

---

## 任务 11：处理边界情况 - color_format_string 获取

**文件：**
- 修改：`src/binary_waterfall_unofficial/generators.py`（如需要）

- [ ] **步骤 1：检查 BinaryWaterfall 是否存储了 color_format_string**

运行：`grep -n "_color_format_string\|color_format_string" src/binary_waterfall_unofficial/generators.py`

如果 `_color_format_string` 属性不存在，需要添加。在 `generators.py` 中找到 `set_color_format` 方法：

```python
def set_color_format(self, color_format_string: str) -> None:
```

在该方法第一行之后添加：

```python
    self._color_format_string: str = color_format_string
```

- [ ] **步骤 2：验证属性可访问**

运行：`python -c "from src.binary_waterfall_unofficial.generators import BinaryWaterfall; bw = BinaryWaterfall(); print(bw._color_format_string)"`
预期：输出默认颜色格式字符串（如 `bgrx`）

---

## 任务 12：验证 Nuitka 构建兼容性

- [ ] **步骤 1：确认 core.py 中有 multiprocessing.freeze_support**

运行：`grep -n "freeze_support" src/binary_waterfall_unofficial/core.py`
预期：包含 `multiprocessing.freeze_support()` 的行

- [ ] **步骤 2：检查 build.py 的 multiprocessing 插件（可选但推荐）**

读取 `build.py`，检查是否需要添加 `--enable-plugin=multiprocessing`。对于 PySide6 的 Nuitka standalone 构建，multiprocessing 通常无需特殊插件即可工作。但如果遇到问题，在 `build.py` 的 `cmd` 列表中添加：

```python
'--enable-plugin=multiprocessing',
```

此步骤可选 — 先测试不加插件的 standalone 构建。
