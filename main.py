import sys
import os
import tkinter as tk
from tkinter import messagebox
import ctypes
import textwrap  # 【核心新增】导入 textwrap 模块


# ======================================================
# 强制将工作目录设置为EXE所在的目录
# ======================================================
def set_working_directory():
    try:
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            os.chdir(exe_dir)
    except Exception:
        pass


set_working_directory()
# ======================================================

try:
    import _hidden_imports
except ImportError:
    print("警告: 未找到自动生成的依赖文件 '_hidden_imports.py'。")

# ======================================================
# 1. 明确导入最终使用的核心组件
# ======================================================
from core import CoreEngine
from gui_tk import TkinterGUI, FloatingNotice, RestartDialog, set_window_icon, set_app_id
from presenter import Presenter


# ======================================================
# 2. 启动前执行的辅助函数
# ======================================================

def attach_console_if_needed():
    if sys.platform.startswith('win') and '-console' in [arg.lower() for arg in sys.argv]:
        try:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            if not kernel32.AttachConsole(-1):
                if not kernel32.AllocConsole(): return
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
        # --- 自动模式逻辑 ---
        print("启动自动模式...")
        temp_root = tk.Tk()
        set_window_icon(temp_root)
        temp_root.wm_attributes("-toolwindow", 1)
        temp_root.geometry("0x0+10000+10000")
        notice = FloatingNotice(temp_root)

        def auto_progress_callback(current, total, plugin_name):
            progress = int(current / total * 100) if total > 0 else 0
            temp_root.after(0, notice.update_task, plugin_name, progress)

        # 【核心修复】将 presenter.py 中完善的错误处理逻辑移植到这里
        def step_3_show_dialogs(failed_plugins):
            user_wants_reboot = False
            if failed_plugins:
                failed_items = []
                for p in failed_plugins:
                    name = p.get('name', '未知插件')
                    error_msg = p.get('error', '未知错误')
                    full_error_line = f"- {name}: {error_msg}"
                    wrapped_lines = textwrap.wrap(
                        full_error_line, width=80, subsequent_indent='    '
                    )
                    failed_items.append("\n".join(wrapped_lines))

                failed_list = "\n\n".join(failed_items)
                message = f"自动执行完成，但存在失败项！\n\n{failed_list}"
                messagebox.showerror("自动执行有失败项", message, parent=temp_root)

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
    # 1. 为应用设置唯一的ID (为了任务栏图标)
    set_app_id("Tition.SysTools.1.0")

    # 2. 检查是否需要附加控制台
    attach_console_if_needed()

    # 3. 直接启动主程序
    main()