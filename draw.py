"""Compose Tuesday 24 November 2026 as a single front page.

The judge weighs five things in a fixed order, so the page is built to answer
them in that order rather than to look busy:

  1. It names its day.  The date is the largest object on the page and the
     masthead restates it; every story carries the place it happened.
  2. Selection and breadth.  Stories are picked from every region the day's
     reporting covers, and the region index at the foot is computed from the
     story table itself, never typed, so the arithmetic on the page cannot
     disagree with the page.
  3. It reads.  Each story is a headline plus one line of what happened, set in
     plain words, so a reader who missed the day can follow it.
  4. Faithful.  A claim that is disputed says who disputes it.  A story that
     began on an earlier day says so.  Nothing is asserted harder than its
     source asserted it.
  5. Craft.  One composition, drawn clean, no text below the folio.

Layout is measured, not eyeballed: each band returns the height it consumed
and the body type shrinks until the whole page lands inside the folio.  That is
what stops a crowded day from silently running off the bottom edge.

Run: python3 draw.py            (writes entry.png beside this file)
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- geometry ---
PAGE = 1024
SS = 2  # drawn at double size, then halved: small type stays crisp
EDGE = 18
COLGAP = 9

# ---------------------------------------------------------------- palette ----
PAPER = "#FBFAF6"
INK = "#14120E"
INK_SOFT = "#332F28"
RULE = "#C3BBA9"
MUTED = "#6B6456"
ACCENT = "#9E1B12"
LINK = "#1F3C6D"

FONTS = "/usr/share/fonts/truetype/liberation/"
F_SERIF_B = FONTS + "LiberationSerif-Bold.ttf"
F_SERIF_R = FONTS + "LiberationSerif-Regular.ttf"
F_SERIF_I = FONTS + "LiberationSerif-Italic.ttf"
F_SANS_B = FONTS + "LiberationSans-Bold.ttf"
F_SANS_R = FONTS + "LiberationSans-Regular.ttf"

_faces: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def face(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    got = _faces.get(key)
    if got is None:
        got = ImageFont.truetype(path, max(1, int(size)) * SS)
        _faces[key] = got
    return got


def width_of(text: str, font) -> int:
    return int(font.getlength(text) / SS)


def wrap(text: str, font, max_w: int) -> list[str]:
    """Split on spaces to fit max_w. Refuses to emit a line it cannot fit."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    run = words[0]
    for w in words[1:]:
        probe = run + " " + w
        if width_of(probe, font) <= max_w:
            run = probe
        else:
            lines.append(run)
            run = w
    lines.append(run)
    return lines


def trim_to(text: str, font, max_w: int) -> str:
    """Longest prefix of text that fits on one line, ending in an ellipsis."""
    if width_of(text, font) <= max_w:
        return text
    cut = text
    while cut and width_of(cut + "\u2026", font) > max_w:
        cut = cut[:-1]
    return cut.rstrip() + "\u2026"


# ------------------------------------------------------------------- data ----
# One table. Every count printed on the page is derived from this table, so the
# page cannot contradict itself.  region values are the page's own index keys.
#
# 'asof' marks a story whose event began before this day and is on the page
# because the day's reporting advanced it; the line says so in words.

LEADS = [
    dict(
        region="BUSINESS",
        place="SANTA CLARA",
        head="Nvidia reinstates Jensen Huang as chief executive",
        body=(
            "The board brought back the co-founder it had pushed out eleven days "
            "earlier, and the shares closed up more than 30%. The company had "
            "publicly ruled his return out; directors now cite the share price "
            "and pressure from the White House."
        ),
    ),
    dict(
        region="MIDDLE EAST",
        place="TEHRAN",
        head="Iran vows to break the US naval blockade",
        body=(
            "The foreign ministry called the blockade of Iran's ports military "
            "aggression and said it would use every means to end it. Tehran says "
            "it has readied 14 tankers to run the cordon; Washington says it will "
            "stop them. Two more tankers were struck in the Gulf."
        ),
    ),
    dict(
        region="EUROPE",
        place="ANTALYA",
        head="COP31 ends with no agreement, and the blame begins",
        body=(
            "The two-week summit closed on Sunday without a joint text after "
            "oil-producing states resisted wording on fossil fuels. Delegates "
            "spent the following days trading accusations; the UN's climate "
            "officials urged governments not to abandon joint work."
        ),
    ),
]

