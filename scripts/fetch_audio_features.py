#!/usr/bin/env python3
"""Attach Spotify-style audio features to every contest entry.

Spotify IDs live in data/song_info.csv. Spotify no longer serves audio
features, so each ID is resolved through the ReccoBeats catalog, which
returns the same measures (danceability, energy, valence, and the rest).

Writes data/audio_features.csv, one row per entry.
"""

import csv
import json
import re
import tempfile
import threading
import time
import unicodedata
from difflib import SequenceMatcher
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SONG_INFO = ROOT / "data" / "song_info.csv"
ENTRIES = ROOT / "data" / "entry_data.csv"
EXPORT = ROOT / "data" / "ShareTheLove.csv"
PITCH = {
    "c": 0, "c#": 1, "db": 1, "d": 2, "d#": 3, "eb": 3, "e": 4, "f": 5,
    "f#": 6, "gb": 6, "g": 7, "g#": 8, "ab": 8, "a": 9, "a#": 10, "bb": 10, "b": 11,
}
OUT = ROOT / "data" / "audio_features.csv"
CACHE = Path(tempfile.gettempdir()) / "stl_audio_feature_cache.json"
API = "https://api.reccobeats.com/v1"
FEATURES = [
    "acousticness", "danceability", "energy", "instrumentalness",
    "key", "liveness", "loudness", "mode", "speechiness", "tempo", "valence",
]


def spotify_id(row):
    for field in reversed(row):
        field = field.strip().strip('"')
        if re.fullmatch(r"[A-Za-z0-9]{22}", field):
            return field
    return ""


def fold(value):
    text = unicodedata.normalize("NFKC", value or "").replace("\xa0", " ")
    text = text.casefold()
    text = "".join(ch if ch.isalnum() else " " for ch in text)
    return " ".join(text.split())


def title_forms(value):
    raw = unicodedata.normalize("NFKC", value or "").replace("\xa0", " ")
    forms = set()

    def add(piece):
        folded = fold(piece)
        if folded:
            forms.add(folded)

    add(raw)
    add(re.sub(r"\([^)]*\)", " ", raw))
    for piece in re.findall(r"\(([^)]*)\)", raw):
        add(piece)
    for piece in re.split(r"\s[-–—/]\s", raw):
        add(piece)
    return forms


def artist_tokens(value):
    text = fold(value)
    text = re.sub(r"\b(feat|ft|featuring|and|with|vs|the)\b", " ", text)
    return {token for token in text.split() if len(token) > 1}


def load_catalog():
    with SONG_INFO.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))[1:]
    catalog = []
    by_form = defaultdict(list)
    for row in rows:
        track_id = spotify_id(row)
        title = row[1] if len(row) == 3 else " ".join(row[1:-1])
        item = {
            "id": track_id,
            "title": title.strip(),
            "artist": row[0].strip(),
            "forms": title_forms(title),
            "tokens": artist_tokens(row[0]),
        }
        index = len(catalog)
        catalog.append(item)
        for form in item["forms"]:
            by_form[form].append(index)
    return catalog, by_form


def load_entries():
    with ENTRIES.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def has_latin(value):
    return any("a" <= char <= "z" for char in fold(value))


def artist_ok(entry_artist, item):
    """Same recording: shared name tokens, a close spelling, or another script."""
    tokens = artist_tokens(entry_artist)
    if tokens & item["tokens"]:
        return True
    ratio = SequenceMatcher(None, fold(entry_artist), fold(item["artist"])).ratio()
    if ratio >= 0.72:
        return True
    return not has_latin(item["artist"]) or not has_latin(entry_artist)


def choose(candidates, entry):
    accepted = [item for item in candidates if artist_ok(entry["Artist"], item)]
    if len(accepted) == 1:
        return accepted[0]
    if len(accepted) < 2:
        return None
    tokens = artist_tokens(entry["Artist"])
    accepted.sort(key=lambda item: (-len(tokens & item["tokens"]), item["id"]))
    if len(tokens & accepted[0]["tokens"]) > len(tokens & accepted[1]["tokens"]):
        return accepted[0]
    return None


