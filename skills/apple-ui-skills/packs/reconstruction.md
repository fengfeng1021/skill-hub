# Reconstruction Pack

Load only for a named Apple/system component or faithful historical/current recreation.

## Never read the full database
Preferred: `python scripts/query_records.py --query "<component + interaction>" --limit 3`.
Fallback: read `data/catalog.json`, choose one shard, read only that shard.

## Selection hierarchy
1. runtime-exposed current system value
2. Apple primary API/documentation
3. explicit open-source replica of named component
4. reverse-engineered/measured reconstruction
5. design-system approximation
6. skill-derived fallback

For exact reconstruction: confidence >=0.75 is suitable default; 0.50–0.74 is approximation; <0.50 should not auto-select.

## Evidence
`APPLE-PRIMARY`: Apple docs/WWDC/documented API.
`PLATFORM-PRIMARY`: official target platform docs.
`THIRD-PARTY-REVERSE-ENGINEERED`: independent measurement/reconstruction.
`OPEN-SOURCE-REPLICA`: public code explicitly mimicking an Apple/system interaction.
`ACADEMIC`: published HCI evidence.
`SKILL-DERIVED`: portability conversion/fallback authored here.
Never promote a replica into an Apple fact.

## Version discipline
Do not silently mix iOS 10 navigation parallax, iPhone X/WWDC18 fluid interactions, modern duration+bounce springs, and iOS 26 Liquid Glass. Historical records are useful for historical behavior, not proof of current constants.

## Runtime beats hard-code
On iOS: keyboard uses notification duration/curve/frame; navigation can use transition coordinator; native sheets/navigation should be preferred when exact system behavior is desired. On any platform honor host Reduce Motion, frame timestamps, keyboard/IME and system transition signals.

## Database coverage
Core Animation cubic curves; SwiftUI smooth/snappy/bouncy; iOS 10 navigation; Calculator; iPhone X flashlight; WWDC18 momentum/rubber-band; FaceTime PiP; UIScrollView rubber-band/deceleration; App Store card; Dynamic Island community replica; keyboard runtime; macOS 26.2 Control Center; iOS 26 Liquid Glass approximations.

## Porting
Separate source representation → canonical Motion IR → target representation. Evidence belongs to source representation. Translation is SKILL-DERIVED. If target spring equations differ, use canonical custom physics.

## Fail reconstruction if
an asserted exact Apple value lacks official/runtime evidence; active drag is delayed; release velocity disappears; historical data is presented as current; framework-specific damping/tension is pasted into another equation; effects cause frame instability; Reduce Motion is ignored.
