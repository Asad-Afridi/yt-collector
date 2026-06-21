"""
Config loader and validator for project.yaml.
"""

import os
import sys

import yaml


def load_config(config_path="project.yaml"):
    """Load and validate the project configuration.
    
    Classes are derived from the keywords file specified in project config.
    """
    if not os.path.exists(config_path):
        print(f"[ERROR] Config file not found: {config_path}")
        print("  Create a project.yaml or specify path with --config")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Validate required sections
    if "project" not in raw:
        print(f"[ERROR] Missing required section 'project' in {config_path}")
        sys.exit(1)

    proj = raw["project"]
    for field in ("name", "target_per_class", "resolution", "keywords_file"):
        if field not in proj:
            print(f"[ERROR] Missing 'project.{field}' in config")
            sys.exit(1)

    config = {
        "name": proj["name"],
        "description": proj.get("description", ""),
        "video_only": bool(proj.get("video_only", False)),
        "target_per_class": int(proj["target_per_class"]),
        "resolution": int(proj["resolution"]),
        "max_duration_seconds": int(proj.get("max_duration_seconds", 3600)),
        "browser": proj.get("browser", "chrome"),
        "cookies_file": proj.get("cookies_file", ""),
        "enable_remote_components": bool(proj.get("enable_remote_components", True)),
        "sleep_interval": proj.get("sleep_interval", [5, 15]),
        "output_dir": proj.get("output_dir", "./data"),
        "classes": {},
    }

    # Load external keywords file (now required)
    keywords_file = proj.get("keywords_file")
    config_dir = os.path.dirname(os.path.abspath(config_path))
    keywords_path = os.path.join(config_dir, keywords_file)
    
    if not os.path.exists(keywords_path):
        print(f"[ERROR] Keywords file not found: {keywords_path}")
        sys.exit(1)
    
    with open(keywords_path, "r", encoding="utf-8") as f:
        keywords_data = yaml.safe_load(f) or {}

    if not keywords_data:
        print(f"[ERROR] Keywords file is empty: {keywords_path}")
        sys.exit(1)

    # Build classes from keywords file
    for cls_name, kw_list in keywords_data.items():
        if not isinstance(kw_list, list):
            print(f"[ERROR] Keywords for class '{cls_name}' must be a list")
            sys.exit(1)
        
        config["classes"][cls_name] = {
            "description": "",  # No description in keywords file
            "keywords": kw_list,
        }

    return config


def get_class_names(config):
    """Return list of class names."""
    return list(config["classes"].keys())


def get_keywords(config, class_name):
    """Return flattened keyword list for a class."""
    return config["classes"][class_name]["keywords"]


def get_video_format(config):
    """Return yt-dlp format string for the configured resolution."""
    res = config["resolution"]
    # If video_only is set, prefer the best video-only stream at or below
    # the requested resolution. Otherwise request video+audio with fallback.
    if config.get("video_only"):
        return f"bestvideo[height<={res}]"
    return f"bestvideo[height<={res}]+bestaudio/best[height<={res}]"


def get_output_dir(config, class_name):
    """Return the output directory for a class."""
    return os.path.join(config["output_dir"], class_name, "Videos")
