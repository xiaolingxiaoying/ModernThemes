"""Static package checks that do not require a running Sublime Text instance."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

VSCode_SCHEME = "VS Code Dark Modern Me.sublime-color-scheme"
MONOKAI_SCHEME = "Monokai Me.sublime-color-scheme"
VSCode_UI_THEME = "VS Code Dark Modern Me.sublime-theme"
MONOKAI_UI_THEME = "Monokai Me.sublime-theme"
FILE_ICON_THEME = "VS Code Dark Modern Me.sublime-file-icons"
PACKAGE_RESOURCE_PREFIX = "ModernThemes/"


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
            FILE_ICON_THEME,
            "tab_square_highlight_thin.png",
            "Modern Themes.sublime-commands",
            "Main.sublime-menu",
            "modern_themes.py",
            "Modern Themes JSON.sublime-syntax",
            "messages.json",
            "README.md",
            "LICENSE",
            "theme-build-report.json",
            "tools/build_theme.py",
            ".python-version",
            "lsp/popups/vscode-dark-modern.css",
            "lsp/popups/monokai-me.css",
            "lsp/annotations/vscode-dark-modern.css",
            "lsp/annotations/monokai-me.css",
        }
        self.assertFalse([name for name in required if not (ROOT / name).is_file()])
        self.assertFalse((ROOT / "package-metadata.json").exists())

    def test_ui_themes_use_packaged_tab_highlight(self) -> None:
        for theme_name in (VSCode_UI_THEME, MONOKAI_UI_THEME):
            theme = json.loads((ROOT / theme_name).read_text(encoding="utf-8"))
            textures = [rule.get("layer2.texture") for rule in theme["rules"]]
            self.assertIn(f"{PACKAGE_RESOURCE_PREFIX}tab_square_highlight_thin.png", textures, theme_name)
            self.assertFalse([texture for texture in textures if texture and texture.startswith("User/")], theme_name)

    def test_ui_theme_texture_paths_are_package_relative(self) -> None:
        for theme_name in (VSCode_UI_THEME, MONOKAI_UI_THEME):
            theme = json.loads((ROOT / theme_name).read_text(encoding="utf-8"))
            local_textures = [
                value
                for rule in theme["rules"]
                for key, value in rule.items()
                if key.endswith(".texture") and value and not value.startswith("Theme - Default/")
            ]
            self.assertTrue(local_textures, theme_name)
            self.assertFalse(
                [texture for texture in local_textures if not texture.startswith(PACKAGE_RESOURCE_PREFIX)],
                theme_name,
            )

    def test_packaged_sidebar_file_icons_include_all_scale_variants(self) -> None:
        icon_names = {"binary", "css", "default", "image", "markup", "source", "text"}
        scale_suffixes = ("", "@2x", "@3x")
        expected = {
            ROOT / "icons" / f"file_type_{name}{suffix}.png"
            for name in icon_names
            for suffix in scale_suffixes
        }
        missing = [path for path in expected if not path.is_file()]
        self.assertFalse(missing, missing)

    def test_sidebar_file_types_map_to_packaged_icons(self) -> None:
        manifest = json.loads((ROOT / FILE_ICON_THEME).read_text(encoding="utf-8"))
        expected = {
            "py": "file_type_source",
            "md": "file_type_markup",
            "json": "file_type_source",
            "sublime-theme": "file_type_source",
            ".gitignore": "file_type_text",
        }
        self.assertEqual(
            {extension: manifest["icons"].get(extension) for extension in expected},
            expected,
        )
        for icon_name in set(manifest["icons"].values()):
            self.assertTrue((ROOT / "icons" / f"{icon_name}.png").is_file(), icon_name)

    def test_ui_themes_render_packaged_file_icons(self) -> None:
        for theme_name in (VSCode_UI_THEME, MONOKAI_UI_THEME):
            theme = json.loads((ROOT / theme_name).read_text(encoding="utf-8"))
            icon_rules = [rule for rule in theme["rules"] if rule.get("class") == "icon_file_type"]
            self.assertEqual(
                icon_rules,
                [{
                    "class": "icon_file_type",
                    "layer0.tint": "#CCCCCC",
                    "layer0.opacity": 0.5,
                    "content_margin": [9, 8],
                }],
                theme_name,
            )

    def test_ui_theme_commands_activate_the_file_icon_theme(self) -> None:
        plugin = (ROOT / "modern_themes.py").read_text(encoding="utf-8")
        self.assertIn('FILE_ICON_THEME = "VS Code Dark Modern Me"', plugin)
        self.assertIn('settings.set("file_icon_theme", FILE_ICON_THEME)', plugin)
        self.assertEqual(plugin.count('settings.set("file_icon_theme", FILE_ICON_THEME)'), 2)

    def test_configuration_syntax_is_packaged_and_only_migrated_to_builtin_json(self) -> None:
        plugin = (ROOT / "modern_themes.py").read_text(encoding="utf-8")
        syntax = (ROOT / "Modern Themes JSON.sublime-syntax").read_text(encoding="utf-8")
        self.assertIn("ModernThemesLegacyJsonSyntaxListener", plugin)
        self.assertIn('DEFAULT_JSON_SYNTAX = "Packages/JSON/JSON.sublime-syntax"', plugin)
        self.assertIn("view.assign_syntax(DEFAULT_JSON_SYNTAX)", plugin)
        self.assertNotIn("view.assign_syntax(MODERN_JSON_SYNTAX)", plugin)
        self.assertNotIn("file_extensions:", syntax)
        for depth in ("one", "two", "three", "four"):
            self.assertIn(f"meta.configuration.depth-{depth}.key", syntax)
            self.assertIn(f"meta.configuration.depth-{depth}.value", syntax)

    def test_configuration_syntax_regular_expressions_compile(self) -> None:
        syntax_path = ROOT / "Modern Themes JSON.sublime-syntax"
        invalid = []
        for line_number, line in enumerate(syntax_path.read_text(encoding="utf-8").splitlines(), 1):
            match = re.match(r"^\s*-\s+match:\s*'(.*)'\s*$", line)
            if match is None:
                continue
            try:
                re.compile(match.group(1))
            except re.error as error:
                invalid.append(f"{line_number}: {match.group(1)!r}: {error}")
        self.assertFalse(invalid, "\n".join(invalid))

    def test_configuration_syntax_does_not_claim_json_or_jsonc_entry_points(self) -> None:
        syntax = (ROOT / "Modern Themes JSON.sublime-syntax").read_text(encoding="utf-8")
        plugin = (ROOT / "modern_themes.py").read_text(encoding="utf-8")
        self.assertNotIn("file_extensions:", syntax)
        self.assertNotIn(".jsonc", plugin)

    def test_plugin_uses_the_python_38_host(self) -> None:
        self.assertEqual((ROOT / ".python-version").read_text(encoding="utf-8").strip(), "3.8")

    def test_lsp_ui_styles_and_commands_are_packaged(self) -> None:
        vscode_css = (ROOT / "lsp/popups/vscode-dark-modern.css").read_text(encoding="utf-8")
        monokai_css = (ROOT / "lsp/popups/monokai-me.css").read_text(encoding="utf-8")
        vscode_annotations = (ROOT / "lsp/annotations/vscode-dark-modern.css").read_text(encoding="utf-8")
        monokai_annotations = (ROOT / "lsp/annotations/monokai-me.css").read_text(encoding="utf-8")
        self.assertIn("Modern Themes LSP Popup Style: vscode", vscode_css)
        self.assertIn("#0078D4", vscode_css)
        self.assertIn("Modern Themes LSP Popup Style: monokai", monokai_css)
        self.assertIn("#F92672", monokai_css)
        self.assertIn(".lsp_popup", vscode_css)
        self.assertIn(".diagnostics", monokai_css)
        self.assertIn("Modern Themes LSP Annotation Style: vscode", vscode_annotations)
        self.assertIn("Modern Themes LSP Annotation Style: monokai", monokai_annotations)
        for stylesheet in (vscode_annotations, monokai_annotations):
            self.assertIn(".error", stylesheet)
            self.assertIn(".warning", stylesheet)
            self.assertIn(".information", stylesheet)
            self.assertIn(".hint", stylesheet)

        commands = json.loads((ROOT / "Modern Themes.sublime-commands").read_text(encoding="utf-8"))
        command_names = {entry["command"] for entry in commands}
        self.assertTrue({
            "modern_themes_apply_vscode_lsp_popup_style",
            "modern_themes_apply_monokai_lsp_popup_style",
            "modern_themes_restore_lsp_popup_style",
        }.issubset(command_names))

        plugin = (ROOT / "modern_themes.py").read_text(encoding="utf-8")
        self.assertIn('LSP_POPUP_STYLE_MARKER = "Modern Themes LSP Popup Style"', plugin)
        self.assertIn('LSP_ANNOTATION_STYLE_MARKER = "Modern Themes LSP Annotation Style"', plugin)
        self.assertIn('Path(sublime.packages_path()) / "LSP" / filename', plugin)
        self.assertIn('"annotations.css": "lsp/annotations/vscode-dark-modern.css"', plugin)
        self.assertIn('"annotations.css": "lsp/annotations/monokai-me.css"', plugin)
        self.assertNotIn('"User" / "LSP" / "popups.css"', plugin)
        self.assertIn('target.with_name(target.name + ".modern-themes-backup")', plugin)
        self.assertIn("_is_modern_themes_lsp_style", plugin)

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
            "meta.semantic-token.namespace",
            "meta.semantic-token.typeparameter",
            "meta.semantic-token.property.static",
            "meta.semantic-token.variable.deprecated",
            "meta.semantic-token.function.defaultlibrary",
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
        # provenance entry per extra global or variable.
        self.assertGreaterEqual(
            len(report["schemes"]["vscode"]["provenance"]),
            report["schemes"]["vscode"]["generated_rule_count"],
        )
        monokai_provenance = report["schemes"]["monokai"]["provenance"]
        monokai_globals = [entry for entry in monokai_provenance if entry["kind"] == "monokai-global"]
        monokai_variables = [entry for entry in monokai_provenance if entry["kind"] == "monokai-variable"]
        self.assertEqual(
            len(monokai_provenance),
            report["schemes"]["monokai"]["generated_rule_count"]
            + len(monokai_globals)
            + len(monokai_variables),
        )


class MonokaiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scheme = json.loads((ROOT / MONOKAI_SCHEME).read_text(encoding="utf-8"))
        cls.rules = cls.scheme["rules"]

    def test_classic_monokai_globals_are_declared_inline(self) -> None:
        self.assertEqual(self.scheme["name"], "Monokai Me")
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
            "meta.semantic-token.namespace",
            "meta.semantic-token.typeparameter",
            "meta.semantic-token.property.static",
            "meta.semantic-token.variable.deprecated",
            "meta.semantic-token.function.defaultlibrary",
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
        for element_class in ("overlay_control", "quick_panel"):
            panel_rule = next(rule for rule in theme["rules"] if rule.get("class") == element_class)
            self.assertEqual(panel_rule["layer0.border_color"], "#6B675E")
            self.assertEqual(panel_rule["layer0.border_size"], 1)
            self.assertEqual(panel_rule["layer0.tint"], "var(overlay_bg)")
            self.assertNotIn("layer0.texture", panel_rule)
        input_rule = next(
            rule for rule in theme["rules"]
            if rule.get("class") == "text_line_control"
            and rule.get("parents") == [{"class": "overlay_control"}]
        )
        self.assertEqual(input_rule["layer0.texture"], "ModernThemes/monokai_me_input.png")
        self.assertEqual(input_rule["layer0.inner_margin"], 4)
        self.assertEqual(input_rule["layer0.tint"], "#FFFFFF")
        self.assertEqual(input_rule["layer0.border_size"], 0)
        self.assertEqual(input_rule["tint_index"], -1)
        for element_class in ("quick_panel_row", "mini_quick_panel_row"):
            selected_row_rule = next(rule for rule in theme["rules"] if rule.get("class") == element_class)
            self.assertEqual(selected_row_rule["layer0.texture"], "ModernThemes/monokai_me_selected_row.png")
            self.assertEqual(selected_row_rule["layer0.inner_margin"], 4)
            self.assertEqual(selected_row_rule["layer0.tint"], "#FFFFFF")
        for scale in ("", "@2x", "@3x"):
            self.assertTrue((ROOT / f"monokai_me_input{scale}.png").is_file())
            self.assertTrue((ROOT / f"monokai_me_selected_row{scale}.png").is_file())
        quick_panel_container = next(
            rule for rule in theme["rules"]
            if rule.get("class") == "kind_container"
            and rule.get("parents") == [{"class": "quick_panel"}]
        )
        self.assertEqual(quick_panel_container["layer0.tint"], "var(overlay_bg)")
        self.assertEqual(quick_panel_container["layer0.opacity"], 1.0)
        for variable in (
            "tabset_dark_bg",
            "tabset_medium_dark_bg",
            "tabset_medium_bg",
            "tabset_light_bg",
        ):
            self.assertEqual(theme["variables"][variable], "#21201d")
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
