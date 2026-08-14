# Phase 4 — Verification of `output_v2/GANs.mp4`

**Render:** 375.0s (6:15), 1920×1080, 30fps, single continuous `Scene`.
**Command:** `manimgl gans_v2.py GANs -w -o --video_dir output_v2`
**Checks:** `python verify_render.py output_v2/GANs.mp4 --meta render_meta.json`

## Automated checks

```
    (camera-motion windows declared: 2)
[1] off-frame content ......... pass (0 frames)
[2] blank-frame windows ....... pass (0 windows, 0.0s)
[3] over-long frozen holds .... pass (0)
[4] hard cuts ................. pass (0)
[5] colour reaching screen .... pass (64% of lit pixels saturated)

All checks passed.
```

Camera push-ins are declared by the scene (`gan_lib.push_in` → `render_meta.json`)
so checks [1] and [4] stay strict everywhere else rather than being loosened
globally to accommodate two deliberate close-ups.

## Text-overlap audit

`GANS_AUDIT=1 manimgl gans_v2.py GANs` walks every visible `Text`/`Tex` on
screen at every hold and reports pairwise bounding-box collisions.

**Result: 0 overlap events across the full run.**

Detector validated against a known-overlapping pair before trusting the zero
(two identical `Text` mobjects at the same point → correctly reported; the same
pair 3 units apart → correctly not reported). The first version of the audit
silently reported zero because `Text` containers hold their glyphs as
submobjects and so fail `has_points()`; that was fixed before the result above.

## Transition boundaries, stepped frame by frame

All 7 section boundaries examined at 30fps across a ±0.35s window:

| Boundary | t | What carries across |
|---|---|---|
| §0→§1 | 26.3s | the yellow `?` persists and grows to centre |
| §1→§2 | 69.5s | the blurred mean face persists, then becomes a point |
| §2→§3 | 136.0s | plane + both clouds persist; camera pulls back |
| §3→§4 | 189.4s | field + profile persist unchanged |
| §4→§5 | 236.4s | field + profile persist unchanged |
| §5→§6 | 287.5s | field + profile persist unchanged |
| §6→§7 | 329.1s | plane + clouds persist |

No boundary passes through black; no object disappears and reappears.

## Narration/visual sync

Section durations against the script's word counts (`SCRIPT.md`):

| § | words | duration | implied delivery |
|---|---|---|---|
| 0 | 55 | 26.3s | 2.09 w/s |
| 1 | 120 | 43.2s | 2.78 w/s |
| 2 | 180 | 66.5s | 2.71 w/s |
| 3 | 145 | 53.4s | 2.72 w/s |
| 4 | 130 | 47.0s | 2.77 w/s |
| 5 | 140 | 51.1s | 2.74 w/s |
| 6 | 110 | 41.6s | 2.64 w/s |
| 7 | 105 | 45.9s | 2.29 w/s |
| **total** | **985** | **375.0s** | **2.63 w/s** |

Every section falls inside natural delivery range (~2.5–3.0 w/s), with the
opening and payoff deliberately slower. The first pass came in at 358s with §2,
§3 and §6 needing 2.99/2.90/3.18 w/s — measurably rushed — and holds were added
at natural landing points in those three sections rather than scaling every hold
uniformly (uniform holds were defect E2 in v1).

## Phase 1 defect list — item by item

