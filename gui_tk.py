import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os
import time
import webbrowser
import ctypes
from typing import List, TYPE_CHECKING, Callable

# GUI_DEBUG_MODE 开关依然保留，用于独立UI调试 True为gui调试，False为正常运行
GUI_DEBUG_MODE = False

if TYPE_CHECKING:
    from plugin_base import BasePlugin


class PulsingFontIndicator:
    """
    一个优雅的、基于字体的多彩变换动画控件。
    通过在颜色列表中平滑插值来实现动画。
    """

    def __init__(self, parent, font=('Arial', 28), bg_color='#F5F5F5'):
        self.parent = parent

        self.frame = tk.Frame(parent, bg=bg_color)

        # 【核心修改】定义一个颜色列表
        self.colors = [
            (231, 76, 60),  # 红色 (Alizarin)
            (241, 196, 15),  # 黄色 (Sun Flower)
            (52, 152, 219),  # 蓝色 (Peter River)
        ]

        self.dots = []
        for i in range(3):
            # 初始颜色可以先随便设置一个
            dot_label = ttk.Label(
                self.frame,
                text='●',
                font=font,
                foreground='#FFFFFF',  # 临时颜色
                background=bg_color
            )
            dot_label.pack(side=tk.LEFT, padx=8)
            self.dots.append(dot_label)

        self._is_running = False
        self._animation_step = 0

    def pack(self, **kwargs):
        """让这个控件支持 pack 布局"""
        self.frame.pack(**kwargs)

    def start(self):
        """开始动画"""
        if not self._is_running:
            self._is_running = True
            self._animate()

    def stop(self):
        """停止动画"""
        self._is_running = False

    def _animate(self):
        """动画循环的核心逻辑"""
        if not self._is_running or not self.frame.winfo_exists():
            self._is_running = False
            return

        # 每个圆点的动画都基于一个随时间变化的“全局”进度
        # 增加动画速度
        progress = (self._animation_step * 0.04) % len(self.colors)

        for i, dot_label in enumerate(self.dots):
            # 每个点都有一个相位差，使它们的颜色变换错开
            dot_progress = (progress + i * 0.7) % len(self.colors)

            # 确定当前颜色和下一个目标颜色
            color_index = int(dot_progress)
            next_color_index = (color_index + 1) % len(self.colors)

            color1 = self.colors[color_index]
            color2 = self.colors[next_color_index]

            # 计算在两种颜色之间的插值比例
            interp_ratio = dot_progress - color_index

            # 对 R, G, B 三个通道分别进行线性插值
            new_rgb = [
                int(color1[c] * (1 - interp_ratio) + color2[c] * interp_ratio)
                for c in range(3)
            ]
            new_color = f'#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}'

            dot_label.config(foreground=new_color)

        self._animation_step += 1
        self.frame.after(16, self._animate)  # 提高帧率到约 60 FPS


def set_window_icon(window):
    """为给定的Tkinter窗口设置图标 (最终强化版)"""
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(base_dir, "SysTools.ico")

        if os.path.exists(icon_path):
            # Tkinter的标准方法，设置窗口左上角图标
            window.iconbitmap(icon_path)

            # --- 【核心强化】使用Windows原生API强制设置任务栏图标 ---
            # 这可以绕过很多缓存问题
            if sys.platform.startswith('win'):
                import ctypes
                # WM_SETICON, ICON_BIG, ICON_SMALL
                WM_SETICON = 0x0080
                ICON_BIG = 1
                ICON_SMALL = 0

                # 获取窗口句柄 (HWND)
                hwnd = window.winfo_id()

                # 加载图标句柄 (HICON)
                h_icon = ctypes.windll.user32.LoadImageW(
                    None, icon_path, 1, 0, 0, 0x00000010 | 0x00008000
                )

                if h_icon:
                    # 为大图标（任务栏）和小图标（标题栏）都设置
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon)
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon)
                    print(f"成功通过原生API为窗口 {hwnd} 设置图标。")
                else:
                    print(f"警告: LoadImageW 未能加载图标: {icon_path}")

        else:
            print(f"图标文件未找到: {icon_path}")
    except Exception as e:
        print(f"设置窗口图标时发生错误: {e}")

def set_app_id(app_id: str):
    """
    为当前进程设置一个唯一的AppUserModelID。
    这有助于Windows任务栏正确地识别应用并显示其图标，
    尤其是在开发环境中 (运行python.exe时)。
    """
    if sys.platform.startswith('win'):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except (AttributeError, ctypes.ArgumentError) as e:
            print(f"警告: 无法设置AppUserModelID: {e}")
            print("这在非Windows系统或是旧版Windows上是正常的。")
        except Exception as e:
            print(f"设置AppUserModelID时发生未知错误: {e}")

