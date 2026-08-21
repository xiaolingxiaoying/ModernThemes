"""Commands for the Modern Themes package (VS Code Dark Modern Me and Monokai Me).

This module intentionally does not listen for buffer edits.  All normal
highlighting is performed by Sublime's color-scheme engine and, when present,
the LSP package's semantic-token support.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any

import sublime
import sublime_plugin


VSCode_SCHEME_FILE = "VS Code Dark Modern Me.sublime-color-scheme"
MONOKAI_SCHEME_FILE = "Monokai Me.sublime-color-scheme"
VSCode_UI_THEME_FILE = "VS Code Dark Modern Me.sublime-theme"
MONOKAI_UI_THEME_FILE = "Monokai Me.sublime-theme"
FILE_ICON_THEME = "VS Code Dark Modern Me"
PACKAGE_PREFIX = "Packages/ModernThemes/"
LSP_SETTINGS_FILE = "LSP.sublime-settings"
REPORT_FILE = "theme-build-report.json"
LSP_POPUP_STYLE_MARKER = "Modern Themes LSP Popup Style"
LSP_POPUP_STYLE_FILES = {
    "vscode": "lsp/popups/vscode-dark-modern.css",
    "monokai": "lsp/popups/monokai-me.css",
}

SCHEME_IDS = {
    VSCode_SCHEME_FILE: "vscode",
    MONOKAI_SCHEME_FILE: "monokai",
}

CONFIGURATION_REGION_PREFIX = "modern-themes.configuration."
CONFIGURATION_DEPTHS = ("one", "two", "three", "four")
JSON_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|true|false|null|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|[{}\[\]:,]')
YAML_MAPPING = re.compile(r"^(?P<indent>[ \t]*)(?P<key>(?:'[^']*'|\"(?:\\.|[^\"\\])*\"|[^:#][^:]*?))\s*:\s*(?P<value>[^#\n]+)?")
TOML_MAPPING = re.compile(r"^(?P<key>[A-Za-z0-9_.-]+|\"(?:\\.|[^\"\\])*\")\s*=\s*(?P<value>.+)$")


def _configuration_depth(depth: int) -> str:
    """Clamp arbitrary nesting to the fourth recursive palette level."""
    return CONFIGURATION_DEPTHS[min(max(depth, 1), len(CONFIGURATION_DEPTHS)) - 1]


def _configuration_regions(view: sublime.View) -> dict[tuple[str, str], list[sublime.Region]]:
    """Return depth-aware key/value regions for JSON, YAML and TOML buffers."""
    filename = (view.file_name() or "").lower()
    text = view.substr(sublime.Region(0, view.size()))
    regions: dict[tuple[str, str], list[sublime.Region]] = {}

    def add(depth: int, kind: str, begin: int, end: int) -> None:
        if begin < end:
            regions.setdefault((_configuration_depth(depth), kind), []).append(sublime.Region(begin, end))

    if filename.endswith((".json", ".sublime-settings", ".sublime-color-scheme", ".sublime-theme")):
        # Sublime's built-in JSON grammar exposes key/value roles but not their
        # nesting. This small token walk supplies the missing structural depth.
        stack: list[dict[str, object]] = [{"kind": "object", "depth": 1, "expect_key": True, "pending_key": None}]
        expecting_value: tuple[int, int] | None = None
        for match in JSON_TOKEN.finditer(text):
            token = match.group(0)
            current = stack[-1] if stack else None
            if token == "{":
                depth = (expecting_value[0] + 1) if expecting_value else (int(current["depth"]) + 1 if current else 1)
                stack.append({"kind": "object", "depth": depth, "expect_key": True, "pending_key": None})
                expecting_value = None
            elif token == "[":
                depth = (expecting_value[0] + 1) if expecting_value else (int(current["depth"]) if current else 1)
                stack.append({"kind": "array", "depth": depth, "expect_key": False, "pending_key": None})
                expecting_value = None
            elif token in ("}", "]"):
                if stack:
                    stack.pop()
                expecting_value = None
            elif token == ",":
                if stack and stack[-1]["kind"] == "object":
                    stack[-1]["expect_key"] = True
                expecting_value = None
            elif token == ":":
                if current and current["kind"] == "object" and current.get("pending_key"):
                    expecting_value = (int(current["depth"]), match.end())
                    current["pending_key"] = None
            elif current and current["kind"] == "object" and current.get("expect_key") and token.startswith('"'):
                add(int(current["depth"]), "key", match.start(), match.end())
                current["pending_key"] = True
                current["expect_key"] = False
            elif expecting_value:
                add(expecting_value[0], "value", match.start(), match.end())
                expecting_value = None
            elif current and current["kind"] == "array" and token not in (",",):
                add(int(current["depth"]), "value", match.start(), match.end())
    elif filename.endswith((".yaml", ".yml")):
        for line in view.lines(sublime.Region(0, view.size())):
            match = YAML_MAPPING.match(view.substr(line))
            if not match:
                continue
            depth = len(match.group("indent").expandtabs(2)) // 2 + 1
            add(depth, "key", line.begin() + match.start("key"), line.begin() + match.end("key"))
            if match.group("value"):
                add(depth, "value", line.begin() + match.start("value"), line.begin() + match.end("value"))
    elif filename.endswith(".toml"):
        depth = 1
        offset = 0
        for line_text in text.splitlines(keepends=True):
            stripped = line_text.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                depth = stripped.strip("[]").count(".") + 1
            else:
                match = TOML_MAPPING.match(line_text)
                if match:
                    add(depth, "key", offset + match.start("key"), offset + match.end("key"))
                    add(depth, "value", offset + match.start("value"), offset + match.end("value"))
            offset += len(line_text)
    return regions


class ModernThemesConfigurationHighlighter(sublime_plugin.EventListener):
    """Add depth semantic scopes for structured configuration formats."""

    def on_activated_async(self, view: sublime.View) -> None:
        self._schedule(view)

    def on_load_async(self, view: sublime.View) -> None:
        self._schedule(view)

    def on_post_save_async(self, view: sublime.View) -> None:
        self._schedule(view)

    def on_modified_async(self, view: sublime.View) -> None:
        self._schedule(view)

    def _schedule(self, view: sublime.View) -> None:
        sublime.set_timeout_async(lambda: self._highlight(view), 180)

    def _highlight(self, view: sublime.View) -> None:
        if view.is_loading() or view.settings().get("color_scheme", "").rsplit("/", 1)[-1] != MONOKAI_SCHEME_FILE:
            return
        for depth in CONFIGURATION_DEPTHS:
            for kind in ("key", "value"):
                view.erase_regions(CONFIGURATION_REGION_PREFIX + depth + "." + kind)
        for (depth, kind), selections in _configuration_regions(view).items():
            view.add_regions(
                CONFIGURATION_REGION_PREFIX + depth + "." + kind,
                selections,
                "meta.configuration.depth-{}.{}".format(depth, kind),
                "",
                sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE,
            )


def _resource(scheme_file: str) -> str:
    """Find the packaged scheme instead of assuming the package directory."""
    resources = sublime.find_resources(scheme_file)
    return resources[0] if resources else PACKAGE_PREFIX + scheme_file


def _selected_point(view: sublime.View) -> int:
    selection = view.sel()
    if selection:
        return selection[0].begin()
    return 0


def _semantic_token_at(view: sublime.View, point: int) -> dict[str, Any] | None:
    """Read LSP's in-memory token list when its optional API is available."""
    try:
        registry = importlib.import_module("LSP.plugin.core.registry")
        listener = registry.windows.listener_for_view(view)
        if listener is None:
            return None
        for session_view in listener.session_views_async():
            for token in session_view.session_buffer.get_semantic_tokens():
                if token.region.contains(point) and point < token.region.end():
                    return {
                        "type": token.type,
                        "modifiers": list(token.modifiers),
                        "server": session_view.session.config.name,
                    }
    except Exception:
        # LSP is optional and its internal inspection API may change between
        # releases. The color scheme itself does not depend on this helper.
        return None
    return None


