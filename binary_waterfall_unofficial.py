import sys
import ctypes
import os


def hide_console_if_detached():
    """双击启动时销毁控制台，命令行启动时保留"""
    if sys.platform != "win32":
        return
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        # 获取当前控制台的进程列表
        procs = (ctypes.c_uint * 2)()
        count = kernel32.GetConsoleProcessList(procs, 2)
        # count == 1 表示只有本进程使用这个控制台（即双击启动）
        if count == 1:
            kernel32.FreeConsole()  # 直接销毁控制台
    
            # 重定向 stdout/stderr，防止写入已关闭的控制台导致程序崩溃
            if hasattr(sys, 'stdout'):
                sys.stdout = open(os.devnull, 'w')
            if hasattr(sys, 'stderr'):
                sys.stderr = open(os.devnull, 'w')
    except Exception:
        pass

# 在程序入口第一行调用
hide_console_if_detached()
print('qt.multimedia.ffmpeg: Using Qt multimedia with FFmpeg version 7.1.3 LGPL version 2.1 or later')

from src import binary_waterfall_unofficial

if __name__ == "__main__":
    binary_waterfall_unofficial.run()
