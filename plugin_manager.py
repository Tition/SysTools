import os
import importlib
import sys
import logging
from typing import List
from plugin_base import BasePlugin


class PluginManager:
    """插件管理器，负责动态加载和管理插件"""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.plugins: List[BasePlugin] = []
        self.logger = self._setup_logger()

        # 修复编码问题
        self._fix_encoding()

    def _fix_encoding(self):
        """修复编码问题"""
        if sys.platform.startswith('win'):
            try:
                # 在Windows下设置标准输出的编码
                import io
                if sys.stdout.encoding != 'utf-8':
                    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                if sys.stderr.encoding != 'utf-8':
                    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            except Exception as e:
                self.logger.warning(f"修复编码失败: {str(e)}")

    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger("PluginManager")
        logger.setLevel(logging.DEBUG)

        # 如果没有处理器，添加一个简单的流处理器
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def discover_plugins(self) -> List[BasePlugin]:
        """发现并加载所有插件"""
        self.plugins.clear()

        if not os.path.exists(self.plugins_dir):
            self.logger.warning(f"插件目录不存在: {self.plugins_dir}")
            return []

        # 将插件目录添加到Python路径
        if self.plugins_dir not in sys.path:
            sys.path.insert(0, self.plugins_dir)

        # 遍历plugins目录下的所有.py文件
        plugin_files = []
        try:
            for filename in os.listdir(self.plugins_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    plugin_files.append(filename)
        except Exception as e:
            self.logger.error(f"读取插件目录失败: {str(e)}")
            return []

        # ===================================================================
        # Python的默认字符串排序对于 "01_xxx.py", "02_xxx.py" 这种格式是完美的
        # ===================================================================
        plugin_files.sort()

        self.logger.info(f"发现并排序后的插件文件: {plugin_files}")

        # 按排序后的顺序，依次加载每个插件文件
        loaded_count = 0
        for filename in plugin_files:
            module_name = filename[:-3]  # 移除.py后缀
            try:
                # self.logger.info(f"正在加载模块: {module_name}") # 日志太多可以注释掉
                plugins_in_module = self._load_plugin_module(module_name)

                for plugin in plugins_in_module:
                    if plugin and self._validate_plugin(plugin):
                        # 因为文件是有序加载的，所以append进去的插件列表自然也是有序的
                        self.plugins.append(plugin)
                        loaded_count += 1
                        self.logger.info(f"[{filename}] 成功加载插件: {plugin.get_name()}")
                    elif plugin:
                        self.logger.warning(f"[{filename}] 插件验证失败: {plugin.get_name()}")
            except Exception as e:
                self.logger.error(f"加载文件 {filename} 失败: {e}")

        self.logger.info(f"最终按顺序加载了 {loaded_count} 个可用插件")
        return self.plugins

    def _validate_plugin(self, plugin: BasePlugin) -> bool:
        """验证插件是否有效"""
        try:
            # 检查必要的方法是否存在
            required_methods = ['get_name', 'get_description', 'execute']
            for method in required_methods:
                if not hasattr(plugin, method) or not callable(getattr(plugin, method)):
                    # self.logger.warning(f"插件缺少 {method} 方法: {type(plugin)}")
                    return False

            # 检查插件是否可用
            if hasattr(plugin, 'is_available') and callable(plugin.is_available):
                return plugin.is_available()
            else:
                # 如果没有is_available方法，默认可用
                return True

        except Exception as e:
            self.logger.error(f"验证插件失败: {e}")
            return False

    def _load_plugin_module(self, module_name: str) -> List[BasePlugin]:
        """加载单个插件模块，返回插件实例列表"""
        plugins = []

        try:
            # 清除模块缓存，确保重新加载
            if module_name in sys.modules:
                del sys.modules[module_name]

            module = importlib.import_module(module_name)

            # 查找模块中所有继承自BasePlugin的类
            for attr_name in dir(module):
                # 跳过私有属性
                if attr_name.startswith('_'):
                    continue

                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                        issubclass(attr, BasePlugin) and
                        attr != BasePlugin):

                    # 实例化插件类
                    try:
                        plugin_instance = attr()
                        plugins.append(plugin_instance)
                    except Exception as e:
                        self.logger.error(f"实例化类 {attr_name} 失败: {e}")

        except Exception as e:
            # 简化错误日志，避免在控制台刷屏
            # self.logger.error(f"导入模块 {module_name} 失败: {e}")
            pass

        return plugins

    # ... (后面的辅助方法保持不变，为了完整性我列在下面) ...

    def _safe_encode_error(self, error: Exception) -> str:
        """安全地编码错误信息"""
        return str(error)  # 简化处理

    def get_plugin_by_name(self, name: str) -> BasePlugin:
        for plugin in self.plugins:
            if plugin.get_name() == name:
                return plugin
        return None

    def get_plugins_by_names(self, names: List[str]) -> List[BasePlugin]:
        return [plugin for plugin in self.plugins if plugin.get_name() in names]

    def reload_plugins(self) -> List[BasePlugin]:
        self.logger.info("重新加载所有插件...")
        return self.discover_plugins()

    def __len__(self) -> int:
        return len(self.plugins)

    def __iter__(self):
        return iter(self.plugins)

    def __getitem__(self, index) -> BasePlugin:
        return self.plugins[index]