# 符号运算符粉红 + LSP 语义高亮色彩扩充 — Monokai Me

Status: implemented

## 决定

- **符号运算符着色**：Monokai Me 中 `keyword.operator`（`+ - = * / % < > & | ~ !` 等
  全部符号运算符，语法无法只区分 `+ - =` 三字符）由白色 `var(white3)` 改为
  **Monokai 粉红 `var(red2)` (#F92672)**（用户指定：与关键字同色的经典 Monokai 惯例）。
- **括号匹配**：用户要求撤回，不做改动；`brackets_options` / `bracket_contents_options`
  （`underline`）保持现状。
- **LSP 语义高亮扩充**（共享映射 `mappings/semantic_tokens.json`）：
  - 从合并组拆出独立取色：namespace（蓝）、typeParameter（橙）、parameter（橙，沿用
    经典 Monokai “Function argument 橙色”约定）、property（蓝）；
  - 新增修饰符组：static（蓝）、deprecated（灰 yellow5）、defaultLibrary（蓝）；
    原有 readonly（紫）保留；
  - 全部颜色取自经典 Monokai 19 个色板变量，不新增变量、不改基础观感；
  - 语义 operator 改为粉红 `var(red2)`，与符号运算符一致。
- 共享映射同步影响 VS Code Dark Modern Me：新分组以 `color_from` 按 VS Code 链取色
  （已核对 dark_vs / dark_plus 中存在 `entity.name.namespace`、`entity.name.type`、
  `variable`、`entity.name.function`、`comment`、`support.function`）；
  其运算符/关键字等既有配色不受影响。
- LaTeX 数学运算符与分组符号（`mappings/enhancements.json`，monokai_color
  `var(white3)`）保持白色，不在本次范围。

## 范围

- `mappings/monokai_extras.json`（Keyword operators → `var(red2)`）
- `mappings/semantic_tokens.json`（拆组 + 新增 modifier_groups + operator 改色）
- 重建产物：两套 `.sublime-color-scheme` + `theme-build-report.json`
- 测试：`tests/test_build_theme.py`（语义颜色断言）、`tests/test_package_contract.py`
  （语义覆盖 required set 扩充）
- 文档：README.md、messages/upgrade.txt（新增 1.3.0 条目）、messages.json（版本键）

## 待办

- [x] 实施与构建（`python tools/build_theme.py`）
- [x] 校验与测试（`python tools/build_theme.py --check`、`python -m unittest discover -s tests`）
- [ ] 已安装包 `ModernThemes.sublime-package` 需手动重新打包安装后生效