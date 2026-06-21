# Keywords Directory

This directory contains language-specific keyword files for the dataset collection toolkit.

## Files

- **keywords_en.yaml** — English keywords for all dataset classes (currently in use by default)
- **keywords_template.yaml** — Template for creating new language keyword files

## Structure

Each keyword file is a YAML file mapping class names to lists of search keywords. **The class names you define here become the available dataset classes** — no need to define them elsewhere.

```yaml
Class_Name:
  - "search keyword 1"
  - "search keyword 2"
  - "search keyword 3"

Another_Class:
  - "different keyword 1"
  - "different keyword 2"
```

## Creating a New Language File

1. **Copy the template:**
   ```bash
   cp keywords_template.yaml keywords_es.yaml  # For Spanish, for example
   ```

2. **Translate the keywords** to your target language in the new file.
   - Class names (the top-level keys) can stay the same or be translated.
   - Keywords (the list items) should be translated for the target language.

3. **Update project.yaml** to point to the new language file:
   ```yaml
   project:
     keywords_file: "./keywords/keywords_es.yaml"
   ```

4. **Run the collector** — it will automatically load keywords from the new file:
   ```bash
   python collect.py download --class ClassName
   ```

## Notes

- Keywords should be simple search phrases (no special characters that break YouTube search)
- Use ASCII-only characters to avoid encoding issues
- Each keyword is searched independently, so be specific
- More keywords = more search results to filter through, but better coverage
- Keep keywords focused on the class definition to improve video relevance

## Adding More Languages

Just create a new file like `keywords_fr.yaml` for French, `keywords_de.yaml` for German, etc., and update `project.yaml` to switch between them.
