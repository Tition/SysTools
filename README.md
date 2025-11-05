# SysTools - 系统封装部署工具

![SysTools](SysTools.ico)

一个完全由AI构建的（Gemini、DeepSeek、Claude），基于Python的模块化系统工具，提供插件化架构，支持GUI和命令行两种操作模式，用于系统优化、部署和自动化任务。

## 🚀 功能特点

*   **插件化架构** - 支持动态加载和管理功能插件
*   **双模式运行** - 支持GUI界面和命令行自动模式
*   **管理员权限** - 自动请求UAC管理员权限
*   **自动打包** - 一键打包为独立可执行文件
*   **智能依赖收集** - 自动分析插件依赖关系
*   **跨环境兼容** - 支持开发环境和打包后环境

## 📁 项目结构

    SysTools/
    ├── 📄 Build.bat                     # 自动化打包脚本
    ├── 📄 build_exclude.txt             # 打包排除列表
    ├── 📄 collect_imports.py            # 依赖收集脚本
    ├── 📄 core.py                       # 核心引擎
    ├── 📄 debug_cli.py                  # 命令行调试界面
    ├── 📄 gui_tk.py                     # Tkinter GUI界面
    ├── 📄 main.py                       # 主程序入口
    ├── 📄 plugin_base.py                # 插件基类
    ├── 📄 plugin_manager.py             # 插件管理器
    ├── 📄 presenter.py                  # GUI表示层
    ├── 📄 requirements.txt              # Python依赖
    ├── 📄 Set_SysTools_RunOnce.reg      # 自启动注册表文件
    ├── 📄 SysTools.ico                  # 应用程序图标
    ├── 📄 version_info.txt              # 版本信息文件
    ├── 📁 plugins/                      # 主插件目录
    │   ├── 📄 00_sample_plugin.py       # 示例插件
    │   ├── 📄 01_reg_repair.py          # 注册表修复插件
    │   └── 📁 tools/                    # 插件工具目录
    │       ├── 📄 sample_logic.py       # 示例插件逻辑
    │       ├── 📄 reg.ps1               # PowerShell注册表脚本
    │       └── 📁 templates/            # 图像识别模板
    ├── 📁 plugins_test/                 # 测试插件目录
    └── 📁 SysTools_FinalPackage/        # 打包输出目录

## 🛠️ 安装与运行

### 环境要求

*   **操作系统**: Windows 10/11
*   **Python**: 3.7+
*   **权限**: 管理员权限（部分功能需要）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

#### GUI模式（默认）

```bash
python main.py
```

#### 命令行调试模式

```bash
python debug_cli.py
```

## ⚙️ 命令行参数

| 参数                  | 说明                        |
| :------------------ | :------------------------ |
| `-auto`             | 全自动模式：顺序执行所有插件            |
| `-test`             | 测试模式：加载`plugins_test`目录插件 |
| `-cleanup`          | 清理模式：执行后删除程序自身            |
| `-console`          | 控制台模式：为GUI附加控制台窗口         |
| `-debug`            | 调试模式：模拟执行（随机成功/失败）        |
| `-debug-success`    | 调试模式：模拟执行（全部成功）           |
| `-debuggui`         | GUI调试模式：在界面中模拟执行          |
| `-debuggui-success` | GUI调试模式：模拟执行（全部成功）        |

### 使用示例

```bash
# 全自动模式执行主插件
python main.py -auto

# 测试模式执行测试插件
python main.py -test -auto

# 全自动执行并清理
python main.py -auto -cleanup

# 调试模式
python main.py -debug
```

## 🔌 插件开发

### 创建新插件

1.  在`plugins`目录下创建新的Python文件，命名格式：`XX_plugin_name.py`
2.  继承`BasePlugin`基类
3.  实现必需的方法

### 插件模板

```python
from plugin_base import BasePlugin

class MyPlugin(BasePlugin):
    def get_name(self) -> str:
        return "我的插件"
    
    def get_description(self) -> str:
        return "插件功能描述"
    
    def is_available(self) -> bool:
        return True
    
    def execute(self):
        try:
            # 插件逻辑
            return {
                'success': True,
                'message': '执行成功',
                'reboot': False  # 是否需要重启
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

### 插件工具

复杂插件可以将逻辑代码放在`plugins/tools/`目录下，通过动态导入使用：

```python
def execute(self):
    try:
        # 动态导入工具模块
        if self.tools_dir not in sys.path:
            sys.path.insert(0, self.tools_dir)
        
        logic_module = importlib.import_module("my_logic")
        logic_instance = logic_module.MyLogic()
        return logic_instance.run()
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

## 📦 打包分发

### 一键打包

运行打包脚本：

```bash
Build.bat
```

打包过程：

1.  **清理** - 删除旧文件
2.  **依赖收集** - 自动分析插件依赖
3.  **PyInstaller打包** - 生成独立EXE
4.  **文件组装** - 整理插件和资源文件
5.  **清理临时文件** - 保持目录整洁

### 打包输出

打包后在`SysTools_FinalPackage/`目录生成：

*   `SysTools.exe` - 主程序
*   `plugins/` - 功能插件
*   `plugins_test/` - 测试插件
*   `templates/` - 图像模板
*   配置文件等

## 🎯 使用指南

### GUI模式

1.  运行程序，显示主界面
2.  插件列表显示所有可用功能
3.  选择要执行的插件（支持多选）
4.  点击"执行选中功能"或"执行全部功能"
5.  查看执行日志和进度

### 自动模式

1.  使用命令行参数启动自动模式
2.  程序按插件文件名顺序执行
3.  显示浮动进度窗口
4.  执行完成后显示结果对话框

### 插件执行流程

1.  **加载插件** - 动态发现和验证插件
2.  **权限检查** - 验证插件可用性
3.  **执行逻辑** - 调用插件execute方法
4.  **结果处理** - 处理成功/失败结果
5.  **重启管理** - 处理需要重启的情况

## 🔧 高级功能

### 自毁机制

使用`-cleanup`参数时，程序支持：

*   **延时自毁** - 执行后删除程序文件
*   **重启自毁** - 重启后删除程序文件
*   **文件夹清理** - 删除整个应用目录

### 图像识别

插件可以访问`templates/`目录中的图像模板，用于GUI自动化任务。

### 注册表操作

提供PowerShell脚本支持，用于复杂的注册表操作。

## ⚠️ 注意事项

1.  **管理员权限** - 部分系统操作需要管理员权限
2.  **杀毒软件** - 可能误报，请添加到白名单
3.  **文件路径** - 避免使用中文和特殊字符路径
4.  **插件安全** - 仅加载可信插件
5.  **备份数据** - 重要操作前建议备份

## 🐛 故障排除

### 常见问题

**Q: 插件加载失败**\
A: 检查插件文件语法和依赖

**Q: 打包后无法运行**\
A: 确保所有依赖文件正确复制

**Q: 权限不足**\
A: 以管理员身份运行程序

**Q: 图标不显示**\
A: 确保图标文件在正确路径

### 调试模式

使用调试参数测试插件逻辑：

```bash
python main.py -debuggui
```

## 📄 许可证

本项目仅供学习和内部使用。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

## 📞 支持

如有问题，请通过以下方式联系：

*   GitHub Issues
*   项目文档
*   开发团队

***

\*最后更新: 2025-11-05\*
