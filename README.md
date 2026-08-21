# Modern Themes

一个面向 Sublime Text 4 的主题包，包含两套完整主题：

- **VS Code Dark Modern Me** —— 复刻 VS Code Dark Modern 的代码配色与 UI 主题。
- **Monokai Me** —— 经典 Monokai 配色 + 增强规则（Markdown / LaTeX / LSP 语义 token），搭配现代暖色 UI 主题。

两套配色由同一条构建管线从共享映射生成，增强规则不漂移。本包不监听缓冲编辑、不用
`add_regions()` 重绘代码，基础高亮完全由 Sublime color scheme 引擎完成，性能与内置主题
同量级。

## 安装与使用

### Package Control

包进入默认频道前，可直接添加 GitHub 仓库：

1. 打开 Command Palette，运行 `Package Control: Add Repository`。
2. 输入本仓库地址（末尾不要加 `.git`）。
3. 运行 `Package Control: Install Package`，搜索并安装 **ModernThemes**（包名与仓库名一致）。

安装完成后可分别启用 UI 主题与代码配色（`Preferences → Package Settings → Modern Themes`，
或 Command Palette 中搜索 `Modern Themes:`）：

- `Modern Themes: Select VS Code Dark Modern Me Color Scheme`
- `Modern Themes: Select Monokai Me Color Scheme`
- `Modern Themes: Select VS Code Dark Modern Me UI Theme`（同时启用同名的侧栏文件图标主题）
- `Modern Themes: Select Monokai Me UI Theme`（同时启用同名的侧栏文件图标主题）
- `Modern Themes: Inspect Highlight`：显示光标下文本的 Sublime scopes、可用的语义 token、
  命中规则与颜色来源。
- `Modern Themes: Check Semantic Highlighting`：检查 LSP 语义高亮的可用状态并给出配置提示。

也可以直接在 Preferences 中手动配置：

```json
{
    "theme": "Monokai Me.sublime-theme",
    "file_icon_theme": "VS Code Dark Modern Me",
    "color_scheme": "Monokai Me.sublime-color-scheme",
    "file_tab_style": "square"
}
```

`.sublime-theme` 控制 Sublime 界面，`.sublime-color-scheme` 控制编辑区代码颜色，两者可以
自由混搭（例如 Monokai 配色 + VS Code UI 主题）。手动配置主题时，请保留上面的
`file_icon_theme` 设置，否则侧栏不会显示本包的文件图标。

### 从源码安装

将仓库克隆到 Sublime Text 的 `Packages` 目录（文件夹名保持 **ModernThemes**，即包名）：

```powershell
git clone <repo-url> "$env:APPDATA\Sublime Text\Packages\ModernThemes"
```

仓库已经包含生成后的 color scheme，安装使用无需运行 Python。只有修改源主题或映射时才
需要重新构建：

```powershell
python tools/build_theme.py
```

构建会输出两套配色与合并的 `theme-build-report.json`（规则、颜色来源与 provenance 报告）。
只校验输入和映射而不写文件：

```powershell
python tools/build_theme.py --check
```

## 两个主题

### VS Code Dark Modern Me

从 VS Code 的 `dark_vs.json → dark_plus.json → dark_modern.json` 主题链构建，尽量在
Sublime 的 TextMate scopes 与可选 LSP 语义 token 上重现 VS Code Dark Modern 的代码高亮。
UI 主题复刻 VS Code 的深灰面板、方形标签与蓝色强调线。

### Monokai Me

配色以 **经典 Monokai**（Sublime 内置，Sublime HQ Pty Ltd / Wimer Hazenberg）为基准：
19 个色板变量、全部经典规则原样保留，交互色（选区、光标、当前行、括号匹配）沿用
经典值，行号采用 Sublime 内置 Monokai 实际渲染的颜色（#90908A / 当前行 #D8D8D2），
并补齐缩进线、失焦选区、引用高亮等细节键。在此基础上叠加增强规则：

- **Markdown 语义高亮**：标题分级着色（h1 粉红 / h2 橙 / h3–h6 黄，加粗，`#` 标记同色）、
  加粗为黄色、行内代码橙色、`==高亮==` 语法支持、链接/列表/围栏/表格/引用等覆盖；
  行内代码与代码块**无背景色**；
- **LaTeX** 覆盖（命令、环境、引用、参数、数学运算符等）；
- **符号运算符**：`+ - = * / % < > & | ~ !` 等符号运算符为 Monokai 粉红 `#F92672`
  （恢复经典 Monokai 对运算符的着色）；
