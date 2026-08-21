"""Tests for the generated local palette preview."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import preview  # noqa: E402


class PreviewTests(unittest.TestCase):
    def test_lsp_css_rows_include_literal_colors_and_css_variables(self) -> None:
        rows = "".join(preview._css_color_rows(preview.LSP_UI_STYLES["VS Code Dark Modern Me"]))

        self.assertIn(".lsp_popup", rows)
        self.assertIn("#252526", rows)
        self.assertIn("#F85149", rows)
        self.assertIn("--mdpopups-admon-tip-accent", rows)
        self.assertIn("CSS variable", rows)

    def test_monokai_popup_top_border_uses_a_subtle_green_accent(self) -> None:
        stylesheet = preview.LSP_UI_STYLES["Monokai Me"].read_text(encoding="utf-8")

        self.assertIn("border-top: 1px solid #78AB17", stylesheet)

    def test_render_includes_lsp_popup_and_annotation_sections(self) -> None:
        html = preview.render()

        self.assertIn("VS Code Dark Modern Me (LSP popup CSS)", html)
        self.assertIn("Monokai Me (LSP popup CSS)", html)
        self.assertIn("VS Code Dark Modern Me Diagnostics Annotation (LSP Diagnostics Annotation CSS)", html)
        self.assertIn("Monokai Me Diagnostics Annotation (LSP Diagnostics Annotation CSS)", html)
        self.assertIn("<th>selector</th><th>property</th><th>color</th>", html)
        self.assertIn("#F92672", html)
        self.assertIn("#F48771", html)


if __name__ == "__main__":
    unittest.main()
