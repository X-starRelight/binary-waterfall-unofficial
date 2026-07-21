# <img src="src/binary_waterfall_unofficial/resources/icon.png" height="20px" alt="Binary Waterfall"/> Binary Waterfall (Unofficial Enhanced Version)

## English

### A Raw Data Media Player (Unofficial Enhanced Version)


<p align="center"><img src="docs/example.png" width="400px" alt="View pictures with mspaint.exe"/></p>

<p align="center"><a href="./video/The sounds of Microsoft Paint.mp4">Inspired by this video.</a></p>

### Downloads
Sorry. Not at the moment.

### Attribution
If you use this program to create videos or other projects, you must provide attribution. Whether your project is for profit or not, attribution is required. Please copy the following attribution statement in full in your video description, or include it in your project's references in another way:
```
Project used:
Modified version maintained by XstarRelight (xr):
https://github.com/X-starRelight/binary-waterfall-unofficial
```

### Showcase Video
The author of this project hasn't recorded any videos yet.

### Original Author
- Ella Jameson

### Modified Author
- XstarRelight (xr).

### License
This project is released under the GNU GPL v3.0 open-source license.

### How to Use the Source Code

#### Installation:

**The maintainer suggests you use uv to install dependencies, so please install uv first.**

Run this in the project's root directory:
``` bash
uv sync
uv sync --group build
```

#### Run:

Run this in the project's root directory:
``` bash
uv run binary_waterfall_unofficial.py
```

#### Build:

Run this in the project's root directory:
``` bash
uv run build.py
```

The build output will be at
'./build/binary_waterfall_unofficial.dist/'

### User Guide

> **Note:** This guide describes the **unofficial enhanced version**. Features marked with 🆕 are **not available** in the original Binary Waterfall.

#### Main Interface

The main window consists of three areas:

| Area | Description |
|------|-------------|
| **Display area** | Shows the waterfall visualization of the currently playing file. |
| **Progress bar** | Indicates playback position; click or drag to seek. |
| **Control bar** | Contains playback buttons, volume controls, and status indicators. |

**Control bar elements** (from left to right):
- Play/Pause button
- Rewind / Fast Forward buttons
- Restart button
- Volume slider
- Volume icon (click to mute/unmute)
- Volume percentage display

---

#### Menu Bar

##### File
| Menu item | Action |
|-----------|--------|
| **Open** | Open a file dialog to select any binary file (`.exe`, `.png`, etc.). |
| **Close** | Close the currently opened file. |

##### Settings
| Menu item | Sub‑items |
|-----------|-----------|
| **Audio Settings** 🆕 | Adjust channels, bit depth, sample rate, file volume, and byte order. |
| **Video Settings** 🆕 | Adjust width/height, color format, audio alignment, playhead visibility, and horizontal/vertical flip. |
| **Player Settings** 🆕 | Adjust maximum display size (pixels) and playback frame rate (FPS). |
| **Language** 🆕 | Switch language, import/remove custom languages, set fallback language. |

##### Export 🆕
| Menu item | Action |
|-----------|--------|
| **Export Audio** | Export the current audio stream as MP3, WAV, FLAC, OGG, or M4A. |
| **Export Image** | Export the current frame as PNG, JPEG, or BMP. |
| **Export Image Sequence** | Export a sequence of frames as images (configurable frame rate, size, and format). |
| **Export Video** | Export the playback as MP4, AVI, MKV, or MOV (choose video/audio codec and encoding speed). |

##### Help
| Menu item | Action |
|-----------|--------|
| **Shortcuts** | Display a list of all keyboard shortcuts. |
| **About** | Show software information and version. |

---

#### Settings Dialog Details

##### Audio Settings 🆕
| Parameter | Description |
|-----------|-------------|
| Channels | Number of audio channels |
| Bit Depth | Sample bit depth |
| Sample Rate | Sampling rate in Hz |
| File Volume | Volume level of the file (not system volume) |
| Byte Order | Endianness (little/big) |

##### Video Settings 🆕
| Parameter | Description |
|-----------|-------------|
| Width / Height | Display dimensions in pixels |
| Color Format | Color mapping scheme |
| Audio Alignment | Synchronization method |
| Playhead | Show/hide the playhead indicator |
| Flip | Horizontal / Vertical flip |

##### Player Settings 🆕
| Parameter | Description |
|-----------|-------------|
| Maximum Size | Max display size in pixels |
| Frame Rate | Playback FPS |

##### Export Codec Settings 🆕 (when exporting video)
| Parameter | Options |
|-----------|---------|
| Video Codec | e.g., H.264, H.265, VP9 |
| Audio Codec | e.g., AAC, MP3, Opus |
| Preset | Encoding speed vs. quality (e.g., fast, medium, slow) |

---

#### Keyboard Shortcuts

| Description | Key |
|-------------|-----|
| Play / Pause | `Spacebar` |
| Rewind | `←` (Left Arrow) |
| Fast Forward | `→` (Right Arrow) |
| Frame Backward | `<` (comma key) |
| Frame Forward | `>` (period key) |
| Restart | `R` |
| Volume Up | `↑` (Up Arrow) |
| Volume Down | `↓` (Down Arrow) |
| Mute / Unmute | `M` |

