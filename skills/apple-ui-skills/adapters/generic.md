# Generic / Any-Language Adapter
For C, C++, Rust, Go, Python, Java, C#, Lua, Zig, custom engines, or unknown APIs.

Need only input positions/timestamps, state, a frame callback with elapsed time, transform/opacity drawing, and accessibility preference when available.

Spring state: `x,v,target,m,k,c`.
Each stable step:
`a=(-k*(x-target)-c*v)/m`
`v=v+a*dt`
`x=x+v*dt`

Retarget by changing target only; keep x and v. During gesture direct-map x, estimate v, release into spring/decay. Stop only when both position error and velocity are small.

If blur/refraction unavailable, use semantic elevated fill, tint, separator/highlight, restrained shadow, and preserve motion quality.

## Build completion

When the target engine is custom, do not stop after providing the spring equation.
Implement the state machine, rendering loop, interaction states, and reduced-motion
fallback in the target language whenever repository-editing tools are available.
