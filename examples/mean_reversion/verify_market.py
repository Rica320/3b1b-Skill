#!/usr/bin/env python3
"""
Check every number the narration says against the data it is said about.

The video makes eighteen quantitative claims. Each one is asserted here
against market.py's output rather than against a note someone made while
writing the script, so editing a parameter in market.py and forgetting to
re-cut the narration is a test failure instead of a wrong number in a
finished render.

    ../../env/bin/python verify_market.py

Also greps script.yaml for the numerals it expects to find, which catches the
opposite mistake: the data changing and the spoken line quietly not matching
any claim listed here.
"""

import re
import sys
from pathlib import Path

import numpy as np

import market as mk

_HERE = Path(__file__).resolve().parent
FAILS = []


def check(name, got, want, tol=0.0, unit=""):
    ok = abs(got - want) <= tol if isinstance(want, float) else got == want
    flag = "ok  " if ok else "FAIL"
    if not ok:
        FAILS.append(name)
    shown = f"{got:.2f}" if isinstance(got, float) else str(got)
    exp = f"{want:.2f}" if isinstance(want, float) else str(want)
    print(f"  [{flag}] {name:<46} {shown}{unit}"
          + ("" if ok else f"   (narration says {exp}{unit})"))


def main():
    m = mk.build()
    s, z, mu, sd = m["spread"], m["z"], m["mu"], m["sd"]
    trades = m["trades"]
    before, after = mk.split(trades)

    quiet = slice(mk.WINDOW, 170)          # the 110 quiet days
    loud = slice(170, mk.BREAK_DAY)        # the next 130 days
    low = mk.DOLLAR_THRESHOLD / 5.0        # the $0.40 line

    print("§1  the dollar threshold")
    check("quiet stretch is this many days", 170 - mk.WINDOW, 110, unit=" d")
    check("loud stretch is this many days", mk.BREAK_DAY - 170, 130, unit=" d")
    check("$2 fires on this many quiet days",
          int((np.abs(s[quiet]) > mk.DOLLAR_THRESHOLD).sum()), 0, unit=" d")
    check("$0.40 fires on this many loud days",
          int((np.abs(s[loud]) > low).sum()), 98, unit=" d")
    # The picture shows this one even though the narration does not say it.
    check("$0.40 fires on this many quiet days",
          int((np.abs(s[quiet]) > low).sum()), 2, unit=" d")

    print("\n§2  the ruler")
    check("rolling window", mk.WINDOW, 60, unit=" d")
    check("quiet-stretch sigma", float(np.nanmean(sd[quiet])), 0.15,
          tol=0.005, unit=" $")

    print("\n§3  the rule, and what it pays")
    check("trades before the break", len(before), 6)
    check("all of them winners", sum(t["net"] > 0 for t in before), 6)
    check("net, before the break",
          sum(t["net"] for t in before), 3.75, tol=0.005, unit=" $")
    check("trade 1 gross move",
          abs(before[0]["s_out"] - before[0]["s_in"]), 0.27, tol=0.005,
          unit=" $")
    check("trade 2 gross move",
          abs(before[1]["s_out"] - before[1]["s_in"]), 0.24, tol=0.005,
          unit=" $")
    check("trade 1 net", before[0]["net"], 0.07, tol=0.005, unit=" $")
    check("trade 2 net", before[1]["net"], 0.04, tol=0.005, unit=" $")
    check("best loud-stretch trade, net",
          max(t["net"] for t in before), 1.58, tol=0.005, unit=" $")
    check("round-trip cost", mk.COST, 0.20, tol=0.001, unit=" $")
    # "Two sigma is worth thirty cents when sigma is fifteen."
    check("two sigma, in the quiet stretch",
          2 * float(np.nanmean(sd[quiet])), 0.30, tol=0.01, unit=" $")

    print("\n§4  the held-out stretch")
    t_low = int(mk.BREAK_DAY + np.argmin(s[mk.BREAK_DAY:]))
    entry = after[0]["entry"]
    check("the gap's furthest point from home",
          float(s[t_low]), -11.15, tol=0.005, unit=" $")
    check("z on that day", float(z[t_low]), -1.4, tol=0.05)
    # "Over the whole collapse it never once passes minus two and a half."
    collapse = z[entry:mk.DAYS - 1]
    check("worst z of the entire collapse", float(collapse.min()), -2.47,
          tol=0.02)
    print(f"        (and -2.47 > -2.5, so 'never past -2.5' holds: "
          f"{float(collapse.min()) > -2.5})")
    if not float(collapse.min()) > -2.5:
        FAILS.append("z never passes -2.5")
    check("trades after the break", len(after), 1)
    check("that trade's net", after[0]["net"], -9.32, tol=0.005, unit=" $")
    check("days it was held", after[0]["exit"] - after[0]["entry"], 89,
          unit=" d")

    print("\n  script.yaml says what the data says")
    text = (_HERE / "script.yaml").read_text().lower()
    for phrase in ["hundred and ten days", "ninety-eight",
                   "hundred and thirty days", "sixty days", "six trades",
                   "six winners", "three dollars seventy-five",
                   "twenty-seven cents", "twenty-four", "seven cents",
                   "dollar fifty-eight", "thirty cents", "sigma is fifteen",
                   "eleven dollars", "two and a half", "minus one point four",
                   "nine dollars and thirty-two cents", "eighty-nine days"]:
        ok = phrase in re.sub(r"\s+", " ", text)
        if not ok:
            FAILS.append(f"script phrase {phrase!r}")
        print(f"  [{'ok  ' if ok else 'FAIL'}] {phrase!r}")

    print()
    if FAILS:
        print(f"{len(FAILS)} FAILED: {FAILS}")
        return 1
    print("all 18 spoken numbers check out against market.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