class FloatingNotice:
    """底部居中半透明提示框 - 完整功能版"""

    def __init__(self, parent, text="系统正在自动执行任务，请不要操作电脑..."):
        self.parent = parent;
        self.notice = tk.Toplevel(parent);
        self.notice.withdraw();
        set_window_icon(self.notice)
        self.notice.overrideredirect(True);
        self.notice.attributes("-alpha", 0.85);
        self.notice.attributes("-topmost", True);
        self.notice.configure(bg="#2c3e50")
        self.win_width = 600;
        self.win_height = 120;
        self.is_running = True;
        self._animation_job_ids = {}
        self.title_frame = tk.Frame(self.notice, bg="#2c3e50");
        self.title_frame.pack(pady=(15, 10))
        self.char_labels = []
        for char in list(text):
            label = tk.Label(self.title_frame, text=char, bg="#2c3e50", fg="#bdc3c7", font=("微软雅黑", 15, "bold"),
                             bd=0);
            label.pack(side=tk.LEFT, padx=0);
            self.char_labels.append(label)
        self._light_position = -5;
        self._gradient_colors = ["#ffffff", "#ecf0f1", "#d0d3d4", "#bdc3c7"]
        self.task_label = tk.Label(self.notice, text="准备中...", bg="#2c3e50", fg="#95a5a6", font=("微软雅黑", 11));
        self.task_label.pack(pady=(0, 10))
        self.progress_canvas = tk.Canvas(self.notice, width=500, height=12, bg="#2c3e50", highlightthickness=0);
        self.progress_canvas.pack(pady=(0, 10));
        self._progress_value = 0
        self._progress_glow_position = -50
        self._progress_glow_width = 80
        self._update_position();
        self.notice.after(100, self.notice.deiconify);
        self._start_animations()

    def _update_position(self):
        if not self.notice.winfo_exists(): return
        self.notice.update();
        sw, sh = self.notice.winfo_screenwidth(), self.notice.winfo_screenheight()
        target_x = (sw - self.win_width) // 2;
        target_y = sh - self.win_height - 70;
        self.notice.geometry(f"{self.win_width}x{self.win_height}+{target_x}+{target_y}")

    def _position_guardian(self):
        if not self.is_running or not self.notice.winfo_exists(): return
        self._update_position();
        self._animation_job_ids['guardian'] = self.notice.after(250, self._position_guardian)

    def _animate_light_sweep(self):
        if not self.is_running or not self.notice.winfo_exists(): return
        num_labels = len(self.char_labels)
        for i, label in enumerate(self.char_labels):
            distance = abs(i - self._light_position);
            color = self._gradient_colors[-1]
            if distance < len(self._gradient_colors): color = self._gradient_colors[distance]
            label.config(foreground=color)
        self._light_position += 1
        if self._light_position > num_labels + 4: self._light_position = -4
        self._animation_job_ids['text_glow'] = self.notice.after(70, self._animate_light_sweep)

    def _draw_progress_bar(self):
        """绘制进度条"""
        self.progress_canvas.delete("all")
        self.progress_canvas.create_rectangle(0, 0, 500, 12, fill="#34495e", outline="")
        progress_width = (self._progress_value / 100) * 500
        if progress_width > 0:
            self.progress_canvas.create_rectangle(0, 0, progress_width, 12, fill="#27ae60", outline="")

    def _animate_progress_glow(self):
        """进度条光效动画"""
        if not self.is_running or not self.notice.winfo_exists(): return
        self.progress_canvas.delete("glow")
        progress_width = (self._progress_value / 100) * 500
        if progress_width > 0:
            glow_start = self._progress_glow_position
            glow_end = glow_start + self._progress_glow_width
            if glow_end > 0 and glow_start < progress_width:
                draw_start = max(0, glow_start)
                draw_end = min(progress_width, glow_end)
                for x in range(int(draw_start), int(draw_end)):
                    if x < progress_width:
                        ratio = (x - draw_start) / self._progress_glow_width
                        ease_ratio = 1 - (1 - ratio) ** 2
                        r1, g1, b1 = 39, 174, 96
                        r2, g2, b2 = 124, 252, 0
                        r = int(r1 * (1 - ease_ratio) + r2 * ease_ratio)
                        g = int(g1 * (1 - ease_ratio) + g2 * ease_ratio)
                        b = int(b1 * (1 - ease_ratio) + b2 * ease_ratio)
                        glow_color = f"#{r:02x}{g:02x}{b:02x}"
                        self.progress_canvas.create_line(x, 1, x, 11, fill=glow_color, width=1, tags="glow")
        self._progress_glow_position += 3
        if self._progress_glow_position > 500 + self._progress_glow_width:
            self._progress_glow_position = -self._progress_glow_width
        self._animation_job_ids['progress_glow'] = self.notice.after(30, self._animate_progress_glow)

    def update_task(self, task_name: str, progress: int = None):
        if self.notice and self.notice.winfo_exists():
            self.task_label.config(text=f"正在执行：{task_name}")
            if progress is not None:
                self._progress_value = progress
                self._draw_progress_bar()  # <-- 使用新的绘制函数
                self.task_label.config(text=f"正在执行：{task_name}（{progress}%）")
            self.notice.update_idletasks()

    def _start_animations(self):
        self._position_guardian()
        self._animate_light_sweep()
        self._animate_progress_glow()  # <-- 新增这一行

    def close(self):
        self.is_running = False
        try:
            for job_id in self._animation_job_ids.values():
                if job_id: self.notice.after_cancel(job_id)
            if self.notice and self.notice.winfo_exists(): self.notice.destroy()
        except Exception:
            pass


