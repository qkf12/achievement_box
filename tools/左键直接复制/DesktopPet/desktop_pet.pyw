# -*- coding: utf-8 -*-
"""
桌面小宠 · DesktopPet
=====================

一只常驻在屏幕最上层、只有两个鼠标指针大小的迷你桌宠：

    * 左键单击        → 把预设内容复制到剪贴板（并弹出"已复制"提示）
    * 按住左键拖动    → 移动位置（松手不会误触复制）
    * 右键单击        → 打开设置面板：编辑预设内容 / 换形状 / 换颜色
    * 右键面板里的"完成" → 保存内容、立即复制、面板消失

实现方式：纯 Python 标准库（tkinter + ctypes），不依赖任何第三方包。
    - 无边框无标题栏窗口 + Win32 透明色键 → 桌面上的"悬浮小球"
    - 定时 SetWindowPos(HWND_TOPMOST) → 永远压在最上面（含全屏程序之外的所有窗口）
    - Win32 剪贴板 API → 程序退出后剪贴板内容依然保留

运行：双击 start.bat，或命令行 pythonw desktop_pet.pyw
"""

import ctypes
import json
import math
import os
import sys
import tkinter as tk
import tkinter.font as tkfont

# --------------------------------------------------------------------------
# 常量
# --------------------------------------------------------------------------

APP_NAME = "桌面小宠"
APP_ID = "DesktopPet.SingleInstance.v1"

BASE_SIZE = 66                 # 默认直径（逻辑像素）≈ 两个 Windows 默认鼠标指针
TRANSPARENT_KEY = "#010203"    # 透明色键（几乎不会与任何配色冲突）

CARD = "#FFFFFF"
BORDER = "#E4E7EC"
TEXT_MAIN = "#1F2329"
TEXT_SUB = "#8B929C"
PRIMARY = "#2F6FED"
PRIMARY_HOVER = "#1E5BD8"
GHOST = "#F2F4F7"
GHOST_HOVER = "#E6EAF0"
FIELD = "#F7F8FA"
DANGER = "#E5484D"

FONT_UI = "Microsoft YaHei UI"

DEFAULT_TEXT = (
    "你好呀！这是桌面小宠帮你复制的内容 ✨\n"
    "左键点我 = 复制这段文字\n"
    "右键点我 = 修改内容 / 换形状 / 换颜色\n"
    "按住拖动 = 换个位置"
)

# 形状：(显示名, 生成函数)
SHAPE_NAMES = {
    "circle": "圆形",
    "rounded": "圆角方块",
    "square": "方块",
    "star": "星星",
    "heart": "爱心",
    "hexagon": "六边形",
    "diamond": "菱形",
}
SHAPE_ORDER = ["circle", "rounded", "square", "star", "heart", "hexagon", "diamond"]

# 颜色：(显示名, 色值)
COLORS = [
    ("白色", "#FFFFFF"),
    ("墨黑", "#1F2329"),
    ("蓝色", "#2F6FED"),
    ("青蓝", "#32ADE6"),
    ("绿色", "#2FBF71"),
    ("黄色", "#FFD426"),
    ("橙色", "#FF9F0A"),
    ("红色", "#FF453A"),
    ("粉红", "#FF5E8A"),
    ("紫色", "#AF52DE"),
    ("棕色", "#A2845E"),
    ("灰色", "#9AA0A6"),
]

# --------------------------------------------------------------------------
# 颜色工具
# --------------------------------------------------------------------------


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    r, g, b = (max(0, min(255, int(round(v)))) for v in rgb)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def mix(c1, c2, t):
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def lighten(c, t=0.3):
    return mix(c, "#FFFFFF", t)


def darken(c, t=0.3):
    return mix(c, "#000000", t)


def luminance(c):
    r, g, b = hex_to_rgb(c)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


# --------------------------------------------------------------------------
# Win32 支持
# --------------------------------------------------------------------------

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
else:  # 仅为便于在非 Windows 上做语法检查
    user32 = None
    kernel32 = None

GA_ROOT = 2
HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040


def enable_dpi_awareness():
    """开启每显示器 DPI 感知，避免高分屏下被系统拉伸模糊。"""
    if not IS_WINDOWS:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)   # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_root_hwnd(widget):
    """取 Tk 控件对应的顶层 HWND。"""
    if not IS_WINDOWS:
        return None
    try:
        user32.GetAncestor.restype = ctypes.c_void_p
        user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        hwnd = user32.GetAncestor(ctypes.c_void_p(widget.winfo_id()), GA_ROOT)
        return hwnd or widget.winfo_id()
    except Exception:
        return None


