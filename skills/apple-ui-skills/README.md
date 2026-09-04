# Apple UI Skills v3.1.1

This release adds **Autonomous Build & Visual QA**.

The user does not need to provide screenshots, websites, or app references. The agent synthesizes a coherent current Apple-quality design brief from the product requirements and target platform, then implements it.

## New production behavior

When asked to make/recreate/redesign a UI, the agent should:

1. inspect the existing project
2. preserve the existing stack when sensible
3. choose a fit-for-purpose stack only for greenfield work
4. synthesize design tokens, hierarchy, components, and motion
5. implement the actual product
6. build/run/preview when tools permit
7. visually inspect and interact with the result
8. iterate on the largest defects
9. pass a quality gate before calling it Apple-quality

## Web technology policy

The skill no longer frames “CSS implementation” as the architecture. CSS is still a browser-native style/rendering layer, but greenfield application UI should normally use a modern component/state architecture, TypeScript where justified, semantic design tokens, and appropriate native or library motion primitives.

For sophisticated web motion, the agent may prefer native View Transitions/WAAPI or a mature layout/spring library over a large hand-authored animation stylesheet.

## Context behavior

The adaptive progressive-disclosure model from v3.0.1 remains unchanged: start with minimal relevant context, expand automatically when needed, and never recursively load the whole skill.
