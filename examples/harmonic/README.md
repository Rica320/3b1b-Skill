# Why does the harmonic series diverge?

A 1:25 scene. The terms shrink to nothing, so why doesn't the sum settle? Group
them into blocks worth at least ½ each, and the staircase gains ½ forever.

This is the skill's **control experiment**. It was written from the skill's
documentation alone — `narrative_template.md`, `animation_rules.md`,
`anti_patterns.md`, `checklists.md` and `manim_helpers.py` — with no other
reference, to test whether the written rules are sufficient on their own or
whether they only work for someone who already remembers the video that
produced them.

It is also the shorter read of the two examples: the same structure as the GANs
scene at a quarter of the length, and the better one to copy from.

## Run it

```bash
cd examples/harmonic

bash ../../skills/3b1b-math-animation/scripts/render.sh harmonic.py Harmonic -l   # draft
bash ../../skills/3b1b-math-animation/scripts/render.sh harmonic.py Harmonic      # 1080p

python ../../skills/3b1b-math-animation/scripts/verify_render.py \
    videos/Harmonic.mp4 --meta render_meta.json
```

Run from this directory — `custom_config.yml` is read from the working
directory. No asset preparation is needed. A draft render finishes in seconds.

```bash
AUDIT=1 manimgl harmonic.py Harmonic     # report any two texts sharing screen space
```

## The spine

| | |
|---|---|
| **Question** | The terms shrink to nothing — so why doesn't the sum settle? |
| **Motivation** | Watch the partial sums. They crawl. It *looks* convergent, and that intuition is the obvious answer, and it is wrong. |
| **Build** | Group the terms into blocks. Every block is worth at least ½. There are infinitely many blocks. |
| **Payoff** | Restate the question, answer it: shrinking is not enough — they have to shrink *fast enough*. |

The carried object is **the staircase** of partial sums: a term is one step's
height, the partial sum is how high you have climbed, "does it settle?" becomes
"does the staircase level off?", and divergence is a staircase with no ceiling.
It is built once in §1 and is still the thing being pointed at in §3.

Colour mapping, fixed for the whole scene: blue for the terms of the series,
orange for the partial sum, teal for the comparison blocks, yellow for transient
emphasis only, grey for scaffolding.