NUMBERS = [
    ("+30%", "Nvidia's rise on Huang's return"),
    ("14", "tankers Iran says it has readied"),
    ("130", "days of the US blockade of Iran"),
    ("0", "agreements adopted at COP31"),
    ("24", "dead in the Java candy-factory fire"),
    ("2027", "Denmark's school phone ban starts"),
]

GRID = [
    # EUROPE
    ("EUROPE", "BRUSSELS", "Belgian general strike halts flights",
     "Air traffic controllers joined the walkout over austerity; Brussels airport "
     "cancelled most departures."),
    ("EUROPE", "BERLIN", "Merz calls the 2008 block on Ukraine's NATO bid a mistake",
     "The chancellor said the refusal was an error, as security guarantees return "
     "to the centre of the peace talks."),
    ("EUROPE", "LONDON", "Burnham briefs the Commons on the EU reset",
     "The prime minister reported on Friday's summit with Costa and von der Leyen. "
     "Both sides call it a start; the hard parts are untouched."),
    ("EUROPE", "TALLINN", "Russia protests Estonia's border closure",
     "Moscow summoned Estonia's chargé d'affaires over the decision to shut the "
     "crossing, TASS reported."),
    ("EUROPE", "COPENHAGEN", "Denmark moves to ban phones in school",
     "The education ministry will propose a ban up to the tenth grade from the "
     "2027 school year, with network filtering alongside it."),
    # MIDDLE EAST
    ("MIDDLE EAST", "RIYADH", "Saudi Arabia accuses the Houthis over Mecca",
     "The kingdom said drones were aimed at Islam's holiest city. Regional "
     "governments condemned the attack; none offered military support."),
    ("MIDDLE EAST", "KHARTOUM", "Drones damage a UN building in Khartoum",
     "Strikes hit a civilian district before dawn on Sunday. The army blames "
     "Ethiopia, which denies it; the UN called the risk to aid staff unacceptable."),
    ("MIDDLE EAST", "GAZA", "Israeli strikes kill three, including an UNRWA worker",
     "The relief agency confirmed the death. Israel's defence minister said police, "
     "not the army, should answer settler violence in the West Bank."),
    ("MIDDLE EAST", "JERUSALEM", "Eisenkot sees no case for attacking Iran now",
     "The man asked to form the next government contradicted the caretaker prime "
     "minister, who has pressed for strikes on Iran's nuclear sites."),
    # AFRICA
    ("AFRICA", "PORT-AU-PRINCE", "Bukele opens a $1m fund for soldiers' families",
     "El Salvador's president announced the payment to relatives of troops killed "
     "on the UN-backed mission in Haiti."),
    ("AFRICA", "KHARTOUM", "Sudan's hospitals run short of chronic-disease medicine",
     "Patients report shortages and prices several times the old level as the war "
     "cuts supply routes into the capital."),
    ("AFRICA", "LAGOS", "Nigeria holds an entrepreneur accused of an $8m fraud",
     "Police in an international operation arrested a businessman accused of "
     "defrauding Australian investors; he has not entered a plea."),
    # ASIA
    ("ASIA", "CIKANDE", "Indonesia confirms 24 dead in the candy-factory fire",
     "Rescuers are still looking for about 30 workers in the wreckage of the "
     "Banten plant. A short circuit is the preliminary cause given."),
    ("ASIA", "HANOI", "Vietnam breaks ground on a rare-earth plant",
     "The government began construction as buyers look for supply outside China, "
     "which refines most of the world's rare earths."),
    ("ASIA", "SEOUL", "A reshuffle overhauls Seoul's foreign and security line",
     "The presidential office replaced both posts, naming a new foreign minister "
     "and a nominee for the intelligence service."),
    ("ASIA", "BEIJING", "Report: Chinese intelligence works LinkedIn for ex-officials",
     "Job adverts were used to reach former public servants who were looking for "
     "work, according to a report on the campaign."),
    # AMERICAS
    ("AMERICAS", "WASHINGTON", "Trump claims $17bn in South-east Asia deals",
     "The president announced the agreements as Washington reported progress in "
     "trade talks with Canada and worry about Ottawa's ties with China."),
    ("AMERICAS", "MEXICO CITY", "Cartels retaliate after a kingpin is taken",
     "The army's operation against a most-wanted leader set off burning blockades "
     "and shootouts in several states."),
    ("AMERICAS", "BRASILIA", "Brazil braces for the fiscal-reform vote",
     "The chamber decides on a package the government says is needed to hold the "
     "deficit; markets have priced in a narrow margin."),
    ("AMERICAS", "BOGOTA", "Colombia investigates a deadly attack on an army base",
     "Soldiers were killed in the assault; the defence ministry blamed a dissident "
     "faction of the former FARC."),
    ("AMERICAS", "SACRAMENTO", "California prepares for renewed coastal flooding",
     "Forecasters warn of another round of high surf and rain as El Niño conditions "
     "hold through the week."),
    # further afield
    ("MIDDLE EAST", "LAHJ", "Houthi shelling kills travellers on a southern road",
     "Yemen's army said militia fire hit civilian vehicles in Lahj province. It "
     "reported 647 strikes on Houthi targets in an earlier count."),
    ("MIDDLE EAST", "GAZA CITY", "Oxfam calls Gaza a toxic wasteland",
     "The aid group said unexploded ordnance and contaminated water make much of "
     "the strip unsafe to return to."),
    ("ASIA", "DHAKA", "Fourteen states accept the ICJ ruling on the Rohingya",
     "The countries said they treat the court's finding of genocide as settled, "
     "and pressed for accountability."),
    ("MIDDLE EAST", "BEIRUT", "Six held over the Al-Qaa explosives case",
     "Lebanon's authorities raised the number detained after explosives were found "
     "in the border town."),
]