def set_topmost(hwnd):
    if not hwnd:
        return
    try:
        user32.SetWindowPos.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_uint,
        ]
        user32.SetWindowPos.restype = ctypes.c_bool
        user32.SetWindowPos(
            ctypes.c_void_p(hwnd),
            ctypes.c_void_p(-1),      # HWND_TOPMOST
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )
    except Exception:
        pass


def set_clipboard_text(text):
    """用 Win32 API 直接写剪贴板，保证本程序关闭后内容仍然保留。"""
    if not IS_WINDOWS:
        return False
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    try:
        data = (text + "\x00").encode("utf-16-le")

        kernel32.GlobalAlloc.restype = ctypes.c_void_p
        kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
        user32.OpenClipboard.argtypes = [ctypes.c_void_p]
        user32.SetClipboardData.restype = ctypes.c_void_p
        user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]

        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not handle:
            return False
        ptr = kernel32.GlobalLock(ctypes.c_void_p(handle))
        if not ptr:
            kernel32.GlobalFree(ctypes.c_void_p(handle))
            return False
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(ctypes.c_void_p(handle))

        if not user32.OpenClipboard(None):
            kernel32.GlobalFree(ctypes.c_void_p(handle))
            return False
        try:
            user32.EmptyClipboard()
            if not user32.SetClipboardData(CF_UNICODETEXT, ctypes.c_void_p(handle)):
                kernel32.GlobalFree(ctypes.c_void_p(handle))
                return False
        finally:
            user32.CloseClipboard()
        return True
    except Exception:
        return False


def copy_text(widget, text):
    """优先用 Win32，失败则退回 Tk 自带剪贴板。"""
    if set_clipboard_text(text):
        return True
    try:
        widget.clipboard_clear()
        widget.clipboard_append(text)
        widget.update_idletasks()
        return True
    except Exception:
        return False


def ensure_single_instance():
    """同一个会话只允许跑一个桌宠（用命名互斥量判断）。"""
    if not IS_WINDOWS:
        return True
    try:
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        # 关键：先把 last error 清零，否则可能读到上一次调用残留的 183
        ctypes.set_last_error(0)
        kernel32.CreateMutexW(None, False, "Local\\" + APP_ID)
        return ctypes.get_last_error() != 183   # ERROR_ALREADY_EXISTS
    except Exception:
        return True


def message_box(text, title=APP_NAME, timeout_ms=4500):
    """弹提示框；带超时，避免在某些异常环境下永久阻塞。"""
    if not IS_WINDOWS:
        print(text)
        return
    try:
        fn = user32.MessageBoxTimeoutW
        fn.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
                       ctypes.c_uint, ctypes.c_ushort, ctypes.c_uint]
        fn.restype = ctypes.c_int
        fn(None, text, title, 0x00000040, 0, timeout_ms)
        return
    except Exception:
        pass
    try:
        user32.MessageBoxW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p,
                                       ctypes.c_wchar_p, ctypes.c_uint]
        user32.MessageBoxW(None, text, title, 0x00000040)
    except Exception:
        print(text)


# --------------------------------------------------------------------------
# 形状几何（返回数学坐标点，y 轴向上，范围约 -1..1）
# --------------------------------------------------------------------------


def _circle(n=96):
    return [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]


def _square():
    h = 0.98
    return [(h, h), (-h, h), (-h, -h), (h, -h)]


