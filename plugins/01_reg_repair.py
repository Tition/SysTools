import os
import subprocess
from plugin_base import BasePlugin


class RegistryRepairPlugin(BasePlugin):
    """注册表修复插件"""

    def get_name(self) -> str:
        return "注册表修复"

    def get_description(self) -> str:
        return "修复包含Administrator路径的注册表项，替换为当前用户名"

    def is_available(self) -> bool:
        """检查PowerShell和脚本文件是否可用"""
        try:
            # 检查PowerShell是否可用
            result = subprocess.run(
                ["powershell", "-Command", "echo 'PowerShell可用'"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )

            # 检查脚本文件是否存在
            script_path = self._get_script_path()
            exists = os.path.exists(script_path)

            return result.returncode == 0 and exists

        except Exception as e:
            print(f"可用性检查失败: {str(e)}")
            return False

    def execute(self):
        """执行注册表修复"""
        try:
            script_path = self._get_script_path()

            if not os.path.exists(script_path):
                return {
                    'success': False,
                    'error': f'找不到PowerShell脚本: {script_path}'
                }

            # 使用更可靠的执行方式
            # 确保使用完整的PowerShell路径和参数
            powershell_path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

            # 隐藏 PowerShell 窗口
            command = [
                powershell_path,
                "-ExecutionPolicy", "Bypass",
                "-NoProfile",
                "-WindowStyle", "Hidden",
                "-File", script_path
            ]

            # 执行命令并捕获输出
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=600,  # 10分钟超时
                encoding='gbk',  # 使用GBK编码处理中文输出
                cwd=os.path.dirname(script_path)  # 在脚本目录执行
            )

            # 处理执行结果
            if result.returncode == 0:
                output = result.stdout.strip() if result.stdout else "注册表修复完成"
                return {
                    'success': True,
                    'message': output
                }
            else:
                error_msg = result.stderr.strip() if result.stderr else f"PowerShell执行失败，返回码: {result.returncode}"
                # 添加标准输出到错误信息，便于调试
                if result.stdout:
                    error_msg += f"\n输出: {result.stdout}"
                return {
                    'success': False,
                    'error': error_msg
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': '注册表修复操作超时（超过10分钟）'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'执行注册表修复时发生错误: {str(e)}'
            }

    def get_progress_message(self) -> str:
        return "正在搜索和替换注册表中的Administrator路径..."

    def _get_script_path(self) -> str:
        """获取PowerShell脚本路径"""
        # 获取当前插件目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建脚本完整路径
        script_path = os.path.join(current_dir, "tools", "reg.ps1")
        return script_path
