# ADR-0001: 两个主题合并为单一主题包，统一构建管线产出两套配色

VSCodeDarkModernEnhanced（成熟包，含 VS Code 复刻 + 手写 Monokai Enhanced 伴生配色）
与 MonokaiDarkModern（半成品，含经典 Monokai 源与青绿调改造）合并为单一主题包
**Modern Themes**：仓库根目录即一个可安装的包，包含两个 UI 主题与两套 color scheme、
一个插件、一条构建管线、一套测试。两套配色共用 `mappings/` 共享映射（语义 token、
scope 别名、Markdown/LaTeX 增强），VS Code 路径按 `color_from` 从 VS Code 主题链解析颜色，
Monokai 路径按 `monokai_color` 字段解析为经典 Monokai 色板变量；Monokai 配色以当前内置
经典 Monokai 为基准原样保留，因此增强规则在两套配色间不漂移且 Monokai 保持经典观感。

**Status**: accepted

**Considered Options**:

- 两个独立包（仓库内 `packages/` 子目录）—— 不符合 Package Control"仓库根 = 包"的约定，
  安装需手动复制，且两套构建工具与映射会继续分叉。拒绝。
- Monokai 配色继续手写（`extends` 内置 Monokai）—— 无法纳入构建管线、provenance 与测试，
  且与共享映射脱节。拒绝。
- Monokai 基准采用 MonokaiDarkModern 的青绿调 `#242422` 改造 —— 违背"经典 Monokai 优先"
  的明确要求。拒绝。

**Consequences**:

- 旧的 "Monokai Enhanced" 配色名退役，配置过它的用户需改选 "Monokai Dark Modern"。
- Monokai 源以字节级 vendored 形式存放在 `source/`，与 Sublime 内置版本保持一致可复现。
- 语义 token 颜色遵循经典 Monokai 约定（类型绿、枚举成员紫、关键字粉），与旧手写
  Monokai Enhanced 的部分实验性取色（类型蓝、JSON 键白）不同。