def _semantic_scope_for(token: dict[str, Any] | None) -> str | None:
    if token is None:
        return None
    token_type = str(token["type"]).lower()
    modifiers = token.get("modifiers") or []
    modifier = ".{}".format(str(modifiers[0]).lower()) if modifiers else ""
    return "meta.semantic-token.{}{}".format(token_type, modifier)


def _active_scheme_id(view: sublime.View) -> str | None:
    """Map the active color scheme resource to its build-report scheme id."""
    resource = view.settings().get("color_scheme") or ""
    basename = resource.rsplit("/", 1)[-1]
    return SCHEME_IDS.get(basename)


def _load_provenance(scheme_id: str | None) -> list[dict[str, Any]]:
    """Load the build report's provenance for the active scheme, if packaged."""
    for resource in sublime.find_resources(REPORT_FILE):
        try:
            value = json.loads(sublime.load_resource(resource))
        except (ValueError, OSError):
            continue
        schemes = value.get("schemes") if isinstance(value, dict) else None
        if not isinstance(schemes, dict):
            continue
        if scheme_id is not None and scheme_id in schemes:
            entries = schemes[scheme_id].get("provenance", [])
        else:
            entries = [
                entry
                for section in schemes.values()
                if isinstance(section, dict)
                for entry in section.get("provenance", [])
                if isinstance(entry, dict)
            ]
        return entries
    return []


