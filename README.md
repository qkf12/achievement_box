# achievement_box · 我的桌面小工具百宝箱

一个私人抽屉：**自己写的小玩具**和**值得留档的软件、链接、灵感截图**，全都塞在这里。

写这些工具的理由很简单——桌面上总有些事重复到烦（记一句话、开个软件、复制一段常用文字），与其每次翻文件夹，不如让它变成桌上的一只小人。

目前仓库里有两件能跑的自制工具，外加一批「用过觉得可以」的软件资料。全部面向 **Windows**。

| 类型 | 数量 | 说明 |
| ---- | ---- | ---- |
| 自研工具 | 2 个 | PyQt5 桌宠 / 纯标准库桌宠，双击即用 |
| 资料收藏 | 6 项 | 装机常用软件、链接、截图，换机时可对照找回 |

---

## 目录一览

```
achievement_box/
├─ README.md
└─ tools/
   ├─ 工具箱桌宠/                      # 自研 · 明日香桌宠 + 工具箱
   │  ├─ bot0.5/                       #   v0.5 桌宠 + 记事本
   │  ├─ bot1.0/                       #   v1.0 新增软件箱
   │  └─ bot1.1/bot/                   #   v1.1 当前主线，代码收在 bot/ 里
   ├─ 左键直接复制/DesktopPet/          # 自研 · 点一下就把预设文字送进剪贴板
   ├─ ladder/                          # 收藏 · Clash Verge 安装包
   ├─ 截图工具/                        # 收藏 · Snipaste 官网地址
   ├─ 自动化测试/                      # 收藏 · Allure 报告工具
   ├─ 类似postman的发送请求工具/        # 收藏 · Insomnia 界面截图
   ├─ qq企鹅/                          # 参考 · qqpet 开源项目截图
   └─ ai制作网页新思路/                 # 参考 · Modern Web Guidance 截图
```

> `ladder/`、`截图工具/` 这类目录只存链接和安装包，点进去没有可运行的代码；能跑的东西都在带 `bot` 和 `DesktopPet` 的目录里。

---

## 自研项目

### 一、明日香桌宠 · 工具箱（`tools/工具箱桌宠/`）

桌面上站着一只明日香，不挡事、会轻轻上下浮动。**左键点它 → 弹出工具箱**，右键 → 调大小、退出。

**桌宠本体**

- 无边框、全透明、始终置顶，拖到哪儿就待在哪儿
- 空闲时按正弦波缓慢浮动；点一下会弹一下并说句话（「嗯？有什么想法吗？」这类）
- 右键菜单里直接拖滑块调大小，50% – 250%，以右下角为锚点缩放，下次启动还记得
- 图片按比例平滑缩放，不抠图，直接用裁掉底部空白的原图

**工具箱**：左侧边栏切换工具，右侧内容区，带淡入淡出和圆角阴影。

| 工具 | 做什么 | 细节 |
| ---- | ---- | ---- |
| 📝 记事本 | 随手记一句想法 | 保存到 `notes/年/月/日/时_分.txt`，文件头自动带时间；可另选保存位置；上限 5000 字，到顶会提示；保存成功 3 秒后提示自动消失 |
| 📦 软件箱 | 桌面式软件启动面板 | 双击图标启动 `.exe`；图标优先自定义图片，否则从 exe 自动提取（带缓存）；右键可改 exe 位置、换图标、删除；末尾「+」添加 |

两个工具的数据都落在 JSON 里，改坏了删掉即可恢复默认：

| 文件 | 存什么 |
| ---- | ---- |
| `assets/software_list.json` | 软件箱列表（名称、exe 路径、图标、唯一 id） |
| `assets/scale.json` | 桌宠缩放比例 |
| `notes/` | 记事本写下的内容 |

**版本演进**

| 版本 | 位置 | 变化 |
| ---- | ---- | ---- |
| v0.5 | `bot0.5/` | 先把透明窗口、置顶、缩放跑通，工具箱里只有记事本 |
| v1.0 | `bot1.0/` | 抽出工具基类与注册表，工具箱变成可扩展的多工具结构，加进软件箱 |
| v1.1 | `bot1.1/bot/` | 代码收进 `bot/` 子目录；修掉反复开关工具箱导致的窗口叠加和关闭动画残留；启动异常写 `pet_error.log`；软件项改用唯一 id 匹配，避免同名软件被误改误删 |

**运行**

```bash
# 依赖只有一个
pip install PyQt5

# 双击启动，或者
python main.py
```

`启动桌宠.bat` 会按顺序找 Python：项目内 `runtime\python\pythonw.exe` → 豆包沙箱自带运行时 → 系统 PATH 里的 `pythonw`。找不到会停下来提示。因为是 `pythonw` 静默启动，看不到报错，所以出错请翻同目录的 `pet_error.log`。

**加一个新工具**

三个文件就能接进工具箱：

```python
# tools/hello.py
from PyQt5.QtWidgets import QLabel
from tools.base_tool import BaseTool


class HelloTool(BaseTool):
    name = "问候"
    icon = "👋"
    tooltip = "点我打个招呼"

    def get_widget(self, parent=None):
        if self._widget is None:
            self._widget = QLabel("你好呀")
        return self._widget
```

然后在 `tools/__init__.py` 里 import 并加进 `TOOL_REGISTRY`，侧边栏就会多一个按钮。`BaseTool` 还留了 `on_show` / `on_hide` / `on_close` / `refresh` 四个钩子，需要刷新时间、暂停计时器时就重写它们。

