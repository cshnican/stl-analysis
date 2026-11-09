#!/usr/bin/env python3
"""Read ScoreWiz result screenshots into ballot rows.

Each screenshot column is one voter. Digits are classified from the STL41
font, then checked against entry_data.csv: a column must be the scores
12, 10, 8, 7–1, and each song's points and 12/10/8 counts must match.

Voters are matched from the column nickname when that person's own songs
are blank. Names that the nickname gets wrong, and names with no unique
blank-song match, are listed in CONFIRMED.

Usage:
  python3 scripts/extract_votes.py
  python3 scripts/extract_votes.py 39 43
  python3 scripts/extract_votes.py --write
"""

import csv
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from itertools import combinations, permutations, product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "results_screenshots"
ENTRY = ROOT / "data" / "entry_data.csv"
BALLOTS = ROOT / "data" / "STL screenshot ballots.csv"
SCRIPTS = Path(__file__).resolve().parent
CARD = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12]

# Nickname -> HOD, used only when that HOD's songs in the column are blank.
ALIAS = {
    "pol": "Polly", "jan": "Jana", "dom": "Dominik", "ani": "Anita",
    "chr": "Chris", "ale": "Alex", "pao": "Paolo", "han": "Hanna",
    "mat": "Matthew", "har": "Harry", "här": "Harry", "ori": "Ori",
    "luk": "Lukas", "twa": "Twan", "sq": "SQ", "dan": "Danny",
}

# Column nicknames, left to right, as read from each screenshot header.
NAMES = {
    28: "Pol Ori Sih Jan Dom Twa Ale Ani Dan Coo Pao Han Har Mat ICE".split(),
    33: "Mat Jan San Dom Ani Chr Dan Luk Ple pol Har Kon Han Ori Pao".split(),
    38: "Har Pol Pao Dom Jan Twa Jus San Zor Mat Ani Chr Han Ori".split(),
    34: "Jan Oil Pol Dom Pao Ani Twa Mat San Han NAT Chr Har Dan Ori".split(),
    35: "Pol Ani Han Ale Luk Pao Mat Say Chr Ana Har Dom als Twa Ori".split(),
    55: "Jan Har Pol Dan Dom SQ Sau Luk Int Ori Loo Pao Mat CHR Ale Han Pre".split(),
    36: "Pol Gun Dom GUN Dan Mat Spe Chr Win Pao Mil Han Har Ioa Ori".split(),
    44: "Ani Jan Dom Pol Twa SAU Chr JUS Mat Pao Han Har Ori Fay".split(),
    48: "Jan Ori Bea Jus Luk SQ Ale Dom Chr Lau Pol Emm Han Her Mat Dan Pao Ani".split(),
    56: "SQ Jan Ori Luk Ani Dom ELL Pol Dan CHR Jal Wik Han Mat Har Pao AAA".split(),
    39: "Pol Jan Dom Int Ani Chr Ale Pao Bri Han Mat Har VII Ori".split(),
    40: "Pol Jan Vii Thi Dom Mat Ell CHR Har Pao Han Ori Tee Ani".split(),
    41: ["Luk", "Pol", "Jan", "Mat", "Chr", "Dom", "Ori", "Pre", "SIH", "Här", "Han", "ABR", "Ani", "Pao", "Ale"],
    43: ["Dom", "Jan", "Pol", "Ani", "Chr", "Luk", "Mat", "Dr.", "Pao", "HRH", "Han", "The", "Ori", "Lau", "Mis"],
    42: ["Luk", "Pol", "Ani", "Dom", "Chi", "Tes", "Lau", "Jan", "Mat", "Wie", "Ano", "Han", "Ori", "Mel", "Pao"],
    45: ["Jan", "CHR", "Ori", "Dom", "Pol", "The", "Dr.", "Twa", "Mat", "Han", "Pao", "yks", "Sar", "Har"],
    46: ["Jan", "Ori", "Chr", "Pol", "Ani", "Dom", "Mat", "Har", "El", "Pao", "Han", "Dr.", "Ich"],
    50: ["Luk", "Ani", "SQ", "Jan", "Pol", "DAB", "Shh", "Dom", "Han", "Dan", "Har", "Ana", "CHR", "Pao", "Ori", "Mat"],
    51: ["Jan", "LIL", "Chr", "SQ", "Luk", "Pol", "Dan", "Dom", "Lau", "Gor", "Han", "Har", "Jon", "Pao", "Ani", "Ori"],
    53: ["Dom", "Jan", "Luk", "SQ", "Pol", "CHR", "Twa", "Mat", "Pao", "Har", "Dr.", "Fin", "Ani", "Elv", "Dan", "Han", "Ori"],
    47: "Dom Jan Pol SQ Pao Ani Luk Mat Har Geo Han Emm Let Sau Ori".split(),
    62: "Ori Dom SQ Why Dan Rom Pao ANN Pol OO Ger Mlt Har Jan Chr Han".split(),
    63: "Dom Geo Ali SQ Mat Pol Dan CHR Lau Fin Pao Ale Han Ani Har Jan Ori".split(),
}