def _provenance_for(
    scope_stack: str, preferred_scopes: list[str], scheme_id: str | None
) -> str | None:
    """Return the highest-priority generated rule matching the inspected token."""
    for entry in reversed(_load_provenance(scheme_id)):
        selectors = entry.get("scope")
        if not isinstance(selectors, str):
            continue
        candidates = [item.strip() for item in selectors.split(",")]
        preferred_match = any(
            preferred == candidate or preferred.startswith(candidate + ".")
            for preferred in preferred_scopes
            for candidate in candidates
        )
        syntax_match = any(sublime.score_selector(scope_stack, candidate) > 0 for candidate in candidates)
        if preferred_match or syntax_match:
            name = entry.get("name") or "unnamed rule"
            source = entry.get("source") or "unknown source"
            return "{} — {}".format(name, source)
    return None


def _semantic_highlighting_enabled() -> tuple[bool, bool]:
    """Return (LSP is installed, semantic highlighting is enabled)."""
    lsp_resources = sublime.find_resources(LSP_SETTINGS_FILE)
    if not lsp_resources:
        return False, False
    return True, bool(sublime.load_settings(LSP_SETTINGS_FILE).get("semantic_highlighting", False))


def _lsp_popup_paths() -> tuple[Path, Path]:
    """Return LSP's loaded popup stylesheet and this package's backup path."""
    # LSP loads this exact resource through ``sublime.load_resource``.  A file
    # below Packages/User/LSP is not part of that resource path and is ignored.
    target = Path(sublime.packages_path()) / "LSP" / "popups.css"
    return target, target.with_name(target.name + ".modern-themes-backup")


def _is_modern_themes_popup_style(content: str) -> bool:
    return LSP_POPUP_STYLE_MARKER in content


def _load_lsp_popup_style(style_id: str) -> str:
    """Load a bundled LSP popup stylesheet by its stable style identifier."""
    return sublime.load_resource(PACKAGE_PREFIX + LSP_POPUP_STYLE_FILES[style_id])


