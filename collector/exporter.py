"""Export accepted videos (and matching metadata) to an external dataset folder."""

import os
import re
import csv
import shutil

VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".avi")
URL_ID_RE = re.compile(r"(?:[?&]v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{6,})")
YOUTUBE_ID_LENGTH = 11


def _video_id_from_filename(filename):
    """Extract the trailing yt-dlp video ID from a --restrict-filenames basename."""
    base = os.path.splitext(filename)[0]
    if len(base) > YOUTUBE_ID_LENGTH and base[-(YOUTUBE_ID_LENGTH + 1)] == "_":
        return base[-YOUTUBE_ID_LENGTH:]
    return None


def _video_id_from_url(url):
    match = URL_ID_RE.search(url or "")
    return match.group(1) if match else None


def _find_accepted_videos(output_dir):
    """Yield (class_name, language, full_path, filename) for every video under
    an _accepted/ folder anywhere under output_dir."""
    for cls_name in sorted(os.listdir(output_dir)):
        cls_path = os.path.join(output_dir, cls_name)
        if not os.path.isdir(cls_path):
            continue
        for root, dirs, files in os.walk(cls_path):
            if os.path.basename(root) != "_accepted":
                continue
            language = os.path.relpath(root, cls_path).split(os.sep)[0]
            if language == "Videos":
                print(
                    f"  [WARN] Skipping non-language-scoped _accepted/ folder: {root}"
                )
                continue
            for f in sorted(files):
                if f.lower().endswith(VIDEO_EXTS):
                    yield cls_name, language, os.path.join(root, f), f


def _render_bar(done, total, copied, skipped, label, bar_width=30):
    """Render a single-line, fixed-width progress bar, padded to the terminal width."""
    pct = int(done / total * 100) if total else 100
    filled = int(bar_width * done / total) if total else bar_width
    bar = "#" * filled + "-" * (bar_width - filled)

    term_width = shutil.get_terminal_size((100, 20)).columns
    prefix = f"  [{bar}] {pct:3d}% ({done}/{total}) copied:{copied} skipped:{skipped}  "
    room = max(10, term_width - len(prefix) - 1)
    if len(label) > room:
        label = "..." + label[-(room - 3) :]
    line = prefix + label
    return line.ljust(term_width - 1)[: term_width - 1]


def export_dataset(config, dest_dir):
    """Copy every accepted video into dest_dir/<Class>/<lang>/<file>, plus a
    filtered source_references.csv containing only the rows for copied videos.

    Returns {"copied": int, "skipped_existing": int, "per_class": {...}, "metadata_rows": int}.
    """
    output_dir = config["output_dir"]
    os.makedirs(dest_dir, exist_ok=True)

    items = list(_find_accepted_videos(output_dir))
    total = len(items)

    all_keys = (
        set()
    )  # (class_name, video_id) for every accepted video seen, copied or skipped
    per_class = {}
    skipped_existing = 0

    for idx, (cls_name, language, full_path, fname) in enumerate(items, 1):
        dest_class_dir = os.path.join(dest_dir, cls_name, language)
        os.makedirs(dest_class_dir, exist_ok=True)
        dest_path = os.path.join(dest_class_dir, fname)

        vid = _video_id_from_filename(fname)
        if vid:
            all_keys.add((cls_name, vid))

        if os.path.exists(dest_path):
            skipped_existing += 1
        else:
            shutil.copy2(full_path, dest_path)
            per_class[cls_name] = per_class.get(cls_name, 0) + 1

        label = f"{cls_name}/{language}/{fname}"
        print(
            "\r"
            + _render_bar(idx, total, sum(per_class.values()), skipped_existing, label),
            end="",
            flush=True,
        )

    if total:
        print()

    metadata_rows = _export_metadata(output_dir, dest_dir, all_keys)

    return {
        "copied": sum(per_class.values()),
        "skipped_existing": skipped_existing,
        "per_class": per_class,
        "metadata_rows": metadata_rows,
    }


def _export_metadata(output_dir, dest_dir, keys):
    """Append source_references.csv rows for every accepted video in `keys`,
    whether it was copied or already present this run. Rows are appended as-is
    on every run, so re-exporting will duplicate rows for videos seen before."""
    csv_path = os.path.join(output_dir, "source_references.csv")
    if not os.path.exists(csv_path) or not keys:
        return 0

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        matched_rows = [
            row
            for row in reader
            if (row.get("Class", ""), _video_id_from_url(row.get("Source_URL", "")))
            in keys
        ]

    dest_csv_path = os.path.join(dest_dir, "source_references.csv")
    write_header = not os.path.exists(dest_csv_path)
    with open(dest_csv_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(matched_rows)

    return len(matched_rows)