| # | Defect (v1) | Status | Evidence |
|---|---|---|---|
| **A1** | Every `Dot` renders white; `Arrow`/`Circle` too | **fixed** | Colour check: 64% of lit pixels saturated vs v1's ~4%. All dots go through `gan_lib.dot()`, which sets colour after construction. Root cause proven empirically: `Dot(color=ORANGE)`→RGB(253,255,253); `Dot().set_color(ORANGE)`→RGB(255,123,0) |
| **A2** | Colour mapping inconsistent (BLUE = real / generated / loss; YELLOW 4 ways) | **fixed** | One mapping declared in `gans_v2.py` and in SCRIPT.md; blue is real-only, orange generated-only, teal discriminator-only. Yellow is transient emphasis and is no longer the generator's identity colour |
| **B1** | 24.0s (11%) blank black frames, 21 windows | **fixed** | Check [2]: 0 windows. Single continuous Scene, so the 10 former scene-boundary blanks cannot occur |
| **B2** | Discriminator box teleports 240px (71.0→72.2s) | **fixed** | No un-animated `move_to` on a displayed mobject; check [4] reports 0 isolated delta spikes |
| **B3** | 0.1s label-snap hack | **fixed** | Labels are positioned inside their boxes at construction and moved as a unit; no correction plays exist |
| **B4** | Network edges drawn before their nodes | **n/a** | The node-graph visual was cut; the landscape metaphor replaced it |
| **C1** | `img2` off the right edge, 3.2s | **fixed** | Check [1]: 0 frames. `assert_in_frame()` now fails the build — it caught exactly this class of error twice during development (`z_lbl` at x=-6.93, closing face at y=-3.75) |
| **C2** | Loss parabola clipped by top edge, 9.8s | **n/a / covered** | The parabola was cut. Check [1] would fail the build if any new element clipped |
| **C3** | Latent inset overlapping the network | **fixed** | Overlap audit: 0 events |
| **C4** | Two captions drawn on top of each other | **fixed** | `Caption` clears before writing, so two captions never coexist in the band; overlap audit confirms 0 |
| **C5** | Closing text drawn through the diagram | **fixed** | Overlap audit: 0. The payoff dims the stage rather than writing over it |
| **C6** | Empty grey rectangles left for the final 10s | **fixed** | The landscape resolves and is faded deliberately; nothing is left disassembled |
| **C7** | "Decision boundary" label colliding with plot/legend | **n/a** | Visual cut |
| **C8** | `D(x)=½` sitting on the axis line | **fixed** | Placed clear of the slice axis; `assert_in_frame` + overlap audit clean |
| **D1** | Highlight box indexed by source-string length → landed on nothing; second box wrapped the whole equation | **fixed** | Equation built from separately addressable `Tex` terms via `gan_lib.equation()`; each term is a real mobject, boxed with `box_around(term)`. No glyph-array indexing anywhere |
| **D2** | `min_G max_D` duplicated on screen 10s | **fixed** | The two terms are `ReplacementTransform`ed *into* `min_G max_D`; no standalone copy is ever left behind |
| **D3** | Interpolation `t`-label stacked digits | **n/a** | Beat cut; no repeated `Transform` on differing-glyph `Tex` remains |
| **D4** | Dead code (`boundary()` never called) | **fixed** | No unused functions in `gans_v2.py` / `gan_lib.py` |
| **E1** | Reveals too fast to read | **fixed** | Holds are narration-derived per caption, not fixed; the densest frame (the objective) gets a 2.2s write plus term-by-term boxing |
| **E2** | 12 uniform 2.2s frozen holds (27.8s) | **fixed** | Check [3]: 0 holds exceed the narration ceiling. Holds now vary 0.3s–10s with the line being spoken |
| **E3** | Ends on 0.9s of black, no closing card | **fixed** | Closes on the two-line statement plus the face the video opened on, then fades |
| **F1** | No driving question; opening question abandoned at 0:18 | **fixed** | "What do you write down as the score, when there is no right answer?" stated at 0:16, restated verbatim at 5:37, answered on screen |
| **F2** | Formalism before motivation | **fixed** | `D(x)` is written only after the surface it names is on screen; the objective arrives after the gradient beat; every notation follows its picture |
| **F3** | 15 distinct visual systems, none carried | **fixed** | One carried object — the landscape over image space — introduced at 2:16 and still on screen at 5:37. The plane, both clouds and the profile are the *same mobjects* from §2 to §7 |
| **F4** | Claims asserted rather than earned | **fixed** | Convergence is not animated as an assertion: the field is literally `D*(x)=p_data/(p_data+p_G)`, so flattening to ½ is a computed consequence of moving the cloud, not a hand-authored keyframe |
| **F5** | Payoff resolves nothing | **fixed** | §7 restates the opening question verbatim, answers it in three words, then points at the object that has been on screen for four minutes |

Two v1 defects (B4, C2, C7, D3) are marked **n/a**: the visuals that carried them
were cut in the rebuild rather than repaired. They cannot recur in this video,
and the general rule that would have prevented each is in the skill's
ANTI-PATTERNS section.
