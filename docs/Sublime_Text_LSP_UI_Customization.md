# Sublime Text LSP UI 定制指南

本文基于 [sublimelsp/LSP](https://github.com/sublimelsp/LSP) 项目的当前配置、文档和源码，整理 Sublime Text 中 LSP 的悬浮窗、诊断信息和相关 UI 定制方式。

---

## 1. LSP 对悬浮窗的定制程度

LSP 的 Hover 悬浮窗并不是完全写死的。

LSP 内部使用 `mdpopups` 渲染悬浮窗，因此可以通过：

```text
Packages/User/mdpopups.css
```

对弹窗内部样式进行覆盖。

例如：

```css
html {
    --mdpopups-font-mono: "JetBrains Mono";
}
```

LSP 自己还提供：

```text
Packages/LSP/popups.css
```

其中定义了 LSP Popup 的字体大小、Padding、代码块、Diagnostics、Actions 等样式。

例如默认包含：

```css
.lsp_popup {
    --font-size: 1rem;
    --font-size-sm: 0.9rem;
    font-family: system;
    font-size: var(--font-size);
}
```

Diagnostic 在悬浮窗中的样式类似：

```css
.error {
    background-color: color(var(--redish) alpha(0.2));
}

.warning {
    background-color: color(var(--yellowish) alpha(0.2));
}
```

因此 Hover Popup 内部可以调整：

- 字体
- 字号
- Padding / Margin
- Code Block 样式
- Error / Warning / Info / Hint 样式
- Actions 区域
- `kbd`
- 分隔线
- Markdown 标题
- 引用和 Alert
- 部分链接样式

### 限制

Sublime Text Popup 最外层并不是普通浏览器窗口，因此以下内容不一定能完全控制：

- 真正的系统级圆角
- 外层窗口阴影
- Native Window Border
- Popup 动画
- Popup 精确定位策略

LSP 主要控制的是 Popup 内部的 HTML/CSS 内容。

### Hover 相关 Settings

```json
{
    "popup_max_characters_width": 120,
    "popup_max_characters_height": 1000,

    "show_diagnostics_in_hover": true,
    "show_code_actions_in_hover": true,
    "show_symbol_action_links": true,

    "hover_highlight_style": ""
}
```

其中：

```json
"hover_highlight_style"
```

支持：

```text
background
underline
stippled
outline
""
```

对应的颜色可以通过 Color Scheme 中的：

```text
markup.highlight.hover
```

进行调整。

---

# 2. Error / Warning / Hint 的样式能否修改

可以，而且分为多个层次。

如果错误信息直接出现在代码右侧，例如：

```text
Argument of type "tuple[int, ...]" cannot be assigned ...
```

那么通常是 **Diagnostic Annotation**。

它由：

```json
"show_diagnostics_annotations_severity_level": 0
```

控制。

等级含义：

```text
0 = 不显示
1 = Error
2 = Warning
3 = Info
4 = Hint
```

例如：

```json
"show_diagnostics_annotations_severity_level": 2
```

表示显示：

- Error
- Warning

---

## 3. 修改 Diagnostic 的颜色

LSP 使用以下 Scope：

```text
Error        markup.error
Warning      markup.warning
Information  markup.info
Hint         markup.info.hint
```

因此可以直接修改 Sublime Text Color Scheme：

```json
{
    "rules": [
        {
            "scope": "markup.error",
            "foreground": "#D05A63"
        },
        {
            "scope": "markup.warning",
            "foreground": "#C58A3A"
        },
        {
            "scope": "markup.info",
            "foreground": "#5B8FB9"
        },
        {
            "scope": "markup.info.hint",
            "foreground": "#808080"
        }
    ]
}
```

Diagnostic Annotation 的主颜色本身也是从这些 Scope 的 `foreground` 中读取的。

---

# 4. 修改 Diagnostic Annotation 的内部样式

LSP 自带：

```text
Packages/LSP/annotations.css
```

默认包含类似：

```css
body {
    margin: 0;
    border-width: 0;
    font-family: system;
}

p {
    display: inline;
}

code {
    font-family: monospace;
    padding: 0.05rem 0.25rem;
}

.error {
    color: color(var(--redish) alpha(0.85));
}

.warning {
    color: color(var(--yellowish) alpha(0.85));
}

.information {
    color: color(var(--bluish) alpha(0.85));
}

.hint {
    color: color(var(--bluish) alpha(0.85));
}
```

因此右侧 Diagnostic Annotation 可以修改：

- 字体
- 字号
- Error 颜色
- Warning 颜色
- Info / Hint 颜色
- Code 样式
- Padding
- 透明度

`annotations.css` 与 `popups.css` 是独立的 LSP 文件；修改 Popup CSS 不会影响右侧注释。
若使用 Modern Themes，请运行对应的 `Apply ... LSP UI Style` 命令。它会成对覆盖并安全备份：

```text
Packages/LSP/popups.css
Packages/LSP/annotations.css
```

两份备份均使用 `.modern-themes-backup` 后缀。恢复命令会还原这两个文件；应用或恢复后需重启
Sublime Text。

例如降低视觉强度：

```css
.error {
    color: color(var(--redish) alpha(0.65));
}

.warning {
    color: color(var(--yellowish) alpha(0.70));
}

.information {
    color: color(var(--bluish) alpha(0.65));
}

.hint {
    color: color(var(--foreground) alpha(0.50));
}
```

也可以统一改成低对比度灰色：

```css
.error,
.warning,
.information,
.hint {
    color: color(var(--foreground) alpha(0.60));
}
```

这种方式可以保留错误波浪线，但让右侧文字不那么刺眼。

---

# 5. Diagnostic 下划线 / 波浪线样式

LSP 当前提供：

```json
"diagnostics_highlight_style": {
    "error": "squiggly",
    "warning": "squiggly",
    "info": "stippled",
    "hint": "stippled"
}
```

可用值：

```text
box
underline
stippled
squiggly
""
```

例如全部改成普通下划线：

```json
"diagnostics_highlight_style": {
    "error": "underline",
    "warning": "underline",
    "info": "underline",
    "hint": ""
}
```

或者更简洁：

```json
"diagnostics_highlight_style": {
    "error": "squiggly",
    "warning": "underline",
    "info": "",
    "hint": ""
}
```

其中：

```text
""
```

表示不绘制该等级的诊断高亮。

---

# 6. Gutter Diagnostic 图标

LSP 提供：

```json
"diagnostics_gutter_marker": "sign"
```

可选：

```text
dot
circle
bookmark
sign
""
```

例如：

```json
"diagnostics_gutter_marker": "dot"
```

可以使用更简洁的圆点。

完全关闭：

```json
"diagnostics_gutter_marker": ""
```

源码中 Error、Warning、Information 默认还分别对应：

```text
Packages/LSP/icons/error.png
Packages/LSP/icons/warning.png
Packages/LSP/icons/info.png
```

---

# 7. LSP 与 UI 直接相关的 Settings

以下是当前 `LSP.sublime-settings` 中与 UI / 显示关系较大的选项。

| Setting | 作用 |
|---|---|
| `show_view_status` | 在状态栏显示 LSP Server 状态 |
| `show_diagnostics_count_in_view_status` | 状态栏显示错误 / Warning 数量 |
| `show_diagnostics_in_view_status` | 光标所在 Diagnostic 显示到状态栏 |
| `show_diagnostics_severity_level` | 控制哪些等级显示 Highlight 和 Gutter |
| `show_diagnostics_annotations_severity_level` | 控制右侧 Diagnostic Annotation |
| `show_diagnostics_panel_on_save` | 保存后自动打开 Diagnostics Panel |
| `diagnostics_panel_include_severity_level` | 控制 Panel 显示哪些等级 |
| `diagnostics_delay_ms` | Diagnostic 延迟 |
| `diagnostics_additional_delay_auto_complete_ms` | 补全打开时额外延迟 |
| `diagnostics_highlight_style` | Diagnostic Highlight 样式 |
| `diagnostics_gutter_marker` | Gutter Marker 样式 |
| `show_multiline_diagnostics_highlights` | 多行 Diagnostic Highlight |
| `popup_max_characters_width` | Hover 最大宽度 |
| `popup_max_characters_height` | Hover 最大高度 |
| `show_diagnostics_in_hover` | Hover 中显示 Diagnostics |
| `show_code_actions_in_hover` | Hover 中显示 Code Actions |
| `show_symbol_action_links` | Hover 中显示 Symbol Actions |
| `show_code_actions` | Code Action 使用 Annotation / Bulb / Hidden |
| `show_signature_help` | Signature Help Popup |
| `show_code_lens` | Code Lens 使用 Annotation / Phantom |
| `show_inlay_hints` | 显示 Inlay Hints |
| `inlay_hints_max_length` | Inlay Hint 最大长度 |
| `document_highlight_style` | 当前符号相关 Highlight |
| `show_multiline_document_highlights` | 多行 Symbol Highlight |
| `hover_highlight_style` | Hover 对象高亮方式 |
| `link_highlight_style` | 文件 / URL 链接下划线 |
| `semantic_highlighting` | Semantic Token Highlight |
| `show_references_in_quick_panel` | References 使用 Quick Panel |

---

# 8. Color Scheme 可以控制的 LSP Scope

LSP 的 UI 并不只由 `LSP.sublime-settings` 控制。

整体可以理解为：

```text
LSP.sublime-settings
        ↓
行为 / 是否显示 / 展示方式

Color Scheme
        ↓
颜色 / Scope 样式

CSS
        ↓
Popup / Annotation / Inlay Hint 等 HTML UI
```

## Diagnostics

```text
markup.error
markup.warning
markup.info
markup.info.hint
```

## Hover

```text
markup.highlight.hover
```

## Code Action

```text
markup.accent.codeaction
```

## Code Lens

```text
markup.accent.codelens
```

## Signature Help

```text
meta.signature-help
meta.signature-help.parameter
variable.parameter.sighelp.active
```

## Semantic Highlighting

例如：

```text
meta.semantic-token.variable
meta.semantic-token.parameter
meta.semantic-token.function
meta.semantic-token.method
meta.semantic-token.class
meta.semantic-token.struct
meta.semantic-token.namespace
meta.semantic-token.property
```

---

# 9. LSP 自带的主要 UI CSS

LSP 当前会加载：

```text
Packages/LSP/popups.css
Packages/LSP/notification.css
Packages/LSP/sheets.css
Packages/LSP/inlay_hints.css
Packages/LSP/annotations.css
```

它们大致对应：

```text
Hover / Signature / Diagnostic Popup
        ↓
popups.css + mdpopups.css

右侧 Diagnostic Annotation
        ↓
annotations.css

Inlay Hint
        ↓
inlay_hints.css

LSP Sheet
        ↓
sheets.css

Notification
        ↓
notification.css
```

其中最值得定制的是：

```text
mdpopups.css
popups.css
annotations.css
inlay_hints.css
```

---

# 10. 一个偏极简的推荐配置

如果希望保留 LSP 的信息完整性，但降低视觉干扰，可以使用：

```json
{
    "show_diagnostics_severity_level": 4,

    "show_diagnostics_annotations_severity_level": 2,

    "show_code_actions": "bulb",

    "diagnostics_highlight_style": {
        "error": "squiggly",
        "warning": "underline",
        "info": "",
        "hint": ""
    },

    "diagnostics_gutter_marker": "dot",

    "show_diagnostics_in_hover": true,
    "show_code_actions_in_hover": true,

    "popup_max_characters_width": 100,

    "hover_highlight_style": ""
}
```

对应的视觉策略：

```text
Error
├─ 波浪线
├─ 小圆点
└─ 右侧错误文字

Warning
├─ 普通下划线
├─ 小圆点
└─ 右侧警告文字

Info
└─ 不直接绘制，仅在 Hover / Panel 中查看

Hint
└─ 不直接绘制，仅在 Hover / Panel 中查看
```

`show_code_actions` 设为 `"bulb"` 是为了避免 Code Action Annotation 与 Diagnostics Annotation
同时占用右侧位置；LSP 官方也提示这两种 Annotation 同时开启时无法保证哪一个优先显示。
以上 JSON 仅为用户可选择粘贴的 LSP 配置，Modern Themes 不会自动修改 `LSP.sublime-settings`。

这种方式可以保留 Diagnostics 的功能，同时让编辑区域更干净。

---

# 11. 总结

Sublime Text LSP 的 UI 定制能力可以分为三层：

```text
Settings
├─ 控制显示与行为
├─ Diagnostic 等级
├─ Highlight 类型
├─ Gutter Marker
└─ Popup 尺寸

Color Scheme
├─ Diagnostic 颜色
├─ Hover Highlight
├─ Code Action
├─ Code Lens
├─ Signature Help
└─ Semantic Highlighting

CSS
├─ Hover Popup
├─ Diagnostic Popup
├─ Diagnostic Annotation
├─ Inlay Hint
├─ Notification
└─ Sheet
```

因此，LSP 的 UI 并不是只能通过 `LSP.sublime-settings` 修改。

对于希望打造更加现代、简洁、低视觉干扰的 Sublime Text 环境，最值得研究的是：

```text
LSP.sublime-settings
Color Scheme
Packages/User/mdpopups.css
Packages/LSP/popups.css
Packages/LSP/annotations.css
Packages/LSP/inlay_hints.css
```

Modern Themes 为两个主题分别提供 Popup 与 Annotation CSS。其 Annotation 样式使用较低干扰的
主题色：Error/Warning 保持可扫读的严重级别区分，Information/Hint 使用更低对比度作为开启四级
注释时的回退样式。

---

## 参考

- LSP 项目
  https://github.com/sublimelsp/LSP

- LSP Features
  https://lsp.sublimetext.io/features/

- mdpopups
  https://github.com/facelessuser/sublime-markdown-popups

- LSP 默认配置
  https://github.com/sublimelsp/LSP/blob/main/LSP.sublime-settings

- LSP `popups.css`
  https://github.com/sublimelsp/LSP/blob/main/popups.css

- LSP `annotations.css`
  https://github.com/sublimelsp/LSP/blob/main/annotations.css
