# Desktop Adapter
Covers Windows/WinUI, Qt/QML/Linux, Electron/Tauri.

Preserve windows, resize behavior, keyboard shortcuts, focus traversal, hover, context menus, dense information layouts. Do not automatically use mobile full-screen navigation metaphors.

Windows: use Composition/Natural Motion/InteractionTracker where appropriate; custom canonical spring when exact trajectory and API semantics differ. Prefer native Mica/Acrylic to a costly iOS-glass imitation.

Qt/QML/Linux: direct PointerHandler/property updates while dragging. Use a C++/QML canonical integrator if SpringAnimation semantics do not match m/k/c.

Electron/Tauri follows Web rendering rules plus native window/shortcut behavior. An opaque well-separated surface with excellent motion is better than laggy blur.
