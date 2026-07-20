"""
Nuitka 打包脚本
"""

import os
import sys
import subprocess
import yaml

def write_version_info(yaml_path: str, output_path: str):
    """从 version.yml 读取字段，生成 Nuitka 可用的版本信息文件"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    # 直接使用原始版本字符串，不修改
    version = data.get('Version', '0.0.0')
    # 其他字段
    company = data.get('CompanyName', '')
    file_desc = data.get('FileDescription', '')
    internal_name = data.get('InternalName', '')
    legal_copyright = data.get('LegalCopyright', '')
    original_filename = data.get('OriginalFilename', '')
    product_name = data.get('ProductName', '')

    # 写入版本信息文件（格式：key=value）
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"FileVersion={version}\n")
        f.write(f"ProductVersion={version}\n")
        if company:
            f.write(f"CompanyName={company}\n")
        if file_desc:
            f.write(f"FileDescription={file_desc}\n")
        if internal_name:
            f.write(f"InternalName={internal_name}\n")
        if legal_copyright:
            f.write(f"LegalCopyright={legal_copyright}\n")
        if original_filename:
            f.write(f"OriginalFilename={original_filename}\n")
        if product_name:
            f.write(f"ProductName={product_name}\n")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, 'src', 'binary_waterfall_unofficial')
    resources_dir = os.path.join(src_dir, 'resources')
    version_yaml = os.path.join(src_dir, 'version.yml')
    icon_ico = os.path.join(resources_dir, 'icon.ico')

    if not os.path.exists(icon_ico):
        print(f"错误：找不到图标文件：{icon_ico}")
        sys.exit(1)
    if not os.path.exists(version_yaml):
        print(f"错误：找不到版本文件：{version_yaml}")
        sys.exit(1)

    # 生成版本信息文件
    version_info_txt = os.path.join(base_dir, 'version_info.txt')
    write_version_info(version_yaml, version_info_txt)

    main_script = os.path.join(base_dir, 'binary_waterfall_unofficial.py')
    if not os.path.exists(main_script):
        print(f"错误：找不到主脚本：{main_script}")
        sys.exit(1)

    # ---------- 构建 Nuitka 命令 ----------
    cmd = [
        sys.executable, '-m', 'nuitka',
        main_script,
        '--standalone',
        # '--windows-console-mode=disable',
        '--enable-plugin=pyqt6',
        f'--windows-icon-from-ico={icon_ico}',
        f'--version-info={version_info_txt}',
        # 数据目录
        f'--include-data-dir={os.path.join(src_dir, "constants")}=src/binary_waterfall_unofficial/constants',
        f'--include-data-dir={os.path.join(src_dir, "helpers")}=src/binary_waterfall_unofficial/helpers',
        f'--include-data-dir={os.path.join(src_dir, "langs")}=src/binary_waterfall_unofficial/langs',
        f'--include-data-dir={resources_dir}=src/binary_waterfall_unofficial/resources',
        f'--include-data-file={version_yaml}=src/binary_waterfall_unofficial/version.yml',
        '--follow-imports',
        '--output-dir=dist',
    ]

    os.chdir(base_dir)
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