class AboutDialog:
    """关于对话框 - 精确还原布局"""

    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent);
        self.dialog.withdraw();
        set_window_icon(self.dialog);
        self.dialog.title("关于");
        self.dialog.geometry("400x280")
        self.dialog.resizable(False, False);
        self.dialog.transient(parent);
        self.dialog.grab_set();
        self.center_window();
        self.setup_ui();
        self.dialog.after(100, self.dialog.deiconify)

    def center_window(self):
        self.dialog.update_idletasks();
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2);
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2);
        self.dialog.geometry(f"+{x}+{y}")

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20");
        main_frame.pack(fill=tk.BOTH, expand=True)
        title_frame = ttk.Frame(main_frame);
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="系统封装部署工具", font=("微软雅黑", 16, "bold"), foreground="#2C3E50").pack(
            pady=(0, 2))
        ttk.Label(title_frame, text="SysTools", font=("微软雅黑", 12), foreground="#7F8C8D").pack()
        desc_frame = ttk.Frame(main_frame);
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        ttk.Label(desc_frame, text="版本: 1.0.0", font=("微软雅黑", 10), foreground="#34495E").pack(pady=2)
        ttk.Label(desc_frame, text="© 2025 Studio T9", font=("微软雅黑", 10), foreground="#95A5A6").pack(pady=2)
        link_frame = ttk.Frame(desc_frame);
        link_frame.pack(pady=8)
        link_label = tk.Label(link_frame, text="https://github.com/Tition/SysTools.git", font=("微软雅黑", 10), fg="#3498DB",
                              cursor="hand2");
        link_label.pack();
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Tition/SysTools.git"))
        button_frame = ttk.Frame(main_frame);
        button_frame.pack(fill=tk.X, pady=(15, 0))
        ttk.Button(button_frame, text="关闭", command=self.dialog.destroy, width=10).pack(side=tk.RIGHT, padx=5)


