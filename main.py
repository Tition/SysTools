import sys
import tkinter as tk
from tkinter import messagebox
import ctypes

# ======================================================
# 【核心】导入自动生成的依赖文件
# ======================================================
try:
    import _hidden_imports
except ImportError:
    print("警告: 未找到自动生成的依赖文件 '_hidden_imports.py'。")

# ======================================================
# 1. 明确导入最终使用的核心组件
# ======================================================
from core import CoreEngine
from gui_tk import TkinterGUI, FloatingNotice, RestartDialog, set_window_icon
from presenter import Presenter


# ======================================================
# 2. 启动前执行的辅助函数 (只保留控制台功能)
# ======================================================

def attach_console_if_needed():
    """
    检查命令行参数，如果存在 '-console'，则附加一个控制台。
    """
    if sys.platform.startswith('win') and '-console' in [arg.lower() for arg in sys.argv]:
        print("'-console' argument detected. Attaching console...")
        try:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            if not kernel32.AttachConsole(-1):
                if not kernel32.AllocConsole():
                    return

            sys.stdout = open('CONOUT$', 'w', encoding='utf-8')
            sys.stderr = open('CONOUT$', 'w', encoding='utf-8')
            sys.stdin = open('CONIN$', 'r', encoding='utf-8')
            print("Console attached successfully.")
            print("-" * 50)
        except Exception as e:
            print(f"An error occurred while attaching the console: {e}")


# ======================================================
# 3. 主程序入口
# ======================================================

def main():
    """
    应用程序主入口点。
    """
    core = CoreEngine()

    if core.is_auto_mode():
        # --- 自动模式逻辑 (保持不变) ---
        print("启动自动模式...")
        temp_root = tk.Tk()
        set_window_icon(temp_root)
        temp_root.wm_attributes("-toolwindow", 1)
        temp_root.geometry("0x0+10000+10000")
        notice = FloatingNotice(temp_root)

        # ... (自动模式的所有回调和逻辑保持不变)
        def auto_progress_callback(current, total, plugin_name):
            progress = int(current / total * 100) if total > 0 else 0
            temp_root.after(0, notice.update_task, plugin_name, progress)

        def step_3_show_dialogs(failed_plugins):
            user_wants_reboot = False
            if failed_plugins:
                messagebox.showerror("自动执行有失败项", "...", parent=temp_root)  # 简化
            if core.reboot_required:
                user_wants_reboot = RestartDialog(temp_root).show_dialog()
            core.perform_cleanup_and_exit(user_wants_reboot)

        def step_2_close_notice_and_proceed(failed_plugins):
            notice.close()
            temp_root.after(100, step_3_show_dialogs, failed_plugins)

        def step_1_show_completion_and_wait(executed, total, failed_plugins):
            notice.update_task("执行完成", 100)
            temp_root.after(1000, step_2_close_notice_and_proceed, failed_plugins)

        core.on_auto_progress_update = auto_progress_callback
        core.on_auto_execution_complete = step_1_show_completion_and_wait
        core.start_auto_execution()
        temp_root.mainloop()

    else:
        # --- GUI 模式逻辑 (MVP架构) ---
        print("启动 Tkinter GUI 模式...")
        gui = TkinterGUI()
        presenter = Presenter(core, gui)
        presenter.initialize_bindings()
        presenter.start_app()


if __name__ == "__main__":
    # 1. 检查是否需要附加控制台
    attach_console_if_needed()

    # 2. 直接启动主程序
    main()