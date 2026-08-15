# 行号颜色 — Monokai Dark Modern

Status: implemented

## 决定

- 行号颜色改用 **Sublime 内置默认 Monokai 实际渲染的颜色**（用户指定）。
- 实测方法：便携副本启动 ST build 4200，加载内置 `Monokai.sublime-color-scheme`，
  经 `view.style()` 取渲染值 —— 经典 Monokai 未定义 gutter 键，渲染为 ST 内部默认：
  - `gutter_foreground`（行号）= `#90908A`
  - `gutter_foreground_highlight`（当前行号）= `#D8D8D2`
- 替换 `mappings/monokai_extras.json` 中 1.1.0 引入的自选值（`#75715E` / `#F8F8F2`）。
- 只改 Monokai 路径；VS Code Dark Modern Enhanced 保持对 VS Code 的忠实复刻，不动。

## 范围

- `mappings/monokai_extras.json`
- 重建产物：两套 `.sublime-color-scheme` + `theme-build-report.json`
- 测试固定值：`tests/test_build_theme.py`、`tests/test_package_contract.py`
- `docs/preview.html` 重新生成
- README 措辞修正（"沿用经典值" → 行号采用内置 Monokai 渲染值）
- `messages/upgrade.txt` 新增 1.1.6 条目
- CONTEXT.md 补充"行号"术语

## 待办

- [x] 实施与构建
- [ ] 已安装包 `ModernThemes.sublime-package` 需手动重新打包安装后生效