def match_entry(entry, catalog, by_form):
    forms = title_forms(entry["Song"])
    seen = set()
    candidates = []
    for form in forms:
        for index in by_form.get(form, []):
            if index not in seen:
                seen.add(index)
                candidates.append(catalog[index])
    chosen = choose(candidates, entry)
    if chosen:
        return chosen
    near = []
    for item in catalog:
        ratios = [
            SequenceMatcher(None, left, right).ratio()
            for left in forms
            for right in item["forms"]
            if min(len(left), len(right)) >= 6
        ]
        if ratios and max(ratios) >= 0.90 and artist_ok(entry["Artist"], item):
            near.append((max(ratios), item))
    near.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    if len(near) == 1 or (len(near) > 1 and near[0][0] > near[1][0] + 0.02):
        return near[0][1]
    return None


def parse_export_key(value):
    text = (value or "").replace("♯", "#").replace("♭", "b")
    parts = text.split()
    if len(parts) < 2:
        return "", ""
    note = parts[0].split("/")[0].casefold()
    mode = 1 if parts[-1].casefold().startswith("maj") else 0
    return PITCH.get(note, ""), mode


def load_export():
    """Older Spotify export. Its 0–100 scores are the same features, scaled."""
    with EXPORT.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_id = {}
    for row in rows:
        track_id = (row.get("Spotify Track Id") or "").strip()
        if not track_id:
            continue
        key, mode = parse_export_key(row.get("Key") or "")

        def scaled(name):
            raw = (row.get(name) or "").strip()
            return "" if raw == "" else float(raw) / 100

        by_id[track_id] = {
            "acousticness": scaled("Acoustic"),
            "danceability": scaled("Dance"),
            "energy": scaled("Energy"),
            "instrumentalness": scaled("Instrumental"),
            "key": key,
            "liveness": scaled("Live"),
            "loudness": (row.get("Loud (Db)") or "").strip(),
            "mode": mode,
            "speechiness": scaled("Speech"),
            "tempo": (row.get("BPM") or "").strip(),
            "valence": scaled("Happy"),
        }
    return by_id


def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "stl-analysis"})
    delay = 1
    for _ in range(6):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 429:
                time.sleep(int(error.headers.get("Retry-After") or delay))
                delay *= 2
                continue
            if error.code == 404:
                return None
            if error.code >= 500:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"gave up on {url}")


def resolve_ids(track_ids, cache):
    known = cache.setdefault("uuids", {})
    pending = [track_id for track_id in track_ids if track_id not in known]
    for start in range(0, len(pending), 20):
        batch = pending[start:start + 20]
        query = "&".join("ids=" + urllib.parse.quote(track_id) for track_id in batch)
        payload = get_json(f"{API}/track?{query}") or {"content": []}
        found = {}
        for item in payload.get("content", []):
            href = item.get("href") or ""
            spotify = href.rsplit("/", 1)[-1]
            if spotify in batch:
                found[spotify] = item["id"]
        for track_id in batch:
            known[track_id] = found.get(track_id)
        missing = [track_id for track_id in batch if track_id not in found]
        for track_id in missing:
            one = get_json(f"{API}/track?ids={urllib.parse.quote(track_id)}") or {"content": []}
            for item in one.get("content", []):
                href = item.get("href") or ""
                if href.rsplit("/", 1)[-1] == track_id:
                    known[track_id] = item["id"]
        print(f"resolved {min(start + 20, len(pending))}/{len(pending)}", flush=True)
        save_cache(cache)
    return known


def fetch_features(uuids, cache):
    features = cache.setdefault("features", {})
    pending = [uuid for uuid in uuids if uuid and uuid not in features]

    def one(uuid):
        payload = get_json(f"{API}/track/{uuid}/audio-features")
        return uuid, payload

    done = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(one, uuid) for uuid in pending]
        for future in as_completed(futures):
            uuid, payload = future.result()
            with CACHE_LOCK:
                features[uuid] = payload
            done += 1
            if done % 100 == 0 or done == len(pending):
                print(f"features {done}/{len(pending)}", flush=True)
                save_cache(cache)
    return features


CACHE_LOCK = threading.Lock()


def save_cache(cache):
    with CACHE_LOCK:
        text = json.dumps(cache)
    CACHE.write_text(text, encoding="utf-8")


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


