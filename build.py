"""
Nuitka 打包脚本
"""

import argparse
import os
import shutil
import sys
import platform
import subprocess
import yaml



# Determine library path
if sys.platform == 'win32':
    lib_name = 'bw_accelerator.dll'
    lib_suffix = 'dll'
elif sys.platform == 'darwin':
    lib_name = 'libbw_accelerator.dylib'
    lib_suffix = 'dylib'
else:
    lib_name = 'libbw_accelerator.so'
    lib_suffix = 'so'


def parse_args():
    parser = argparse.ArgumentParser(description='Nuitka 打包脚本')
    parser.add_argument('--lib-path', type=str, default=None,
                        help='预编译的动态库路径，传入时跳过 cargo build')
    return parser.parse_args()


def main():
    args = parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, 'src', 'binary_waterfall_unofficial')
    resources_dir = os.path.join(src_dir, 'resources')
    version_yaml = os.path.join(src_dir, 'version.yml')
    icon_ico = os.path.join(resources_dir, 'icon.ico')
    main_script = os.path.join(base_dir, 'binary_waterfall_unofficial.py')

    # 检查必要文件
    for path in (icon_ico, version_yaml, main_script):
        if not os.path.exists(path):
            print(f"错误：找不到文件 {path}")
            sys.exit(1)

    # 读取 version.yml
    with open(version_yaml, 'r', encoding='utf-8') as f:
        ver = yaml.safe_load(f)

    # ---------- 基础命令 ----------
    cmd = [
        sys.executable, '-m', 'nuitka',
        main_script,
        '--standalone',
        '--enable-plugin=pyqt6',
        '--follow-imports',
        '--output-dir=build',
    ]

    # ---------- Qt6 多媒体插件 DLL ----------
    import PyQt6; 
    qt_multimedia_plugins = os.path.join(
        PyQt6.__path__[0], 'Qt6', 'plugins', 'multimedia'
    )
    qt_multimedia_plugins = os.path.normpath(qt_multimedia_plugins)
    if os.path.isdir(qt_multimedia_plugins):
        import glob as glob_mod
        dll_files = glob_mod.glob(os.path.join(qt_multimedia_plugins, f'*.{lib_suffix}'))
        for dll in dll_files:
            dll_name = os.path.basename(dll)
            cmd.append(f'--include-data-files={dll}=PyQt6/Qt6/plugins/multimedia/{dll_name}')
    else:
        print(f"警告：未找到 Qt6 多媒体插件目录 {qt_multimedia_plugins}，播放预览可能无法工作。")

    # ---------- 通用数据目录 ----------
    data_dirs = [
        ('langs', 'langs'),
        ('resources', 'resources'),
    ]
    for dir_name, target in data_dirs:
        src_path = os.path.join(src_dir, dir_name)
        if os.path.exists(src_path):
            cmd.append(f'--include-data-dir={src_path}=src/binary_waterfall_unofficial/{target}')
    cmd.append(f'--include-data-file={version_yaml}=src/binary_waterfall_unofficial/version.yml')

    # ---------- 版本信息（Nuitka 4.x 独立参数） ----------
    version_str = ver.get('Version', '0.0.0')
    # 去掉后缀，只保留数字部分（如果包含 '-' 则取前面）
    if '-' in version_str:
        version_num = version_str.split('-')[0]
    else:
        version_num = version_str
    # 确保是四段，不足补 .0
    parts = version_num.split('.')
    while len(parts) < 4:
        parts.append('0')
    version_four = '.'.join(parts[:4])

    cmd.append(f'--file-version={version_four}')
    cmd.append(f'--product-version={version_four}')

    # 其他字段直接传递
    if ver.get('CompanyName'):
        cmd.append(f'--company-name={ver["CompanyName"]}')
    if ver.get('FileDescription'):
        cmd.append(f'--file-description={ver["FileDescription"]}')
    if ver.get('ProductName'):
        cmd.append(f'--product-name={ver["ProductName"]}')
    if ver.get('LegalCopyright'):
        cmd.append(f'--copyright={ver["LegalCopyright"]}')
    # InternalName 和 OriginalFilename 没有直接对应选项，但可忽略或通过 --product-name 包含

    # ---------- 平台专用参数 ----------
    system = platform.system()
    if system == 'Windows':
        cmd.append(f'--windows-icon-from-ico={icon_ico}')
        # 如果希望隐藏控制台，取消注释：
        # cmd.append('--windows-console-mode=disable')
        print("检测到 Windows，已添加图标。")
    elif system == 'Linux':
        # Linux 可以添加图标（如果有 .png）
        # cmd.append(f'--linux-icon={icon_png}')
        print("检测到 Linux。")
    elif system == 'Darwin':
        # macOS 可添加图标（.icns）
        # cmd.append(f'--macos-app-icon={icon_icns}')
        print("检测到 macOS。")

    os.chdir(base_dir)

    # ---------- Rust accelerator ----------
    rust_dir = os.path.join(base_dir, 'src', 'bw_accelerator')
    dst_dir = os.path.join(base_dir, 'src', 'binary_waterfall_unofficial', 'bw_accelerator')
    os.makedirs(dst_dir, exist_ok=True)

    if args.lib_path:
        # 使用预编译的动态库
        lib_path = os.path.abspath(args.lib_path)
        if not os.path.isfile(lib_path):
            print(f"错误：指定的动态库不存在: {lib_path}")
            sys.exit(1)
        print(f"使用预编译动态库: {lib_path}")
        dst_lib = os.path.join(dst_dir, os.path.basename(lib_path))
        shutil.copy2(lib_path, dst_lib)
        import glob as glob_mod
        dll_files = glob_mod.glob(os.path.join(dst_dir, f'*.{lib_suffix}'))
        for dll in dll_files:
            dll_name = os.path.basename(dll)
            cmd.append(f'--include-data-files={dll}=bw_accelerator/{dll_name}')
    elif os.path.isdir(rust_dir):
        # 自动编译
        print("检测到 Rust 加速模块，尝试编译...")
        rust_cmd = ['cargo', 'build', '--release', '--manifest-path', os.path.join(rust_dir, 'Cargo.toml')]
        try:
            result = subprocess.run(rust_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print("Rust 加速模块编译成功！")
                src_lib = os.path.join(rust_dir, 'target', 'release', lib_name)
                dst_lib = os.path.join(dst_dir, lib_name)
                shutil.copy2(src_lib, dst_lib)
                import glob as glob_mod
                dll_files = glob_mod.glob(os.path.join(dst_dir, f'*.{lib_suffix}'))
                for dll in dll_files:
                    dll_name = os.path.basename(dll)
                    cmd.append(f'--include-data-files={dll}=bw_accelerator/{dll_name}')
            else:
                print(f"警告：Rust 编译失败，将使用 numpy 回退路径：\n{result.stderr}")
        except FileNotFoundError:
            print("警告：未找到 cargo 命令，Rust 加速模块将不可用。")
        except subprocess.TimeoutExpired:
            print("警告：Rust 编译超时，将使用 numpy 回退路径。")

    print("开始 Nuitka 编译...")
    print(f"命令：{' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("编译失败！")
        sys.exit(1)
    else:
        print("编译完成！")
        

if __name__ == '__main__':
    main()
