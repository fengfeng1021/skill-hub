# Apple Adapter
Prefer native behavior when the OS already provides the named component. Keyboard: read animation curve/duration from notifications. Navigation: coordinate via transition coordinator. Native sheet/navigation beats manual reconstruction when exact system behavior is desired.

SwiftUI: use `.spring(duration:bounce:)` for perceptual springs and appropriate interpolating physical spring representation for explicit m/k/c. Modern SwiftUI spring animations preserve velocity across overlapping springs. Keep gesture updates direct rather than implicitly animating every drag sample.

UIKit/Core Animation: use property animators/spring timing when interruption matters; exact cubic records can use native timing curves. macOS keeps windowing, menus, keyboard shortcuts, hover/focus, and desktop density.