## 中文

### 原始数据媒体播放器（非官方增强版）


<p align="center"><img src="docs/example.png" width="400px" alt="查看 mspaint.exe 的图片"/></p>

<p align="center"><a href="./video/The sounds of Microsoft Paint.mp4">受此视频启发</a></p>

### 下载方式
对不起，暂时没有。

### 署名
如果你使用这个程序制作视频或其他项目，你必须提供署名。无论你的项目是否盈利，署名都是必须的。请在你的视频描述中完整复制以下署名声明，或者以其他方式将其包含在你项目的参考资料中：
```
使用的项目:
由 XstarRelight (xr) 维护的修改版本:
https://github.com/X-starRelight/binary-waterfall-unofficial
```

### 展示视频
本项目作者暂未录制视频。

### 原作者
- Ella Jameson

### 修改作者
- XstarRelight (xr)

### 许可证
本项目使用 GNU GPL v3.0 开源发布。

### 如何使用源代码

#### 安装：

**维护者建议您使用 uv 安装依赖，所以请首先安装 uv 。**

在项目根目录下执行：
``` bash
uv sync
uv sync --group build
```

#### 运行：

在项目根目录下执行：
``` bash
uv run binary_waterfall_unofficial.py
```

#### 编译：

``` bash
uv run build.py
```

编译结果就在
'./build/binary_waterfall_unofficial.dist/'

### 使用指南

> **注意：** 本指南针对**非官方增强版**。标记 🆕 的功能在原始 Binary Waterfall 中**不存在**。

---

#### 主界面

主窗口分为三个区域：

| 区域 | 说明 |
|------|------|
| **显示区** | 显示当前播放文件的瀑布流可视化效果。 |
| **进度条** | 显示播放位置，点击或拖动可跳转。 |
| **控制栏** | 包含播放按钮、音量控制和状态指示。 |

**控制栏元素**（从左到右）：
- 播放/暂停按钮
- 快退 / 快进按钮
- 重新开始按钮
- 音量滑块
- 音量图标（点击可静音/取消静音）
- 音量百分比显示

---

#### 菜单栏

##### 文件
| 菜单项 | 操作 |
|--------|------|
| **打开** | 弹出文件选择框，选择任意二进制文件（`.exe`、`.png` 等）打开。 |
| **关闭** | 关闭当前打开的文件。 |

##### 设置
| 菜单项 | 子项 |
|--------|------|
| **音频设置** 🆕 | 调整声道数、采样位数、采样率、文件音量、字节序。 |
| **视频设置** 🆕 | 调整宽/高、颜色格式、音频对齐方式、播放头可见性、水平/垂直翻转。 |
| **播放器设置** 🆕 | 调整最大显示尺寸（像素）、播放帧率（FPS）。 |
| **语言** 🆕 | 切换语言、导入/移除自定义语言、设置回退语言。 |

##### 导出 🆕
| 菜单项 | 操作 |
|--------|------|
| **导出音频** | 导出当前音频流为 MP3、WAV、FLAC、OGG 或 M4A。 |
| **导出图像** | 导出当前帧为 PNG、JPEG 或 BMP。 |
| **导出图像序列** | 导出连续帧为图片序列（可设置帧率、尺寸、格式）。 |
| **导出视频** | 导出播放内容为 MP4、AVI、MKV 或 MOV（可选择视频/音频编码器和编码速度）。 |

##### 帮助
| 菜单项 | 操作 |
|--------|------|
| **快捷键** | 显示所有键盘快捷键列表。 |
| **关于** | 显示软件信息和版本。 |

---

#### 设置对话框详解

##### 音频设置 🆕
| 参数 | 说明 |
|------|------|
| 声道数 | 音频声道数量 |
| 采样位数 | 采样位深 |
| 采样率 | 采样频率（Hz） |
| 文件音量 | 文件自身的音量（非系统音量） |
| 字节序 | 大小端（小端/大端） |

##### 视频设置 🆕
| 参数 | 说明 |
|------|------|
| 宽度/高度 | 显示尺寸（像素） |
| 颜色格式 | 颜色映射方案 |
| 音频对齐 | 同步方式 |
| 播放头 | 显示/隐藏播放头指示器 |
| 翻转 | 水平/垂直翻转 |

##### 播放器设置 🆕
| 参数 | 说明 |
|------|------|
| 最大尺寸 | 最大显示尺寸（像素） |
| 帧率 | 播放帧率（FPS） |

##### 导出视频编码器设置 🆕（导出视频时）
| 参数 | 可选值 |
|------|--------|
| 视频编码器 | 如 H.264、H.265、VP9 |
| 音频编码器 | 如 AAC、MP3、Opus |
| 预设 | 编码速度与质量平衡（如 fast、medium、slow） |

---

#### 键盘快捷键

| 描述 | 按键 |
|------|------|
| 播放 / 暂停 | `空格键` |
| 后退 | `←`（左箭头） |
| 前进 | `→`（右箭头） |
| 逐帧后退 | `<`（逗号键） |
| 逐帧前进 | `>`（句号键） |
| 重新开始 | `R` |
| 音量增大 | `↑`（上箭头） |
| 音量减小 | `↓`（下箭头） |
| 静音 / 取消静音 | `M` |
