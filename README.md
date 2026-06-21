# YouTube Video Collection Toolkit

A config-driven CLI for collecting, organizing, and reviewing YouTube videos for dataset building. Edit `project.yaml` and run the CLI.

## Setup

1. Create a virtual environment:

```bash
python -m venv env
```

2. Activate it and install dependencies:

```bash
# Windows
env\Scripts\activate

# macOS / Linux
source env/bin/activate

pip install -r requirements.txt
```

3. Install FFmpeg (required for video/audio merging) and ensure it is on PATH.

Runtime dependencies:
- FFmpeg must be installed and available on PATH for merges.
- A browser-supported cookies export is needed if YouTube requires sign-in. Visit [Cookies Setup Guide](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies).
- A JavaScript runtime (Deno or Node.js) may be required for yt-dlp JS challenges.

## Configuration

### Project Config (project.yaml)

Copy `project.example.yaml` to `project.yaml` and edit it to define your dataset and download behavior:

```yaml
project:
  name: "My Dataset"
  description: "Dataset description"
  keywords_file: "./keywords/keywords_en.yaml"  # Path to language-specific keywords file
  target_per_class: 200
  resolution: 720
  max_duration_seconds: 3600
  browser: chrome
  cookies_file: ""  # optional cookies.txt to avoid closing your browser
  # If true, yt-dlp will download video-only streams (no audio)
  video_only: false
  enable_remote_components: true
  sleep_interval: [10, 20]
  output_dir: "./data"
```

**Note:** Class names are automatically derived from the keywords file. You don't need to define a `classes` section.

### Keywords File (keywords/keywords_*.yaml)

Keywords are now stored in separate language files under the `keywords/` directory. The `keywords_file` setting in project.yaml points to the file to use.

**Available keyword files:**
- `keywords/keywords_en.yaml` — English keywords (default)
- `keywords/keywords_template.yaml` — Template for creating new language files

**Structure of keyword files:**
```yaml
Class_1:
  - "search keyword 1"
  - "search keyword 2"
  - "search keyword 3"

Class_2:
  - "search keyword 4"
  - "search keyword 5"
```

### Switching Languages

To use different language keywords:

1. Copy and rename a keywords file (e.g., `keywords_es.yaml` for Spanish)
2. Update the keywords in your language
3. Update `project.yaml`: `keywords_file: "./keywords/keywords_es.yaml"`
4. Run your collector — it automatically loads the new language keywords

See `keywords/keywords_template.yaml` for a starting template when creating new language files.

## Usage

```bash
python collect.py init
python collect.py download --class MyClass
python collect.py download --all
python collect.py status
python collect.py review
python collect.py dedup
python collect.py clean
```

If you are using this repo while it is under active development, pull updates periodically:

```bash
git pull
```

Optional flags:

```bash
python collect.py download --class MyClass --keyword "q"
python collect.py download --class MyClass --url "..."
python collect.py download --class MyClass --max-per-keyword 15
python collect.py download --class MyClass --no-cookies
python collect.py download --class MyClass --browser edge
```

## Review Tool

The review UI runs at `http://localhost:8765`:

- Click-to-play, so videos only stream on demand
- Pagination (20 per page)
- Keyboard shortcuts: `A` accept, `R` reject, `U` undo, `↑↓` navigate, `Space` play
- Filters by class and review status
