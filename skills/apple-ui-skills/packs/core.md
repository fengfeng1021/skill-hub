# Core Motion Pack

Load for generic Apple-quality interaction/motion.

## Driver selection
- active drag/swipe → direct input mapping
- gesture release to anchor → spring with inherited velocity
- free scrolling → exponential decay/inertia
- overscroll → nonlinear resistance + spring return
- position/size/shared geometry → spring
- opacity/color/tiny hover → timed tween/cubic
- repeated retargeting → spring/smoothed tracking
- Reduce Motion → fade/local movement/instant state

Do not use one global `300ms ease` for everything.

## Canonical spring
`m*x'' + c*x' + k*(x-target) = 0`

Damping ratio: `ζ = c / (2*sqrt(k*m))`.
- ζ < 1 underdamped
- ζ = 1 critically damped
- ζ > 1 overdamped

### Apple perceptual duration+bounce mapping
For the compatible mapping documented by Flutter as matching SwiftUI:
`m=1`
`k=4π²m/duration²`
If bounce > 0: `ζ=1-bounce`; otherwise `ζ=1/(bounce+1)`.
Then `c=ζ*2*sqrt(m*k)`.

Apple's documented example `duration=0.5, bounce=0.3` is approximately `mass=1, stiffness=157.9, damping=17.6`.

Source duration/bounce can be Apple-primary; a cross-platform conversion remains SKILL-DERIVED.

## Velocity
Canonical velocity is property-units/second: px/s, pt/s, dp/s, scale-units/s, radians/s, etc.

When an API expects normalized initial velocity:
`relativeVelocity = physicalVelocity / (target-current)`.
Guard tiny distances; clamp only for numerical stability.

Never reset velocity on retarget, mix coordinate spaces, or tune in units/frame.

## Gesture state
Use `idle → interacting → settling` and allow `settling → interacting`.

During interaction: direct-map input and estimate recent velocity. On release: project/select target when relevant, retain current state/velocity, settle physically.

## Scroll projection
For UIScrollView-style per-millisecond decay `r`:
`projection = (velocity/1000) * r/(1-r)`.
Common compatibility mappings: normal `0.998`, fast `0.99`. Evaluate by elapsed time, not once/rendered frame.

## Rubber band
Common third-party UIScrollView reconstruction:
`f(x,d,c)=(x*d*c)/(d+c*x)` with reported `c=0.55`.
This is reverse engineered, not an Apple-published constant.

A different public WWDC18-inspired generic elastic demo uses `sign(x)*abs(x)^0.7`; do not confuse the two models.

## Composition
Primary: position, size, scale/shared geometry. Secondary: opacity, corner radius, blur/material, shadow/highlight. Geometry tells the story.

## Performance
Integrate with elapsed time; use stable time steps; cap huge deltas after suspension; stop only when position error and velocity are both small. Prefer transform/opacity, bound blur, pause irrelevant animation.

## Accessibility
With Reduce Motion preserve direct control, remove large zoom/parallax/depth travel, use fade/local movement, reduce repeated bounce, retain essential state feedback.