def _rounded_square(r=0.30, h=0.98, seg=10):
    pts = []
    centers = [
        (h - r, h - r, 0, 90),
        (-(h - r), h - r, 90, 180),
        (-(h - r), -(h - r), 180, 270),
        (h - r, -(h - r), 270, 360),
    ]
    for cx, cy, a0, a1 in centers:
        for i in range(seg + 1):
            a = math.radians(a0 + (a1 - a0) * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _star(points=5, inner=0.45):
    pts = []
    for i in range(points * 2):
        a = math.radians(90 + i * (180.0 / points))
        rad = 1.0 if i % 2 == 0 else inner
        pts.append((rad * math.cos(a), rad * math.sin(a)))
    return pts


def _heart(n=100):
    raw = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        raw.append((x, y))
    xs = [p[0] for p in raw]
    ys = [p[1] for p in raw]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    m = max(max(xs) - min(xs), max(ys) - min(ys)) / 2.0
    return [((x - cx) / m, (y - cy) / m) for x, y in raw]


def _hexagon():
    return [(math.cos(math.radians(90 + 60 * i)), math.sin(math.radians(90 + 60 * i))) for i in range(6)]


def _diamond():
    return [(0.0, 1.0), (0.82, 0.0), (0.0, -1.0), (-0.82, 0.0)]


SHAPE_POINTS = {
    "circle": _circle,
    "rounded": _rounded_square,
    "square": _square,
    "star": _star,
    "heart": _heart,
    "hexagon": _hexagon,
    "diamond": _diamond,
}

_CACHE = {}


def shape_points(key):
    if key not in _CACHE:
        _CACHE[key] = SHAPE_POINTS.get(key, _circle)()
    return _CACHE[key]


# --------------------------------------------------------------------------
# 绘制
# --------------------------------------------------------------------------


def round_rect_points(x1, y1, x2, y2, r, seg=10):
    """Canvas 坐标系（y 向下）下的圆角矩形顶点。"""
    pts = []
    corners = [
        (x2 - r, y1 + r, -90, 0),
        (x2 - r, y2 - r, 0, 90),
        (x1 + r, y2 - r, 90, 180),
        (x1 + r, y1 + r, 180, 270),
    ]
    for cx, cy, a0, a1 in corners:
        for i in range(seg + 1):
            a = math.radians(a0 + (a1 - a0) * i / seg)
            pts.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
    return pts


def draw_pet(canvas, shape_key, color, size, tag="pet", k=1.0, dx=0.0, dy=0.0, pad_ratio=0.055):
    """
    在 canvas 上画一只"有体积感"的小宠物。

    Tk 的 Canvas 不支持渐变与抗锯齿，这里用「多层同心收缩 + 逐层调色 + 逐层偏移」
    模拟出球体受光的效果，肉眼看上去是柔和的渐变而不是硬邦邦的同心圆。

    k      : 整体缩放（做点击动画用）
    dx, dy : 以半径 R 为单位的整体偏移（dy 正方向向下）
    """
    canvas.delete(tag)

    pad = size * pad_ratio
    R = (size / 2.0 - pad) * k
    cx = size / 2.0 + dx * R
    cy = size / 2.0 + dy * R
    pts = shape_points(shape_key)

    def poly(scale, ox, oy, fill):
        coords = []
        for x, y in pts:
            coords.append(cx + ox * R + x * R * scale)
            coords.append(cy + oy * R - y * R * scale)
        canvas.create_polygon(coords, fill=fill, outline=fill, width=1, tag=tag)

    lum = luminance(color)
    edge = darken(color, 0.36 if lum > 0.55 else 0.44)
    core = lighten(color, 0.14 if lum > 0.55 else 0.40)

    # 主体：从外圈暗色逐层过渡到中心亮色，同时向左上偏移 → 球体受光感
    layers = 16 if size >= 60 else 10
    for i in range(layers):
        t = i / float(layers - 1)
        e = 1.0 - (1.0 - t) ** 2.0   # 前段收敛快 → 中间是大片纯色，只有边缘有暗部
        poly(1.0 - 0.40 * e,
             -0.130 * e, 0.145 * e,
             mix(edge, core, e))

    # 镜面高光点
    hr = max(1.2, R * 0.115)
    hx = cx - R * 0.275
    hy = cy - R * 0.305
    canvas.create_oval(hx - hr, hy - hr, hx + hr, hy + hr,
                       fill=mix(color, "#FFFFFF", 0.95), outline="", tag=tag)


# --------------------------------------------------------------------------
# 配置
# --------------------------------------------------------------------------


def config_path():
    here = os.path.dirname(os.path.abspath(sys.argv[0] if getattr(sys, "frozen", False) else __file__))
    for folder in (here, os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "DesktopPet")):
        try:
            os.makedirs(folder, exist_ok=True)
            probe = os.path.join(folder, ".write_test")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe)
            return os.path.join(folder, "pet_config.json")
        except Exception:
            continue
    return os.path.join(os.path.expanduser("~"), "pet_config.json")