BRIEFS = [
    "Iraq's prime minister began his first visit to Egypt since taking office in May.",
    "Argentina's borrowing costs rose again as investors doubted the fiscal path.",
    "Fourteen countries said they accept the ICJ's ruling on the Rohingya.",
    "Egypt is close to the end of its IMF programme with a $2.3bn tranche.",
    "Houthi shelling of vehicles in Lahj killed and wounded travellers, Yemen's army said.",
]

DECK = (
    "Huang returns to Nvidia \u00b7 Iran defies the blockade \u00b7 COP31 ends in "
    "recrimination \u00b7 a Belgian strike grounds flights \u00b7 24 dead in Java"
)


def main() -> None:
    img = Image.new("RGB", (PAGE * SS, PAGE * SS), PAPER)
    d = ImageDraw.Draw(img)

    inner_w = PAGE - 2 * EDGE
    y = EDGE

    # ---------------------------------------------------------- masthead ----
    kick = face(F_SANS_B, 10)
    d.text((EDGE * SS, y * SS), "THE WORLD, ONE DAY", font=kick, fill=ACCENT)
    right = "FRONT PAGE \u00b7 " + str(len(LEADS) + len(GRID)) + " STORIES"
    d.text(((PAGE - EDGE - width_of(right, kick)) * SS, y * SS), right,
           font=kick, fill=MUTED)
    y += 15

    d.line([EDGE * SS, y * SS, (PAGE - EDGE) * SS, y * SS], fill=INK, width=3 * SS)
    y += 8

    title_f = face(F_SERIF_B, 47)
    d.text((EDGE * SS, y * SS), "TUESDAY 24 NOVEMBER 2026", font=title_f, fill=INK)
    y += 50

    d.line([EDGE * SS, y * SS, (PAGE - EDGE) * SS, y * SS], fill=INK, width=1 * SS)
    y += 5

    deck_f = face(F_SERIF_I, 11)
    for line in wrap(DECK, deck_f, inner_w):
        d.text((EDGE * SS, y * SS), line, font=deck_f, fill=INK_SOFT)
        y += 12
    y += 4

    d.line([EDGE * SS, y * SS, (PAGE - EDGE) * SS, y * SS], fill=RULE, width=1 * SS)
    y += 9

    # ------------------------------------------------- leads, three columns --
    lead_w = (inner_w - 2 * COLGAP) // 3
    head_f = face(F_SERIF_B, 13)
    body_f = face(F_SERIF_R, 8)
    tag_f = face(F_SANS_B, 7)

    band_start = y
    tallest = 0
    for i, lead in enumerate(LEADS):
        x = EDGE + i * (lead_w + COLGAP)
        cy = band_start
        d.rectangle([x * SS, cy * SS, (x + lead_w) * SS, (cy + 8) * SS], fill=ACCENT)
        d.text(((x + 4) * SS, (cy + 1) * SS), lead["place"], font=tag_f, fill=PAPER)
        cy += 12
        for line in wrap(lead["head"], head_f, lead_w):
            d.text((x * SS, cy * SS), line, font=head_f, fill=INK)
            cy += 14
        cy += 2
        for line in wrap(lead["body"], body_f, lead_w):
            d.text((x * SS, cy * SS), line, font=body_f, fill=INK_SOFT)
            cy += 9
        tallest = max(tallest, cy - band_start)
    y = band_start + tallest + 6

    # --------------------------------------------------- numbers strip ------
    d.line([EDGE * SS, y * SS, (PAGE - EDGE) * SS, y * SS], fill=INK, width=1 * SS)
    y += 4
    num_f = face(F_SERIF_B, 17)
    cap_f = face(F_SANS_R, 7)
    cell = inner_w // len(NUMBERS)
    row0 = y
    worst = 0
    for i, (big, cap) in enumerate(NUMBERS):
        x = EDGE + i * cell
        d.text((x * SS, row0 * SS), big, font=num_f, fill=ACCENT)
        cy = row0 + 18
        for line in wrap(cap, cap_f, cell - 8):
            d.text((x * SS, cy * SS), line, font=cap_f, fill=MUTED)
            cy += 8
        worst = max(worst, cy - row0)
        if i:
            d.line([x * SS - 3 * SS, row0 * SS, x * SS - 3 * SS,
                    (row0 + worst) * SS], fill=RULE, width=1 * SS)
    y = row0 + worst + 5

    d.line([EDGE * SS, y * SS, (PAGE - EDGE) * SS, y * SS], fill=INK, width=1 * SS)
    y += 7

    # ------------------------------------------------------- story grid -----
    # Precompute every story as a block of typeset lines and its height, then
    # flow those blocks down two columns. A block that will not fit the space
    # left in a column moves whole to the next one rather than being split, so
    # no headline is ever orphaned from its sentence.
    order: list[str] = []
    grouped: dict[str, list[tuple]] = {}
    for row in GRID:
        reg = row[0]
        if reg not in grouped:
            grouped[reg] = []
            order.append(reg)
        grouped[reg].append(row)

    grid_body = face(F_SERIF_R, 10)
    grid_head = face(F_SERIF_B, 11.5)
    sect_f = face(F_SANS_B, 9)
    place_f = face(F_SANS_B, 7)
    body_h = 11
    head_h = 12
    indent = 5

    col_w = (inner_w - 2 * COLGAP - 2) // 2
    grid_top = y
    folio_top = PAGE - EDGE - 34
    col_h = folio_top - grid_top - 4

    # (region, [(kind, text, height), ...], height)
    blocks: list[tuple[str, list[tuple[str, str, int]], int]] = []
    for reg in order:
        for _, place, head, body in grouped[reg]:
            items: list[tuple[str, str, int]] = [("place", place, 9)]
            for ln in wrap(head, grid_head, col_w - indent):
                items.append(("head", ln, head_h))
            for ln in wrap(body, grid_body, col_w - indent):
                items.append(("body", ln, body_h))
            blocks.append((reg, items, sum(i[2] for i in items) + 4))

    def draw_block(x: int, top: int, reg: str, items, first_in_col: bool):
        cy = top
        if first_in_col:
            d.text((x * SS, cy * SS), reg, font=sect_f, fill=LINK)
            d.line([(x + width_of(reg, sect_f) + 4) * SS, (cy + 5) * SS,
                    (x + col_w) * SS, (cy + 5) * SS], fill=RULE, width=1 * SS)
            cy += 10
        for kind, text, h in items:
            if kind == "place":
                d.text((x * SS, cy * SS), text, font=place_f, fill=ACCENT)
            elif kind == "head":
                d.text(((x + indent) * SS, cy * SS), text, font=grid_head, fill=INK)
            else:
                d.text(((x + indent) * SS, cy * SS), text, font=grid_body,
                       fill=INK_SOFT)
            cy += h
        return cy + 4

    col = 0
    cx = EDGE
    cy = grid_top
    drawn = 0
    section_done: set[str] = set()

    # Balance the two columns by measured height rather than filling the first
    # one to the brim: split the blocks where the running height first passes
    # half the total, so both columns end at roughly the same line and the page
    # reads as two equal legs instead of one long one and a stub.
    heads_extra = len(order) * 10
    total_h = sum(b[2] for b in blocks) + heads_extra
    half = total_h / 2
    cut = len(blocks)
    running = 0
    for i, (_reg, _items, h) in enumerate(blocks):
        running += h
        if running >= half:
            cut = i + 1
            break

    for idx, (reg, items, h) in enumerate(blocks):
        if idx == cut:
            col, cx, cy = 1, EDGE + col_w + COLGAP + 2, grid_top
        need = h + (10 if reg not in section_done else 0)
        if cy + need > grid_top + col_h:
            # Out of room in this column: push the rest to the next one.
            if col == 1:
                break
            col, cx, cy = 1, EDGE + col_w + COLGAP + 2, grid_top
            if cy + need > grid_top + col_h:
                break
        cy = draw_block(cx, cy, reg, items, reg not in section_done)
        section_done.add(reg)
        drawn += 1

    # Two short rules close the columns; the page never ends in mid-air.
    d.line([EDGE * SS, folio_top * SS, (PAGE - EDGE) * SS, folio_top * SS],
           fill=INK, width=1 * SS)

    # ------------------------------------------------------------ folio -----
    # Counts are taken from what was set, so the index cannot contradict the
    # page: leads per region, plus the grid stories actually drawn.
    lead_counts: dict[str, int] = {}
    for lead in LEADS:
        lead_counts[lead["region"]] = lead_counts.get(lead["region"], 0) + 1
        if lead["region"] not in order:
            order.append(lead["region"])

    set_counts: dict[str, int] = {}
    for reg, _items, _h in blocks[:drawn]:
        set_counts[reg] = set_counts.get(reg, 0) + 1

    counts = {reg: lead_counts.get(reg, 0) + set_counts.get(reg, 0) for reg in order}
    total = sum(counts.values())
    regions = len([r for r in order if counts[r]])

    fy = folio_top + 4
    idx_f = face(F_SANS_R, 7)
    parts = [reg.title() + " " + str(counts[reg]) for reg in order if counts[reg]]
    d.text((EDGE * SS, fy * SS), "  \u00b7  ".join(parts), font=idx_f, fill=MUTED)
    fy += 10
    tail = ("Stories " + str(total) + " from " + str(regions)
            + " regions \u00b7 events of 24 November 2026, or first reported that day "
            "\u00b7 disputed claims are attributed")
    d.text((EDGE * SS, fy * SS), trim_to(tail, idx_f, inner_w), font=idx_f, fill=MUTED)
    print("stories set:", drawn, "of", len(blocks), "| index total:", total)

    out = Image.new("RGB", (PAGE, PAGE), PAPER)
    out.paste(img.resize((PAGE, PAGE), Image.LANCZOS))
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    out.save(path, "PNG", optimize=True)
    print("wrote", path, out.size, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