# Screenshot row index -> country, for songs that share points and 12/10/8 counts.
TIE = {
    28: {25: "australia", 26: "malaysia"},
    33: {29: "sweden", 30: "switzerland"},
    38: {
        3: "united states", 4: "jamaica",
        9: "switzerland", 10: "greece",
        11: "wales", 12: "argentina",
        13: "england", 14: "serbia",
        23: "montenegro", 24: "scotland",
    },
    34: {28: "turkey", 29: "suriname", 30: "germany", 31: "united states"},
    55: {20: "colombia", 22: "israel", 32: "mexico", 33: "northern ireland"},
    36: {28: "kosovo", 29: "germany"},
    44: {12: "finland", 14: "lebanon", 24: "switzerland", 25: "estonia"},
    48: {25: "switzerland", 26: "turkey", 28: "scotland", 29: "spain"},
    56: {21: "argentina", 22: "sweden", 24: "united states", 25: "germany", 29: "netherlands", 30: "italy"},
    39: {9: "spain", 10: "kazakhstan"},
    41: {28: "germany", 29: "norway"},
    40: {18: "sweden", 19: "germany", 25: "new zealand", 26: "israel", 27: "ukraine", 28: "spain"},
    43: {12: "sweden", 13: "serbia"},
    50: {23: "australia", 24: "scotland", 26: "latvia", 27: "france"},
    46: {20: "england", 21: "brazil"},
    51: {28: "israel", 29: "united kingdom", 30: "algeria"},
    53: {21: "iceland", 22: "belgium", 27: "canada", 28: "spain"},
    62: {
        14: "norway", 15: "denmark",
        17: "israel", 18: "bulgaria",
        20: "russia", 21: "ireland", 22: "france",
        29: "hong kong", 30: "poland",
    },
    63: {
        15: "south korea", 17: "denmark",
        24: "argentina", 25: "russia",
        26: "japan", 27: "egypt",
        28: "mexico", 29: "portugal",
    },
}

# Names supplied after the blank-song test could not decide, or the nickname
# pointed at a different person.
CONFIRMED = {
    28: {"ICE": "Chris", "Pao": "Paolo"},
    33: {"Ple": "Twan", "Kon": "Sihan"},
    38: {"Jus": "Alex", "San": "Sandra", "Zor": "Sihan"},
    34: {"Oil": "Alex", "NAT": "Sihan"},
    35: {"Ana": "Sihan", "Say": "Sandra", "als": "Jana"},
    36: {"GUN": "Twan", "Spe": "Alex", "Win": "Sandra", "Mil": "Sihan", "Ioa": "Ioannis"},
    56: {"ELL": "Twan", "Jal": "Alex", "Wik": "Sihan", "AAA": "Sandra"},
    44: {"SAU": "Sandra", "Fay": "Sihan", "JUS": "Alex"},
    48: {"Bea": "Sihan", "Jus": "Sandra", "Lau": "Twan", "Emm": "Emma", "Her": "Harry"},
    40: {"Ell": "Sihan", "Vii": "Twan"},
    41: {"SIH": "Sandra", "ABR": "Sihan", "Pre": "Twan"},
    42: {"Wie": "Sihan", "Lau": "Twan", "Chi": "Chris", "Tes": "Sandra", "Ano": "Harry"},
    46: {"Dr.": "Alex", "El": "Sihan", "Ich": "Sandra"},
    43: {"Lau": "Twan", "HRH": "Sihan", "Dr.": "Alex", "The": "Harry", "Mis": "Sandra", "Mat": "Matthew"},
    50: {"Ana": "Sihan", "DAB": "Sandra", "Shh": "Alex"},
    51: {"LIL": "Sihan", "Lau": "Twan", "Jon": "Sandra"},
    53: {"Dr.": "Alex", "Elv": "Sihan"},
    47: {"Luk": "Sandra", "Geo": "Georga", "Emm": "Emma", "Let": "Sihan", "Sau": "Twan"},
    62: {"Why": "Sihan", "Rom": "Anita", "ANN": "Twan", "OO": "Sandra", "Mlt": "Matthew"},
}


