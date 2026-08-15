"""Regression tests for the Modern Themes color-scheme builder."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import build_theme  # noqa: E402
import jsonc  # noqa: E402


class JsoncTests(unittest.TestCase):
    def test_comments_and_trailing_commas_preserve_string_content(self) -> None:
        data = jsonc.loads(
            '''{
                // A line comment
                "url": "https://example.test/a//b", /* block comment */
                "items": [1, 2,],
                "nested": {"value": true,},
            }'''
        )

        self.assertEqual(
            data,
            {
                "url": "https://example.test/a//b",
                "items": [1, 2],
                "nested": {"value": True},
            },
        )

    def test_unterminated_block_comment_is_rejected(self) -> None:
        with self.assertRaisesRegex(jsonc.JsoncError, "Unterminated block comment"):
            jsonc.loads('{ /* unfinished')


class ThemeResolutionTests(unittest.TestCase):
    def _write_theme(self, folder: Path, name: str, contents: dict[str, object]) -> Path:
        path = folder / name
        path.write_text(json.dumps(contents), encoding="utf-8")
        return path

    def test_three_level_inheritance_preserves_rule_order_and_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self._write_theme(
                folder,
                "base.json",
                {
                    "name": "Base",
                    "colors": {"editor.background": "#111111", "editor.foreground": "#AAAAAA"},
                    "tokenColors": [{"name": "base", "scope": "keyword", "settings": {"foreground": "#111111"}}],
                    "semanticTokenColors": {"thing": "#111111"},
                },
            )
            self._write_theme(
                folder,
                "middle.json",
                {
                    "include": "base.json",
                    "colors": {"editor.foreground": "#BBBBBB"},
                    "tokenColors": [{"name": "middle", "scope": "string", "settings": {"foreground": "#222222"}}],
                    "semanticTokenColors": {"thing": "#222222", "other": "#333333"},
                },
            )
            leaf = self._write_theme(
                folder,
                "leaf.json",
                {
                    "name": "Leaf",
                    "include": "middle.json",
                    "colors": {"editor.background": "#444444"},
                    "tokenColors": [{"name": "leaf", "scope": "comment", "settings": {"foreground": "#555555"}}],
                    "semanticTokenColors": {"other": "#666666"},
                },
            )

            theme = build_theme.resolve_theme(leaf)

        self.assertEqual(theme.name, "Leaf")
        self.assertEqual([rule["name"] for rule in theme.token_colors], ["base", "middle", "leaf"])
        self.assertEqual(theme.colors["editor.background"].value, "#444444")
        self.assertEqual(theme.colors["editor.foreground"].value, "#BBBBBB")
        self.assertEqual(theme.semantic_colors["thing"].value, "#222222")
        self.assertEqual(theme.semantic_colors["other"].value, "#666666")
        self.assertEqual([Path(item).name for item in theme.chain], ["base.json", "middle.json", "leaf.json"])

    def test_missing_include_reports_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = self._write_theme(Path(directory), "root.json", {"include": "missing.json"})
            with self.assertRaisesRegex(build_theme.BuildError, "Missing theme include"):
                build_theme.resolve_theme(source)

    def test_include_cycle_reports_full_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = self._write_theme(folder, "one.json", {"include": "two.json"})
            self._write_theme(folder, "two.json", {"include": "one.json"})
            with self.assertRaisesRegex(build_theme.BuildError, r"Theme include cycle detected: one\.json -> two\.json -> one\.json"):
                build_theme.resolve_theme(source)


class ConversionTests(unittest.TestCase):
    def test_scope_aliases_and_font_style_are_converted_without_reordering(self) -> None:
        rules, provenance = build_theme._convert_token_rules(
            [
                {
                    "__source": "source.json",
                    "name": "Function",
                    "scope": ["entity.name.function", "keyword"],
                    "settings": {"foreground": "#DCDCAA", "background": "#111111", "fontStyle": "bold italic"},
                }
            ],
            {"entity.name.function": ["variable.function", "entity.name.function"]},
        )

        self.assertEqual(
            rules,
            [{
                "name": "Function",
                "scope": "entity.name.function, variable.function, keyword",
                "foreground": "#DCDCAA",
                "background": "#111111",
                "font_style": "bold italic",
            }],
        )
        self.assertEqual(provenance[0]["source"], "source.json")

    def test_vscode_strikethrough_uses_supported_sublime_style(self) -> None:
        rules, _ = build_theme._convert_token_rules(
            [{
                "__source": "source.json",
                "scope": "markup.strikethrough",
                "settings": {"fontStyle": "strikethrough"},
            }],
            {},
        )

        self.assertEqual(rules[0]["font_style"], "stippled_underline")

    def test_semantic_token_and_language_selector_conversion(self) -> None:
        theme = build_theme.ResolvedTheme(
            name="Test",
            chain=[],
            colors={},
            token_colors=[
                {"__source": "base.json", "scope": "entity.name.function", "settings": {"foreground": "#DCDCAA"}},
                {"__source": "base.json", "scope": "keyword", "settings": {"foreground": "#C586C0"}},
            ],
            semantic_colors={
                "newOperator": build_theme.TracedValue("#C586C0", "leaf.json"),
                "variable:typescript": build_theme.TracedValue({"foreground": "#9CDCFE", "fontStyle": "italic"}, "leaf.json"),
            },
        )
        rules, provenance = build_theme._convert_semantic_rules(
            theme,
            {"groups": [{"name": "Functions", "tokens": ["function"], "color_from": "entity.name.function"}], "modifier_groups": []},
        )

        self.assertEqual(rules[0]["background"], build_theme.LSP_ACTIVATION_BACKGROUND)
        self.assertEqual(rules[1], {"name": "Functions", "scope": "meta.semantic-token.function", "foreground": "#DCDCAA"})
        self.assertIn(
            {"name": "VS Code semantic token: newOperator", "scope": "meta.semantic-token.newoperator", "foreground": "#C586C0"},
            rules,
        )
        self.assertIn(
            {"name": "VS Code semantic token: variable:typescript", "scope": "source.typescript meta.semantic-token.variable", "foreground": "#9CDCFE", "font_style": "italic"},
            rules,
        )
        self.assertEqual(provenance[-1]["source"], "leaf.json")


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = build_theme.build_all()
        cls.vscode, cls.vscode_report = cls.results["vscode"]
        cls.monokai, cls.monokai_report = cls.results["monokai"]

    def test_vscode_build_has_expected_chain_and_semantic_activation(self) -> None:
        self.assertEqual(
            self.vscode_report["source_chain"],
            ["source/vscode/dark_vs.json", "source/vscode/dark_plus.json", "source/vscode/dark_modern.json"],
        )
        self.assertEqual(self.vscode["globals"]["background"], "#1F1F1F")
        self.assertGreater(self.vscode_report["generated_rule_count"], 50)
        self.assertTrue(any(rule.get("background") == build_theme.LSP_ACTIVATION_BACKGROUND for rule in self.vscode["rules"]))

    def test_legacy_sublime_ui_colors_are_applied(self) -> None:
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
        provenance = {
            entry["name"]: entry
            for entry in self.vscode_report["provenance"]
            if entry["kind"] == "sublime-global-override"
        }
        self.assertEqual(set(provenance), set(expected))
        self.assertTrue(all(entry["mapping"] == "mappings/sublime_ui_overrides.json" for entry in provenance.values()))
        self.assertTrue(all(entry["scheme"] == "vscode" for entry in self.vscode_report["provenance"]))

    def test_every_generated_vscode_syntax_color_has_source_provenance(self) -> None:
        source_colors = self._all_source_colors(ROOT / "source" / "vscode" / "dark_modern.json")
        generated_colors = {
            value
            for rule in self.vscode["rules"]
            for key, value in rule.items()
            if key in {"foreground", "background"}
        }
        override_colors = {
            entry["value"]
            for entry in self.vscode_report["provenance"]
            if entry["kind"] == "sublime-global-override" and entry["value"].startswith("#")
        }
        generated_colors.update(
            value for value in self.vscode["globals"].values() if value.startswith("#")
        )
        self.assertTrue(
            generated_colors - source_colors
            <= override_colors | {build_theme.LSP_ACTIVATION_BACKGROUND}
        )

        source_backed = [
            entry for entry in self.vscode_report["provenance"]
            if entry["kind"] not in {"lsp-activation", "sublime-global-override"}
        ]
        for entry in source_backed:
            for key in ("foreground", "background", "color"):
                if entry.get(key) is not None:
                    self.assertIn(entry[key], source_colors, entry)

    def test_monokai_build_preserves_classic_base_verbatim(self) -> None:
        source = jsonc.load(ROOT / "source" / "Monokai.sublime-color-scheme")
        self.assertEqual(self.monokai["name"], "Monokai Dark Modern")
        self.assertEqual(self.monokai["variables"], source["variables"])
        self.assertEqual(
            {
                name: self.monokai["globals"].get(name)
                for name in source["globals"]
                if name != "background"
            },
            {name: value for name, value in source["globals"].items() if name != "background"},
        )
        # The classic "markup code" rule (markup.raw background) is intentionally
        # replaced by the foreground-only Monokai markdown rules.
        expected_base = [
            rule for rule in source["rules"]
            if "markup.raw" not in str(rule.get("scope", "")).split()
        ]
        base_count = len(expected_base)
        self.assertEqual(self.monokai["rules"][:base_count], expected_base)
        self.assertFalse("extends" in self.monokai)
        self.assertEqual(self.monokai_report["source_chain"], ["source/Monokai.sublime-color-scheme"])
        kinds = {entry["kind"] for entry in self.monokai_report["provenance"]}
        self.assertEqual(
            kinds,
            {"base", "monokai-extra", "monokai-markdown", "monokai-global",
             "enhancement", "semantic-standard", "semantic-modifier", "lsp-activation"},
        )
        self.assertTrue(all(entry["scheme"] == "monokai" for entry in self.monokai_report["provenance"]))

    def _named_rules(self) -> dict[str, dict]:
        return {rule["name"]: rule for rule in self.monokai["rules"] if rule.get("name")}

    def test_monokai_enhancements_use_classic_consistent_colors(self) -> None:
        rules = self._named_rules()
        self.assertEqual(rules["Markdown links and URLs"]["foreground"], "var(blue)")
        self.assertEqual(rules["Markdown list and quote markers"]["foreground"], "var(purple)")
        self.assertEqual(rules["Markdown block quotes"]["foreground"], "var(yellow5)")
        self.assertEqual(rules["Markdown fenced code punctuation"]["foreground"], "var(blue)")
        self.assertEqual(rules["LaTeX environments and sections"]["foreground"], "var(blue)")
        self.assertEqual(rules["LaTeX environments and sections"]["font_style"], "italic")
        self.assertEqual(rules["LaTeX parameters"]["foreground"], "var(orange)")
        self.assertEqual(rules["LaTeX parameters"]["font_style"], "italic")
        self.assertEqual(rules["Regular expressions"]["foreground"], "var(red)")
        self.assertEqual(rules["Markdown strikethrough"]["font_style"], "stippled_underline")

    def test_monokai_semantic_tokens_follow_classic_conventions(self) -> None:
        rules = self._named_rules()
        self.assertEqual(rules["Semantic functions"]["foreground"], "var(yellow2)")
        self.assertEqual(rules["Semantic types"]["foreground"], "var(yellow2)")
        self.assertEqual(rules["Semantic variables"]["foreground"], "var(white3)")
        self.assertEqual(rules["Semantic keywords"]["foreground"], "var(red2)")
        self.assertEqual(rules["Semantic comments"]["foreground"], "var(yellow5)")
        self.assertEqual(rules["Semantic strings"]["foreground"], "var(yellow)")
        self.assertEqual(rules["Semantic numbers"]["foreground"], "var(purple)")
        self.assertEqual(rules["Semantic regular expressions"]["foreground"], "var(red)")
        self.assertEqual(rules["Semantic operators"]["foreground"], "var(white3)")
        self.assertEqual(rules["Semantic readonly values"]["foreground"], "var(purple)")
        activation = next(rule for rule in self.monokai["rules"] if rule.get("name") == "LSP semantic highlighting activation")
        self.assertEqual(activation["background"], build_theme.LSP_ACTIVATION_BACKGROUND)

    def test_monokai_markdown_rules_replace_code_background(self) -> None:
        rules = self._named_rules()
        self.assertEqual(rules["Markdown headings"]["foreground"], "var(yellow)")
        self.assertEqual(rules["Markdown headings"]["font_style"], "bold")
        self.assertEqual(rules["Markdown heading level 1"]["foreground"], "var(red2)")
        self.assertEqual(rules["Markdown heading level 2"]["foreground"], "var(yellow2)")
        self.assertEqual(rules["Markdown heading levels 3-6"]["foreground"], "var(yellow)")
        self.assertEqual(rules["Markdown bold"]["foreground"], "var(yellow)")
        self.assertEqual(rules["Markdown bold"]["font_style"], "bold")
        self.assertEqual(rules["Markdown raw code"]["foreground"], "var(blue)")
        self.assertEqual(rules["Markdown raw punctuation"]["foreground"], "var(blue)")
        self.assertEqual(rules["Markdown highlight"]["background"], "color(var(yellow) alpha(0.3))")
        for rule in self.monokai["rules"]:
            scope = rule.get("scope", "")
            if "markup.raw" in str(scope).split() and "punctuation" not in str(scope):
                self.assertNotIn("background", rule, rule)
                self.assertIn("foreground", rule, rule)

    def test_monokai_globals_extended_from_classic_palette(self) -> None:
        expected = {
            "background": "#242422",
            "gutter_foreground": "#90908A",
            "gutter_foreground_highlight": "#D8D8D2",
            "guide": "#33322C",
            "inactive_selection": "color(var(grey) alpha(0.4))",
            "highlight": "color(var(white3) alpha(0.08))",
        }
        self.assertEqual(
            {name: self.monokai["globals"].get(name) for name in expected},
            expected,
        )
        global_entries = [
            entry for entry in self.monokai_report["provenance"]
            if entry["kind"] == "monokai-global"
        ]
        self.assertEqual({entry["name"] for entry in global_entries}, set(expected))

    def test_monokai_alias_coverage_gap_is_filled(self) -> None:
        rules = self._named_rules()
        self.assertEqual(
            rules["Enum members and readonly values"]["foreground"],
            "var(purple)",
        )

    def test_monokai_emitted_colors_are_all_var_based(self) -> None:
        source = jsonc.load(ROOT / "source" / "Monokai.sublime-color-scheme")
        base_count = len([
            rule for rule in source["rules"]
            if "markup.raw" not in str(rule.get("scope", "")).split()
        ])
        for rule in self.monokai["rules"][base_count:]:
            if rule.get("name") == "LSP semantic highlighting activation":
                continue
            for key in ("foreground", "background"):
                value = rule.get(key)
                if value is not None:
                    self.assertTrue(
                        value.startswith("var(") or value.startswith("color(var("),
                        f"{rule.get('name')}: {key}={value!r}",
                    )

    def test_check_mode_does_not_write_requested_outputs(self) -> None:
        outputs = [
            ROOT / "VS Code Dark Modern Enhanced.sublime-color-scheme",
            ROOT / "Monokai Dark Modern.sublime-color-scheme",
            ROOT / "theme-build-report.json",
        ]
        before = [path.read_bytes() for path in outputs]
        result = subprocess.run(
            [sys.executable, str(TOOLS / "build_theme.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Built VS Code Dark Modern Enhanced", result.stdout)
        self.assertIn("Built Monokai Dark Modern", result.stdout)
        self.assertEqual(before, [path.read_bytes() for path in outputs])

    def _all_source_colors(self, source: Path) -> set[str]:
        theme = build_theme.resolve_theme(source)
        colors = {item.value for item in theme.colors.values()}
        for rule in theme.token_colors:
            settings = rule.get("settings", {})
            if isinstance(settings, dict):
                colors.update(value for key, value in settings.items() if key in {"foreground", "background"})
        for item in theme.semantic_colors.values():
            if isinstance(item.value, str):
                colors.add(item.value)
            elif isinstance(item.value, dict):
                colors.update(value for key, value in item.value.items() if key in {"foreground", "background"})
        return colors


if __name__ == "__main__":
    unittest.main()
