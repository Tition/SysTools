import abc
from typing import Any, Dict


class BasePlugin(metaclass=abc.ABCMeta):
    """插件基类，所有功能插件必须继承此类"""

    @abc.abstractmethod
    def get_name(self) -> str:
        """返回插件名称"""
        pass

    @abc.abstractmethod
    def get_description(self) -> str:
        """返回插件描述"""
        pass

    @abc.abstractmethod
    def execute(self) -> Dict[str, Any]:
        """执行插件功能，返回执行结果"""
        pass

    def is_available(self) -> bool:
        """检查插件是否可用"""
        return True

    def get_progress_message(self) -> str:
        """返回执行时的进度消息"""
        return f"正在执行: {self.get_name()}"