def norm_country(value):
    text = value.replace("\xa0", " ").lower()
    text = "".join(ch for ch in text if ord(ch) < 128)
    text = " ".join(text.split())
    return {
        "the netherlands": "netherlands",
        "holland": "netherlands",
        "usa": "united states",
        "türkiye": "turkey",
        "turkiye": "turkey",
    }.get(text, text)


def load_entries():
    with ENTRY.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    by_edition = defaultdict(list)
    for row in rows:
        if row and row[0].isdigit():
            by_edition[int(row[0])].append(row)
    return by_edition


def compile_tools():
    out = Path(tempfile.gettempdir())
    tools = {}
    for name in ("grid_lines", "read_grid", "photo_lines", "cell_color"):
        binary = out / name
        source = SCRIPTS / f"{name}.m"
        subprocess.check_call(
            ["clang", "-fobjc-arc", "-framework", "Foundation", "-framework", "AppKit", "-o", str(binary), str(source)],
            stdout=subprocess.DEVNULL,
        )
        tools[name] = binary
    return tools


def line_peaks(binary, image):
    output = subprocess.check_output([str(binary), str(image)], text=True)
    mode = None
    vertical, horizontal = [], []
    for line in output.splitlines()[1:]:
        if line == "V":
            mode = "v"
            continue
        if line == "H":
            mode = "h"
            continue
        position, strength = map(int, line.split())
        (vertical if mode == "v" else horizontal).append((position, strength))
    return vertical, horizontal


def suppressed(peaks, radius, strength):
    """One peak per grid line when a photo or a thick line produces a pair."""
    strong = [(pos, dots) for pos, dots in peaks if dots >= strength]
    kept = []
    for index, (pos, dots) in enumerate(strong):
        if any(abs(other - pos) <= radius and other_dots > dots for other, other_dots in strong):
            continue
        if not kept or pos - kept[-1][0] > 2:
            kept.append((pos, dots))
    return kept


def find_run(peaks, n_lines, gap_min, gap_max, strength):
    strong = [(pos, dots) for pos, dots in peaks if dots >= strength]
    found = []
    for index, (start, _) in enumerate(strong):
        chain = [start]
        for pos, _dots in strong[index + 1:]:
            if len(chain) == n_lines:
                break
            gap = pos - chain[-1]
            if gap < gap_min:
                continue
            if gap <= gap_max:
                chain.append(pos)
            else:
                break
        if len(chain) != n_lines:
            continue
        gaps = [chain[i + 1] - chain[i] for i in range(n_lines - 1)]
        if max(gaps) - min(gaps) <= 12 and chain not in found:
            found.append(chain)
    return found


def read_grid(binary, template, image, xs, ys):
    coords = Path(tempfile.gettempdir()) / "stl_coords.txt"
    coords.write_text(
        f"{len(xs) - 1} {len(ys) - 1}\n"
        + " ".join(map(str, xs)) + "\n"
        + " ".join(map(str, ys)) + "\n"
    )
    output = subprocess.check_output(
        [str(binary), str(template), str(image), str(coords)],
        text=True,
        stderr=subprocess.DEVNULL,
    )
    grid = []
    for line in output.splitlines():
        if not line.startswith("R"):
            continue
        cells = line.split("\t")[1:-1]
        grid.append([0 if cell == "." else int(cell) for cell in cells])
    return grid


def column_scores(grid, column):
    return [row[column] for row in grid if row[column]]


