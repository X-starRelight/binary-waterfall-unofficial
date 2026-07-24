"""
Nuitka packaging script
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
    parser = argparse.ArgumentParser(description='Nuitka packaging script')
    parser.add_argument('--lib-path', type=str, default=None,
                        help='Path to the precompiled dynamic library, skip cargo build when passed in')
    parser.add_argument('--assume-yes-for-downloads', action='store_true',
                        help='Pass --assume-yes-for-downloads to Nuitka for CI usage')
    return parser.parse_args()


def main():
    args = parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, 'src', 'binary_waterfall_unofficial')
    resources_dir = os.path.join(src_dir, 'resources')
    version_yaml = os.path.join(src_dir, 'version.yml')
    icon_ico = os.path.join(resources_dir, 'icon.ico')
    main_script = os.path.join(base_dir, 'binary_waterfall_unofficial.py')

    # Check the necessary documents
    for path in (icon_ico, version_yaml, main_script):
        if not os.path.exists(path):
            print(f"Error: Can't find the file {path}")
            sys.exit(1)

    # Read version.yml
    with open(version_yaml, 'r', encoding='utf-8') as f:
        ver = yaml.safe_load(f)

    # ---------- Basic Commands ----------
    cmd = [
        sys.executable, '-m', 'nuitka',
        main_script,
        '--standalone',
        '--enable-plugin=pyside6',
        '--follow-imports',
        '--output-dir=build',
    ]

    if args.assume_yes_for_downloads:
        cmd.append('--assume-yes-for-downloads')

    # ---------- Qt6 multimedia plugin dynamic library ----------
    import PySide6
    qt_multimedia_plugins = os.path.join(
        PySide6.__path__[0], 'plugins', 'multimedia'
    )
    qt_multimedia_plugins = os.path.normpath(qt_multimedia_plugins)
    if os.path.isdir(qt_multimedia_plugins):
        import glob as glob_mod
        dll_files = glob_mod.glob(os.path.join(qt_multimedia_plugins, f'*.{lib_suffix}'))
        for dll in dll_files:
            dll_name = os.path.basename(dll)
            cmd.append(f'--include-data-files={dll}=PySide6/plugins/multimedia/{dll_name}')
    else:
        print(f"Warning: Qt6 multimedia plugin directory {qt_multimedia_plugins} not found, preview playback may not work.")

    # ---------- General Data Catalog ----------
    data_dirs = [
        ('langs', 'langs'),
        ('resources', 'resources'),
    ]
    for dir_name, target in data_dirs:
        src_path = os.path.join(src_dir, dir_name)
        if os.path.exists(src_path):
            cmd.append(f'--include-data-dir={src_path}=src/binary_waterfall_unofficial/{target}')
    cmd.append(f'--include-data-file={version_yaml}=src/binary_waterfall_unofficial/version.yml')

    # ---------- Version Info ----------
    version_str = ver.get('Version', '0.0.0')
    if '-' in version_str:
        version_num = version_str.split('-')[0]
    else:
        version_num = version_str
    parts = version_num.split('.')
    while len(parts) < 4:
        parts.append('0')
    version_four = '.'.join(parts[:4])

    cmd.append(f'--file-version={version_four}')
    cmd.append(f'--product-version={version_four}')

    if ver.get('CompanyName'):
        cmd.append(f'--company-name={ver["CompanyName"]}')
    if ver.get('FileDescription'):
        cmd.append(f'--file-description={ver["FileDescription"]}')
    if ver.get('ProductName'):
        cmd.append(f'--product-name={ver["ProductName"]}')
    if ver.get('LegalCopyright'):
        cmd.append(f'--copyright={ver["LegalCopyright"]}')

    # ---------- Platform-specific parameters ----------
    system = platform.system()
    if system == 'Windows':
        cmd.append(f'--windows-icon-from-ico={icon_ico}')
        # cmd.append('--windows-console-mode=disable')
        print("Windows detected, icon added.")
    elif system == 'Linux':
        # cmd.append(f'--linux-icon={icon_png}')
        print("Linux detected.")
    elif system == 'Darwin':
        # cmd.append(f'--macos-app-icon={icon_icns}')
        print("macOS detected.")

    os.chdir(base_dir)

    # ---------- Rust accelerator ----------
    rust_dir = os.path.join(base_dir, 'src', 'bw_accelerator')
    dst_dir = os.path.join(base_dir, 'src', 'binary_waterfall_unofficial', 'bw_accelerator')
    os.makedirs(dst_dir, exist_ok=True)

    if args.lib_path:
        # Using precompiled dynamic libraries
        lib_path = os.path.abspath(args.lib_path)
        if not os.path.isfile(lib_path):
            print(f"Error: The specified dynamic library does not exist: {lib_path}")
            sys.exit(1)
        print(f"Using precompiled dynamic library: {lib_path}")
        dst_lib = os.path.join(dst_dir, os.path.basename(lib_path))
        shutil.copy2(lib_path, dst_lib)
        import glob as glob_mod
        dll_files = glob_mod.glob(os.path.join(dst_dir, f'*.{lib_suffix}'))
        for dll in dll_files:
            dll_name = os.path.basename(dll)
            cmd.append(f'--include-data-files={dll}=bw_accelerator/{dll_name}')
    elif os.path.isdir(rust_dir):
        # Automatic compilation
        print("Rust acceleration module detected, trying to compile...")
        rust_cmd = ['cargo', 'build', '--release', '--manifest-path', os.path.join(rust_dir, 'Cargo.toml')]
        try:
            result = subprocess.run(rust_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print("Rust module compilation acceleration succeeded!")
                src_lib = os.path.join(rust_dir, 'target', 'release', lib_name)
                dst_lib = os.path.join(dst_dir, lib_name)
                shutil.copy2(src_lib, dst_lib)
                import glob as glob_mod
                dll_files = glob_mod.glob(os.path.join(dst_dir, f'*.{lib_suffix}'))
                for dll in dll_files:
                    dll_name = os.path.basename(dll)
                    cmd.append(f'--include-data-files={dll}=bw_accelerator/{dll_name}')
            else:
                print(f"Warning: Rust compilation failed, falling back to the numpy path: \n{result.stderr}")
        except FileNotFoundError:
            print("Warning: The cargo command was not found, the Rust acceleration module will be unavailable.")
        except subprocess.TimeoutExpired:
            print("Warning: Rust compilation timed out, will fall back to numpy.")

    print("Starting Nuitka compilation...")
    print(f"Commands: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("Compilation failed!")
        sys.exit(1)
    else:
        print("Compilation complete!")
        

if __name__ == '__main__':
    main()
