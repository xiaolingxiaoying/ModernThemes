# CONTEXT

术语表（glossary）。本文件只收录领域词汇与概念，不含实现细节。

## 核心概念

- **主题包 (theme package)** — 一个可安装的 Sublime 包，同时提供 UI 主题与配色。本仓库是一个主题包，内含两套完整主题。
- **UI 主题 (UI theme)** — `.sublime-theme` 文件，控制 Sublime 界面外观：标题栏、标签栏、侧栏、面板、状态栏。
- **配色 (color scheme)** — `.sublime-color-scheme` 文件，控制编辑区代码颜色。
- **经典 Monokai 色板 (classic Monokai palette)** — Sublime 内置 Monokai 配色（作者 Sublime HQ Pty Ltd / Wimer Hazenberg）的变量色板与规则集。它是 Monokai 配色的基准，任何增强不得改变其基础观感。
- **增强规则 (enhanced rules)** — 主题包的"高级功能"集合，包括：scope 别名统一、Markdown/LaTeX 覆盖规则、LSP 语义 token 样式、UI 交互色（光标、选区、当前行、括号匹配、行号）。这些规则以共享映射的形式存在，两套配色共用。
- **共享映射 (shared mappings)** — 两套配色共用的规则映射，通过颜色间接引用（color-from）指向各配色自己的基准色，因此同一映射在两套配色下渲染出各自的语言。
- **统一构建管线 (unified build pipeline)** — 一条构建管线从"基准色规则集 + 共享映射"生成两套配色，保证增强规则在两套配色间不漂移。
- **LSP 语义高亮 (semantic highlighting)** — 可选增强：LSP 提供语义 token，配色为 token 类型（函数、类型、参数、只读值等）提供独立颜色。不安装 LSP 时配色仍完整可用。
- **Markdown 语义高亮 (markdown semantic highlighting)** — 基于语法 scope 的 Markdown 语义着色：标题分级、加粗、斜体、删除线、链接、行内代码、列表、引用、表格等，由 color scheme 规则实现，与 LSP 语义高亮无关。行内代码与代码块刻意不设背景色。
- **压抑 (oppressive)** — 用户对 UI 主题的反目标：近乎纯黑的统一面板、低饱和、无暖调、大面积同色的界面观感。VS Code Dark Modern 风格被评价为压抑；Monokai UI 主题的明确设计约束是"不压抑"。

## 主题（具名实体）

- **VS Code Dark Modern** — 对 VS Code Dark Modern 主题链（dark_vs → dark_plus → dark_modern）的复刻主题：UI 主题 + 对应配色。
- **Monokai Dark Modern** — 经典 Monokai 配色与增强规则的组合主题：UI 主题 + 对应配色。配色遵循经典 Monokai 色板，UI 主题采用"现代暖色"方向（结构现代、色板温暖、点缀高饱和）。