def signatures(grid):
    found = []
    for row in grid:
        scores = [value for value in row if value]
        found.append((sum(scores), scores.count(12), scores.count(10), scores.count(8)))
    return tuple(sorted(found))


def column_variants(pairs):
    """Ways to turn ten scored cells into the 12–1 card by relabeling duplicate reads."""
    if len(pairs) != 10:
        return []
    values = [value for _, value in pairs]
    if sorted(values) == CARD:
        return [pairs]
    counts = Counter(values)
    missing = [value for value in CARD if counts[value] == 0]
    groups = []
    changing = 0
    for value, count in counts.items():
        keep = 1 if value in CARD else 0
        extra = count - keep
        if extra <= 0:
            continue
        changing += extra
        indexes = [index for index, (_, cell) in enumerate(pairs) if cell == value]
        groups.append(list(combinations(indexes, extra)))
    if changing != len(missing) or not 1 <= changing <= 3:
        return []
    variants = []
    for choice in product(*groups):
        chosen = [index for group in choice for index in group]
        for labels in permutations(missing):
            updated = list(pairs)
            for index, label in zip(chosen, labels):
                updated[index] = (updated[index][0], label)
            variants.append(updated)
    return variants


def repair(grid, entry_signatures):
    """Keep the one relabeling that restores every card and the published score profile."""
    working = [row[:] for row in grid]
    plans = []
    for column in range(len(working[0])):
        pairs = [(row, working[row][column]) for row in range(len(working)) if working[row][column]]
        variants = column_variants(pairs)
        if not variants:
            return None
        if len(variants) == 1 and variants[0] == pairs:
            continue
        if len(variants) > 500:
            return None
        plans.append((column, variants))
    if not plans:
        return working if signatures(working) == entry_signatures else None
    total = 1
    for _, variants in plans:
        total *= len(variants)
        if total > 8000:
            return None
    found = []
    for combo in product(*[variants for _, variants in plans]):
        trial = [row[:] for row in working]
        for (column, _), variant in zip(plans, combo):
            for row in range(len(trial)):
                trial[row][column] = 0
            for row, value in variant:
                trial[row][column] = value
        if signatures(trial) == entry_signatures:
            found.append(trial)
            if len(found) > 1:
                return None
    return found[0] if len(found) == 1 else None


def image_size(image):
    output = subprocess.check_output(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(image)],
        text=True,
    )
    width = height = 0
    for line in output.splitlines():
        if "pixelWidth" in line:
            width = int(line.split()[-1])
        elif "pixelHeight" in line:
            height = int(line.split()[-1])
    return width, height


def ridge_peaks(binary, image, y0, y1, x0, x1, lum_min, contrast_min):
    """Bright local ridges. Returns vertical and horizontal positions."""
    output = subprocess.check_output(
        [str(binary), str(image), str(y0), str(y1), str(x0), str(x1)],
        text=True,
    )
    mode = None
    vertical, horizontal = {}, {}
    for line in output.splitlines():
        if line == "V":
            mode = "v"
            continue
        if line == "H":
            mode = "h"
            continue
        parts = line.split()
        if len(parts) < 3 or parts[0] == "SIZE":
            continue
        pos, lum, contrast = int(float(parts[0])), float(parts[1]), float(parts[2])
        if lum < lum_min or contrast < contrast_min:
            continue
        dest = vertical if mode == "v" else horizontal
        dest[pos] = max(dest.get(pos, 0), contrast)
    return vertical, horizontal


def merged_ridges(binary, image, width, height):
    vertical, horizontal = {}, {}
    for start, end in ((0.12, 0.42), (0.28, 0.62), (0.45, 0.78), (0.15, 0.72)):
        found_v, found_h = ridge_peaks(
            binary, image, int(height * start), int(height * end), 0, 1, 380, 35,
        )
        for pos, contrast in found_v.items():
            vertical[pos] = max(vertical.get(pos, 0), contrast)
    for start, end in ((0.42, 0.72), (0.50, 0.80), (0.55, 0.88), (0.45, 0.85)):
        found_v, found_h = ridge_peaks(
            binary, image, 0, 1, int(width * start), int(width * end), 400, 22,
        )
        for pos, contrast in found_h.items():
            horizontal[pos] = max(horizontal.get(pos, 0), contrast)

    def nms(peaks):
        kept = []
        for pos in sorted(peaks):
            if not kept or pos - kept[-1] > 8:
                kept.append(pos)
        return kept

    return nms(vertical), nms(horizontal)


