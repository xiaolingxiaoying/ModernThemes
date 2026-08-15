"""Commands for the Modern Themes package (VS Code Dark Modern Enhanced and Monokai Dark Modern).

This module intentionally does not listen for buffer edits.  All normal
highlighting is performed by Sublime's color-scheme engine and, when present,
the LSP package's semantic-token support.
"""

from __future__ import annotations

import importlib
import json
from typing import Any

import sublime
import sublime_plugin


VSCode_SCHEME_FILE = "VS Code Dark Modern Enhanced.sublime-color-scheme"
MONOKAI_SCHEME_FILE = "Monokai Dark Modern.sublime-color-scheme"
VSCode_UI_THEME_FILE = "VS Code Dark Modern.sublime-theme"
MONOKAI_UI_THEME_FILE = "Monokai Dark Modern.sublime-theme"
PACKAGE_PREFIX = "Packages/ModernThemes/"
LSP_SETTINGS_FILE = "LSP.sublime-settings"
REPORT_FILE = "theme-build-report.json"

SCHEME_IDS = {
    VSCode_SCHEME_FILE: "vscode",
    MONOKAI_SCHEME_FILE: "monokai",
}


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


class ModernThemesSelectVscodeColorSchemeCommand(sublime_plugin.ApplicationCommand):
    """Select the VS Code Dark Modern Enhanced color scheme globally."""

    def run(self) -> None:
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set("color_scheme", _resource(VSCode_SCHEME_FILE))
        sublime.save_settings("Preferences.sublime-settings")
        sublime.status_message("VS Code Dark Modern Enhanced color scheme selected")


class ModernThemesSelectMonokaiColorSchemeCommand(sublime_plugin.ApplicationCommand):
    """Select the Monokai Dark Modern color scheme globally."""

    def run(self) -> None:
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set("color_scheme", _resource(MONOKAI_SCHEME_FILE))
        sublime.save_settings("Preferences.sublime-settings")
        sublime.status_message("Monokai Dark Modern color scheme selected")


class ModernThemesSelectVscodeUiThemeCommand(sublime_plugin.ApplicationCommand):
    """Select the VS Code Dark Modern UI theme and square file tabs globally."""

    def run(self) -> None:
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set("theme", VSCode_UI_THEME_FILE)
        settings.set("file_tab_style", "square")
        sublime.save_settings("Preferences.sublime-settings")
        sublime.status_message("VS Code Dark Modern UI theme and square tabs selected")


class ModernThemesSelectMonokaiUiThemeCommand(sublime_plugin.ApplicationCommand):
    """Select the Monokai Dark Modern UI theme and square file tabs globally."""

    def run(self) -> None:
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set("theme", MONOKAI_UI_THEME_FILE)
        settings.set("file_tab_style", "square")
        sublime.save_settings("Preferences.sublime-settings")
        sublime.status_message("Monokai Dark Modern UI theme and square tabs selected")


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
