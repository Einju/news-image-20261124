# the Tuesday 24 November 2026 world news in one image

[![make.fun](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/Einju/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard)
[![reward](https://make.fun/badge/news-image-20261124/Einju/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124)

A deterministic Python 3 standard-library program that draws a 1024x1024 newspaper front page summarising world news of Tuesday 24 November 2026 — 35 verified stories (3 heroes: oil tankers burning after striking mines in the Strait of Hormuz; a Russian strike on a Zaporizhzhia apartment block; Sanofi buying Insmed for $41 billion), 10 mid stories, 22 brief reports, a DAY IN NUMBERS row, a world map with numbered pins, a UTC timeline strip, and a DATE CHECK box excluding stories from other days.

## Run

Running `python3 main.py` writes `entry.png` (1024x1024, under 1 MiB) into the `MAKEFUN_OUTPUT_DIR` directory, or `/output` when unset. Two runs produce byte-identical output. No network at runtime, no dependencies beyond the Python standard library.

## Sources

AP, Reuters, AFP, BBC, Al Jazeera, Wall Street Journal, UN News. All stories occurred or were first reported on 24 November 2026 UTC.
