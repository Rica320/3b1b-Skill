# The Narrative Spine

A 3b1b video is an **argument**, not a tour. The difference is that every
section answers *"why does this follow from the last?"* rather than *"what's
next?"*. Write the script as prose and get it approved **before** any animation
code exists — visuals built against a weak spine cannot be rescued by polish.

## The four movements

```
QUESTION      one driving question, stated in the first 20 seconds
   │
MOTIVATION    the obvious answer, tried and shown to fail
   │            (this is what earns everything after it)
BUILD         each step forced by the previous step's failure
   │            formalism only ever AFTER the picture it names
PAYOFF        the opening question restated verbatim, then answered
```

## 1. The driving question

**One question. Stated out loud within the first 20 seconds. Answered explicitly
at the end.** Not a topic ("today we're looking at GANs"), not a promise
("you'll understand X"). A question the viewer can hold in their head for six
minutes.

Test it: *could someone who watched only the first 20 seconds and the last 30
seconds tell you what the video was about?* If not, the question is too vague.

A good question names a **missing thing**, so the rest of the video is a search:

> "What do you write down as the score, when there is no right answer?"

Anchor it to something concrete on screen — a single highlighted box, a gap in
a diagram — so the question attaches to a specific hole rather than a mood.

## 2. Motivation before formalism

Before introducing the real machinery, **try the obvious thing and watch it
fail**. This is the single highest-leverage section and the one most often
skipped.

It must be a *fair* attempt — the strongest naive answer, not a straw man — and
its failure must be shown, not asserted:

> Grade the generator on pixel distance to real faces → the lowest-loss output
> is the dataset average → and the average of ten thousand faces is fog.

The *specific way* it fails is the seed of the next section. Here, "it wants a
single answer, and a face isn't a single answer" is what forces the reframe into
a *space* of images, which is what makes the plane necessary.

If you cannot say which later section a failure sets up, the failure is
decoration; cut it.

## 3. The single carried metaphor

**One visual object, introduced early, still on screen at the end.** Not a
series of apt analogies — one object that keeps earning new meaning.

Test it with a table before you build anything. If you cannot fill four rows,
the metaphor is too thin:

| Concept | Same object, later |
|---|---|
| the discriminator D(x) | the height of the surface |
| "which way is more real?" | the slope |
| the training signal | walking uphill |
| the adversarial loop | the surface repainting under your feet |
| convergence, D = ½ | the surface going flat |
| mode collapse | the whole cloud on one peak |

The v1 GANs video used **fifteen distinct visual systems across eleven scenes** —
photos, a 1-D curve, 2-D blobs, a latent square, block diagrams, a node graph, a
number line, a scatter plot, text lists, a parabola. That is the defect this rule
exists to prevent.

**Prefer a metaphor that is literally true.** The GANs landscape is
`D*(x) = p_data/(p_data + p_G)` evaluated on a grid — so the surface flattening
to ½ at convergence is a *computed consequence* of moving the cloud, not a
hand-authored keyframe. When the metaphor is the real object, you cannot
accidentally animate a false claim.

## 4. Section-to-section forcing

Write the chain out explicitly and check every arrow is a *because*, not an
*and then*:

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
§5  D repaints → the chase → flattens → D = ½
      │  what did we never ask for?
§6  mode collapse = the gap in the objective
      │  so, the original question
§7  you never write the grade — you grow it
```

Each connective belongs in the narration as an actual spoken sentence. If a
section's opening line could be deleted without the viewer noticing, the section
is not connected to the one before it.

## 5. Formalism arrives last, and names something already visible

Order within any beat:

1. the picture
2. what it does, in words
3. **then** the symbol for it

`D(x)` is written *onto* a curve that is already on screen. The objective
function appears only after the viewer has watched a point walk uphill. A symbol
should feel like a compressed summary of something already watched.

Never introduce notation during a transition, and never let an equation be the
first thing in a section.

## 6. The payoff

- **Restate the opening question verbatim**, in the same styling it had at the
  start. The literal repetition is what closes the loop.
- **Answer it in one short line.** ("Nothing. You don't write it down.")
- **Then point at the object** the viewer has been watching, and show that it
  *was* the answer all along.
- Close on the image you opened with.

A payoff that introduces a new idea is not a payoff.

## Script deliverable format

Before writing code, produce a document containing:

- the spine in one paragraph
- the driving question and the timestamp it lands
- the carried metaphor, with its meaning table
- the **colour mapping table** (see `animation_rules.md` §5)
- per-section: narration as prose + a visuals paragraph + a
  *"why this follows from the last"* note
- the dependency chain diagram
- any open choice that changes the build, flagged for the user

Get this approved before implementing.

## Pacing the script against the render

Word count drives runtime. At ~2.55 words/second delivered:

```
section duration ≈ words / 2.55
```

After rendering, check each section's implied delivery rate
(`words / actual_duration`). Anything above **3.0 w/s is rushed**; below
**2.2 w/s drags** unless it is the opening or the payoff, which should breathe.
Fix by adding holds at natural landing points in the tight sections — never by
scaling every hold uniformly, which is what makes a video feel metronomic.
