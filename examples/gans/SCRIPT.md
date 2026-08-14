# GANs — Script v2

**Target length:** ~6:00 (≈985 words of narration at ~2.6 w/s, plus comprehension holds).
**Driving question stated at:** 0:16.
**Payoff resolves it at:** 5:05.

---

## The spine in one paragraph

Training a network requires a grader. Generation has no right answer, so there is
nothing to write down as the grade. The obvious pixel-distance grade actively
rewards blur, so it must be abandoned. Recast the problem geometrically — move a
cloud of generated points onto a cloud of real ones — and the missing thing becomes
a *direction*. A second network can supply that direction, because *classifying* is
an ordinary supervised problem even when *generating* isn't. What that network
learns is a **landscape** over image space: high where things look real. Its slope
is the training signal. Its repainting is the adversarial loop. Its flattening is
convergence. Its single peak is mode collapse. The answer to the opening question
is that you never write the grade down — you grow a surface that the data sculpts,
and that dissolves at the moment it succeeds.

## The single visual metaphor

**A landscape over image space.**

Every image is a point on a plane. The discriminator is a *height* over every point
on that plane — how real it looks. This one object carries the entire video:

| Concept | Same object, later |
|---|---|
| The discriminator D(x) | the height of the surface |
| "which way is more real?" | the slope |
| G's training signal | walking uphill |
| the adversarial loop | the surface repainting itself under your feet |
| convergence, D(x)=½ | the surface going flat |
| mode collapse | the whole cloud on one peak |

It is introduced at 2:10 and is still on screen at 5:35. Nothing replaces it.

**Rendering approach:** top-down 2D plane with the height field drawn as a shaded
teal field, *plus* a 1-D slice profile along the bottom third of the frame — the
slice is where "uphill" and "flattens to ½" read most legibly. (A true 3D
`ParametricSurface` is the alternative; it looks better but renders slower and is
riskier. Flagging this as the one open choice — see note at the end.)

## Colour mapping (fixed for the entire video)

| Colour | Means | Never means anything else |
|---|---|---|
| `BLUE_C` | **real data** — real images, the real cloud, p_data | ✓ |
| `ORANGE` | **generated** — the seed z, G's outputs, the fake cloud, p_G | ✓ |
| `TEAL_C` | **the discriminator** — the box, the surface, the height field | ✓ |
| `GREEN` | **gradient / direction of improvement** | ✓ |
| `YELLOW` | **currently load-bearing** — the one thing being discussed right now | transient only |
| `GREY_B`/`WHITE` | neutral scaffolding: axes, seeds, connectives | ✓ |

Note the fix vs. v1: yellow is *no longer* the generator's identity colour (it was
overloaded four ways). The generator has no colour of its own — it is identified by
the colour of what it *produces*, orange. This is deliberate: the generator is only
ever visible through its outputs.

---

# The script

## §0 — The question (0:00 – 0:20)

> This face was never photographed. There's no such person; a network invented it.
>
> But to train that network, something had to score its guesses. That's what
> training *is* — guess, get graded, adjust.
>
> So: what do you write down as the score, when there's no right answer?

**Visuals.** Open on the generated face, full frame, still. Hold 2s in silence.
The face shrinks and settles into a small three-node loop: `guess → score → adjust`,
drawn in grey. On "score," that node lights **yellow**. On the question, the yellow
node's label transforms into a question mark; the question text writes below it.
Hold 1.5s.

*Why this opening:* the loop diagram is the only thing on screen when the question
lands, so the question is anchored to a specific missing piece — not to a mood.

---

## §1 — Why the obvious answer fails (0:20 – 1:08)

> The obvious thing to try: take a real face, measure how far your guess is from it,
> pixel by pixel, and punish the distance.
>
> Watch what that gives you.
>
> If a network is graded on its average distance to every face in the dataset, then
> the output that scores best is the one closest to all of them at once. Which is
> their average.
>
> And the average of ten thousand faces is fog.
>
> So the obvious score doesn't merely work badly. It points the wrong way — it
> *rewards* the blur. Every pixel-wise score has this problem. It wants a single
> answer, and "a face" isn't a single answer. It's a whole space of them.

**Visuals.** The question mark transforms into an orange output square beside one
blue real photo, dashed grey line between them labelled `distance`. Then the single
photo fans out into a 4×3 grid of real photos (blue), every one connected to the
orange square by a thin line — the lines crowd it from all sides. On "which is
their average," all twelve photos *collapse inward* and merge into the orange
square, which becomes the actual pixel-mean of the dataset: a grey blur. Hold 2s
in silence on the blur. Caption: `the lowest-loss face`.

