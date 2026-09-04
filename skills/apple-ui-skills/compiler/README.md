# Universal Motion Compiler
Pipeline: `reference/design intent → Motion IR → canonical physics → target code/config`.

Use: `python scripts/compile_motion.py examples/motion-ir.json --target web`.
Targets: `web`, `swiftui`, `compose`, `flutter`, `react-native`, `winui`, `qml`, `generic`. Unknown labels fall back to generic.

IR timing types: `spring-perceptual` (duration+bounce), `spring-physical` (m/k/c), `bezier`, `direct`.

Compiler output is an implementation scaffold. It does not replace gesture state, interruption, runtime system timing, Reduce Motion, or host-platform conventions.
