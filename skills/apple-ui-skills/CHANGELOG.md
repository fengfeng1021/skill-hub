# Changelog

## 3.1.1 — Apple UI Skills Rename

- Renamed the skill to **Apple UI Skills**.
- Internal skill ID changed to `apple-ui-skills`.
- Package directory and ZIP naming now use `apple-ui-skills`.
- No design, reconstruction, compiler, build, QA, or adaptive-loading capability was removed.

## 3.1.0 — Autonomous Build & Visual QA

### Added
- `packs/build.md` with build-mode contract, stack selection, reference synthesis, and QA loop.
- No-reference design synthesis: users do not need screenshots/sites/apps.
- Direct implementation requirement when the user asks to build/recreate/redesign.
- Render/preview/interaction QA when tools exist.
- Fallback structural/runtime QA when visual tools do not exist.
- 20-point Apple-quality acceptance gate, target >= 17.
- Modern web stack policy: raw monolithic CSS is not the default architecture.
- Modern web motion primitive routing: direct input, View Transitions, WAAPI, layout-motion libraries, canonical spring.

### Changed
- Web adapter now treats CSS as a browser-native styling layer rather than the full engineering strategy.
- Existing project stack is preserved by default; greenfield stack is chosen from constraints, not fashion.
- Completion now requires product-level visual/interaction validation when capabilities permit.

## 3.0.1 — Adaptive Context Routing
- User does not need to request deep/exhaustive mode.
- Agent expands skill context automatically when needed.

## 3.0.0 — Universal Motion Compiler + Context Optimization

## 2.0.0 — Apple Reconstruction Database

## 1.5.0 — Motion Intelligence

## 1.0.0 — Foundation
