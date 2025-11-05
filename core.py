import sys
import os
import threading
import time
import io
import argparse
import subprocess
import tempfile
from typing import List
from plugin_manager import PluginManager
from plugin_base import BasePlugin


# =============================================
# 修复编码问题
# =============================================
def fix_encoding():
    """修复Windows下的编码问题"""
    if sys.platform.startswith('win'):
        try:
            if (sys.stdout is not None and
                    hasattr(sys.stdout, 'encoding') and
                    sys.stdout.encoding != 'utf-8' and
                    hasattr(sys.stdout, 'buffer')):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            if (sys.stderr is not None and
                    hasattr(sys.stderr, 'encoding') and
                    sys.stderr.encoding != 'utf-8' and
                    hasattr(sys.stderr, 'buffer')):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass


fix_encoding()


# ======================================================
# 文件日志记录器
# ======================================================
class Logger(object):
    def __init__(self, filename="Default.log", stream=sys.stdout):
        if stream is None:
            print(f"警告: 原始输出流为None，日志将只写入文件: {filename}")
        self.terminal = stream
        self.log = open(filename, "a", encoding='utf-8', buffering=1)

    def write(self, message):
        if self.terminal is not None:
            try:
                self.terminal.write(message)
            except Exception:
                pass
        try:
            self.log.write(message)
        except Exception:
            pass

    def flush(self):
        if self.terminal is not None:
            try:
                self.terminal.flush()
            except Exception:
                pass
        try:
            self.log.flush()
        except Exception:
            pass

    def __del__(self):
        try:
            if self.log:
                self.log.close()
        except Exception:
            pass


# ======================================================
# 命令行参数解析
# ======================================================
def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='系统封装部署工具')
    parser.add_argument('-auto', '--auto', action='store_true', help='全自动模式：顺序执行所有插件')
    parser.add_argument('-debug', '--debug', action='store_true',
                        help='调试模式：模拟执行但不实际运行插件（随机成功/失败）')
    parser.add_argument('-debug-success', '--debug-success', action='store_true',
                        help='调试模式（全部成功）：模拟执行且所有插件都成功')
    parser.add_argument('-debuggui', '--debuggui', action='store_true',
                        help='GUI调试模式：在GUI界面中模拟执行插件（随机成功/失败）')
    parser.add_argument('-debuggui-success', '--debuggui-success', action='store_true',
                        help='GUI调试模式（全部成功）：在GUI界面中模拟执行插件且全部成功')
    parser.add_argument('-cleanup', '--cleanup', action='store_true',
                        help='在自动化任务执行完毕后，删除程序自身及其所有文件。')
    parser.add_argument('-test', '--test', action='store_true', help='测试模式：从 "plugins_test" 目录加载插件。')
    parser.add_argument('-console', '--console', action='store_true',
                        help='(内部使用) 为GUI应用附加一个控制台以显示日志。')
    return parser.parse_args()