# Edition number and folded song title. These are the pairs confirmed
# after the title review: every closest track that shares an artist name,
# plus the extra titles named by hand.
CONFIRMED = {
    ("1", "licht en donker"): "519hk8UnV4mPTc0Ph3avw7",
    ("2", "stargazing"): "5CLrEjpbnLl0cHaSBQprlC",
    ("2", "плакала plakala"): "2rbIlflPwepvyNgxreRMuR",
    ("2", "学猫叫 learn to meow"): "56y9Vdi0PWuDqjz6RQ2K93",
    ("3", "the 7th element"): "5iFhkFf9JLA3XiROdYsg1i",
    ("3", "été 90"): "1p9dxTMtG4gZpLp7yzvT54",
    ("4", "boliš me"): "0TPuCJR4bDNMAQOZxfH2fr",
    ("6", "talk to me"): "1aCcTh955i82DV6LEe0Igr",
    ("7", "margaashiin nar luu hamt ayalah uu"): "6HI8FvpS1zug6hRHyWFkem",
    ("7", "έγκλημα egklima"): "77dIQNvSUPMeLvEl603bDr",
    ("9", "04 15"): "0KilmlKbnfk8Xspi2Cwj9r",
    ("10", "jy kyk na my"): "1M7MysgN1UDqdoYb5W69BX",
    ("10", "любовь карусель lyobov karusel"): "0OxRfQ6StPkpULhbDXTwWQ",
    ("11", "tatuazh në zëmer"): "2sy7IUBFp7XaTeBbtnKXOy",
    ("12", "lozh navik"): "0RzzvgWCP2l819QVZ2FvbZ",
    ("12", "petit à petit"): "784v9YCbkyslPWRTpKAP9k",
    ("13", "vanilla"): "2llt0JXDa76xRbXvomRly5",
    ("13", "ξημερώματα ksimeromata"): "6MdI6aFcPIcBdRV6IZQjW2",
    ("15", "angel"): "6hGTOtfKYnhSGWNfyCNPw0",
    ("16", "the take off"): "0DmEHIFMk1bsEiAXKGq9ex",
    ("18", "frankfurt am main live"): "7Kpqjspw4Y7HrvItIRcBiW",
    ("18", "south sudanese music"): "7Kik2JtGRjdO5uSbnhfimf",
    ("21", "guld svett och tårar"): "2zGLGkAB3zesY32WR38F43",
    ("24", "petit à petit 2"): "784v9YCbkyslPWRTpKAP9k",
    ("25", "beribiam laike"): "368pHUv8e2hYaBNd5TSZrH",
    ("25", "la la la maltese folk"): "6iOndD4OFo7GkaDypWQIou",
    ("26", "2pa 2"): "1Vd3YqV8DYS1U3rsJads3H",
    ("27", "mom cœur"): "2uuHjWY6yqEkTZMftzTCzL",
    ("28", "dance the night away"): "11C4y2Yz1XbHmaQwO06s9f",
    ("28", "kriva sum"): "2llt0JXDa76xRbXvomRly5",
    ("28", "ramie w ramie"): "02RqhFaAYzWScfVzKfTZ7L",
    ("29", "braveheart"): "19kHhX6f6EfLU7rcO3RqjO",
    ("29", "ciunga cianga"): "5MfWnXRxtaQssMsWgH2Ely",
    ("29", "mashallah"): "69T9dnHt4G4YG8992R4rgY",
    ("29", "μάτια μου γλυκά mátia moy glyká"): "3vynlu1fYmNZQRqb0KubTI",
    ("32", "agonía"): "4uuyY7ENKhsKlO83KT4BFF",
    ("32", "cevapsiz çinlama"): "2W6XpjOKbmZ1NNVNtwBr5b",
    ("33", "alive"): "6WVUQmHBQ8Wn5Wfnsy2gJW",
    ("34", "κρυφτό kriftó"): "3YHFMGSXL84yodz8Jm4Phm",
    ("35", "maria parado de bellido"): "67kQIZGMAN0WruRBPz3RWC",
    ("36", "dă mă mamă după iura"): "1e27DsfBuV0ub4WivXL86B",
    ("37", "i like to move it"): "63Se4AtqR6HSdkfsMS3mDl",
    ("38", "čini"): "6TB6hxDXEgUtPRWq8LqeC7",
    ("38", "3ala bali على بالي"): "6Ne0DGBMgtmY1Maj3QAVIF",
    ("39", "bailar"): "45sGyAtAxD6efaN0bJAFgh",
    ("40", "resilient"): "4abn7Lc3illnEHFc9ki6x2",
    ("40", "slay"): "6aAclXBj0CK4EKkk0bU5Ra",
    ("41", "30 c"): "19DHPlTC2gx1j4jrFzNbwL",
    ("42", "më e fortë"): "34dYRKHYlvcFovNY6rpWzM",
    ("43", "σ αγαπάω γιατί"): "4AH6H9E36YcyVRhcxcP00x",
    ("44", "electric dreams"): "2J9yZBKajggHsCmoSiaVCw",
    ("44", "second heart"): "1sLV92W7VpuziBYvQMwRd5",
    ("45", "madame"): "6m6oaAugKIwqZpLhqtOXMX",
    ("46", "kalam eneih"): "6g95dK7o7vVh8ZCnDAseU5",
    ("48", "if only you knew"): "2w5iEdgKsFms9vAFq2n3Yy",
    ("49", "darlana"): "7CvgVJQSqfZUur2Q2Gkgps",
    ("49", "guess"): "38tKqQuqodiUYOsw6HWyeQ",
    ("49", "neințentionat"): "3K5VZfyDi1SvgTjhma4eq2",
    ("49", "treiterburen"): "5YYeOieVKYk5fH0dtqZvpp",
    ("49", "בדרך אל הים baderech el hayam"): "2hP9NafYxyCOztEUuVSeyR",
    ("51", "πεπρομένο pepromeno"): "1SZGNJFKmM7ZCfx6uDc7Yj",
    ("51", "空無之地 in between"): "2DL4gdIataq0FWEreuh8LP",
    ("53", "cowboy killer"): "2gNZ7vl4Leb6IQ1UUHMJKb",
    ("53", "the power"): "756YWkvx1EIVXT0ZO3F9PT",
    ("54", "kush mi qan"): "3dbvk5WNNWbFrbe52Deud3",
    ("55", "fenomenal"): "4CrtgDoRlrafpZxowRGwyN",
    ("55", "öwrenişdim indi"): "2v2SgVgnpkyAmHCcayFF98",
    ("56", "autrament"): "3SMtVY7EyN0tSYhAZl1AA7",
    ("60", "7 9 2013"): "4hI32tR0eb0hCIetaYQXYU",
    ("60", "holy war ii"): "4mhdCnaysDRwOZkgUbwDgN",
    ("60", "old afghan song"): "6v4ABPB255HDSWyIj3S9Wn",
    ("60", "החליפה האחרונה hachalifa ha afora"): "3lFRDa7pMB4QkNyJf3puIM",
    ("61", "fuck forever"): "3p0bCnkB373MOnqgMQhHf5",
    ("61", "wish you the worst"): "3bidbhpOYeV4knp8AIu8Xn",
    ("62", "babydoll"): "1UO7xiV3QaRfPXUpiVRsEp",
}