*Why this follows from §0:* §0 asked what to write down. §1 writes down the one
obvious candidate and watches it fail — and the specific way it fails (it wants one
answer) is the seed of §2.

---

## §2 — Image space, and two clouds (1:08 – 2:10)

> "A whole space of them." Let's take that literally.
>
> Flatten every image down to a single point. Pictures that look alike sit near each
> other; pictures that look nothing alike sit far apart. This whole plane is every
> image that could exist — and almost all of it is noise.
>
> The real faces aren't scattered across it. They're bunched, in one small bright
> region. That region is the thing we actually want.
>
> Now — a generator is just a machine that takes a random seed and drops it
> somewhere on this plane. Untrained, it drops points wherever. Over here. Far from
> the good region.
>
> So the goal stops being "make a good image," and becomes something concrete:
> move the orange cloud onto the blue one.
>
> Which is real progress. But it hands us a new problem. Standing on an orange
> point — which direction is *toward blue*? Nothing about the plane tells you. The
> blue region isn't labelled. There's no arrow.

**Visuals.** The blur **shrinks and becomes a single point** on an appearing plane —
the same mobject, transformed, not replaced. This is the hinge of the video: the
image literally becomes a coordinate. Blue points fade up in one region
(`lag_ratio`, ~1.2s); three of them bloom back into face thumbnails for a beat to
prove the correspondence, then re-collapse. An orange seed dot enters left, passes
through a small `G` box, and lands as an orange point elsewhere on the plane —
repeated, staggered, until an orange cloud exists. Hold 1s with both clouds still.

Then the **camera pushes in** on one orange point. Eight grey arrows radiate from
it in all directions, all identical weight. Hold. They fade out together, leaving
the bare point and the text `which way?`

*Why this follows from §1:* §1 ended on "a whole space of them." §2 draws that space.
The failure of §1 (no single target) becomes the geometry of §2 (a region, not a point).

---

## §3 — The critic paints the landscape (2:10 – 3:05)

> Here's the move.
>
> We can't write down which way is toward blue. But we can *train a second network*
> to tell us — because that job, unlike generating, is an ordinary supervised
> problem. It has right answers. Blue points are labelled real. Orange points are
> labelled fake. Any classifier can learn that.
>
> Call it the discriminator. And picture what it learns as a surface lying over the
> plane: a height at every point, for how real that point looks.
>
> D of x. High ground over the blue cloud. Low ground over the orange.
>
> Now notice what we've got. The discriminator never learns what a face *is*. It
> only has to be higher over there than over here. But that's enough — because a
> surface has slope. And a slope is a direction.

**Visuals.** Camera pulls back to both clouds. A teal field washes over the plane
(`lag_ratio` across a grid of cells, ~1.5s), bright over blue, dark over orange.
Simultaneously a 1-D slice profile draws in along the bottom third — a teal curve,
high on the blue side, low on the orange side.

`D(\mathbf{x})` writes onto the profile **only after** the surface exists — the
notation names something already on screen. Then camera returns to the single
orange point; the eight grey arrows come back, and exactly one of them lights
**green** and lengthens: uphill. Hold 1.5s.

*Why this follows from §2:* §2 ended on "there's no arrow." §3 supplies the arrow,
and supplies it from the one thing that was still easy — classification.

---

## §4 — Walking uphill (3:05 – 3:55)

> So the generator stops guessing. It reads the slope beneath its own output, and
> nudges its weights so that next time, that output lands a little further up the
> hill.
>
> That's the entire training signal. Not "here is the correct face" — there isn't
> one. Just: *from where you're standing, up is that way.*
>
> And with that, the objective function is only bookkeeping. The discriminator wants
> to raise the surface over real points, and lower it over fake ones — that's its
> two terms. The generator wants exactly one of those terms to fail. It wants its
> own points high.
>
> One surface. One player pushing it apart, the other pushing it flat.

**Visuals.** The single orange point slides uphill along the profile; as it does, a
few edges inside the small `G` box brighten — the weights are what moved, not the
point. Then the whole orange cloud creeps upslope together, staggered.

The objective writes in one piece, centred. Then **term 1 detaches and flies to
hover over the blue cloud**, term 2 detaches and hovers over the orange cloud —
each term physically labelling the region it governs. `min_G max_D` is formed by
*transforming the two hovering terms' colour keys*, not written as a separate line.
Hold 1.5s.

*Why this follows from §3:* §3 gave a direction. §4 walks it, and only then names
the walk. The formula arrives sixth in this section, not first.

---

## §5 — The landscape fights back (3:55 – 4:45)