def ridge_chain(positions, n_lines, gap_min, gap_max):
    """One run of n_lines whose pitch may drift a little, as on a tilted screen."""
    for index, start in enumerate(positions):
        chain = [start]
        cursor = index + 1
        while cursor < len(positions):
            pos = positions[cursor]
            gap = pos - chain[-1]
            if gap < gap_min * 0.5:
                cursor += 1
                continue
            if len(chain) == 1:
                if gap_min <= gap <= gap_max:
                    chain.append(pos)
                elif gap > gap_max * 1.2:
                    break
                cursor += 1
                continue
            previous = chain[-1] - chain[-2]
            if previous * 0.70 <= gap <= previous * 1.30:
                chain.append(pos)
            elif gap > previous * 1.30:
                break
            cursor += 1
        if len(chain) == n_lines:
            return chain
    return None


def demote_red_twelves(binary, image, grid, xs, ys):
    """On a photo the flat-screenshot reader calls a red 10 an orange 12."""
    coords = Path(tempfile.gettempdir()) / "stl_coords.txt"
    coords.write_text(
        f"{len(xs) - 1} {len(ys) - 1}\n"
        + " ".join(map(str, xs)) + "\n"
        + " ".join(map(str, ys)) + "\n"
    )
    output = subprocess.check_output([str(binary), str(image), str(coords)], text=True)
    for line in output.splitlines():
        row, column, _mean, _light, _red, yellow = map(int, line.split())
        if grid[row][column] == 12 and yellow < 50:
            grid[row][column] = 10
    return grid


def photo_grid(tools, image, voters, songs, profile):
    width, height = image_size(image)
    vertical, horizontal = merged_ridges(tools["photo_lines"], image, width, height)
    xs = ridge_chain(vertical, voters + 1, 16, 70)
    ys = ridge_chain(horizontal, songs + 1, 14, 60)
    if not xs or not ys:
        return None
    grid = read_grid(tools["read_grid"], SHOTS / "STL41.jpg", image, xs, ys)
    demote_red_twelves(tools["cell_color"], image, grid, xs, ys)
    return repair(grid, profile)


def extract_grid(tools, edition, entries):
    image = SHOTS / f"STL{edition}.jpg"
    if not image.exists():
        image = SHOTS / f"STL{edition}.jpeg"
    if not image.exists():
        return {"edition": edition, "error": "no screenshot"}
    voters = round(sum(int(row[7]) for row in entries) / 58)
    songs = len(entries)
    vertical, horizontal = line_peaks(tools["grid_lines"], image)
    template = SHOTS / "STL41.jpg"
    profile = tuple(sorted(
        (int(row[7]), int(row[8]), int(row[9]), int(row[10])) for row in entries
    ))
    leader = max(int(row[7]) for row in entries)

    def search(vertical_runs, horizontal_runs):
        found = None
        for xs in vertical_runs or []:
            for ys in horizontal_runs or []:
                grid = read_grid(tools["read_grid"], template, image, xs, ys)
                fixed = repair(grid, profile)
                if not fixed:
                    continue
                first = sum(fixed[0])
                rank = (first == leader, -abs(first - leader))
                if found is None or rank > found[0]:
                    found = (rank, fixed)
        return found

    best = search(
        find_run(vertical, voters + 1, 28, 55, 90) or find_run(vertical, voters + 1, 26, 60, 70),
        find_run(horizontal, songs + 1, 26, 46, 70) or find_run(horizontal, songs + 1, 24, 50, 50),
    )
    if not best:
        best = search(
            find_run(suppressed(vertical, 16, 60), voters + 1, 28, 46, 0),
            find_run(suppressed(horizontal, 12, 50), songs + 1, 26, 40, 0),
        )
    if not best:
        fixed = photo_grid(tools, image, voters, songs, profile)
        if fixed:
            return {"edition": edition, "grid": fixed, "entries": entries}
        return {"edition": edition, "error": "grid does not match the results"}
    return {"edition": edition, "grid": best[1], "entries": entries}


