import os
import sys
import importlib
import traceback
from plugin_base import BasePlugin


class SamplePlugin(BasePlugin):
    """一个示例插件，用于演示插件的创建和功能。"""

    def __init__(self):
        super().__init__()
        # 动态构建路径，确保在打包和开发环境下都有效
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.tools_dir = os.path.join(base_dir, "plugins", "tools")
        self.logic_script_path = os.path.join(self.tools_dir, "sample_logic.py")

    def get_name(self) -> str:
        return "功能演示插件"

    def get_description(self) -> str:
        return "演示如何创建文件、获取用户信息，并展示一个独立的Tkinter动画窗口。"

    def is_available(self) -> bool:
        # 检查其逻辑脚本是否存在
        return os.path.exists(self.logic_script_path)

    def get_progress_message(self) -> str:
        return "正在运行功能演示插件..."

    def execute(self):
        """执行示例插件的逻辑"""
        try:
            # 确保 tools 目录在Python的搜索路径中
            if self.tools_dir not in sys.path:
                sys.path.insert(0, self.tools_dir)

            # 动态导入逻辑模块
            logic_module_name = "sample_logic"
            if logic_module_name in sys.modules:
                logic_module = importlib.reload(sys.modules[logic_module_name])
            else:
                logic_module = importlib.import_module(logic_module_name)

            # 创建逻辑类的实例并运行
            logic_instance = logic_module.SampleLogic()
            result = logic_instance.run()

            # 直接返回逻辑脚本的结果字典
            return result

        except Exception as e:
            return {
                'success': False,
                'error': f"加载或执行示例插件时发生异常: {str(e)}",
                'traceback': traceback.format_exc()
            }