class RestartDialog:
    """【最终修复版】重启对话框 - 始终作为 Toplevel 运行，不再创建独立的 Tk()"""

    def __init__(self, parent):
        self.parent = parent
        self.user_choice = False
        self.countdown = 15
        self.dialog = None
        self.countdown_label = None
        self.countdown_id = None

    def show_dialog(self):
        # 1. 创建一个 Toplevel 窗口
        self.dialog = tk.Toplevel(self.parent)

        # 2. 【核心】立即设置为无边框模式，这可以防止 Windows 绘制默认框架
        self.dialog.overrideredirect(True)

        # 3. 【核心】在它完全不可见的状态下，立即将它移出屏幕
        self.dialog.geometry("+10000+10000")

        # 4. 现在，恢复正常的窗口边框和标题栏
        # 因为窗口在屏幕外，所以这个过程用户完全看不到
        self.dialog.overrideredirect(False)

        # 5. 进行所有常规的窗口配置
        self.dialog.title("系统部署完成")
        self.dialog.geometry("400x240")
        self.dialog.resizable(False, False)
        self.dialog.attributes('-topmost', True)
        set_window_icon(self.dialog)

        # 6. 设置模态并构建UI
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.setup_ui()

        # 7. 在所有配置完成后，最后一步才将窗口居中显示
        self.center_window()

        # 8. 开始倒计时和等待
        self.start_countdown()
        self.parent.wait_window(self.dialog)

        return self.user_choice
    def on_choice(self, choice):
        """处理用户选择"""
        if self.countdown_id:
            self.dialog.after_cancel(self.countdown_id)

        self.user_choice = choice

        # 5. 【核心】不再需要 quit()，因为没有独立的 mainloop，只需销毁窗口
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.destroy()

    # --- 以下方法 (setup_ui, start_countdown, center_window) 保持不变 ---
    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20");
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="系统部署完成", font=("微软雅黑", 16, "bold"), foreground="#2C3E50").pack(
            pady=(0, 2))
        ttk.Label(main_frame, text="需要重新启动计算机使部署完全生效", font=("微软雅黑", 12),
                  foreground="#7F8C8D").pack()
        desc_frame = ttk.Frame(main_frame);
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.countdown_label = ttk.Label(desc_frame, text=f"系统将在 {self.countdown} 秒内自动重启",
                                         font=("微软雅黑", 12, "bold"), foreground="#E74C3C");
        self.countdown_label.pack(pady=5)
        ttk.Label(desc_frame, text="是否立即重启？", font=("微软雅黑", 12), foreground="#34495E").pack(pady=5)
        button_frame = ttk.Frame(main_frame);
        button_frame.pack(fill=tk.X, pady=(5, 0));
        button_frame.columnconfigure((0, 1), weight=1)
        yes_btn = ttk.Button(button_frame, text="是(Y)", command=lambda: self.on_choice(True));
        yes_btn.grid(row=0, column=0, padx=10, sticky='ew', ipady=5);
        yes_btn.focus_set()
        ttk.Button(button_frame, text="否(N)", command=lambda: self.on_choice(False)).grid(row=0, column=1, padx=10,
                                                                                           sticky='ew', ipady=5)
        self.dialog.bind('<KeyPress-y>', lambda e: self.on_choice(True));
        self.dialog.bind('<KeyPress-n>', lambda e: self.on_choice(False));
        self.dialog.bind('<Return>', lambda e: self.on_choice(True));
        self.dialog.bind('<Escape>', lambda e: self.on_choice(False))

    def start_countdown(self):
        if self.dialog and self.dialog.winfo_exists():
            if self.countdown > 0:
                self.countdown_label.config(text=f"系统将在 {self.countdown} 秒内自动重启");
                self.countdown -= 1;
                self.countdown_id = self.dialog.after(1000, self.start_countdown)
            else:
                self.on_choice(True)

    def center_window(self):
        self.dialog.update_idletasks();
        w = self.dialog.winfo_width();
        h = self.dialog.winfo_height();
        x = (self.dialog.winfo_screenwidth() - w) // 2;
        y = (self.dialog.winfo_screenheight() - h) // 2;
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")


