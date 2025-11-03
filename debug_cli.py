import sys
import os
import time
import subprocess
from core import CoreEngine
from plugin_base import BasePlugin
from typing import List, Dict


class CommandLineUI:
    """
    一个简单的命令行界面，用于调试和与 CoreEngine 交互。
    这个类扮演了 GUI 的角色。
    """
    # 【新增】定义一个包含描述和参数的字典
    COMMAND_LINE_OPTIONS: Dict[str, str] = {
        "全自动模式 (-auto)": "-auto",
        "全自动模式并清理 (-auto -cleanup)": "-auto -cleanup",
        "调试模式 (随机成功/失败) (-debug)": "-debug",
        "调试模式 (全部成功) (-debug-success)": "-debug-success",
        "测试模式 (使用_test插件) (-test)": "-test",
        "全自动测试模式 (-auto -test)": "-auto -test"
    }

    def __init__(self):
        self.core = CoreEngine()
        self.plugins: List[BasePlugin] = []

        self.core.on_log_message = self.handle_log_message
        self.core.on_progress_update = self.handle_progress_update
        self.core.on_execution_complete = self.handle_execution_complete

        # 【修改】检查启动参数，如果是自动模式，则不进入交互界面
        if self.core.is_auto_mode():
            print("检测到自动模式参数，核心引擎将自动执行。")
            # 在自动模式下，我们只需要一个简单的回调来显示最终结果
            self.core.on_auto_execution_complete = self.handle_auto_mode_complete
            self.core.start_auto_execution()
            # 保持主线程存活以等待后台线程完成
            while self.core.is_running:
                time.sleep(1)
            # 自动模式执行完毕后，等待用户确认
            input("\n自动执行完成，按 Enter 键退出...")

        else:
            print("命令行调试界面已启动。")
            print("=" * 40)
            self.run()  # 只有在非自动模式下才运行交互式循环

    # --- 回调处理函数 ---

    def handle_log_message(self, message: str, level: str):
        timestamp = time.strftime("%H:%M:%S")
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
        print(f"[{timestamp}][{level.upper()}] {message}")

    def handle_progress_update(self, progress: float, current: int, total: int):
        bar_length = 40
        filled_len = int(round(bar_length * progress / 100))
        bar = '█' * filled_len + '-' * (bar_length - filled_len)
        percent_str = f"{progress:.1f}%"
        sys.stdout.write(f"\r进度: [{bar}] {percent_str} ({current}/{total})")
        sys.stdout.flush()

    def handle_execution_complete(self, failed_plugins: list):
        print("\n" + "=" * 40)
        if not failed_plugins:
            print("🎉 所有任务执行成功！")
        else:
            print("⚠️ 执行完成，但有部分任务失败：")
            for plugin in failed_plugins:
                print(f"  - 插件: {plugin['name']}, 原因: {plugin['error']}")

        if self.core.reboot_required:
            print("\n系统需要重启才能使所有更改生效。")
            user_input = input("是否立即重启? (y/n): ").lower()
            if user_input == 'y':
                print("模拟重启...")
            else:
                print("用户选择稍后重启。")

        print("=" * 40)
        input("按 Enter 键返回主菜单...")

    def handle_auto_mode_complete(self, executed: int, total: int, failed_plugins: list):
        """【新增】一个专门用于自动模式的回调，简化输出。"""
        print("\n" + "=" * 40)
        print("自动模式执行完毕！")
        print(f"结果: 成功 {executed}/{total}")
        if failed_plugins:
            print("失败的插件:")
            for plugin in failed_plugins:
                print(f"  - {plugin['name']}: {plugin['error']}")
        print("=" * 40)
        self.core.is_running = False  # 标记任务结束

    # --- 菜单和用户交互 ---

    def load_plugins(self):
        print("\n正在加载插件...")
        self.core.load_plugins()
        self.plugins = self.core.plugins
        if self.plugins:
            print(f"成功加载 {len(self.plugins)} 个插件。")
        else:
            print("未能加载任何插件，请检查 'plugins' 目录。")
        time.sleep(1)

    def display_menu(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("======= 系统工具 - 命令行调试器 =======")
        if not self.plugins:
            print("\n当前未加载任何插件。")
        else:
            print("\n可用插件列表:")
            for i, plugin in enumerate(self.plugins):
                print(f"  [{i + 1}] {plugin.get_name()} - {plugin.get_description()}")

        print("\n--- 操作命令 ---")
        print("  a                - 执行所有插件")
        print("  e <编号...>      - 执行选中的插件 (例如: e 6 7)")
        print("  r                - 重新加载插件")
        print("  c                - 以指定的命令行参数重启")
        print("  q                - 退出程序")
        print("=" * 40)

    # --- 主循环 ---
    def run(self):
        """启动命令行界面的主循环"""
        self.load_plugins()

        while True:
            self.display_menu()
            user_input = input("请输入命令: ").strip()

            if not user_input: continue

            parts = user_input.lower().split()
            command = parts[0]
            args = parts[1:]

            if command == 'q':
                print("程序退出。")
                break

            elif command == 'r':
                self.load_plugins()

            elif command == 'a':
                if not self.plugins:
                    print("没有可执行的插件。");
                    time.sleep(1.5);
                    continue
                print("\n即将执行所有插件...")
                self.core.execute_plugins(self.plugins)
                while self.core.is_running: time.sleep(0.1)

            elif command == 'e':
                if not self.plugins:
                    print("没有可选择的插件。");
                    time.sleep(1.5);
                    continue
                if not args:
                    print("错误: 请提供插件编号。格式: e <编号1> <编号2> ...");
                    time.sleep(2);
                    continue
                try:
                    indices = [int(i) - 1 for i in args]
                    plugins_to_run = [self.plugins[i] for i in indices if 0 <= i < len(self.plugins)]
                    if plugins_to_run:
                        print(f"\n即将执行选中的 {len(plugins_to_run)} 个插件...")
                        self.core.execute_plugins(plugins_to_run)
                        while self.core.is_running: time.sleep(0.1)
                    else:
                        print("没有选择任何有效的插件。"); time.sleep(1.5)
                except ValueError:
                    print("输入无效，编号必须是数字。");
                    time.sleep(2)

            # 【新增】处理 'c' 命令的逻辑
            elif command == 'c':
                self.handle_restart_with_args()
                break  # 如果重启成功，就退出当前进程

            else:
                print(f"无效的命令: '{command}'");
                time.sleep(1.5)

    def handle_restart_with_args(self):
        """【新增】处理带参数重启的逻辑"""
        print("\n--- 选择一个命令行模式以重启 ---")

        # 将字典转换为列表以便通过索引访问
        options_list = list(self.COMMAND_LINE_OPTIONS.items())

        for i, (desc, _) in enumerate(options_list):
            print(f"  [{i + 1}] {desc}")

        try:
            choice = int(input("\n请输入选项编号: "))
            if not (1 <= choice <= len(options_list)):
                print("无效的编号。");
                time.sleep(1.5);
                return

            # 获取选择的参数字符串
            _, selected_args_str = options_list[choice - 1]

            # 准备重启命令
            # sys.executable 是当前 Python 解释器的路径
            # sys.argv[0] 是当前脚本的名称 (debug_cli.py)
            command_to_run = [sys.executable, sys.argv[0]] + selected_args_str.split()

            print("\n" + "=" * 40)
            print(f"正在以参数 '{selected_args_str}' 重启...")
            print("=" * 40)

            # 使用 Popen 启动一个新进程，当前进程可以继续并退出
            subprocess.Popen(command_to_run)

        except ValueError:
            print("输入无效，请输入数字。");
            time.sleep(1.5)
        except Exception as e:
            print(f"重启失败: {e}");
            time.sleep(2)


if __name__ == "__main__":
    # 检查是否有自动模式参数，如果有，直接启动核心逻辑
    # 否则，启动交互式UI
    ui = CommandLineUI()