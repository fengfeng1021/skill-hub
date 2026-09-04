#!/usr/bin/env python3
from pathlib import Path
import argparse,json,math
def physical(t):
 if t['type']=='spring-physical':
  m=float(t['mass']);k=float(t['stiffness']);c=float(t['damping']);iv=float(t.get('initialVelocity',0));return m,k,c,c/(2*math.sqrt(m*k)),iv
 if t['type']=='spring-perceptual':
  d=float(t['duration']);b=float(t['bounce']);m=1.;k=4*math.pi*math.pi/(d*d);z=(1-b) if b>0 else 1/(b+1);c=z*2*math.sqrt(m*k);return m,k,c,z,float(t.get('initialVelocity',0))
def compile_ir(ir,target):
 known={'web','swiftui','compose','flutter','react-native','winui','qml','generic'}; req=target; target=target if target in known else 'generic';t=ir['timing']; head=[f"// Motion: {ir['name']}",f"// Target: {req}"+("" if req==target else " (generic fallback)"),f"// Source records: {', '.join(ir.get('sourceRecordIds',[])) or 'none'}"]
 if t['type']=='direct': return '\n'.join(head+['// Direct interaction: bind visual state to input without tweening.','// Estimate velocity from timestamped samples for release.'])
 if t['type']=='bezier':
  cp=t['controlPoints'];d=t['duration'];curve=f"cubic-bezier({cp[0]}, {cp[1]}, {cp[2]}, {cp[3]})"
  m={'web':[f'transition-timing-function: {curve};',f'transition-duration: {d}s;'],'swiftui':[f'let animation = Animation.timingCurve({cp[0]}, {cp[1]}, {cp[2]}, {cp[3]}, duration: {d})'],'compose':[f'val easing = CubicBezierEasing({cp[0]}f, {cp[1]}f, {cp[2]}f, {cp[3]}f)',f'val spec = tween<YourType>(durationMillis = {round(d*1000)}, easing = easing)'],'flutter':[f'const curve = Cubic({cp[0]}, {cp[1]}, {cp[2]}, {cp[3]});',f'const duration = Duration(milliseconds: {round(d*1000)});'],'react-native':[f'const easing = Easing.bezier({cp[0]}, {cp[1]}, {cp[2]}, {cp[3]});',f'const duration = {round(d*1000)};']}
  return '\n'.join(head+m.get(target,[f'Bezier control points = {cp}',f'Duration = {d}s','Implement a standard cubic Bézier progress sampler.']))
 m,k,c,z,iv=physical(t); pc=f'// canonical spring: mass={m:.6g}, stiffness={k:.6g}, damping={c:.6g}, dampingRatio={z:.6g}, initialVelocity={iv:.6g}'
 if target=='swiftui' and t['type']=='spring-perceptual': body=[f"let animation = Animation.spring(duration: {t['duration']}, bounce: {t['bounce']})",'// Keep gesture updates direct; preserve velocity on retarget.']
 elif target=='swiftui': body=[f'let animation = Animation.interpolatingSpring(mass: {m:.6g}, stiffness: {k:.6g}, damping: {c:.6g}, initialVelocity: {iv:.6g})']
 elif target=='flutter': body=[f'final spring = SpringDescription(mass: {m:.6g}, stiffness: {k:.6g}, damping: {c:.6g});',f'final simulation = SpringSimulation(spring, current, target, {iv:.6g});','controller.animateWith(simulation);']
 elif target=='react-native': body=[f'Animated.spring(value, {{ toValue: target, mass: {m:.6g}, stiffness: {k:.6g}, damping: {c:.6g}, velocity: {iv:.6g}, useNativeDriver: true }}).start();']
 elif target=='compose': body=[f'val spec = spring<YourType>(dampingRatio = {z:.6g}f, stiffness = {k:.6g}f)','// Seed/retain current velocity through gesture physics where applicable.']
 elif target=='web': body=['let x = current, v = currentVelocity;',f'const m={m:.12g}, k={k:.12g}, c={c:.12g};','function step(dt){ const a=(-k*(x-target)-c*v)/m; v+=a*dt; x+=v*dt; render(x); }','// Drive with requestAnimationFrame elapsed seconds; retain x/v on retarget.']
 elif target=='winui': body=[f'CanonicalSpring(mass={m:.6g}, stiffness={k:.6g}, damping={c:.6g}, initialVelocity={iv:.6g})','Map to Composition/Natural Motion only if semantics match; otherwise use canonical integrator.']
 elif target=='qml': body=[f'CanonicalSpring(mass={m:.6g}, stiffness={k:.6g}, damping={c:.6g}, initialVelocity={iv:.6g})','For exactness use canonical oscillator; do not assume QML spring == physical stiffness.']
 else: body=[f'mass = {m:.12g}',f'stiffness = {k:.12g}',f'damping = {c:.12g}',f'initialVelocity = {iv:.12g}','a = (-stiffness*(x-target) - damping*v) / mass','v += a*dt','x += v*dt','Retarget by changing target only; keep x and v.']
 return '\n'.join(head+[pc]+body)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('ir');ap.add_argument('--target',default='generic');a=ap.parse_args();ir=json.loads(Path(a.ir).read_text(encoding='utf-8'));print(compile_ir(ir,a.target))
if __name__=='__main__':main()