def song_rows(edition, grid, entries):
    grouped = defaultdict(list)
    for entry in entries:
        signature = (int(entry[7]), int(entry[8]), int(entry[9]), int(entry[10]))
        grouped[signature].append(entry)
    matched = []
    for index, row in enumerate(grid):
        scores = [value for value in row if value]
        signature = (sum(scores), scores.count(12), scores.count(10), scores.count(8))
        choices = grouped[signature]
        if index in TIE.get(edition, {}):
            country = TIE[edition][index]
            choices = [entry for entry in choices if norm_country(entry[3]) == country]
        if len(choices) != 1:
            raise ValueError(f"STL{edition} row {index + 1} matches {len(choices)} songs")
        matched.append(choices[0])
    return matched


def assign_voters(edition, names, grid, songs):
    songs_of = defaultdict(list)
    for index, entry in enumerate(songs):
        songs_of[entry[2].strip()].append(index)
    assigned = {}
    pool = set(songs_of)

    def blanks(column, hod):
        return not any(grid[row][column] for row in songs_of[hod])

    for column, name in enumerate(names):
        hod = ALIAS.get(name.lower().rstrip("."))
        if hod and hod in pool and blanks(column, hod):
            assigned[name] = hod
            pool.discard(hod)
    for name, hod in CONFIRMED.get(edition, {}).items():
        if name in assigned and assigned[name] != hod:
            pool.add(assigned[name])
        for other, current in list(assigned.items()):
            if current == hod and other != name:
                del assigned[other]
                pool.add(hod)
        assigned[name] = hod
        pool.discard(hod)
    changed = True
    while changed:
        changed = False
        for column, name in enumerate(names):
            if name in assigned:
                continue
            fits = [hod for hod in pool if songs_of[hod] and blanks(column, hod)]
            if len(fits) == 1:
                assigned[name] = fits[0]
                pool.discard(fits[0])
                changed = True
    open_columns = []
    for name in names:
        if name in assigned:
            continue
        column = names.index(name)
        fits = [hod for hod in sorted(pool) if blanks(column, hod)]
        open_columns.append((name, fits))
    return assigned, open_columns


def ballot_rows(edition, names, assigned, grid, songs):
    rows = []
    for column, name in enumerate(names):
        if name not in assigned:
            continue
        voter = assigned[name]
        for index, entry in enumerate(songs):
            points = grid[index][column]
            if not points:
                continue
            rows.append([str(edition), f"STL{edition}", voter, entry[2].strip(), entry[3], str(points), "", "", "", "", ""])
    rows.sort(key=lambda row: (row[2].lower(), -int(row[5])))
    return rows


def main(argv):
    write = "--write" in argv
    requested = [int(arg) for arg in argv if arg.isdigit()]
    editions = requested or sorted(NAMES)
    entries = load_entries()
    tools = compile_tools()
    collected = []
    for edition in editions:
        if edition not in NAMES:
            print(f"STL{edition}: no column names recorded")
            continue
        result = extract_grid(tools, edition, entries[edition])
        if "error" in result:
            print(f"STL{edition}: {result['error']}")
            continue
        songs = song_rows(edition, result["grid"], entries[edition])
        assigned, open_columns = assign_voters(edition, NAMES[edition], result["grid"], songs)
        named = sum(1 for name in NAMES[edition] if name in assigned)
        print(f"STL{edition}: {named}/{len(NAMES[edition])} voters named")
        for name, fits in open_columns:
            print(f"  {name}: {', '.join(fits) if fits else 'no entrant fits'}")
        if named != len(NAMES[edition]):
            continue
        collected.extend(ballot_rows(edition, NAMES[edition], assigned, result["grid"], songs))
    if write and collected:
        collected.sort(key=lambda row: (int(row[0]), row[2].lower(), -int(row[5])))
        header = ["Edition", "Code", "HOD", "Receiving HOD", "Receiving Country", "Points", "", "", "", "", ""]
        body = "\r\n".join(",".join(row) for row in [header, *collected]) + "\r\n"
        BALLOTS.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
        print(f"wrote {len(collected)} rows to {BALLOTS.name}")


if __name__ == "__main__":
    main(sys.argv[1:])