---

### 二、桌面小宠 · 左键直接复制（`tools/左键直接复制/DesktopPet/`）

另一个方向的桌宠：不是替你记事，而是**把一段固定的话随时递到你手里**。

屏幕上有个白色小圆球，左键一点，预设内容立刻进剪贴板，球弹一下，不弹任何提示窗。开工前那句模板、常用命令、报错链接，都能塞进去。

- **零依赖**：`tkinter` + `ctypes`，纯标准库，不用 `pip install`
- **透明穿透**：无边框 + 分层窗口色键，球以外的区域完全透明且能点穿，不挡桌面图标
- **右键设置**：改内容（支持多行）、选 7 种形状（圆 / 圆角方块 / 方块 / 星星 / 爱心 / 六边形 / 菱形）、选 12 种颜色，主球实时预览
- **拖得动**：按住拖动超过 4 像素算移动，不会误触发复制；位置自动记住
- **关掉还在**：走 Win32 原生剪贴板接口，程序退出后内容依然留着
- **单实例**：重复双击不会再蹦出一个球
- **高 DPI**：125% / 150% / 175% 缩放下大小一致、不发虚

| 文件 | 作用 |
| ---- | ---- |
| `desktop_pet.pyw` | 主程序，单文件约千行 |
| `启动桌宠.bat` | 双击启动 |
| `启动桌宠(无黑框).vbs` | 静默启动，不闪控制台，适合放启动目录 |
| `pet_config.json` | 自动生成，存内容 / 形状 / 颜色 / 位置 / 大小 |

操作一览：左键单击复制 · 拖动移动 · 右键开面板 · 面板里 `Ctrl + Enter` 等于「完成」· `Esc` 关面板不保存。

> 想看更细的说明（开机自启、改大小、恢复默认、常见问题），那份目录里还有一份独立 README。

---

## 收藏与参考

不是代码，是「以后装机还想装、以后还想再看一眼」的东西。

| 目录 | 里面是什么 | 留它的原因 |
| ---- | ---- | ---- |
| `ladder/` | Clash Verge 2.5.2 x64 安装包 | 换机器时不用再找一遍；注意这是二进制大文件 |
| `截图工具/` | Snipaste 官网地址 | 截图 + 贴图，日常用得最多的一个 |
| `自动化测试/` | Allure 2 releases 地址 + `allure --version` 截图 | 生成测试报告；截图记录的是装好的 2.46.1 |
| `类似postman的发送请求工具/` | Insomnia 13.2.0 界面截图 | 调 HTTP 接口的备选，界面比 Postman 干净些 |
| `qq企鹅/` | qqpet 开源项目截图（QQ 宠物复刻版） | 做桌宠时参考它的交互与窗口行为 |
| `ai制作网页新思路/` | Modern Web Guidance 项目截图 | Chrome 团队给编程助手写的前端实践，写网页前值得翻 |

---

## 技术栈

- **Python 3** · PyQt5（`QWidget` 自绘 + `QPropertyAnimation` 动画 + `QStackedWidget` 切换工具页）
- **Python 3** · tkinter + ctypes（不引入任何第三方包的那一版）
- **Win32 细节**：分层窗口色键、`SetWindowPos(HWND_TOPMOST)`、`OpenClipboard` / `SetClipboardData`、`SetProcessDpiAwareness`
- **数据**：本地 JSON + 纯文本，不上数据库、不联网

---

## 快速开始

```powershell
git clone <本仓库地址>
cd achievement_box
```

**想用明日香桌宠** → 进 `tools\工具箱桌宠\bot1.1\bot\`，`pip install PyQt5`，双击 `启动桌宠.bat`。

**想要点击复制** → 进 `tools\左键直接复制\DesktopPet\`，双击 `启动桌宠.bat`（想完全无黑框就双击那个 `.vbs`）。

两只桌宠可以同时开着，互不干扰，只是屏幕上会比较热闹。

---

## 一点约定

新加一个工具时，按现有习惯来，后面翻起来不乱：

1. 一个工具一个文件夹，放自己的 `README.md`，说明怎么跑、依赖什么；
2. 可执行入口保持「双击就能用」——要么 `.bat`，要么 `.pyw`；
3. 配置和用户数据用 JSON 存在工具目录内，不要写注册表和全局路径；
4. 不提交 `__pycache__/`、`*.pyc`、`pet_error.log`、`*.exe` 安装包这类可以从别处重新拿到的东西（体积上去了，仓库就不好 clone 了）；
5. 收藏类目录只放链接或截图，附一句话说明用途。

---

## Git 多远程推送

仓库同时绑了两个远程，一次推到两边：

```bash
git remote -v
# origin   -> Gitee
# github   -> GitHub

git push origin master
git push github master
```

为了少敲一行，配置了别名 `pushall`：

```bash
git config --global alias.pushall '!git push origin master && git push github master'
git pushall
```

换机器后重建这两条远程即可：

```bash
git remote add origin <Gitee 仓库地址>
git remote add github <GitHub 仓库地址>
```

---

## 说明

个人自用项目，未指定开源协议；第三方软件与项目的版权归各自作者，这里只做资料留存和截图引用。桌宠形象取自公开图源，仅作本机使用。

如果这些代码恰好帮到你，随便拿去改。