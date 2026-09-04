# Visual Design Pack

Load only when layout, typography, materials, component appearance, or Apple-like visual hierarchy matters. Recreate design grammar, not Apple branding.

## Order
1. information structure
2. layout/spacing
3. typography
4. component geometry
5. semantic color
6. materials/depth
7. motion polish

## Spacing
Practical SKILL-DERIVED rhythm: `4,8,12,16,20,24,32,40,48,64`. Tighter inside groups, larger between groups. Align edges first. Desktop can be denser; touch targets remain generous.

## Radius
Use a small family: compact 6, control 10, card 14, large surface 20, floating 28. Nested corners should relate; avoid making everything a pill.

## Typography
Prefer target-platform/system fonts unless brand requires otherwise. Maintain title/heading/body/secondary/caption hierarchy, scalable text, adequate contrast, no fixed-height clipping.

## Semantic color
Use roles: background, elevatedBackground, primaryText, secondaryText, tertiaryText, separator, accent, destructive, success, warning, focusRing, selection, materialTint. Resolve for light/dark/high-contrast.

## Materials
A material must separate chrome/content, preserve context, indicate floating structure, or focus attention. Portable recipe: translucent semantic tint + bounded backdrop blur + subtle edge highlight/separator + small local shadow + opaque fallback.

Drop expensive blur before sacrificing interaction smoothness.

## Controls
Every interactive control needs rest, hover where relevant, pressed, focus, disabled, selected/on as needed. Pressed feedback begins immediately. Touch controls may use subtle 0.97–0.99 press scale; desktop generally needs less scale and stronger hover/focus.

## Platform fit
Apple-quality does not mean iOS everywhere. Desktop keeps keyboard/context menus/windowing; Android keeps back/system behavior; Web keeps semantic HTML/focus/browser behavior; Apple platforms prefer native controls/materials when suitable.

## Liquid Glass era
Treat third-party numeric Liquid Glass records as approximations, not Apple's proprietary shader specification. Preserve hierarchy and geometry/morph first, approximate material second, degrade blur/refraction if needed.