# ======================================================
# 核心引擎类
# ======================================================
class CoreEngine:
    """
    应用程序的核心引擎。
    负责所有非GUI的逻辑，包括插件管理、执行、日志记录和状态管理。
    通过回调函数与GUI进行通信。
    """

    def __init__(self):
        # 1. 解析命令行参数
        self.args = parse_arguments()

        # 2. 状态变量
        self.reboot_required = False
        self.is_running = False
        self.plugins: List[BasePlugin] = []
        self.stop_requested = False

        # 3. 设置插件目录
        plugin_dir_name = "plugins_test" if self.args.test else "plugins"
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.plugins_dir = os.path.join(base_dir, plugin_dir_name)

        # 4. 初始化插件管理器
        self.plugin_manager = PluginManager(self.plugins_dir)

        # 5. 设置文件日志 (仅在自动模式下)
        if self.is_auto_mode():
            self._setup_file_logger()

        # 6. 定义与GUI通信的回调函数
        # GUI需要实现这些回调函数，并将它们赋值给CoreEngine的实例
        self.on_log_message = None  # (message: str, level: str) -> None
        self.on_progress_update = None  # (progress: float, current: int, total: int) -> None
        self.on_execution_complete = None  # (failed_plugins: list) -> None
        self.on_auto_progress_update = None  # (current: int, total: int, plugin_name: str) -> None
        self.on_auto_execution_complete = None  # (executed: int, total: int, failed_plugins: list) -> None
        self.on_plugin_state_change = None  # (plugin_name: str, state: str) -> None

    def is_auto_mode(self) -> bool:
        """检查当前是否处于任何一种非GUI的自动/调试模式"""
        return self.args.auto or self.args.debug or self.args.debug_success

    def request_stop(self):
        """外部请求停止当前执行的任务。"""
        self._log("接收到外部停止请求...", "warning")
        self.stop_requested = True

    def _log(self, message: str, level: str = "info"):
        """
        内部日志方法。
        如果注册了回调，则调用它；否则，打印到控制台。
        """
        print(f"[{level.upper()}] {message}")  # 始终在后台打印一份
        if self.on_log_message:
            self.on_log_message(message, level)

    def _setup_file_logger(self):
        """在自动化模式下，设置并启用文件日志记录"""
        try:
            log_dir = tempfile.gettempdir()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_filename = f"SysTools_AutoRun_{timestamp}.log"
            log_filepath = os.path.join(log_dir, log_filename)
            sys.stdout = Logger(log_filepath, sys.stdout)
            sys.stderr = Logger(log_filepath, sys.stderr)
            print("===================================================")
            print(f"自动化模式已启动，日志将被记录到: {log_filepath}")
            print(f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("===================================================")
        except Exception as e:
            print(f"错误：无法设置文件日志记录 - {e}")

    def load_plugins(self):
        """加载插件并更新内部列表"""
        self._log("开始加载插件...", "info")
        self.plugins = self.plugin_manager.discover_plugins()
        self._log(f"插件管理器返回了 {len(self.plugins)} 个插件", "info")

        if not self.plugins:
            self._log("警告: 未找到任何功能插件！", "warning")
            self._log(f"插件目录: {self.plugins_dir}", "info")
            if os.path.exists(self.plugins_dir):
                files = os.listdir(self.plugins_dir)
                self._log(f"插件目录内容: {files}", "info")
            else:
                self._log("插件目录不存在", "error")
        else:
            self._log(f"已加载 {len(self.plugins)} 个功能插件", "info")

    # --- GUI模式执行逻辑 ---

    def execute_plugins(self, plugins_to_execute: List[BasePlugin]):
        """
        启动一个新线程来执行指定的插件列表 (供GUI模式调用)。
        """
        if self.is_running:
            self._log("已有任务正在执行！", "warning")
            return

        self.is_running = True
        self.reboot_required = False
        self.stop_requested = False
        thread = threading.Thread(target=self._execute_plugins_thread, args=(plugins_to_execute,))
        thread.daemon = True
        thread.start()

    def _execute_plugins_thread(self, plugins_to_execute: List[BasePlugin]):
        """在后台线程中执行插件 (GUI模式)"""
        total_plugins = len(plugins_to_execute)
        failed_plugins = []
        debug_mode = self.args.debuggui or self.args.debuggui_success
        debug_success_mode = self.args.debuggui_success

        for i, plugin in enumerate(plugins_to_execute):
            if self.on_progress_update:
                progress = (i / total_plugins) * 100
                self.on_progress_update(progress, i, total_plugins)

            plugin_name = plugin.get_name()
            if self.on_plugin_state_change:
                self.on_plugin_state_change(plugin_name, 'starting')
            if self.stop_requested:
                self._log("执行被用户中断。", "warning")
                # 将当前插件和所有后续插件都标记为失败
                failed_plugins.append({'name': plugin.get_name(), 'error': '用户取消'})
                # 可以选择将后续所有未执行的插件也加入失败列表
                for p in plugins_to_execute[i+1:]:
                    failed_plugins.append({'name': p.get_name(), 'error': '未执行 (用户取消)'})
                break  # 跳出循环

            self._log(f"开始执行: {plugin_name}")

            try:
                result = {}
                if debug_mode:
                    import re, random
                    sleep_time = max(0.5, min(3.0, int(re.search(r'(\d+)', plugin_name).group(1)) * 0.3 if re.search(
                        r'(\d+)', plugin_name) else 1.0))
                    time.sleep(sleep_time)

                    if debug_success_mode or random.random() > 0.3:
                        result = {'success': True, 'message': f'GUI调试模式模拟成功 (耗时{sleep_time:.1f}秒)'}
                    else:
                        result = {'success': False, 'error': f'GUI调试模式模拟失败 (耗时{sleep_time:.1f}秒)'}
                else:
                    result = plugin.execute()

                if result.get('reboot', False):
                    self.reboot_required = True
                    self._log(f"  - {plugin_name} 请求在完成后重启系统。", "warning")

                if result.get('success', False):
                    self._log(f"✓ {plugin_name} 执行成功", "success")
                    if 'message' in result: self._log(f"    {result['message']}")
                else:
                    error_msg = result.get('error', '未知错误')
                    self._log(f"✗ {plugin_name} 执行失败: {error_msg}", "error")
                    failed_plugins.append({'name': plugin_name, 'error': error_msg})

            except Exception as e:
                self._log(f"✗ {plugin_name} 执行异常: {str(e)}", "error")
                failed_plugins.append({'name': plugin_name, 'error': str(e)})
            if self.on_plugin_state_change:
                self.on_plugin_state_change(plugin_name, 'finished')
        # 所有插件执行完毕
        self.is_running = False
        if self.on_execution_complete:
            self.on_execution_complete(failed_plugins)

    # --- 自动模式执行逻辑 ---

    def start_auto_execution(self):
        """
        启动自动执行模式。
        """
        print("进入自动执行模式" + (" (调试模式)" if (self.args.debug or self.args.debug_success) else ""))
        self.load_plugins()

        if not self.plugins:
            print("错误：未找到任何插件")
            if self.on_auto_progress_update:
                self.on_auto_progress_update(0, 0, "错误：未找到任何插件！")
            # 等待GUI显示错误后退出
            time.sleep(3)
            sys.exit(1)

        print(f"找到 {len(self.plugins)} 个插件，开始顺序执行...")
        thread = threading.Thread(target=self._auto_execute_plugins)
        thread.daemon = True
        thread.start()

    def _auto_execute_plugins(self):
        """在后台线程中自动执行所有插件"""
        total_plugins = len(self.plugins)
        failed_plugins = []

        for i, plugin in enumerate(self.plugins):
            if self.on_auto_progress_update:
                self.on_auto_progress_update(i, total_plugins, plugin.get_name())

            print(f"执行插件 {i + 1}/{total_plugins}: {plugin.get_name()}")

            result = {}
            if self.args.debug or self.args.debug_success:
                import re, random
                sleep_time = max(1.5, min(5.0, int(re.search(r'(\d+)', plugin.get_name()).group(1)) * 0.5 if re.search(
                    r'(\d+)', plugin.get_name()) else 2.0))
                time.sleep(sleep_time)

                if self.args.debug_success or random.random() > 0.3:
                    result = {'success': True, 'message': f'调试模式模拟成功 (耗时{sleep_time:.1f}秒)'}
                else:
                    result = {'success': False, 'error': f'调试模式模拟失败 (耗时{sleep_time:.1f}秒)'}
            else:
                try:
                    result = plugin.execute()
                except Exception as e:
                    result = {'success': False, 'error': str(e)}

            if result.get('reboot', False):
                self.reboot_required = True
                print(f"  - {plugin.get_name()} 请求在完成后重启系统。")

            if result.get('success', False):
                print(f"✓ {plugin.get_name()} 执行成功")
            else:
                error_msg = result.get('error', '未知错误')
                failed_plugins.append({'name': plugin.get_name(), 'error': error_msg})
                print(f"✗ {plugin.get_name()} 执行失败: {error_msg}")

        # 执行完成
        if self.on_auto_execution_complete:
            self.on_auto_execution_complete(len(self.plugins) - len(failed_plugins), total_plugins, failed_plugins)

    # --- 清理与自毁逻辑 ---

    def perform_cleanup_and_exit(self, user_wants_reboot: bool):
        """
        根据用户选择和命令行参数，执行最终的清理、重启或自毁操作。
        """
        if self.args.cleanup and user_wants_reboot:
            print("正在注册重启后自毁任务...")
            if self._schedule_post_reboot_cleanup():
                print("已注册重启后自毁任务，将在5秒后重启。")
                os.system("shutdown /r /t 5")
            else:
                print("错误：注册自毁任务失败！请手动清理。")
        elif self.args.cleanup:
            print("正在启动延时自毁...")
            self._initiate_delayed_self_destruct(reboot=False)
        elif user_wants_reboot:
            print("用户选择立即重启。将在5秒后重启计算机。")
            os.system("shutdown /r /t 5")

        print("程序即将退出...")
        os._exit(0)

    def _schedule_post_reboot_cleanup(self) -> bool:
        """创建重启后清理任务 (V2 - 文件夹模式)。"""
        try:
            if not getattr(sys, 'frozen', False):
                print("开发环境，跳过重启后自毁任务注册。")
                return True

            app_dir = os.path.dirname(sys.executable)
            temp_dir = tempfile.gettempdir()
            pid = os.getpid()
            task_name = f"SysToolsCleanup_{pid}"
            bat_path = os.path.join(temp_dir, f"systools_cleanup_{pid}.bat")
            log_file = os.path.join(temp_dir, f"systools_cleanup_log_{pid}.txt")

            # 直接删除整个应用目录
            bat_content = f"""
@echo off
cd /d %~dp0

(
    echo Post-Reboot Cleanup Started at %date% %time%
    echo Target Directory: {app_dir}
    echo.

    echo [Step 1] Deleting the entire application directory...
    rmdir /s /q "{app_dir}"
    echo Done.
    echo.
    
    echo [Step 2] Deleting the scheduled task itself...
    schtasks /Delete /TN "{task_name}" /F
    echo Done.
    echo.

    echo Post-Reboot Cleanup Finished.
) > "{log_file}" 2>&1

REM 最后，删除自己
(goto) 2>nul & del "%~f0"
"""
            with open(bat_path, "w", encoding="oem") as f:
                f.write(bat_content)

            command = ['schtasks', '/Create', '/TN', task_name, '/TR', f'"{bat_path}"', '/SC', 'ONLOGON', '/RL',
                       'HIGHEST', '/F']
            result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode == 0:
                print("成功创建开机自毁任务。")
                return True
            else:
                print(f"错误：创建任务计划失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"创建开机自毁任务时出错: {str(e)}")
            return False

    def _initiate_delayed_self_destruct(self, reboot: bool = False):
        """创建并以管理员权限启动一个延时的自毁脚本 (V2 - 文件夹模式)。"""
        try:
            if not getattr(sys, 'frozen', False):
                print("开发环境，跳过自毁。")
                return

            app_dir = os.path.dirname(sys.executable)
            temp_dir = tempfile.gettempdir()
            pid = os.getpid()
            bat_path = os.path.join(temp_dir, f"systools_cleanup_{pid}.bat")
            vbs_path = os.path.join(temp_dir, f"systools_elevate_{pid}.vbs")
            log_file = os.path.join(temp_dir, f"systools_cleanup_log_{pid}.txt")

            reboot_cmd = 'shutdown /r /t 15 /c "SysTools cleanup complete. System is restarting."' if reboot else ''

            # 直接删除整个应用目录
            bat_content = f"""
@echo off
cd /d %~dp0

(
    echo Self-Destruct Sequence Started at %date% %time%
    echo Target Directory: {app_dir}
    
    echo [Step 1] Waiting 10 seconds for main application to fully exit...
    ping 127.0.0.1 -n 11 > nul
    echo Done.

    echo [Step 2] Deleting the entire application directory...
    rmdir /s /q "{app_dir}"
    echo Done.
    
    {reboot_cmd}
    
    echo Self-Destruct Sequence Finished.

) > "{log_file}" 2>&1

REM 最后，删除VBS包装器和自己
(goto) 2>nul & del "{vbs_path}" & del "%~f0"
"""
            reboot_arg = "REBOOT" if reboot else "NOREBOOT"
            vbs_content = f'CreateObject("Shell.Application").ShellExecute "{bat_path}", "{reboot_arg}", "", "runas", 0'

            with open(bat_path, "w", encoding="oem") as f: f.write(bat_content)
            with open(vbs_path, "w", encoding="utf-8") as f: f.write(vbs_content)

            subprocess.Popen(['wscript.exe', vbs_path], creationflags=subprocess.DETACHED_PROCESS)
            print("自毁流程已启动。")
        except Exception as e:
            print(f"创建自毁脚本时出错: {str(e)}")