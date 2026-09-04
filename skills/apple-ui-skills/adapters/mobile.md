# Mobile Cross-Platform Adapter
Covers Android/Compose, Flutter, React Native.

Compose: direct gesture values while interacting; use Animatable/physics for settle; preserve Android back/predictive-back semantics. Map damping ratio/stiffness only when compatible.

Flutter: SpringDescription/SpringSimulation maps well to mass/stiffness/damping/initial velocity. Flutter documents `withDurationAndBounce` as producing the same result as SwiftUI duration+bounce mapping.

React Native: prefer native/UI-thread animation for gestures, transforms/opacity for frequent updates, and verify physical spring field semantics. Do not route every pointer move through slow render state.

Keep OS accessibility, keyboard/safe-area behavior, back behavior, touch target sizing.
