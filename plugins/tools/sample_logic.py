import os
import getpass
import configparser
import tkinter as tk
import random
import time
import sys
import math
from typing import Dict, Any


# ======================================================
# 【核心】将 set_window_icon 函数从 gui_tk.py 复制过来
# 这是为了让这个逻辑脚本可以独立运行和测试，而无需依赖主GUI文件
# ======================================================
def set_window_icon(window):
    """为给定的Tkinter窗口设置图标"""
    try:
        # 寻找图标文件的路径，需要向上回溯到项目根目录
        if getattr(sys, 'frozen', False):
            # 打包后的.exe，根目录就是.exe所在的目录
            base_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境下，从当前文件 (__file__) 向上回溯两级
            # sample_logic.py -> tools -> plugins -> (项目根目录)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        icon_path = os.path.join(base_dir, "SysTools.ico")

        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
    except Exception as e:
        print(f"设置窗口图标失败: {e}")


class CoolAnimationWindow:
    """一个带有“星座连接”效果的炫酷粒子动画窗口（优化布局版）"""

    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("插件动画演示")
        self.root.geometry("+10000+10000")
        self.root.attributes("-topmost", True)
        set_window_icon(self.root)

        # --- 新的布局：使用主Frame ---
        main_frame = tk.Frame(self.root, bg='#0d1117')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 【核心修改】1. 将说明文字放在一个独立的Label中 ---
        info_text = (
            "这是一个粒子动画\n"
            "将在15秒后自动关闭\n\n"
            "本示例插件将在您的桌面创建文件：插件成功运行.txt"
        )
        self.info_label = tk.Label(
            main_frame,
            text=info_text,
            bg='#0d1117',
            fg='#aab8c2',
            font=("微软雅黑", 12),
            justify=tk.CENTER
        )
        self.info_label.pack(pady=(20, 10))  # 在顶部留出一些空间

        # --- 画布创建 ---
        self.width = 600
        # 减小画布高度，为上方的Label留出空间
        self.height = 300
        self.canvas = tk.Canvas(main_frame, bg='#0d1117', width=self.width, height=self.height, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- 粒子参数 ---
        self.particle_count = 50
        self.particles = []
        self.colors = ['#ff007f', '#00ff7f', '#007fff', '#ffff00', '#ff00ff', '#00ffff']
        self.line_threshold = 120

        # --- 状态与初始化 ---
        self.is_running = False
        self.init_particles()

        # 将窗口居中 (使用新的总高度)
        self.center_window(self.width, 400)  # 总高度约为 100(Label) + 300(Canvas)

    def init_particles(self):
        """初始化或重置所有粒子的状态"""
        self.particles = []
        for _ in range(self.particle_count):
            self.particles.append({
                'x': random.uniform(0, self.width),
                'y': random.uniform(0, self.height),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'radius': random.uniform(1, 2.5),
                'color': random.choice(self.colors)
            })

    def _animate(self):
        """动画主循环"""
        if not self.is_running or not self.root or not self.root.winfo_exists():
            self.is_running = False
            return

        self.canvas.delete("all")

        # 更新和绘制粒子
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            if p['x'] <= 0 or p['x'] >= self.width: p['vx'] *= -1
            if p['y'] <= 0 or p['y'] >= self.height: p['vy'] *= -1
            r = p['radius']
            self.canvas.create_oval(p['x'] - r, p['y'] - r, p['x'] + r, p['y'] + r, fill=p['color'], outline="")

        # 绘制连接线
        for i in range(self.particle_count):
            for j in range(i + 1, self.particle_count):
                p1 = self.particles[i]
                p2 = self.particles[j]
                distance = math.sqrt((p1['x'] - p2['x']) ** 2 + (p1['y'] - p2['y']) ** 2)
                if distance < self.line_threshold:
                    alpha = 1.0 - (distance / self.line_threshold)
                    r = int(int(p1['color'][1:3], 16) * alpha)
                    g = int(int(p1['color'][3:5], 16) * alpha)
                    b = int(int(p1['color'][5:7], 16) * alpha)
                    line_color = f'#{r:02x}{g:02x}{b:02x}'
                    self.canvas.create_line(p1['x'], p1['y'], p2['x'], p2['y'], fill=line_color, width=1)

        self.root.after(30, self._animate)

    # --- 生命周期管理方法 (保持不变) ---
    def run_and_destroy(self):
        self.is_running = True
        self._animate()
        self.root.after(15000, self.destroy)
        self.root.grab_set()
        self.parent.wait_window(self.root)

    def destroy(self):
        self.is_running = False
        if self.root and self.root.winfo_exists():
            self.root.destroy()
            self.root = None

    def center_window(self, width, height):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")


class SampleLogic:
    """示例插件的核心逻辑实现"""

    def __init__(self):
        # 【核心修复】采用与您其他插件完全一致的环境感知路径逻辑
        if getattr(sys, 'frozen', False):
            # --- 打包环境 ---
            # .exe 所在的目录就是根目录，INI文件应该在这里创建
            self.output_dir = os.path.dirname(sys.executable)
        else:
            # --- 开发环境 ---
            # 当前文件(sample_logic.py)所在的目录，即 plugins/tools/
            self.output_dir = os.path.dirname(os.path.abspath(__file__))

        # 获取当前用户的桌面路径（这个逻辑保持不变）
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    def create_ini_file(self) -> bool:
        """创建一个INI文件并写入当前用户名"""
        try:
            # 使用 self.output_dir 作为路径，现在它的值是动态的
            ini_path = os.path.join(self.output_dir, "SysTools_Sample.ini")
            config = configparser.ConfigParser()

            username = getpass.getuser()

            config['UserInfo'] = {
                'CurrentUser': username,
                'Timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(ini_path, 'w', encoding='utf-8') as f:
                config.write(f)

            print(f"成功创建INI文件: {ini_path}")
            return True
        except Exception as e:
            print(f"创建INI文件失败: {e}")
            return f"创建INI文件时发生错误: {e}"

    # ... (create_txt_file, show_animation_window, run 方法保持不变) ...
    def create_txt_file(self) -> bool:
        try:
            txt_path = os.path.join(self.desktop_path, "插件运行成功.txt")
            content = (
                "SysTools 示例插件已成功运行！\n\n欢迎访问我们的GitHub仓库以获取更多信息或贡献代码：\nhttps://github.com/Tition/SysTools.git\n")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"成功创建TXT文件: {txt_path}")
            return True
        except Exception as e:
            print(f"创建TXT文件失败: {e}")
            return f"创建桌面TXT文件时发生错误: {e}"

    def show_animation_window(self):
        root = None
        try:
            root = tk.Tk()
            root.withdraw()
            print("正在创建并显示动画窗口...")
            anim_window = CoolAnimationWindow(root)
            anim_window.run_and_destroy()
            print("动画窗口已关闭。")
            return True
        except Exception as e:
            print(f"显示动画窗口时发生错误: {e}")
            return f"显示动画窗口时发生错误: {e}"
        finally:
            if root and root.winfo_exists():
                root.destroy()

    def run(self) -> Dict[str, Any]:
        print("\n--- 开始执行示例插件逻辑 ---")
        errors = []
        result_ini = self.create_ini_file()
        if result_ini is not True: errors.append(str(result_ini))
        result_txt = self.create_txt_file()
        if result_txt is not True: errors.append(str(result_txt))
        result_anim = self.show_animation_window()
        if result_anim is not True: errors.append(str(result_anim))
        if errors:
            return {'success': False, 'error': " | ".join(errors)}
        else:
            return {'success': True, 'message': '所有示例任务均已成功完成！'}


if __name__ == '__main__':
    logic = SampleLogic()
    result = logic.run()
    print("\n--- 测试结果 ---")
    print(result)