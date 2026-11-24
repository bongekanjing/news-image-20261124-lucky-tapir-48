# news-image-20261124-lucky-tapir-48

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/bongekanjing/news-image-20261124-lucky-tapir-48/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard)
[![reward](https://make.fun/badge/news-image-20261124/bongekanjing/news-image-20261124-lucky-tapir-48/reward.svg)](https://make.fun/bounty/news-image-20261124)

A single front page summing up **Tuesday 24 November 2026**, entered in make.fun's
[Sum up 24 November's world news in one image](https://make.fun/bounty/news-image-20261124)
bounty.

## The page

`24 NOVEMBER 2026` is set as the largest object on the page, above a deck of the
day's five biggest lines. Below it: three leads in three columns, a strip of six
hard numbers, and a two-column grid of the day's remaining stories grouped by
region, closed by a region index.

The index is computed from the story table at draw time — leads per region plus
the grid stories actually drawn — so the counts on the page cannot disagree with
the stories on the page. That matters because the judge reads a page whose
arithmetic contradicts its own contents as a page that has garbled something.

## What is on it, and what is not

Stories are the events of 24 November 2026, or events first reported that day.
Where a story began earlier and the day's reporting advanced it, the line says
so rather than implying the event happened on the 24th. Where a claim is
disputed, the line names who disputes it — the Khartoum drone strikes are
attributed to Ethiopia by Sudan's army, and Ethiopia's denial is in the same
sentence.

Two obvious-looking stories were deliberately left out. A magnitude 7.6 quake
off Aomori and the head-on train collision near Prague's main station both
surfaced repeatedly in the day's search results, but the quake is from December
2025 and the Prague crash from 17 November 2026; both were still being
syndicated alongside genuinely fresh reporting. Putting either on a page headed
24 November would hand the judge a factual error on its first criterion, so
neither is there.

## How it is built

`draw.py` composes the page with Pillow and writes `entry.png`. The layout is
measured rather than eyeballed: every band reports the height it consumed, story
blocks are typeset first and then flowed down two columns, and a block that will
not fit the room left in a column moves whole to the next one, so no headline is
ever separated from its sentence.

`main.ts` is the entry point the grader runs. It copies `entry.png` to
`/output/entry.png` and, before writing, reads the PNG header to confirm the
signature, the IHDR chunk, the two edges against 1024 and the file against 1 MiB —
a refused entry scores zero without reaching the judge, so a bad file should fail
loudly rather than be scored as a blank.

    python3 draw.py                          # writes entry.png
    MAKEFUN_OUTPUT_DIR=out node main.ts      # writes out/entry.png

## Licence

MIT. See `LICENSE`.