def main():
    catalog, by_form = load_catalog()
    entries = load_entries()
    cache = load_cache()
    ids = [item["id"] for item in catalog if item["id"]]
    uuids = resolve_ids(ids, cache)
    fetch_features([uuid for uuid in uuids.values() if uuid], cache)

    exported = load_export()
    header = [
        "Edition", "Code", "Head of Delegation", "Country", "Song", "Artist",
        "Spotify ID", *FEATURES, "Feature Source",
    ]
    matched = 0
    from_catalog = 0
    from_export = 0
    rows = []
    for entry in entries:
        item = match_entry(entry, catalog, by_form)
        track_id = item["id"] if item else ""
        if not track_id:
            track_id = CONFIRMED.get((entry["Edition"], fold(entry["Song"])), "")
        payload = None
        source = ""
        if track_id:
            matched += 1
            uuid = uuids.get(track_id)
            payload = cache["features"].get(uuid) if uuid else None
            if payload:
                from_catalog += 1
                source = "reccobeats"
            elif track_id in exported:
                payload = exported[track_id]
                from_export += 1
                source = "spotify export"
        row = [
            entry["Edition"], entry["Code"], entry["Head of Delegation"],
            entry["Country"], entry["Song"], entry["Artist"], track_id,
        ]
        for name in FEATURES:
            value = "" if not payload or payload.get(name) is None else payload[name]
            row.append(value)
        row.append(source)
        rows.append(row)

    with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\r\n")
        writer.writerow(header)
        writer.writerows(rows)
    unresolved = sum(1 for track_id in ids if not uuids.get(track_id))
    print(
        f"entries {len(entries)} matched {matched} "
        f"reccobeats {from_catalog} export {from_export} "
        f"spotify ids {len(ids)} unresolved {unresolved}"
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
