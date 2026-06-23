"""
CSV reference logging and deduplication.
"""

import os
import csv
from datetime import datetime


CSV_HEADER = [
    "Class",
    "Source_URL",
    "Date_Accessed",
    "License",
    "Keyword",
    "Title",
    "Channel",
    "Duration",
]


def get_csv_path(config):
    """Return path to source_references.csv."""
    return os.path.join(config["output_dir"], "source_references.csv")


def get_decisions_path(config):
    """Return path to review_decisions.json."""
    return os.path.join(config["output_dir"], "review_decisions.json")


def log_entries(config, class_name, entries, keyword):
    """Log video metadata entries to the CSV."""
    csv_path = get_csv_path(config)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header if file is empty
        if os.path.getsize(csv_path) == 0:
            writer.writerow(CSV_HEADER)
        for entry in entries:
            url = entry.get("webpage_url") or entry.get("url", "")
            title = entry.get("title", "Unknown")
            channel = entry.get("channel", entry.get("uploader", "Unknown"))
            license_info = entry.get("license", "YouTube Standard")
            duration = entry.get("duration", 0)

            writer.writerow(
                [
                    class_name,
                    url,
                    datetime.now().strftime("%Y-%m-%d"),
                    license_info,
                    keyword,
                    title,
                    channel,
                    str(duration) if duration is not None else "",
                ]
            )


def count_videos(config, class_name, language=None):
    """Count video files on disk for a class, optionally filtered by language.
    If language is specified (e.g., 'en', 'zh'), counts only that language folder.
    """
    class_dir = os.path.join(config["output_dir"], class_name)
    count = 0

    if language:
        # Count videos in a specific language folder
        video_dir = os.path.join(class_dir, language, "Videos")
        if os.path.exists(video_dir):
            for root, dirs, files in os.walk(video_dir):
                dirs[:] = [d for d in dirs if d != "_rejected"]
                count += len(
                    [f for f in files if f.lower().endswith((".mp4", ".mkv", ".webm"))]
                )
    else:
        # Backward compat: count all videos in the class
        video_dir = os.path.join(class_dir, "Videos")
        if os.path.exists(video_dir):
            for root, dirs, files in os.walk(video_dir):
                dirs[:] = [d for d in dirs if d != "_rejected"]
                count += len(
                    [f for f in files if f.lower().endswith((".mp4", ".mkv", ".webm"))]
                )

    return count


def get_language_folders(config, class_name):
    """Return a sorted list of language folders present for a class."""
    class_dir = os.path.join(config["output_dir"], class_name)
    if not os.path.exists(class_dir):
        return []

    languages = []
    for item in sorted(os.listdir(class_dir)):
        item_path = os.path.join(class_dir, item)
        if os.path.isdir(item_path) and item not in {"Videos", "_rejected"}:
            # Check if it has a Videos subfolder
            video_path = os.path.join(item_path, "Videos")
            if os.path.exists(video_path):
                languages.append(item)

    return languages


def deduplicate(config):
    """Remove duplicate and fallback rows from the CSV. Returns stats."""
    csv_path = get_csv_path(config)
    if not os.path.exists(csv_path):
        return {"before": 0, "after": 0, "removed": 0}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    before = len(rows)

    # Remove fallback rows
    cleaned = [r for r in rows if not r["Source_URL"].startswith("YouTube search:")]

    # Deduplicate by URL
    seen = set()
    deduped = []
    for r in cleaned:
        url = r["Source_URL"]
        if url not in seen:
            seen.add(url)
            deduped.append(r)

    # Write back
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped)

    return {"before": before, "after": len(deduped), "removed": before - len(deduped)}


def get_progress(config):
    """Get download progress for all classes and languages.

    Returns nested dict: {class: {language: {count, target, pct}, ...}, ...}
    """
    target = config["target_per_class"]
    progress = {}
    # Derive class list from actual folders under output_dir. This avoids
    # relying on the keywords file to determine which classes exist on disk.
    out = config.get("output_dir", "./data")
    if not os.path.exists(out):
        return progress

    for name in sorted(os.listdir(out)):
        class_path = os.path.join(out, name)
        # Only consider directories that contain a Videos folder or look like a class dir
        videos_dir = os.path.join(class_path, "Videos")
        if not os.path.isdir(class_path):
            continue
        if not os.path.exists(videos_dir):
            # skip non-class dirs like metadata files
            # but allow directories which contain video files directly
            # (backwards compatibility)
            has_video_files = False
            for root, dirs, files in os.walk(class_path):
                for f in files:
                    if f.lower().endswith((".mp4", ".mkv", ".webm", ".avi")):
                        has_video_files = True
                        break
                if has_video_files:
                    break
            if not has_video_files:
                continue

        # Check for language folders
        languages = get_language_folders(config, name)

        if languages:
            # New structure: language subfolders
            progress[name] = {}
            for lang in languages:
                count = count_videos(config, name, language=lang)
                progress[name][lang] = {
                    "count": count,
                    "target": target,
                    "pct": min(100, round(count / target * 100)) if target > 0 else 0,
                }
        else:
            # Legacy: single Videos folder
            count = count_videos(config, name)
            progress[name] = {
                "count": count,
                "target": target,
                "pct": min(100, round(count / target * 100)) if target > 0 else 0,
            }

    return progress


def print_progress(config):
    """Print a formatted progress bar for all classes and languages."""
    progress = get_progress(config)
    target = config["target_per_class"]
    bar_width = 35

    print(f"\n{'='*75}")
    print(f"  {config['name']} - Collection Progress")
    print(f"{'='*75}")

    for cls_name, data in progress.items():
        # Check if this class has language subfolders
        if isinstance(data, dict) and any(
            isinstance(v, dict) and "count" in v for v in data.values()
        ):
            # Has language structure
            print(f"\n  {cls_name}:")
            for lang, lang_data in sorted(data.items()):
                if isinstance(lang_data, dict) and "count" in lang_data:
                    count = lang_data["count"]
                    pct = lang_data["pct"]
                    filled = (
                        min(bar_width, int(bar_width * count / target))
                        if target > 0
                        else 0
                    )
                    bar = "#" * filled + "-" * (bar_width - filled)
                    print(f"    {lang:4s}: {count:4d}/{target}  [{bar}] {pct:3d}%")
        else:
            # Legacy structure (single Videos folder)
            if isinstance(data, dict) and "count" in data:
                count = data["count"]
                pct = data["pct"]
                filled = (
                    min(bar_width, int(bar_width * count / target)) if target > 0 else 0
                )
                bar = "#" * filled + "-" * (bar_width - filled)
                print(f"  {cls_name:20s}: {count:4d}/{target}  [{bar}] {pct:3d}%")

    print()