class Config:
    def __init__(self):
        self.path = config_path()
        self.existed = os.path.exists(self.path)   # 是否已有配置文件（判断是否首次运行）
        self.text = DEFAULT_TEXT
        self.shape = "circle"
        self.color = "#FFFFFF"
        self.x = None
        self.y = None
        self.size = BASE_SIZE

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return self
        self.text = data.get("text", self.text)
        shape = data.get("shape", self.shape)
        self.shape = shape if shape in SHAPE_NAMES else "circle"
        color = data.get("color", self.color)
        self.color = color if isinstance(color, str) and len(color) == 7 else "#FFFFFF"
        self.x = data.get("x")
        self.y = data.get("y")
        size = data.get("size", BASE_SIZE)
        self.size = size if isinstance(size, int) and 40 <= size <= 160 else BASE_SIZE
        return self

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({
                    "text": self.text,
                    "shape": self.shape,
                    "color": self.color,
                    "x": self.x,
                    "y": self.y,
                    "size": self.size,
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False


# --------------------------------------------------------------------------
# 主程序
# --------------------------------------------------------------------------


class DesktopPet:
    def __init__(self, cfg=None, forced_pos=None):
        self.cfg = cfg or Config().load()
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        try:
            self.root.attributes("-topmost", True)
        except Exception:
            pass
        self.root.configure(bg=TRANSPARENT_KEY)
        try:
            self.root.attributes("-transparentcolor", TRANSPARENT_KEY)
        except Exception:
            pass

        self.scale = max(1.0, min(3.0, self.root.winfo_fpixels("1i") / 96.0))
        self.size = int(round(self.cfg.size * self.scale))
        self.size = max(40, min(220, self.size))

        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        if forced_pos:
            px, py = forced_pos
        elif self.cfg.x is not None and self.cfg.y is not None:
            px, py = self.cfg.x, self.cfg.y
        else:
            px, py = sw - self.size - 120, int(sh * 0.32)
        px = max(0, min(sw - self.size, px))
        py = max(0, min(sh - self.size, py))

        self.root.geometry("%dx%d+%d+%d" % (self.size, self.size, px, py))

        self.canvas = tk.Canvas(self.root, width=self.size, height=self.size,
                                bg=TRANSPARENT_KEY, highlightthickness=0, bd=0,
                                cursor="hand2")
        self.canvas.pack(fill="both", expand=True)

        self.panel = None
        self.toast_win = None
        self.hwnd = None
        self._press = None
        self._origin = None
        self._dragging = False
        self._anim = None
        self._hover = False

        self.bind_events()
        self.draw()
        self.root.update_idletasks()
        self.root.lift()
        self.root.after(60, self._post_show)
        self.root.after(900, self._guard_topmost)

    # ---------------- 窗口与绘制 ----------------

    def _post_show(self):
        self.hwnd = get_root_hwnd(self.root)
        set_topmost(self.hwnd)
        self.first_tip()

    def _guard_topmost(self):
        """每隔一段时间重新顶置一次，防止被其它置顶窗口压住。"""
        try:
            if self.panel is None:
                set_topmost(self.hwnd)
        except Exception:
            pass
        self.root.after(1500, self._guard_topmost)

    def draw(self, k=1.0, dx=0.0, dy=0.0):
        draw_pet(self.canvas, self.cfg.shape, self.cfg.color, self.size,
                 k=k, dx=dx, dy=dy)

    def apply_theme(self, shape=None, color=None, redraw=True):
        if shape:
            self.cfg.shape = shape
        if color:
            self.cfg.color = color
        if redraw:
            self.draw()
        self.cfg.save()

    # ---------------- 事件 ----------------

    def bind_events(self):
        c = self.canvas
        c.bind("<ButtonPress-1>", self.on_press)
        c.bind("<B1-Motion>", self.on_drag)
        c.bind("<ButtonRelease-1>", self.on_release)
        c.bind("<ButtonPress-3>", self.on_right_click)
        c.bind("<Enter>", self.on_enter)
        c.bind("<Leave>", self.on_leave)

    def on_enter(self, _e=None):
        if not self._hover:
            self._hover = True
            self.draw(k=1.05)

    def on_leave(self, _e=None):
        if self._hover:
            self._hover = False
            self.draw()

    def on_press(self, e):
        self._press = (e.x_root, e.y_root)
        self._origin = (self.root.winfo_x(), self.root.winfo_y())
        self._dragging = False
        self._hover = True
        self.draw(k=0.93)

    def on_drag(self, e):
        if not self._press:
            return
        dx = e.x_root - self._press[0]
        dy = e.y_root - self._press[1]
        if not self._dragging and math.hypot(dx, dy) >= 4:
            self._dragging = True
        if self._dragging:
            nx = self._origin[0] + dx
            ny = self._origin[1] + dy
            self.root.geometry("+%d+%d" % (nx, ny))

    def on_release(self, e):
        if not self._press:
            return
        dragged = self._dragging
        self._press = None
        self._dragging = False
        self._hover = False

        if dragged:
            self.cfg.x, self.cfg.y = self.root.winfo_x(), self.root.winfo_y()
            self.cfg.save()
            self.draw()
            return

        if self.panel is not None:
            self.close_panel()
        self.copy_preset()

    def on_right_click(self, e):
        if self.panel is not None:
            self.close_panel()
            return
        self.open_panel(e.x_root, e.y_root)

    # ---------------- 核心动作 ----------------

    def copy_preset(self, notice=None):
        """复制预设内容。成功后默认静默（只有球的弹跳反馈，不弹提示窗）。"""
        text = self.cfg.text or ""
        if not text.strip():
            self.toast("还没有内容，先右键设置")
            return False
        ok = copy_text(self.root, text)
        if ok:
            self.bounce()
            if notice:
                self.toast(notice)
        else:
            self.toast("复制失败，请重试")
        return ok

    def bounce(self):
        """点击后的弹性反馈动画。"""
        if self._anim:
            try:
                self.root.after_cancel(self._anim)
            except Exception:
                pass
        frames = [(1.12, 0.018), (0.96, -0.010), (1.04, 0.004), (1.0, 0.0)]

        def step(i=0):
            if i >= len(frames):
                self._anim = None
                self.draw()
                return
            k, dy = frames[i]
            self.draw(k=k, dy=dy)
            self._anim = self.root.after(45, lambda: step(i + 1))

        step()

    # ---------------- 提示气泡 ----------------

    def toast(self, text, ms=1100):
        if self.toast_win is not None:
            try:
                self.toast_win.destroy()
            except Exception:
                pass
            self.toast_win = None

        s = self.scale
        font = tkfont.Font(family=FONT_UI, size=-int(round(13 * s)))
        pad_x, pad_y = int(round(12 * s)), int(round(7 * s))
        tw = font.measure(text) + pad_x * 2
        th = int(round(14 * s)) + pad_y * 2
        radius = th / 2.0

        px = self.root.winfo_x() + self.size // 2 - tw // 2
        py = self.root.winfo_y() + self.size + int(round(6 * s))
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        px = max(4, min(sw - tw - 4, px))
        if py + th > sh - 8:
            py = self.root.winfo_y() - th - int(round(6 * s))
        py = max(4, py)

        win = tk.Toplevel(self.root)
        win.withdraw()
        win.overrideredirect(True)
        win.configure(bg=TRANSPARENT_KEY)
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        try:
            win.attributes("-transparentcolor", TRANSPARENT_KEY)
        except Exception:
            pass
        win.geometry("%dx%d+%d+%d" % (tw, th, px, py))

        cv = tk.Canvas(win, width=tw, height=th, bg=TRANSPARENT_KEY,
                       highlightthickness=0, bd=0)
        cv.pack()
        cv.create_polygon(round_rect_points(0.5, 0.5, tw - 0.5, th - 0.5, radius, 14),
                          fill="#262B33", outline="")
        cv.create_text(tw / 2.0, th / 2.0 + 0.5, text=text, fill="#FFFFFF", font=font)
        cv.bind("<ButtonPress-1>", lambda e: self._close_toast())

        self.toast_win = win
        win.deiconify()
        win.lift()
        self.root.after(ms, self._close_toast)

    def _close_toast(self):
        if self.toast_win is not None:
            try:
                self.toast_win.destroy()
            except Exception:
                pass
            self.toast_win = None

    def first_tip(self):
        """仅在第一次运行（还没有配置文件）时给一次操作引导。"""
        if not self.cfg.existed:
            self.toast("左键复制 · 右键设置 · 按住拖动", 2400)

    # ---------------- 面板 ----------------

    def open_panel(self, x, y):
        if self.panel is not None:
            return
        self._hover = False
        self.draw()
        self.panel = ControlPanel(self, x, y)

    def close_panel(self):
        if self.panel is not None:
            panel = self.panel
            self.panel = None
            try:
                panel.destroy()
            except Exception:
                pass
            set_topmost(self.hwnd)

    # ---------------- 运行 ----------------

    def run(self):
        try:
            self.root.mainloop()
        finally:
            self._close_toast()


class ControlPanel:
    """右键弹出的设置面板：编辑内容 + 选形状 + 选颜色。"""

    def __init__(self, app, x, y):
        self.app = app
        self.s = app.scale
        self.closed = False

        s = self.s
        self.win = tk.Toplevel(app.root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.configure(bg=TRANSPARENT_KEY)
        try:
            self.win.attributes("-topmost", True)
        except Exception:
            pass
        try:
            self.win.attributes("-transparentcolor", TRANSPARENT_KEY)
        except Exception:
            pass

        self.canvas = tk.Canvas(self.win, bg=TRANSPARENT_KEY, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.pad = int(round(18 * s))
        self.body = tk.Frame(self.win, bg=CARD)
        self.body.place(x=self.pad, y=self.pad)

        self._build_widgets()

        self.win.update_idletasks()
        bw = self.body.winfo_reqwidth()
        bh = self.body.winfo_reqheight()
        w = bw + self.pad * 2
        h = bh + self.pad * 2

        sw, sh = app.root.winfo_screenwidth(), app.root.winfo_screenheight()
        px = x + int(round(16 * s))
        py = y - int(round(28 * s))
        if px + w > sw - 8:
            px = x - w - int(round(16 * s))
        if py + h > sh - 8:
            py = sh - h - 8
        px = max(8, px)
        py = max(8, py)

        self.win.geometry("%dx%d+%d+%d" % (w, h, px, py))
        self.canvas.configure(width=w, height=h)
        self.win.update_idletasks()
        self.body.place(x=self.pad, y=self.pad, width=bw, height=bh)

        r = int(round(18 * s))
        self.canvas.create_polygon(
            round_rect_points(1.0, 1.0, w - 1.0, h - 1.0, r, 14),
            fill=CARD, outline=BORDER, width=1,
        )

        self.win.bind("<Escape>", lambda e: self.close())
        self.text_field.bind("<Control-Return>", lambda e: self.on_done())
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()
        self.text_field.focus_set()
        self.text_field.mark_set("insert", "end-1c")

    # ---------- UI ----------

    def _label(self, parent, text, size=13, color=TEXT_MAIN, bold=False, bg=CARD):
        f = tkfont.Font(family=FONT_UI, size=-int(round(size * self.s)),
                        weight="bold" if bold else "normal")
        return tk.Label(parent, text=text, bg=bg, fg=color, font=f, anchor="w")

    def _button(self, parent, text, command, kind="primary", width=None):
        s = self.s
        palette = {
            "primary": (PRIMARY, "#FFFFFF", PRIMARY_HOVER),
            "ghost": (GHOST, "#3A4150", GHOST_HOVER),
            "danger": (CARD, DANGER, "#FDECEC"),
        }
        bg, fg, hover = palette[kind]
        f = tkfont.Font(family=FONT_UI, size=-int(round(13 * s)),
                        weight="bold" if kind == "primary" else "normal")
        lbl = tk.Label(parent, text=text, bg=bg, fg=fg, font=f,
                       padx=int(round(16 * s)), pady=int(round(8 * s)),
                       cursor="hand2")
        if width:
            lbl.configure(width=width)
        lbl.bind("<Button-1>", lambda e: command())
        lbl.bind("<Enter>", lambda e: lbl.configure(bg=hover))
        lbl.bind("<Leave>", lambda e: lbl.configure(bg=bg))
        return lbl

    def _sep(self, parent):
        line = tk.Frame(parent, bg=BORDER, height=1)
        line.pack(fill="x", pady=(int(12 * self.s), int(12 * self.s)))
        return line

    def _build_widgets(self):
        s = self.s
        body = self.body
        MIN_W = int(round(332 * s))

        # 宽度占位条，保证面板不会被内容撑得太窄
        tk.Frame(body, bg=CARD, width=MIN_W, height=1).pack(fill="x")

        # 标题行
        head = tk.Frame(body, bg=CARD)
        head.pack(fill="x")
        self._label(head, "桌面小宠", size=15, bold=True).pack(side="left")
        close = tk.Label(head, text="✕", bg=CARD, fg=TEXT_SUB,
                         font=tkfont.Font(family=FONT_UI, size=-int(round(14 * s))),
                         cursor="hand2", padx=int(round(6 * s)))
        close.pack(side="right")
        close.bind("<Button-1>", lambda e: self.close())
        close.bind("<Enter>", lambda e: close.configure(fg=DANGER))
        close.bind("<Leave>", lambda e: close.configure(fg=TEXT_SUB))

        self._label(body, "左键单击时复制下面这段内容", size=12, color=TEXT_SUB).pack(
            anchor="w", pady=(int(10 * s), int(6 * s)))

        # 输入框
        wrap = tk.Frame(body, bg=FIELD, highlightthickness=1,
                        highlightbackground=BORDER, highlightcolor=PRIMARY)
        wrap.pack(fill="x")
        self.text_field = tk.Text(
            wrap, width=1, height=4, wrap="word", bg=FIELD, fg=TEXT_MAIN, bd=0,
            highlightthickness=0, padx=int(round(9 * s)), pady=int(round(7 * s)),
            font=tkfont.Font(family=FONT_UI, size=-int(round(13 * s))),
            insertbackground=TEXT_MAIN, selectbackground="#CFE0FF",
            spacing1=1, spacing3=1,
        )
        self.text_field.pack(fill="x")
        self.text_field.insert("1.0", self.app.cfg.text)

        self._label(body, "支持多行 · Ctrl+Enter 快速完成", size=11, color=TEXT_SUB).pack(
            anchor="w", pady=(int(5 * s), 0))

        # 主按钮行
        row = tk.Frame(body, bg=CARD)
        row.pack(fill="x", pady=(int(12 * s), 0))
        self._button(row, "完成", self.on_done, "primary").pack(side="left")
        self._button(row, "仅保存", self.on_save_only, "ghost").pack(
            side="left", padx=(int(8 * s), 0))
        self._label(row, "", size=11).pack(side="left", expand=True)

        self._sep(body)

        # 形状
        self._label(body, "形状", size=12, color=TEXT_SUB).pack(anchor="w")
        self.shape_row = tk.Frame(body, bg=CARD)
        self.shape_row.pack(anchor="w", pady=(int(7 * s), 0))
        self._build_shapes()

        # 颜色
        self._label(body, "颜色", size=12, color=TEXT_SUB).pack(
            anchor="w", pady=(int(12 * s), 0))
        self.color_row = tk.Frame(body, bg=CARD)
        self.color_row.pack(anchor="w", pady=(int(7 * s), 0))
        self._build_colors()

        self._sep(body)

        # 底部
        foot = tk.Frame(body, bg=CARD)
        foot.pack(fill="x")
        self._button(foot, "退出桌宠", self.on_quit, "danger").pack(side="right")
        self._label(foot, "拖动可移动 · 右键开关此面板", size=11, color=TEXT_SUB).pack(side="left")

        body.update_idletasks()

    def _build_shapes(self):
        for w in self.shape_row.winfo_children():
            w.destroy()
        s = self.s
        cell = int(round(42 * s))
        for key in SHAPE_ORDER:
            selected = (key == self.app.cfg.shape)
            cv = tk.Canvas(self.shape_row, width=cell, height=cell,
                           bg=CARD, highlightthickness=0, bd=0, cursor="hand2")
            cv.pack(side="left", padx=(0, int(round(4 * s))))
            r = int(round(8 * s))
            if selected:
                cv.create_polygon(round_rect_points(0.5, 0.5, cell - 0.5, cell - 0.5, r, 8),
                                  fill="#EAF1FE", outline=PRIMARY, width=2)
            else:
                cv.create_polygon(round_rect_points(0.5, 0.5, cell - 0.5, cell - 0.5, r, 8),
                                  fill=CARD, outline=BORDER, width=1)
            draw_pet(cv, key, self.app.cfg.color, cell, tag="mini", pad_ratio=0.17)
            cv.bind("<Button-1>", lambda e, k=key: self.pick_shape(k))
            if not selected:
                cv.bind("<Enter>", lambda e, c=cv: c.itemconfigure(1, outline=PRIMARY))
                cv.bind("<Leave>", lambda e, c=cv: c.itemconfigure(1, outline=BORDER))

    def _build_colors(self):
        for w in self.color_row.winfo_children():
            w.destroy()
        s = self.s
        cell = int(round(30 * s))
        accent = self.app.cfg.color.upper()
        for idx, (name, value) in enumerate(COLORS):
            selected = (value.upper() == accent)
            cv = tk.Canvas(self.color_row, width=cell, height=cell,
                           bg=CARD, highlightthickness=0, bd=0, cursor="hand2")
            cv.grid(row=idx // 6, column=idx % 6,
                    padx=(0, int(round(4 * s))), pady=(0, int(round(4 * s))))
            if selected:
                cv.create_oval(1, 1, cell - 1, cell - 1, outline=PRIMARY, width=2)
                cv.create_oval(4, 4, cell - 4, cell - 4,
                               fill=value, outline=darken(value, 0.16), width=1)
            else:
                cv.create_oval(2, 2, cell - 2, cell - 2,
                               fill=value, outline=darken(value, 0.16), width=1)
            cv.bind("<Button-1>", lambda e, v=value: self.pick_color(v))
            if not selected:
                cv.bind("<Enter>", lambda e, c=cv, v=value:
                        c.itemconfigure(1, outline=darken(v, 0.45)))
                cv.bind("<Leave>", lambda e, c=cv, v=value:
                        c.itemconfigure(1, outline=darken(v, 0.16)))

    # ---------- 行为 ----------

    def pick_shape(self, key):
        self.app.apply_theme(shape=key, redraw=True)
        self._build_shapes()

    def pick_color(self, value):
        self.app.apply_theme(color=value, redraw=True)
        self._build_shapes()
        self._build_colors()

    def _current_text(self):
        return self.text_field.get("1.0", "end-1c")

    def on_done(self):
        self.app.cfg.text = self._current_text()
        self.app.cfg.save()
        self.close()
        self.app.copy_preset()      # 面板关闭即反馈，不再弹提示

    def on_save_only(self):
        self.app.cfg.text = self._current_text()
        self.app.cfg.save()
        self.close()

    def on_quit(self):
        try:
            self.app.cfg.x, self.app.cfg.y = self.app.root.winfo_x(), self.app.root.winfo_y()
            self.app.cfg.save()
        except Exception:
            pass
        self.close()
        try:
            self.app.root.after(60, self.app.root.destroy)
        except Exception:
            pass

    def close(self):
        if self.closed:
            return
        self.closed = True
        app = self.app
        app.panel = None
        try:
            self.win.destroy()
        except Exception:
            pass
        try:
            app.root.after(80, lambda: set_topmost(app.hwnd))
        except Exception:
            pass

    def destroy(self):
        try:
            self.win.destroy()
        except Exception:
            pass


# --------------------------------------------------------------------------
# 演示 / 自测模式（用于截图检查渲染效果）
# --------------------------------------------------------------------------


def _arg(argv, name, default):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


def run_demo(argv):
    shape = _arg(argv, "--shape", "circle")
    color = _arg(argv, "--color", "#FFFFFF")
    size = int(_arg(argv, "--size", "72"))
    x = int(_arg(argv, "--x", "120"))
    y = int(_arg(argv, "--y", "120"))
    hold = float(_arg(argv, "--hold", "3"))

    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg=TRANSPARENT_KEY)
    try:
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", TRANSPARENT_KEY)
    except Exception:
        pass
    root.geometry("%dx%d+%d+%d" % (size, size, x, y))
    cv = tk.Canvas(root, width=size, height=size, bg=TRANSPARENT_KEY,
                   highlightthickness=0, bd=0)
    cv.pack()
    draw_pet(cv, shape, color, size)
    root.after(int(hold * 1000), root.destroy)
    root.mainloop()


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------


def main():
    if "--demo" in sys.argv:
        enable_dpi_awareness()
        run_demo(sys.argv)
        return

    enable_dpi_awareness()

    if "--probe" in sys.argv:
        app = DesktopPet()
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_probe.json")

        def report():
            try:
                info = {
                    "geom": app.root.winfo_geometry(),
                    "mapped": app.root.winfo_ismapped(),
                    "canvas_w": app.canvas.winfo_width(),
                    "canvas_h": app.canvas.winfo_height(),
                    "items": len(app.canvas.find_all()),
                    "bbox": str(app.canvas.bbox("all")),
                    "size": app.size,
                    "scale": app.scale,
                    "shape": app.cfg.shape,
                    "color": app.cfg.color,
                }
            except Exception as exc:
                info = {"error": repr(exc)}
            with open(out, "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            app.root.after(200, app.root.destroy)

        app.root.after(1800, report)
        app.run()
        return

    if not ensure_single_instance():
        message_box("桌面小宠已经在运行啦～\n\n如果看不到它，请看看屏幕右侧。")
        return

    app = DesktopPet()
    app.run()


if __name__ == "__main__":
    main()