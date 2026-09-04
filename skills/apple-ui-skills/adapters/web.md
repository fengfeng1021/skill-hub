# Web Adapter

Use for browser UI regardless of framework.

## Architecture

Preserve the project's current framework. For greenfield application UI, prefer a
modern component architecture and TypeScript when complexity justifies it.

Do not treat raw CSS files as the complete solution. CSS remains the native style
layer; component/state/motion architecture should live at the appropriate level.

## Motion primitive selection

Use the simplest primitive that preserves the required behavior:

- direct gesture → Pointer Events + direct transform/motion value
- simple opacity/color → CSS transition or WAAPI
- page/view continuity → View Transitions API where appropriate
- complex layout/shared element → mature layout-motion system or explicit FLIP/shared geometry
- velocity-carrying spring → verified spring library or custom canonical integrator

For React projects, Motion-style layout/shared-element/spring primitives are often
more appropriate than a large hand-authored animation stylesheet.

## Direct interaction

- capture the pointer during drag
- update the visual state directly
- estimate velocity from timestamped samples
- do not run an easing transition while the pointer owns the object
- retain current value/velocity when retargeting

## Rendering

Prefer:
- transform
- opacity
- bounded clip/mask
- semantic CSS variables/tokens

Be cautious with:
- large backdrop-filter surfaces
- animated filter blur
- large soft shadows
- reflow/layout on every pointer event
- framework rerender loops for high-frequency motion values

## Accessibility

- semantic HTML
- visible focus
- keyboard activation/navigation
- `prefers-reduced-motion`
- sufficient contrast after material compositing

## Browser support

When using newer native APIs such as View Transitions:
- use progressive enhancement
- provide a coherent fallback
- do not make core navigation depend on animation support