- **LSP 语义 token**（函数、方法、类型、命名空间、类型参数、参数、属性、只读值、
  枚举成员、static / deprecated / 库成员修饰符等），颜色遵循经典 Monokai 的对应约定
  （如类型为绿色、枚举成员为紫色、关键字为粉色、参数为橙色）；
- 正则表达式、关键字运算符、删除线、枚举成员/常量别名（`variable.other.constant` 等）
  等细化规则。

UI 主题采用"现代暖色"方向：结构与 VS Code 版一致（方形标签、顶部强调线），但面板为暖色
`#1F1E1A`、强调色为 Monokai 粉 `#F92672`，避免 VS Code 深灰配色的压抑感。

## LSP 语义高亮（可选）

安装 [LSP](https://packagecontrol.io/packages/LSP) 以及所用语言的服务器插件，并在 LSP
设置中启用：

```json
{
    "semantic_highlighting": true
}
```

没有 LSP 时，两套主题仍使用 Sublime 的原生 syntax scopes 完成基础高亮。LSP 可进一步将
函数、方法、参数、属性、类型、枚举成员和只读值区分开来。语言服务器是否支持 semantic
tokens、启动时间和大工程的资源消耗由该服务器决定；本包不会安装、启动或修改任何 LSP
配置。

### LSP 弹窗样式（可选）

本包还可为 LSP 的 hover、签名帮助和诊断 minihtml 弹窗安装匹配主题的 CSS 覆盖。它是显式、
全局的 LSP 用户覆盖：切换主题后，请手动运行对应命令，不会自动改写你的 User 文件。

- `Modern Themes: Apply VS Code Dark Modern Me LSP Popup Style`
- `Modern Themes: Apply Monokai Me LSP Popup Style`
- `Modern Themes: Restore Previous LSP Popup Style`

首次安装会将已有的 `Packages/User/LSP/popups.css` 备份为
`popups.css.modern-themes-backup`，再写入选定样式。恢复命令会还原该备份；没有备份时只删除
由本包安装的覆盖。安装或恢复后需要重启 Sublime Text。若已存在旧备份而当前 CSS 不是本包
管理的文件，命令会停止，以免覆盖未知的用户修改。

## 侧栏文件图标

本包提供基于扩展名的侧栏文件图标主题（`VS Code Dark Modern Me.sublime-file-icons` 与
`icons/` 目录内的 `file_type_*` PNG，含 1x/2x/3x 三档缩放）。执行任一
`Select ... UI Theme` 命令会自动把 `file_icon_theme` 设为 `VS Code Dark Modern Me`；
手动配置时需显式保留该设置（见上文）。未设置 `file_icon_theme` 时侧栏显示 Sublime
默认图标。

## 构建与测试

- 构建：`python tools/build_theme.py`（仅用 Python 标准库，支持 JSONC 注释、尾随逗号与
  递归 `include`）。
- 校验：`python tools/build_theme.py --check`。
- 测试：`python -m unittest discover -s tests`。

目录结构：

```
source/vscode/            VS Code 主题链源（dark_vs / dark_plus / dark_modern）
source/Monokai.*          经典 Monokai 配色源（vendored）
mappings/                 共享映射：semantic_tokens / scope_aliases / enhancements /
                          monokai_extras / ui_colors / sublime_ui_overrides
icons/                    侧栏文件图标（file_type_*，含 @2x/@3x 缩放）
tools/                    构建工具（build_theme.py, jsonc.py）
tests/                    pytest 兼容的 unittest 套件
```

## 颜色来源与许可证

配色源文件来自 [microsoft/vscode](https://github.com/microsoft/vscode) 的 Dark Modern /
Dark+ / Dark (Visual Studio) 主题链，并受其 [MIT License](https://github.com/microsoft/vscode/blob/main/LICENSE.txt)
约束；经典 Monokai 源来自 Sublime Text 内置配色（Sublime HQ Pty Ltd / Wimer Hazenberg）。
本仓库的适配代码和文档以 MIT License 发布；详见 [LICENSE](LICENSE)。

发布到 Package Control 时不要提交 `package-metadata.json`；该文件由 Package Control 在
安装阶段自动生成。仓库应通过语义化 Git tag 发布，并声明 `sublime_text: ">=4095"`。

本项目与 Microsoft、Visual Studio Code 或 Sublime HQ 无关联，也未获其背书。
