---
name: apple-ui-skills
description: >
  Universal cross-platform UI design, implementation, motion engineering, and
  visual QA skill for building Apple-quality interfaces in any programming
  language or framework. Includes autonomous reference synthesis, adaptive
  context routing, evidence-backed Apple/system reconstruction, stack selection,
  Motion IR compilation, and implementation validation.
---

# Apple UI Skills — v3.1.1

Goal: **build the product, not merely describe how it should look.**

The user only needs to ask to use this skill. Do not require screenshots, Apple
reference links, an “exhaustive” mode, or knowledge of the skill's internals.

## 1. Autonomous execution contract

When the user asks to create, recreate, redesign, implement, or improve a page/app:

- inspect the existing project if one exists
- preserve working product behavior unless change is requested
- choose an appropriate technical stack if greenfield
- synthesize a design reference when the user provides none
- implement the UI and motion directly
- run/build/preview when execution tools are available
- inspect the rendered result when visual/browser tools are available
- fix the largest fidelity problems
- validate interaction, accessibility, responsiveness, and performance

Do not stop at recommendations, a style guide, sample CSS, or pseudocode when the
agent has the ability to modify/build the product.

## 2. Adaptive context routing

**Do not recursively read this skill directory.**

Start small, then expand automatically when needed.

Typical starting set:
- this `SKILL.md`
- one relevant pack
- one target adapter
- a few reconstruction records only when useful

These are starting points, not hard limits. The agent **does not** need user permission to expand when
confidence, fidelity, source conflicts, platform translation, or validation require it.

Stop when additional skill context is unlikely to materially improve the result.

## 3. Route the task

### Generic design/build
Load:
- `packs/build.md`
- `packs/core.md` when motion/interaction matters
- one adapter
- `packs/visual.md` when visual hierarchy/material matters

### Named Apple/system reconstruction
Load:
- `packs/reconstruction.md`
- query matching records with `scripts/query_records.py`
- one adapter
- add `packs/core.md` / `packs/visual.md` as required

### Motion/code translation
Load:
- `compiler/README.md`
- one adapter
- relevant reconstruction record when matching a named reference

## 4. No-reference design behavior

If the user provides no screenshot/site/app reference, **do not block and do not ask
for one unless their product requirements themselves are missing**.

Instead:
1. infer product type, primary task, information hierarchy, and input method
2. choose a coherent current Apple-quality design profile rather than mixing eras
3. use system/native conventions of the target platform
4. synthesize spacing, typography, components, material hierarchy, and motion map
5. implement and visually validate

If web research is available and a current Apple visual reference would materially
improve accuracy, consult current Apple primary design guidance autonomously.

## 5. Technology-stack policy

Do not equate “modern” with “maximum dependencies.”

### Existing project
Prefer the existing stack unless it materially prevents fidelity, accessibility,
performance, or maintainability. Do not rewrite a working project just to use a
preferred framework.

### Greenfield
Choose using:
- target OS/device
- interaction complexity
- performance budget
- accessibility
- team/runtime constraints
- packaging/deployment needs
- native integration requirements

For web, do **not** default to a giant hand-written stylesheet. Prefer a modern
component architecture, typed logic when appropriate, design tokens, and suitable
motion primitives. CSS remains a browser-native rendering/style layer, not the
entire engineering strategy.

Load stack rules from `packs/build.md`.

## 6. Motion rules

Prefer:
`input → immediate response → direct manipulation → preserved velocity →
continuous geometry → physical settle → interruption → accessible fallback`

- active drag follows input directly
- release inherits velocity
- retarget from current presentation state
- geometry usually uses spring/physics
- opacity/color may use short timed easing
- scrolling uses decay + boundary spring
- reduced motion removes large depth/zoom/parallax

## 7. Evidence rules

Never invent “exact Apple values.” Keep separate:
- `APPLE-PRIMARY`
- `PLATFORM-PRIMARY`
- `THIRD-PARTY-REVERSE-ENGINEERED`
- `OPEN-SOURCE-REPLICA`
- `ACADEMIC`
- `SKILL-DERIVED`

Runtime-exposed current system values outrank historical replicas.

## 8. Completion gate

A UI implementation is not complete merely because it compiles.

Before declaring completion, apply `packs/build.md` quality loop:
- render/inspect if tools permit
- test responsive states
- test hover/pressed/focus/keyboard/touch as applicable
- verify reduced motion
- check motion interruption/velocity
- check visual hierarchy and spacing
- check performance-sensitive effects
- fix material defects, not only code errors

If visual inspection tools are unavailable, use the strongest available structural,
interaction, computed-style, test, and runtime validation instead and state the
remaining limitation only if it materially affects confidence.
