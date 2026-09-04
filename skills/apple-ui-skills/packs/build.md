# Autonomous Build, Stack Selection & Visual QA Pack

Load this when the user asks the agent to **make**, **recreate**, **redesign**, or
**implement** a page/application.

## A. Definition of done

The deliverable is a working implementation, not design advice.

When tools permit, the agent should:
1. inspect repository/project structure
2. identify the target runtime and existing stack
3. define design/motion tokens
4. implement components and states
5. run/build the product
6. open/render the result
7. interact with it
8. identify the largest visual/behavioral mismatches
9. fix them
10. repeat until the quality gate passes

Do not ask the user to manage this loop.

## B. Reference synthesis when the user provides nothing

No screenshot is required.

Build an internal reference brief from:
- product category
- user task
- target platform
- information density
- input method
- current Apple-quality visual grammar
- native host-platform conventions
- reconstruction records only when a named Apple behavior is useful

### Default aesthetic direction

For a contemporary neutral product:
- content-first hierarchy
- restrained chrome
- system/native typography or high-quality equivalent
- semantic spacing/radius tokens
- subtle translucency only where it explains layering
- low-noise color palette with one accent role
- high-quality hover/press/focus states
- spring-driven geometry and short timed secondary effects

Do not create a parody “Apple UI” made from excessive blur, white cards, giant
corner radii, and bouncing everything.

## C. Technology stack decision

### Rule 1 — existing product wins

If a project already exists, preserve its framework and architecture unless there
is a concrete blocker. Upgrade locally rather than rewrite globally.

Examples:
- existing React → keep React
- existing Vue → keep Vue
- existing Svelte → keep Svelte
- existing Flutter → keep Flutter
- existing Qt → keep Qt

### Rule 2 — greenfield web

Prefer **TypeScript** for application logic when complexity justifies it.

Choose a component framework based on the product rather than fashion:
- React ecosystem: strong choice for large application UI and advanced motion tooling
- Svelte/Vue/Solid-class frameworks: strong choices when they fit project constraints
- framework-light/native web: suitable for small products with modest state

Motion hierarchy:
1. native direct input + compositor transforms
2. native View Transitions where appropriate
3. WAAPI for controlled timelines
4. a mature motion library for spring/layout/shared-element/gesture complexity
5. custom canonical physics when exact cross-platform trajectory matters

For React-class projects, a mature motion layer such as Motion can be preferable to
hand-building complex shared-layout and spring systems.

### CSS policy

CSS is still a native browser styling/rendering mechanism. The skill should avoid
**raw monolithic CSS as the architecture**, not pretend CSS no longer exists.

Prefer:
- semantic components
- TypeScript/typed state where useful
- design tokens / CSS custom properties
- scoped styles, modules, utility systems, or component styling already used by the project
- compositor-friendly transform/opacity animation
- native browser APIs or motion libraries for behavior

Avoid:
- one giant global stylesheet
- hundreds of magic numbers
- animation logic encoded only in class toggles when velocity/interruption is required
- JavaScript layout thrashing merely to avoid CSS

### Rule 3 — native platforms

Apple platforms:
- Swift + SwiftUI first for greenfield native UI
- bridge UIKit/AppKit/Core Animation when their capabilities are needed

Android:
- Kotlin + Jetpack Compose for greenfield native UI when appropriate

Windows:
- use the project's native stack; WinUI/.NET/Composition when native Windows is the goal

Linux/custom desktop:
- Qt/QML is strong for custom fluid cross-platform desktop UI
- GTK or existing toolkit should be preserved when already used

Cross-platform mobile:
- Flutter or React Native according to product/team/native integration constraints

Cross-platform desktop:
- Tauri/web frontend can be appropriate for lightweight cross-platform desktop
- Qt is appropriate when native/custom rendering and deep desktop behavior matter
- do not choose Electron/Tauri/Qt solely because it is mentioned in this skill

### Rule 4 — stack selection must not damage the product

Prefer the simplest stack that can meet:
- fidelity
- accessibility
- runtime performance
- packaging constraints
- maintainability
- native integration

## D. Design-token pass before implementation

Create a small semantic token system before scattering values.

At minimum:
- spacing scale
- radius scale
- typography roles
- color roles
- material/elevation roles
- motion presets
- focus/selection states

Do not create hundreds of tokens for a single small page.

## E. Component-state completeness

Every actionable component needs relevant states:
- rest
- hover (pointer platforms)
- pressed
- focus-visible
- disabled
- selected/on/off when applicable
- loading/error/success when applicable

Motion should reinforce state; it must not be the only state cue.

## F. Visual QA loop

### If browser/preview/screenshot tools exist

Render and inspect at minimum:
- compact/mobile width when applicable
- primary desktop width
- one wider/narrower stress case

Inspect:
- first-glance hierarchy
- alignment and rhythm
- text wrapping/truncation
- component density
- corner consistency
- background/material contrast
- shadows/highlights
- hover/pressed/focus
- modal/popover anchoring
- scroll behavior
- clipping/overflow

Then interact:
- click/tap
- keyboard/focus
- drag/swipe if present
- open/close overlays
- resize
- repeat/reverse transitions

Fix the largest mismatch first, rerender, and recheck.

### If visual tools do not exist

Use:
- build/typecheck/lint/tests
- DOM/semantic inspection
- computed layout/style if available
- accessibility tree
- unit/integration interaction tests
- runtime performance instrumentation if available

Do not falsely claim visual pixel-level validation without a rendered view.

## G. Motion QA

Fail when:
- active drag trails the pointer because of tweening
- interrupted animation restarts from old state
- release velocity is lost
- every property shares the same arbitrary duration
- shared geometry teleports
- backdrop/material effects lag or drop frames
- reduced-motion mode still contains large zoom/parallax

## H. Performance QA

Web/desktop UI should favor:
- compositor transforms
- opacity
- bounded blur/material regions
- direct motion values instead of full-tree rerenders per pointer event
- lazy/offscreen animation suspension

Do not sacrifice input response to visual effects.

## I. Acceptance scoring

Score 0–2 each:
- hierarchy
- spacing/alignment
- typography
- component states
- responsive behavior
- direct manipulation
- velocity/interruption
- material/depth restraint
- accessibility
- frame stability

Target ≥ 17/20 before describing the result as Apple-quality.
If below target and tools allow iteration, keep improving automatically.