class HelpDialog:
    """一个自定义的、内容可复制的帮助对话框"""

    def __init__(self, parent):
        # --- 窗口初始化与防闪烁 ---
        self.dialog = tk.Toplevel(parent)
        self.dialog.overrideredirect(True)
        self.dialog.geometry("+10000+10000")

        self.dialog.title("启动参数帮助")
        self.dialog.attributes("-topmost", True)
        set_window_icon(self.dialog)

        # --- UI 构建 ---
        self.setup_ui()

        # --- 模态与显示 ---
        self.dialog.overrideredirect(False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.center_window(600, 700)  # 给予更大的尺寸

        # 使用 wait_window 使其阻塞，像 messagebox 一样
        parent.wait_window(self.dialog)

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding=(15, 15, 15, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="SysTools - 命令行参数帮助", font=("微软雅黑", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # --- 核心：使用 ScrolledText 控件来显示可选择、可滚动的文本 ---
        self.help_text_widget = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=("微软雅黑", 10),
            height=20,
            padx=10,
            pady=10,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.help_text_widget.pack(fill=tk.BOTH, expand=True)

        self.help_message = (
            "SysTools.exe 支持以下命令行参数:\n\n"
            "-auto\n"
            "    全自动模式：按顺序静默执行所有 'plugins' 目录中的插件。\n\n"
            "-test\n"
            "    测试模式：加载并执行 'plugins_test' 目录中的插件。\n\n"
            "-cleanup\n"
            "    清理模式：在 -auto 模式执行完毕后，自动删除程序自身及其所有相关文件。\n"
            "    请注意一定要将本程序解压到独立文件夹，否则可能误删其他文件\n\n"
            "-console\n"
            "    控制台模式：为GUI应用附加一个控制台窗口，用于显示详细的运行日志。\n\n"
            "-debug\n"
            "    调试模式 (自动)：在 -auto 模式下模拟插件执行（随机成功/失败），不进行实际操作。\n\n"
            "-debug-success\n"
            "    调试模式 (全部成功)：在 -auto 模式下模拟插件执行，并总是返回成功。\n\n"
            "-debuggui\n"
            "    调试模式 (GUI)：在GUI界面中模拟插件执行（随机成功/失败）。\n\n"
            "-debuggui-success\n"
            "    调试模式 (GUI - 全部成功)：在GUI界面中模拟插件执行，并总是返回成功。\n\n"
            "示例用法：\n"
            "    -test -auto >> 以自动模式加载并执行 'plugins_test' 目录中的插件。\n"
            "    -auto -cleanup >> 以自动模式加载并执行 'plugins' 目录中的插件，并清理程序本身。"

        )

        self.help_text_widget.insert(tk.END, self.help_message)
        # 将文本框设为只读（但内容仍可被选中和复制）
        self.help_text_widget.config(state=tk.DISABLED)

        # --- 按钮栏 ---
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.pack(fill=tk.X)

        self.copy_button = ttk.Button(button_frame, text="复制全部内容", command=self._copy_to_clipboard)
        self.copy_button.pack(side=tk.LEFT)

        close_button = ttk.Button(button_frame, text="关闭", command=self.dialog.destroy)
        close_button.pack(side=tk.RIGHT)

    def _copy_to_clipboard(self):
        """将帮助文本复制到系统剪贴板"""
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(self.help_message)

        # 提供视觉反馈
        original_text = self.copy_button['text']
        self.copy_button.config(text="已复制!")
        self.dialog.after(1500, lambda: self.copy_button.config(text=original_text))

    def center_window(self, width, height):
        self.dialog.update_idletasks()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

class TkinterGUI:
    """
    Tkinter View (视图) 层。
    这个类只负责创建和布局UI控件，
    并将用户操作（如点击）通知给 Presenter。
    它不包含任何业务逻辑。
    """

    def __init__(self):
        self.plugin_vars = {}
        self.root = tk.Tk()
        self.stop_callback = None

        # 1. 像以前一样，先 withdraw() 来进行所有后台配置
        self.root.withdraw()

        set_window_icon(self.root)

        title = "系统封装部署工具"
        if GUI_DEBUG_MODE:
            title += " - [GUI调试模式 - 无功能]"

        self.root.title(title)

        self._setup_styles()
        self._setup_gui()

        # 2. 在所有组件都创建好之后，居中
        self.center_window(self.root, 900, 700)

        # 3. 【核心修复】执行“欺骗”任务栏的技巧
        #    这个函数会在短暂延迟后执行，确保窗口已准备好
        def force_taskbar_icon_update():
            # a. 短暂地将窗口完全隐藏（从任务栏也消失）
            self.root.withdraw()
            # b. 立即重新显示它
            #    deiconify() 会让窗口以其最后的位置和大小重新出现
            self.root.deiconify()

        # 4. 正常地显示窗口
        self.root.deiconify()

        # 5. 在窗口显示后，安排一个极短延迟（例如200毫秒）后执行我们的“欺骗”函数
        self.root.after(200, force_taskbar_icon_update)

    def show_help_dialog(self):
        """弹出一个自定义的、内容可复制的帮助对话框。"""
        HelpDialog(self.root)

    def bind_command(self, name: str, callback: Callable[[], None]):
        """【新增】Presenter 用此方法为按钮等控件绑定命令。"""
        if name == "execute_selected":
            self.execute_btn.config(command=callback)
        elif name == "execute_all":
            self.execute_all_btn.config(command=callback)
        elif name == "refresh_plugins":
            self.refresh_btn.config(command=callback)
        elif name == "select_all":
            self.select_all_btn.config(command=callback)
        elif name == "deselect_all":
            self.deselect_all_btn.config(command=callback)
        elif name == "clear_log":
            self.clear_log_btn.config(command=callback)
        elif name == "show_about":
            self.about_btn.config(command=callback)
        elif name == "show_help":
            self.help_btn.config(command=callback)
        elif name == "stop_execution":
            self.stop_callback = callback
        elif name == "stop_execution":
            self.stop_callback = callback

    def display_plugins(self, plugins: List['BasePlugin']):
        """【新增】接收 Presenter 发来的插件数据并更新列表。"""
        self._clear_plugin_list()
        for i, plugin in enumerate(plugins):
            status_text = "✓ 可用" if plugin.is_available() else "✗ 不可用"
            item_id = self.plugin_tree.insert("", "end",
                                              values=("⚪", plugin.get_name(), plugin.get_description(), status_text))
            self.plugin_vars[i] = {'selected': False, 'item_id': item_id}
        self._add_log_message(f"已加载 {len(plugins)} 个功能插件", "info")

    def get_selected_indices(self) -> List[int]:
        """【新增】向 Presenter 提供当前选中的插件索引列表。"""
        return [index for index, data in self.plugin_vars.items() if data['selected']]

    # ======================================================
    # Section 2: 线程安全的 UI 更新方法
    # ======================================================

    def safe_add_log_message(self, message: str, level: str):
        self.root.after(0, self._add_log_message, message, level)

    def safe_update_progress(self, progress: float, current: int, total: int):
        self.root.after(0, self._update_progress, progress, current, total)

    def safe_show_running_indicator(self, plugin_name: str):
        self.root.after(0, self._show_running_indicator, plugin_name)

    def safe_hide_running_indicator(self):
        self.root.after(0, self._hide_running_indicator)

    def safe_on_execution_complete_ui_reset(self):
        """【新增】一个专用于UI重置的安全方法"""
        self.root.after(0, self._ui_reset_on_complete)

    # ======================================================
    # Section 3: UI 内部实现方法 (以下方法通常由 Presenter 通过安全接口调用)
    # ======================================================

    def _add_log_message(self, message: str, level: str):
        try:
            self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n", level);
            self.log_text.see(tk.END)
        except tk.TclError:
            pass

    def _update_progress(self, progress: float, current: int, total: int):
        self.progress_var.set(progress);
        self.progress_label.config(text=f"{current}/{total}");
        self.root.update_idletasks()

    def _ui_reset_on_complete(self):
        """仅重置UI元素，不显示任何消息框。"""
        self.progress_var.set(100)
        self.progress_label.config(text="完成")
        self.set_buttons_state(True)

    # ======================================================
    # Section 4: UI 控件和布局 (保持不变)
    # ======================================================

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Custom.Treeview", font=("微软雅黑", 11), rowheight=32)
        style.configure("Custom.Treeview.Heading", font=("微软雅黑", 11, "bold"), background="#F0F0F0", relief="flat")
        style.configure("Custom.TButton", font=("微软雅黑", 10), padding=(12, 6))

    def _setup_gui(self):
        # --- 创建主框架 ---
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # --- 配置根窗口和主框架的权重 ---
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=2)  # 插件列表区域
        main_frame.rowconfigure(4, weight=1)  # 日志区域

        # --- 1. 标题 ---
        ttk.Label(main_frame, text="系统封装部署工具", font=("微软雅黑", 16, "bold"), foreground="#2C3E50").grid(
            row=0, column=0, pady=(0, 10), sticky=tk.W)

        # --- 2. 顶部功能按钮 ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, pady=15)
        self.execute_btn = ttk.Button(button_frame, text="执行选中功能", style="Custom.TButton")
        self.execute_btn.pack(side=tk.LEFT, padx=8)
        self.execute_all_btn = ttk.Button(button_frame, text="执行全部功能", style="Custom.TButton")
        self.execute_all_btn.pack(side=tk.LEFT, padx=8)
        self.refresh_btn = ttk.Button(button_frame, text="刷新功能列表", style="Custom.TButton")
        self.refresh_btn.pack(side=tk.LEFT, padx=8)
        self.select_all_btn = ttk.Button(button_frame, text="全选", style="Custom.TButton")
        self.select_all_btn.pack(side=tk.LEFT, padx=8)
        self.deselect_all_btn = ttk.Button(button_frame, text="全不选", style="Custom.TButton")
        self.deselect_all_btn.pack(side=tk.LEFT, padx=8)

        # --- 3. 插件列表 ---
        list_frame = ttk.LabelFrame(main_frame, text="可用功能", padding="10")
        list_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        columns = ("选择", "功能名称", "描述", "状态")
        self.plugin_tree = ttk.Treeview(list_frame, columns=columns, show="headings", style="Custom.Treeview")
        for col, w in {"选择": 70, "功能名称": 180, "描述": 450, "状态": 100}.items():
            self.plugin_tree.heading(col, text=col)
            self.plugin_tree.column(col, width=w, anchor='center' if col in ["选择", "状态"] else 'w')
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.plugin_tree.yview)
        self.plugin_tree.configure(yscrollcommand=scrollbar.set)
        self.plugin_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.plugin_tree.bind("<Button-1>", self._on_tree_click)

        # --- 4. 进度条 ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, sticky="ew", pady=10)
        ttk.Label(progress_frame, text="执行进度:", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, padx=15, fill=tk.X, expand=True)
        self.progress_label = ttk.Label(progress_frame, text="0/0")
        self.progress_label.pack(side=tk.RIGHT)

        # --- 5. 日志框 ---
        log_frame = ttk.LabelFrame(main_frame, text="执行日志", padding="10")
        log_frame.grid(row=4, column=0, sticky="nsew", pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD, font=("微软雅黑", 10))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        for tag, color in {"error": "#E74C3C", "warning": "#E67E22", "success": "#27AE60", "info": "#3498DB"}.items():
            self.log_text.tag_config(tag, foreground=color)

        # --- 6. 底部按钮栏 ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))

        left_bottom_frame = ttk.Frame(bottom_frame)
        left_bottom_frame.pack(side=tk.LEFT)

        self.about_btn = ttk.Button(left_bottom_frame, text="关于", style="Custom.TButton")
        self.about_btn.pack(side=tk.LEFT, padx=5)

        self.help_btn = ttk.Button(left_bottom_frame, text="启动参数", style="Custom.TButton")
        self.help_btn.pack(side=tk.LEFT, padx=5)

        self.clear_log_btn = ttk.Button(bottom_frame, text="清空日志", style="Custom.TButton")
        self.clear_log_btn.pack(side=tk.RIGHT, padx=5)

    # ======================================================
    # Section 5: UI 内部事件和辅助方法 (不涉及逻辑)
    # ======================================================

    def _on_tree_click(self, event):
        item = self.plugin_tree.identify_row(event.y)
        if not item or self.plugin_tree.identify_column(event.x) != "#1": return
        new_val = "⚪" if self.plugin_tree.set(item, "选择") == "✅" else "✅"
        self.plugin_tree.set(item, "选择", new_val);
        self.plugin_tree.item(item, tags=("selected",) if new_val == "✅" else ())
        if (idx := self.plugin_tree.index(item)) in self.plugin_vars: self.plugin_vars[idx]['selected'] = (
                    new_val == "✅")

    def _clear_plugin_list(self):
        for item in self.plugin_tree.get_children(): self.plugin_tree.delete(item)
        self.plugin_vars = {}

    def set_buttons_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in [self.execute_btn, self.execute_all_btn, self.refresh_btn, self.select_all_btn,
                    self.deselect_all_btn]: btn.config(state=state)

    def select_all(self):
        for data in self.plugin_vars.values(): data['selected'] = True; self.plugin_tree.set(data['item_id'], "选择",
                                                                                             "✅"); self.plugin_tree.item(
            data['item_id'], tags=("selected",))

    def deselect_all(self):
        for data in self.plugin_vars.values(): data['selected'] = False; self.plugin_tree.set(data['item_id'], "选择",
                                                                                              "⚪"); self.plugin_tree.item(
            data['item_id'], tags=())

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def show_about_dialog(self):
        AboutDialog(self.root)

    def show_restart_dialog(self):
        return RestartDialog(self.root).show_dialog()

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self.root)

    def show_warning(self, title, message):
        messagebox.showwarning(title, message, parent=self.root)

    def ask_yes_no(self, title, message):
        return messagebox.askyesno(title, message, icon='warning', parent=self.root)

    def center_window(self, window, width=None, height=None):
        window.update_idletasks();
        w = width or window.winfo_width();
        h = height or window.winfo_height()
        x = (window.winfo_screenwidth() - w) // 2;
        y = (window.winfo_screenheight() - h) // 2;
        window.geometry(f"{w}x{h}+{x}+{y}")

    def _show_running_indicator(self, plugin_name):
        if not hasattr(self, 'running_window') or not self.running_window.winfo_exists():
            self.running_window = tk.Toplevel(self.root)
            self.running_window.withdraw()
            set_window_icon(self.running_window)
            self.running_window.title("正在执行")
            self.running_window.geometry("450x300")
            self.running_window.resizable(False, False)
            self.running_window.transient(self.root)
            self.running_window.grab_set()
            self.running_window.protocol("WM_DELETE_WINDOW", self._on_running_window_close)

            # 设置窗口背景色 (重要，为 Canvas 提供背景)
            self.running_window.configure(bg='#F5F5F5')

            content_frame = ttk.Frame(self.running_window, padding="20 25 20 20", style="TFrame")
            # 确保 Frame 也有正确的背景色
            ttk.Style().configure("TFrame", background='#F5F5F5')
            content_frame.pack(fill=tk.BOTH, expand=True)

            self.animation_indicator = PulsingFontIndicator(
                content_frame,
                font=('Arial', 28),  # 使用 Arial 或其他通用字体确保兼容性
                bg_color='#F5F5F5'
            )
            self.animation_indicator.pack(pady=(10, 15))

            self.running_label = ttk.Label(content_frame, text=f"正在执行: {plugin_name}",
                                           font=("微软雅黑", 14, "bold"), foreground="#2C3E50", background='#F5F5F5');
            self.running_label.pack(pady=(0, 15))

            ttk.Label(content_frame, text="此操作可能需要几分钟时间，请耐心等待...", font=("微软雅黑", 10),
                      foreground="#7F8C8D", background='#F5F5F5').pack()

            stop_button = ttk.Button(content_frame, text="停止运行", command=self._on_running_window_close,
                                     style="Custom.TButton")
            stop_button.pack(pady=(20, 0))

            self.center_window(self.running_window, 450, 300)
            self.running_window.after(100, self.running_window.deiconify)

            # 【核心修改】启动新动画
            # 2. 启动动画
            self.animation_indicator.start()
        else:
            self.running_label.config(text=f"正在执行: {plugin_name}")

    # 关闭“正在执行”窗口时的处理函数
    def _on_running_window_close(self):
        # 1. 弹窗向用户确认
        if messagebox.askyesno("确认停止", "关闭此窗口将中断当前及后续插件的执行。\n您确定要停止吗？", parent=self.running_window):
            # 2. 如果用户确认，调用 Presenter 注入的回调
            if self.stop_callback:
                self.stop_callback()
            # 3. 无论如何，关闭这个提示窗口
            self._hide_running_indicator()

    def _hide_running_indicator(self):
        if hasattr(self, 'running_window') and self.running_window.winfo_exists():
            # 【核心修改】在销毁窗口前，先停止动画
            if hasattr(self, 'animation_indicator'):
                self.animation_indicator.stop()
            self.running_window.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    # 检查开关是否处于调试模式
    if not GUI_DEBUG_MODE:
        print("错误: 此文件不能在正常模式下直接运行。")
        print("请运行 main.py 来启动完整应用程序。")
        print("如果想独立调试GUI，请将本文件顶部的 GUI_DEBUG_MODE 设置为 True。")
    else:
        # --- 在没有Presenter的情况下，创建一个模拟的调试环境 ---
        print("正在以 GUI 调试模式 (无 Presenter) 启动...")

        # 1. 创建 GUI 实例
        app = TkinterGUI()


        # 2. 模拟 Presenter 的绑定过程，但回调函数是简单的打印或弹窗
        def mock_callback(name):
            print(f"[GUI DEBUG] 事件 '{name}' 被触发。")
            messagebox.showinfo("GUI 调试", f"按钮 '{name}' 被点击，但无功能。")


        for cmd in ["execute_selected", "execute_all", "refresh_plugins",
                    "select_all", "deselect_all", "clear_log", "show_about"]:
            # 使用 lambda 捕获 name 变量
            app.bind_command(cmd, lambda name=cmd: mock_callback(name))

        # 3. 模拟 Presenter 加载插件数据
        app.display_plugins([
            # 【修复】为所有 lambda 添加一个参数（通常用 _ 表示忽略）来接收 self
            type('MockPlugin', (), {
                'get_name': lambda _: '01_模拟优化',
                'get_description': lambda _: '这是一个模拟插件的描述。',
                'is_available': lambda _: True
            })(),
            type('MockPlugin', (), {
                'get_name': lambda _: '02_模拟安装',
                'get_description': lambda _: '安装模拟的软件。',
                'is_available': lambda _: True
            })(),
            type('MockPlugin', (), {
                'get_name': lambda _: '03_模拟清理',
                'get_description': lambda _: '这是一个不可用的模拟插件。',
                'is_available': lambda _: False
            })(),
        ])

        # 4. 运行 GUI
        app.run()