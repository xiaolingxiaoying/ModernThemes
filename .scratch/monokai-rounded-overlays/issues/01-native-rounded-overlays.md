# Native Monokai Me rounded overlays

Type: task
Status: resolved
Blocked by: none

## Goal

Give Monokai Me's native elevated overlays a natural visual hierarchy: rounded outer containers, nested rounded interactive surfaces, warm boundaries, and restrained elevation. This delivers the native Sublime UI portion of the approved rounded-overlay specification independently of LSP styling.

## Scope

- Replace or revise the package-local, scalable Monokai Me assets for the overlay container, overlay input, and quick-list selected rows. Supply standard, 2x, and 3x variants for every revised custom asset.
- Update the Monokai Me UI theme so the themeable command panel, quick list, and dialog overlay use the 8px elevated-overlay treatment: a 1px warm-gray outline and a very subtle dark shadow.
- Update normal and mini quick-list selected rows and overlay inputs to use the 6px nested-interactive-surface treatment, with visible 6px horizontal breathing room around the interactive surface.
- Preserve the warm, non-oppressive Monokai Me visual language, package-relative resource paths, and the square treatment of tabs, sidebar, status bar, and bottom-docked panels.
- Extend the existing package-level contract coverage for the externally observable asset inventory and Monokai Me UI-theme connections.

## Acceptance Criteria

- [ ] The packaged Monokai Me theme has standard, 2x, and 3x assets for every revised overlay, input, and selected-row surface.
- [ ] Command panels, quick lists, and themeable dialogs render as 8px rounded elevated overlays with a thin warm-gray boundary and restrained dark shadow.
- [ ] Overlay inputs, normal quick-list selections, and mini quick-list selections render as 6px nested interactive surfaces with 6px horizontal separation from their container edges.
- [ ] The selected-row treatment is not visually edge-to-edge within the quick-panel container.
- [ ] Tabs, sidebar, status bar, and bottom-docked panels retain their existing square geometry.
- [ ] All revised texture references are package-relative and existing package-contract checks pass along with new or updated behavior-focused assertions.

## Verification

Run the package-contract test suite. Inspect the Monokai Me theme resources at all supported scales and, where a local Sublime Text runtime is available, visually confirm command panel, quick list, and themeable dialog behavior.

## Out of Scope

- LSP popup or diagnostics annotation styling.
- Any changes to the Monokai color scheme, shared mappings, unified build pipeline, or VS Code Dark Modern Me theme.

## Answer

Implemented the native Monokai Me rounded-overlay treatment. The overlay, input, and selected-row textures now ship at 1x, 2x, and 3x; the theme connects them through package-relative paths with 8px outer and 6px nested corner treatments. Quick-panel and overlay content reserve 6px horizontal breathing room, while package-contract coverage verifies the asset inventory and theme connections.
