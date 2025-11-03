from typing import TYPE_CHECKING

# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from core import CoreEngine
    from gui_tk import TkinterGUI
    # 可以添加其他GUI类的类型提示
    # from gui_flet import FletGUI


class Presenter:
    """
    Presenter (主持人) 层。
    负责协调 Model 和 View。
    """

    def __init__(self, core: 'CoreEngine', view):
        """
        初始化 Presenter。
        view 可以是任何符合接口规范的GUI对象。
        """
        self.core = core
        self.view = view

    def initialize_bindings(self):
        """
        建立所有绑定。
        """
        # --- 1. 将 View 的事件绑定到 Presenter ---
        self.view.bind_command("execute_selected", self.handle_execute_selected)
        self.view.bind_command("execute_all", self.handle_execute_all)
        self.view.bind_command("refresh_plugins", self.handle_refresh_plugins)
        self.view.bind_command("select_all", self.handle_select_all)
        self.view.bind_command("deselect_all", self.handle_deselect_all)
        self.view.bind_command("clear_log", self.handle_clear_log)
        self.view.bind_command("show_about", self.handle_show_about)
        self.view.bind_command("show_help", self.handle_show_help)
        self.view.bind_command("stop_execution", self.handle_stop_request)
        self.view.bind_command("stop_execution", self.handle_stop_request)

        # --- 2. 将 Core 的回调绑定到 Presenter ---
        self.core.on_log_message = self.handle_log_message
        self.core.on_progress_update = self.handle_progress_update
        self.core.on_execution_complete = self.handle_execution_complete
        self.core.on_plugin_state_change = self.handle_plugin_state_change

        # --- 3. 为异步GUI（如Flet）注册“就绪”回调 ---
        if hasattr(self.view, 'bind_on_ready'):
            self.view.bind_on_ready(self.on_view_ready)

    def start_app(self):
        """
        启动应用程序的初始流程。
        """
        # 对于同步GUI（如Tkinter, PySide），UI在创建后立即就绪
        # 我们可以直接加载插件
        if not hasattr(self.view, 'bind_on_ready'):
            self.on_view_ready()

        # 启动 GUI 主循环 (由各个GUI的run()方法自己实现)
        self.view.run()

    def on_view_ready(self):
        """当View通知UI已就绪时（或对于同步UI立即执行），此方法被调用。"""
        self.handle_refresh_plugins()

    # ======================================================
    # 其余所有 handle_... 方法与您之前的版本完全相同，无需修改
    # (为了简洁，此处省略)
    # ======================================================
    def handle_stop_request(self):
        self.core.request_stop()

    def handle_execute_selected(self):
        selected_indices = self.view.get_selected_indices()
        if not selected_indices:
            self.view.show_warning("警告", "请至少选择一个功能！")
            return
        plugins_to_execute = [self.core.plugins[i] for i in selected_indices]
        self.view.set_buttons_state(False)
        self.core.execute_plugins(plugins_to_execute)

    def handle_execute_all(self):
        if not self.core.plugins:
            self.view.show_warning("警告", "没有可执行的功能！")
            return
        if self.view.ask_yes_no("请确认执行", "您确认要执行【全部功能】吗？"):
            self.view.set_buttons_state(False)
            self.core.execute_plugins(self.core.plugins)

    def handle_refresh_plugins(self):
        self.core.load_plugins()
        self.view.display_plugins(self.core.plugins)

    def handle_select_all(self):
        self.view.select_all()

    def handle_deselect_all(self):
        self.view.deselect_all()

    def handle_clear_log(self):
        self.view.clear_log()

    def handle_show_about(self):
        self.view.show_about_dialog()

    def handle_show_help(self):
        self.view.show_help_dialog()

    def handle_log_message(self, message: str, level: str):
        self.view.safe_add_log_message(message, level)

    def handle_progress_update(self, progress: float, current: int, total: int):
        self.view.safe_update_progress(progress, current, total)

    def handle_plugin_state_change(self, plugin_name: str, state: str):
        if state == 'starting':
            self.view.safe_show_running_indicator(plugin_name)
        elif state == 'finished':
            self.view.safe_hide_running_indicator()

    def handle_execution_complete(self, failed_plugins: list):
        self.view.safe_on_execution_complete_ui_reset()
        if failed_plugins:
            failed_list = "\n".join([f"- {p['name']}: {p['error']}" for p in failed_plugins])
            message = f"执行完成！\n\n以下插件执行失败：\n{failed_list}"
            self.view.show_warning("执行完成", message)
        else:
            self.view.show_info("执行完成", "所有功能执行成功！")
        if self.core.reboot_required:
            if self.view.show_restart_dialog():
                self.core.perform_cleanup_and_exit(user_wants_reboot=True)