def _apply_lsp_popup_style(style_id: str, display_name: str) -> None:
    """Install one managed LSP popup override without discarding user CSS."""
    if not sublime.find_resources(LSP_SETTINGS_FILE):
        sublime.message_dialog(
            "Sublime LSP was not detected. Install the LSP package before applying a "
            "Modern Themes LSP popup style."
        )
        return

    target, backup = _lsp_popup_paths()
    try:
        if target.is_file():
            existing = target.read_text(encoding="utf-8")
            if not _is_modern_themes_popup_style(existing):
                if backup.exists():
                    sublime.error_message(
                        "Modern Themes did not replace Packages/LSP/popups.css because "
                        "a previous Modern Themes backup already exists. Restore it or handle "
                        "the files manually first."
                    )
                    return
                backup.write_text(existing, encoding="utf-8")
        elif backup.exists():
            sublime.error_message(
                "Modern Themes found a previous LSP popup backup in Packages/LSP but no managed popup style. "
                "Restore or handle the files manually before applying a new style."
            )
            return

        stylesheet = _load_lsp_popup_style(style_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(stylesheet, encoding="utf-8")
    except OSError as error:
        sublime.error_message("Modern Themes could not install the LSP popup style: {}".format(error))
        return

    sublime.message_dialog(
        "{} LSP popup style installed. Restart Sublime Text to apply the LSP CSS override.".format(display_name)
    )


def _restore_lsp_popup_style() -> None:
    """Restore the user stylesheet saved when Modern Themes first installed an override."""
    target, backup = _lsp_popup_paths()
    try:
        if not target.is_file() or not _is_modern_themes_popup_style(target.read_text(encoding="utf-8")):
            sublime.message_dialog(
                "No Modern Themes-managed LSP popup style is installed; no files were changed."
            )
            return
        if backup.is_file():
            target.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
            backup.unlink()
        else:
            target.unlink()
    except OSError as error:
        sublime.error_message("Modern Themes could not restore the LSP popup style: {}".format(error))
        return

    sublime.message_dialog("Previous LSP popup style restored. Restart Sublime Text to apply the change.")


class ModernThemesSelectVscodeColorSchemeCommand(sublime_plugin.ApplicationCommand):
    """Select the VS Code Dark Modern Me color scheme globally."""

    def run(self) -> None:
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set("color_scheme", _resource(VSCode_SCHEME_FILE))
        sublime.save_settings("Preferences.sublime-settings")
        sublime.status_message("VS Code Dark Modern Me color scheme selected")


class ModernThemesSelectMonokaiColorSchemeCommand(sublime_plugin.ApplicationCommand):
    """Select the Monokai Me color scheme globally."""

    def run(self) -> None:
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set("color_scheme", _resource(MONOKAI_SCHEME_FILE))
        sublime.save_settings("Preferences.sublime-settings")
        sublime.status_message("Monokai Me color scheme selected")


class ModernThemesSelectVscodeUiThemeCommand(sublime_plugin.ApplicationCommand):
    """Select the VS Code Dark Modern Me UI theme, square file tabs and sidebar file icons."""

    def run(self) -> None:
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set("theme", VSCode_UI_THEME_FILE)
        settings.set("file_icon_theme", FILE_ICON_THEME)
        settings.set("file_tab_style", "square")
        sublime.save_settings("Preferences.sublime-settings")
        sublime.status_message("VS Code Dark Modern Me UI theme, square tabs and file icons selected")


class ModernThemesSelectMonokaiUiThemeCommand(sublime_plugin.ApplicationCommand):
    """Select the Monokai Me UI theme, square file tabs and sidebar file icons."""

    def run(self) -> None:
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set("theme", MONOKAI_UI_THEME_FILE)
        settings.set("file_icon_theme", FILE_ICON_THEME)
        settings.set("file_tab_style", "square")
        sublime.save_settings("Preferences.sublime-settings")
        sublime.status_message("Monokai Me UI theme, square tabs and file icons selected")


class ModernThemesInspectHighlightCommand(sublime_plugin.WindowCommand):
    """Show scopes and resolved foreground information at the caret."""

    def run(self) -> None:
        view = self.window.active_view()
        if view is None:
            sublime.status_message("No active view to inspect")
            return

        scheme_id = _active_scheme_id(view)
        point = _selected_point(view)
        word_region = view.word(point)
        text = view.substr(word_region) or view.substr(sublime.Region(point, min(point + 1, view.size())))
        scope_name = view.scope_name(point).strip()
        scopes = scope_name.split()
        semantic_token = _semantic_token_at(view, point)
        semantic_scope = _semantic_scope_for(semantic_token)
        syntax_style = view.style_for_scope(scope_name)
        semantic_style = view.style_for_scope(semantic_scope) if semantic_scope else None
        lookup_scopes = ([semantic_scope] if semantic_scope else []) + list(reversed(scopes))
        source_note = _provenance_for(scope_name, lookup_scopes, scheme_id)

        lines = [
            "Modern Themes — Highlight Inspector",
            "",
            "Text: {}".format(repr(text)),
            "Point: {}".format(point),
            "",
            "Syntax scopes:",
            "  {}".format(scope_name or "(none)"),
            "",
            "Semantic token: {}".format(
                "{} [{}] via {}".format(
                    semantic_token["type"],
                    ", ".join(semantic_token["modifiers"]) or "no modifiers",
                    semantic_token["server"],
                ) if semantic_token else "(none)"
            ),
            "Syntax foreground: {}".format(syntax_style.get("foreground", "(default)")),
        ]
        if semantic_style:
            lines.append("Semantic foreground: {}".format(semantic_style.get("foreground", "(default)")))
        if syntax_style.get("background"):
            lines.append("Syntax background: {}".format(syntax_style["background"]))
        if source_note:
            lines.extend(("", "Generated rule source: {}".format(source_note)))
        else:
            lines.extend(("", "Generated rule source: unavailable (build report not packaged or no exact match)"))
        sublime.message_dialog("\n".join(lines))


class ModernThemesCheckSemanticHighlightingCommand(sublime_plugin.WindowCommand):
    """Report the optional LSP semantic-highlighting state without changing it."""

    def run(self) -> None:
        installed, enabled = _semantic_highlighting_enabled()
        view = self.window.active_view()
        active = False
        if view is not None:
            active = _semantic_token_at(view, _selected_point(view)) is not None

        if not installed:
            message = (
                "Sublime LSP was not detected. Base syntax highlighting is active.\n\n"
                "Install the LSP package and set \"semantic_highlighting\": true "
                "in LSP.sublime-settings to enable semantic tokens."
            )
        elif active:
            message = "Sublime LSP semantic highlighting is enabled and active in the current view."
        elif not enabled:
            message = (
                "Sublime LSP is installed, but semantic highlighting is disabled.\n\n"
                "Add \"semantic_highlighting\": true to LSP.sublime-settings. "
                "This package does not change your LSP settings automatically."
            )
        else:
            message = (
                "Sublime LSP semantic highlighting is enabled. No semantic token is currently "
                "visible at the caret; the current language server may not support it, may still "
                "be starting, or the caret may be on unclassified text."
            )
        sublime.message_dialog(message)


class ModernThemesApplyVscodeLspPopupStyleCommand(sublime_plugin.ApplicationCommand):
    """Install the VS Code Dark Modern Me LSP minihtml popup override."""

    def run(self) -> None:
        _apply_lsp_popup_style("vscode", "VS Code Dark Modern Me")


class ModernThemesApplyMonokaiLspPopupStyleCommand(sublime_plugin.ApplicationCommand):
    """Install the Monokai Me LSP minihtml popup override."""

    def run(self) -> None:
        _apply_lsp_popup_style("monokai", "Monokai Me")


class ModernThemesRestoreLspPopupStyleCommand(sublime_plugin.ApplicationCommand):
    """Restore the LSP popup stylesheet that predated Modern Themes."""

    def run(self) -> None:
        _restore_lsp_popup_style()
