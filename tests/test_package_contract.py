"""Static package checks that do not require a running Sublime Text instance."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

VSCode_SCHEME = "VS Code Dark Modern Enhanced.sublime-color-scheme"
MONOKAI_SCHEME = "Monokai Dark Modern.sublime-color-scheme"
VSCode_UI_THEME = "VS Code Dark Modern.sublime-theme"
MONOKAI_UI_THEME = "Monokai Dark Modern.sublime-theme"


class PackageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vscode = json.loads((ROOT / VSCode_SCHEME).read_text(encoding="utf-8"))
        cls.monokai = json.loads((ROOT / MONOKAI_SCHEME).read_text(encoding="utf-8"))
        cls.schemes = (cls.vscode, cls.monokai)

    def test_required_runtime_resources_exist(self) -> None:
        required = {
            VSCode_SCHEME,
            MONOKAI_SCHEME,
            VSCode_UI_THEME,
            MONOKAI_UI_THEME,
            "tab_square_highlight_thin.png",
            "Modern Themes.sublime-commands",
            "Main.sublime-menu",
            "modern_themes.py",
            "messages.json",
            "README.md",
            "LICENSE",
            "theme-build-report.json",
            "tools/build_theme.py",
        }
        self.assertFalse([name for name in required if not (ROOT / name).is_file()])
        self.assertFalse((ROOT / "package-metadata.json").exists())

    def test_ui_themes_use_packaged_tab_highlight(self) -> None:
        for theme_name in (VSCode_UI_THEME, MONOKAI_UI_THEME):
            theme = json.loads((ROOT / theme_name).read_text(encoding="utf-8"))
            textures = [rule.get("layer2.texture") for rule in theme["rules"]]
            self.assertIn("tab_square_highlight_thin.png", textures, theme_name)
            self.assertFalse([texture for texture in textures if texture and texture.startswith("User/")], theme_name)

    def test_no_continuous_buffer_processing_hooks(self) -> None:
        plugin = (ROOT / "modern_themes.py").read_text(encoding="utf-8")
        forbidden = ("on_modified", "add_regions(", "find_all(")
        self.assertFalse([name for name in forbidden if name in plugin])

    def test_semantic_categories_are_covered_by_both_schemes(self) -> None:
        required = {
            "meta.semantic-token.function",
            "meta.semantic-token.method",
            "meta.semantic-token.macro",
            "meta.semantic-token.type",
            "meta.semantic-token.class",
            "meta.semantic-token.parameter",
            "meta.semantic-token.property",
            "meta.semantic-token.enummember",
            "meta.semantic-token.variable.readonly",
            "meta.semantic-token.newoperator",
        }
        for scheme in self.schemes:
            selectors = " ".join(rule["scope"] for rule in scheme["rules"])
            missing = [scope for scope in required if scope not in selectors]
            self.assertFalse(missing, scheme["name"])

    def test_markdown_and_latex_enhancements_are_present_in_both(self) -> None:
        required = {
            "Markdown links and URLs",
            "Markdown list and quote markers",
            "Markdown fenced code punctuation",
            "Markdown table punctuation",
            "LaTeX commands",
            "LaTeX environments and sections",
            "LaTeX references and citations",
            "LaTeX parameters",
            "LaTeX math operators",
        }
        for scheme in self.schemes:
            names = {rule.get("name") for rule in scheme["rules"]}
            self.assertFalse(sorted(required - names), scheme["name"])

    def test_only_supported_sublime_font_styles_are_emitted(self) -> None:
        supported = {"bold", "italic", "glow", "underline", "stippled_underline", "squiggly_underline"}
        for scheme in self.schemes:
            for rule in scheme["rules"]:
                styles = set(rule.get("font_style", "").split())
                self.assertFalse(styles - supported, (scheme["name"], rule))

    def test_legacy_editor_interaction_colors_are_packaged(self) -> None:
        expected = {
            "line_highlight": "#2A2D2E",
            "gutter_foreground_highlight": "#CCCCCC",
            "caret": "#AEAFAD",
            "brackets_options": "underline",
            "brackets_foreground": "#FFFFFF",
            "bracket_contents_options": "underline",
            "bracket_contents_foreground": "#FFFFFF",
            "selection": "#264F78",
            "selection_border": "#264F78",
        }
        self.assertEqual(
            {name: self.vscode["globals"].get(name) for name in expected},
            expected,
        )

    def test_merged_build_report_has_both_schemes(self) -> None:
        report = json.loads((ROOT / "theme-build-report.json").read_text(encoding="utf-8"))
        self.assertEqual(set(report["schemes"]), {"vscode", "monokai"})
        for scheme_id, section in report["schemes"].items():
            self.assertGreater(section["generated_rule_count"], 50, scheme_id)
            self.assertTrue(all(entry.get("source") for entry in section["provenance"]), scheme_id)
        # The VS Code report also records global/override provenance entries,
        # so its provenance count exceeds the rule count; Monokai adds one
        # provenance entry per extra global.
        self.assertGreaterEqual(
            len(report["schemes"]["vscode"]["provenance"]),
            report["schemes"]["vscode"]["generated_rule_count"],
        )
        monokai_provenance = report["schemes"]["monokai"]["provenance"]
        monokai_globals = [entry for entry in monokai_provenance if entry["kind"] == "monokai-global"]
        self.assertEqual(
            len(monokai_provenance),
            report["schemes"]["monokai"]["generated_rule_count"] + len(monokai_globals),
        )


class MonokaiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scheme = json.loads((ROOT / MONOKAI_SCHEME).read_text(encoding="utf-8"))
        cls.rules = cls.scheme["rules"]

    def test_classic_monokai_globals_are_declared_inline(self) -> None:
        self.assertEqual(self.scheme["name"], "Monokai Dark Modern")
        self.assertFalse("extends" in self.scheme)
        # Editor background is overridden via monokai_extras.json globals.
        self.assertEqual(self.scheme["globals"]["background"], "#242422")
        self.assertEqual(self.scheme["globals"]["selection"], "var(grey)")
        self.assertEqual(self.scheme["globals"]["caret"], "color(var(white2) alpha(0.9))")
        self.assertEqual(self.scheme["globals"]["brackets_options"], "underline")

    def test_classic_base_rules_are_present(self) -> None:
        names = {rule.get("name") for rule in self.rules}
        self.assertTrue(
            {"Comment", "String Key", "Function call", "Entity name", "markup links", "markup h1"}.issubset(names)
        )
        scopes = " ".join(rule.get("scope", "") for rule in self.rules)
        self.assertIn("diff.deleted.char", scopes)

    def test_semantic_categories_and_document_enhancements_are_covered(self) -> None:
        selectors = " ".join(rule["scope"] for rule in self.rules)
        required_semantic = {
            "meta.semantic-token.function",
            "meta.semantic-token.method",
            "meta.semantic-token.macro",
            "meta.semantic-token.type",
            "meta.semantic-token.class",
            "meta.semantic-token.parameter",
            "meta.semantic-token.property",
            "meta.semantic-token.enummember",
            "meta.semantic-token.variable.readonly",
            "meta.semantic-token.newoperator",
        }
        self.assertFalse([scope for scope in required_semantic if scope not in selectors])
        names = {rule.get("name") for rule in self.rules}
        self.assertTrue(
            {
                "Markdown links and URLs",
                "LaTeX commands",
                "LSP semantic highlighting activation",
            }.issubset(names)
        )

    def test_markdown_semantic_highlighting_and_no_code_background(self) -> None:
        rules = {rule.get("name"): rule for rule in self.rules}
        self.assertEqual(rules["Markdown headings"]["foreground"], "var(yellow)")
        self.assertEqual(rules["Markdown heading level 1"]["foreground"], "var(red2)")
        self.assertEqual(rules["Markdown heading level 2"]["foreground"], "var(yellow2)")
        self.assertEqual(rules["Markdown bold"]["foreground"], "var(yellow)")
        self.assertEqual(rules["Markdown raw code"]["foreground"], "var(blue)")
        for rule in self.rules:
            scope = rule.get("scope", "")
            if "markup.raw" in str(scope).split():
                self.assertNotIn("background", rule, rule)
        self.assertIn("variable.other.constant", " ".join(rule.get("scope", "") for rule in self.rules))

    def test_interaction_globals_are_extended(self) -> None:
        expected = {
            "gutter_foreground": "#90908A",
            "gutter_foreground_highlight": "#D8D8D2",
            "guide": "#33322C",
            "inactive_selection": "color(var(grey) alpha(0.4))",
            "highlight": "color(var(white3) alpha(0.08))",
        }
        self.assertEqual(
            {name: self.scheme["globals"].get(name) for name in expected},
            expected,
        )

    def test_selection_commands_are_packaged(self) -> None:
        commands = json.loads((ROOT / "Modern Themes.sublime-commands").read_text(encoding="utf-8"))
        command_names = {entry["command"] for entry in commands}
        self.assertIn("modern_themes_select_monokai_color_scheme", command_names)
        self.assertIn("modern_themes_select_vscode_color_scheme", command_names)
        self.assertIn("modern_themes_select_monokai_ui_theme", command_names)

    def test_monokai_ui_theme_is_warm_not_oppressive(self) -> None:
        theme = json.loads((ROOT / MONOKAI_UI_THEME).read_text(encoding="utf-8"))
        text = json.dumps(theme)
        self.assertIn("#558B2F", text)
        self.assertIn("#F92672", text)
        self.assertIn("#1F1E1A", text)
        self.assertNotIn("#181818", text)
        self.assertNotIn("#04395E", text)
        self.assertNotIn("#075C55", text)
        self.assertNotIn("#0078D4", text)
        self.assertIn('"file_tab_style": "square"', text)
        self.assertEqual(theme["variables"]["sidebar_row_selected"], "#558B2F")
        self.assertEqual(theme["variables"]["quick_panel_selected_row_bg"], "#558B2F")
        square_tabset = next(
            rule for rule in theme["rules"]
            if rule.get("class") == "tabset_control" and rule.get("settings", {}).get("file_tab_style") == "square"
        )
        self.assertEqual(
            {key: square_tabset[key] for key in ("tab_overlap", "tab_width", "tab_min_width")},
            {"tab_overlap": 0, "tab_width": 0, "tab_min_width": 0},
        )
        selected_tab = next(
            rule for rule in theme["rules"]
            if rule.get("class") == "tab_control"
            and "selected" in rule.get("attributes", [])
            and "!selected" not in rule.get("attributes", [])
        )
        self.assertEqual(selected_tab["layer2.tint"], "#F92672")


if __name__ == "__main__":
    unittest.main()