> Except the surface isn't fixed.
>
> Every time the orange cloud climbs, the discriminator gets retrained — and it
> repaints the landscape to separate them again. The hill moves. The generator
> climbs. The hill moves again.
>
> That's the whole loop. And it's why the two networks have to improve together:
> the grader is only ever as good as it needs to be to catch the current forger.
>
> Now watch where this ends. As the orange cloud spreads over the blue one, the
> discriminator's job gets harder — there's less and less left to separate. The high
> ground comes down. The low ground comes up.
>
> Until the two clouds coincide, and no surface can separate them at all. The
> landscape goes flat. D of x is one-half, everywhere. A coin flip.
>
> The grader has been rendered useless. That was the goal.

**Visuals.** Three cycles, each shorter than the last: cloud climbs → the *same*
profile mobject `Transform`s to a re-separated shape → cloud climbs again. Amplitude
visibly decreases each cycle. The clouds interpenetrate; the teal field desaturates
toward uniform; the profile flattens to a horizontal line at mid-height.
`D(\mathbf{x}) = \tfrac{1}{2}` writes on the flat line. **Hold 2.5s, silent.**
This is the emotional peak of the video and gets the longest hold in it.

*Why this follows from §4:* §4 assumed a fixed hill. §5 removes that assumption,
which is the only thing that makes it adversarial — and the removal produces the
convergence result for free.

---

## §6 — When it goes wrong (4:45 – 5:20)

> One failure mode falls straight out of this picture.
>
> Nothing here ever told the orange cloud to *spread*. It was only told to get high.
> So if it finds one peak, it can pile every point it has onto that one peak — and be
> perfectly satisfied.
>
> The discriminator will eventually notice, and flatten that peak. But the generator
> just moves the pile to the next one. It never learns to cover the region, because
> covering the region was never what we asked for.
>
> That's mode collapse. It isn't a bug in the code. It's a gap in the objective.

**Visuals.** Rewind the field to a mid-training state. The orange cloud contracts —
every point converging on a single peak. On the right, eight generated faces fade
in, all identical (orange borders). The peak sinks under them; the pile slides
laterally to the next peak; the faces refresh — still eight identical ones, a
different face. Hold 1.5s.

*Why this follows from §5:* §5 showed the loop succeeding. §6 asks what the loop
*didn't* say — using the same picture, with nothing new introduced.

---

## §7 — Payoff (5:20 – 6:00)

> So. Back to the question.
>
> What do you write down as the score, when there's no right answer?
>
> Nothing. You don't write it down.
>
> You let the data sculpt it. The score is a surface that the real examples raise up
> and the fake ones wear down; that reshapes itself every time the generator
> improves; and that flattens into nothing at the exact moment the generator gets it
> right.
>
> Nobody ever tells this network what a good face looks like. It learns because a
> second network keeps rebuilding the hill it has to climb.

**Visuals.** Return to the flat landscape. **The opening question text fades back
in**, in the same style and position it had at 0:16 — the loop closes literally.
On "you don't write it down," the question mark from §0 returns and **transforms
into the teal profile curve**. The clouds recolour to a single shared hue as the
plane empties. Finally the plane collapses back into a single point, which blooms
into **the same face the video opened on**. Hold 3s. Fade.

*Why this resolves §0:* the question is restated verbatim, answered in three words,
and then the answer is shown to be the object the viewer has been watching for four
minutes.

---

## Section-to-section dependency chain

Each arrow is a "why does this follow?" that the narration says out loud:

```
§0  need a grade
      │  the obvious grade is…
§1  pixel distance → rewards the blur → "a face is a whole space"
      │  so draw that space
§2  image space, two clouds → "which way is toward blue?"
      │  we can't write the direction, but we can learn it
§3  a classifier → a landscape → slope IS the direction
      │  so walk it
§4  gradient ascent on D → the objective is just bookkeeping
      │  but D isn't fixed
§5  D repaints → the chase → surface flattens → D = ½
      │  what did we never ask for?
§6  mode collapse = the gap in the objective
      │  so, the original question
§7  you never write the grade — you grow it
```

---

## One open choice before I build

The landscape can be rendered two ways:

- **(A) 2D shaded field + 1D slice profile** *(assumed above)* — robust, fast to
  render, and the slice makes "uphill" and "flattens to ½" unmistakable. Reads as
  classic 3b1b.
- **(B) True 3D `ParametricSurface` on a tilted camera** — more striking, and the
  "landscape" metaphor becomes literal rather than implied. Slower renders, and
  camera moves in 3D are where ManimGL scenes most often break.

I've written the visuals for (A) and will build that unless you'd rather have (B).
Everything else in the script is independent of this choice.
