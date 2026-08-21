#!/usr/bin/env python3
"""Render a local HTML palette preview for color schemes, UI themes, and LSP CSS.

Writes docs/preview.html (gitignored).  Usage:

    python tools/preview.py
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any

try:
    from . import jsonc
except ImportError:
    import jsonc  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "preview.html"

SCHEMES = {
    "VS Code Dark Modern Me": ROOT / "VS Code Dark Modern Me.sublime-color-scheme",
    "Monokai Me": ROOT / "Monokai Me.sublime-color-scheme",
}
UI_THEMES = {
    "VS Code Dark Modern Me": ROOT / "VS Code Dark Modern Me.sublime-theme",
    "Monokai Me": ROOT / "Monokai Me.sublime-theme",
}
LSP_POPUP_STYLES = {
    "VS Code Dark Modern Me": ROOT / "lsp" / "popups" / "vscode-dark-modern.css",
    "Monokai Me": ROOT / "lsp" / "popups" / "monokai-me.css",
}

CSS_BLOCK = re.compile(r"(?P<selector>[^{}]+)\{(?P<declarations>[^{}]*)\}")
CSS_DECLARATION = re.compile(r"(?P<property>[-\w]+)\s*:\s*(?P<value>[^;]+)")
CSS_COLOR = re.compile(r"#[0-9A-Fa-f]{3,8}|\btransparent\b|var\(--[-\w]+\)")


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return (round((r + m) * 255), round((g + m) * 255), round((b + m) * 255))


def _to_hex(rgb: tuple[int, int, int], alpha: float | None = None) -> str:
    r, g, b = rgb
    if alpha is None:
        return "#{:02X}{:02X}{:02X}".format(r, g, b)
    return "#{:02X}{:02X}{:02X}{:02X}".format(r, g, b, round(alpha * 255))


def _parse_hsl(value: str) -> tuple[tuple[int, int, int], float | None] | None:
    match = re.fullmatch(r"hsla?\(([\d.]+),\s*([\d.]+)%,\s*([\d.]+)%(?:,\s*([\d.]+))?\)", value.strip())
    if not match:
        return None
    h = float(match.group(1)) % 360
    s = float(match.group(2)) / 100
    l = float(match.group(3)) / 100
    alpha = float(match.group(4)) if match.group(4) is not None else None
    return _hsl_to_rgb(h, s, l), alpha


class ColorResolver:
    def __init__(self, variables: dict[str, str]) -> None:
        self._variables = {name: self._resolve_expr(expr) for name, expr in variables.items()}

    def _resolve_expr(self, expr: str) -> str:
        expr = expr.strip()
        var_match = re.fullmatch(r"var\((\w+)\)", expr)
        if var_match:
            return self._variables.get(var_match.group(1), "#000000")
        color_match = re.fullmatch(
            r"color\(var\((\w+)\)\s+alpha\(([\d.]+)\)\)", expr
        )
        if color_match:
            base = self._variables.get(color_match.group(1), "#000000")
            alpha = float(color_match.group(2))
            if len(base) == 7:
                rgb = tuple(int(base[i : i + 2], 16) for i in (1, 3, 5))
                return _to_hex(rgb, alpha)
            return base
        if expr.startswith("#"):
            return expr
        parsed = _parse_hsl(expr)
        if parsed is not None:
            rgb, alpha = parsed
            return _to_hex(rgb, alpha)
        return expr

    def resolve(self, expr: str) -> str:
        return self._resolve_expr(expr)


def _swatch_row(
    name: str,
    scope: str,
    color: str | None,
    font_style: str = "",
    swatch_color: str | None = None,
) -> str:
    color = color or "transparent"
    swatch_color = swatch_color or color
    return (
        "<tr>"
        f"<td class='swatch' style='background:{swatch_color}'></td>"
        f"<td class='name'>{_esc(name)}</td>"
        f"<td class='scope'>{_esc(scope)}</td>"
        f"<td class='hex'>{_esc(color)}</td>"
        f"<td class='style'>{_esc(font_style)}</td>"
        "</tr>"
    )


def _esc(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _scheme_section(title: str, path: Path) -> str:
    data = jsonc.load(path)
    resolver = ColorResolver(data.get("variables", {}))
    rows = []
    for name, expr in data.get("globals", {}).items():
        if name in ("brackets_options", "bracket_contents_options", "tags_options"):
            continue
        rows.append(_swatch_row(name, "", resolver.resolve(expr)))
    for rule in data.get("rules", []):
        if not isinstance(rule, dict):
            continue
        name = rule.get("name")
        if not name:
            continue
        foreground = rule.get("foreground")
        background = rule.get("background")
        rows.append(_swatch_row(name, rule.get("scope", ""), resolver.resolve(foreground) if foreground else None))
    return (
        f"<h2>{_esc(title)}</h2>"
        "<table><thead><tr><th></th><th>name</th><th>scope</th><th>color</th><th>style</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def _ui_section(title: str, path: Path) -> str:
    data = jsonc.load(path)
    variables = data.get("variables", {})
    rows = []
    for name, color in variables.items():
        rows.append(_swatch_row(name, "", color))
    return (
        f"<h2>{_esc(title)} (UI theme variables)</h2>"
        "<table><thead><tr><th></th><th>variable</th><th></th><th>color</th><th></th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def _css_color_rows(path: Path) -> list[str]:
    """Return color-bearing declarations from a simple CSS stylesheet in source order."""
    stylesheet = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    rows = []
    for block in CSS_BLOCK.finditer(stylesheet):
        selector = " ".join(block.group("selector").split())
        for declaration in CSS_DECLARATION.finditer(block.group("declarations")):
            property_name = declaration.group("property")
            value = declaration.group("value").strip()
            colors = CSS_COLOR.findall(value)
            if not colors:
                continue
            for color in colors:
                is_variable = color.startswith("var(")
                rows.append(
                    _swatch_row(
                        selector,
                        property_name,
                        color,
                        "CSS variable" if is_variable else "",
                        "transparent" if is_variable else color,
                    )
                )
    return rows


def _lsp_css_section(title: str, path: Path) -> str:
    return (
        f"<h2>{_esc(title)} (LSP popup CSS)</h2>"
        "<table><thead><tr><th></th><th>selector</th><th>property</th><th>color</th><th>style</th></tr></thead>"
        "<tbody>" + "".join(_css_color_rows(path)) + "</tbody></table>"
    )


def render() -> str:
    parts = [
        "<!DOCTYPE html><html lang='zh'><head><meta charset='utf-8'>",
        "<title>Modern Themes — palette preview</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;background:#111;color:#ddd;margin:2rem;max-width:1100px}",
        "h1{color:#fff}h2{margin-top:3rem;color:#F92672}",
        "table{border-collapse:collapse;margin-bottom:2rem}",
        "td,th{border:1px solid #333;padding:3px 10px;font-size:13px;text-align:left}",
        "th{color:#999;font-weight:600}",
        ".swatch{width:52px;border:1px solid #555}",
        ".name{white-space:nowrap;color:#fff}.scope{font-family:monospace;color:#8a8a8a;font-size:11px;max-width:520px;overflow:hidden;text-overflow:ellipsis}",
        ".hex{font-family:monospace;color:#F8F8F2}.style{color:#66D9EF}",
        "</style></head><body>",
        "<h1>Modern Themes — palette preview</h1>",
        "<p>Generated by <code>tools/preview.py</code>; colors in the Monokai section resolve its classic "
        "variables to hex for display only — the scheme itself keeps <code>var()</code> references.</p>",
    ]
    for name, path in SCHEMES.items():
        parts.append(_scheme_section(name, path))
    for name, path in UI_THEMES.items():
        parts.append(_ui_section(name, path))
    for name, path in LSP_POPUP_STYLES.items():
        parts.append(_lsp_css_section(name, path))
    parts.append("</body></html>")
    return "\n".join(parts)


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
