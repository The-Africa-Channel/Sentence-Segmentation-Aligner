# Sentence-Segmentation-Aligner

A Python tool for segmenting and aligning sentences in transcriptions, with speaker and timing information. Supports multiple languages and robust handling of acronyms and long segments.

## Features
- Groups words into segments based on pauses and speaker changes
- Merges segments on sentence boundaries using NLTK, with language-specific rules
- Prevents sentence splits inside acronyms (e.g., B.M.W., A.B.S.)
- Splits any segment longer than 15 seconds at the nearest sentence boundary
- Prints segments with speaker, start/end time, and text
- Supports a wide range of source and target languages
- Configurable pause length and minimum words per segment
- Optional speaker label formatting with brackets and a hyphen (e.g., `- [speaker_1]`)
- Ability to skip punctuation-only segments

## Supported Languages

**Source Languages:**
- English, Spanish, Portuguese, French, German, Italian, Dutch, Mandarin, Korean, Arabic, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Punjabi, Malayalam, Urdu

**Target Languages:**
- English, Spanish, Portuguese, French, German, Italian, Dutch, Mandarin, Korean, Arabic, Hindi, Tamil

## Installation

1. Clone this repository or download the source code.
2. (Recommended) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install the package in editable mode:
   ```bash
   pip install -e .
   ```
4. Install NLTK data (for Docker, add this to your Dockerfile; for local, run manually):
   ```bash
   python -m nltk.downloader punkt
   ```

## Usage

### Command Line
After installation, run the aligner on a transcription JSON file:
```bash
aligner sample/transcription.json
```

Key options:

- `--big-pause-seconds` – pause length that starts a new segment.
- `--min-words-in-segment` – minimum number of words in a segment.
- `--speaker-brackets` – prefix lines with `- [Speaker]` (e.g., `- [speaker_1]`).
- `--skip-punctuation-only` – remove segments that contain only punctuation.

### As a Script
You can also run the script directly:
```bash
python aligner.py sample/transcription.json
```

### Sample Data
A sample transcription file is provided in the `sample/` directory. The file must include a `language_code` key. Both ISO 639-3 codes (e.g., `"deu"`) and ISO 639-1 codes (e.g., `"de"`) are accepted.

### Output Format

When using the `--speaker-brackets` option, each segment will be printed as:

```
Segment N: - [speaker_X] (start-end)
text...
```

This preserves the speaker label in brackets as in the JSON, with a hyphen at the front.

### Python API Usage

You can also use the aligner directly from Python. Import
`segment_transcription` and pass either a transcription dictionary or the path
to the JSON file:

```python
from aligner import segment_transcription

segments = segment_transcription(
    "sample/transcription.json",
    big_pause_seconds=1.0,
    min_words_in_segment=3,
    language_code="en",
    speaker_brackets=True,
    skip_punctuation_only=True,
)
```

Each item in `segments` is a dictionary containing at minimum:

- `speaker` – label of the speaker (string). If `speaker_brackets=True`, the
  value is returned in the form `- [speaker_X]`.
- `start` – segment start time in seconds (float)
- `end` – segment end time in seconds (float)
- `text` – transcribed text for the segment (string)

The function returns a `List[Dict]` with these keys. Optional metadata such as a
segment index is not included but can be derived when iterating over the list.

`segment_transcription` raises `ValueError` if the input transcription is
missing required fields.

### Function Reference

| Function | Parameters | Returns |
| --- | --- | --- |
| `normalize_language_code(code)` | `code: str` | `str` |
| `initial_grouping(words, big_pause_seconds=0.75, min_words_in_segment=2)` | `words: List[Dict]` | `List[List[Dict]]` |
| `merge_on_sentence_boundary(segments, language_code='eng')` | `segments: List[List[Dict]]` | `List[List[Dict]]` |
| `split_long_segments_on_sentence(segments, max_duration=15.0, language_code='eng')` | `segments: List[List[Dict]]` | `List[List[Dict]]` |
| `remove_punctuation_only_segments(segments)` | `segments: List[List[Dict]]` | `List[List[Dict]]` |
| `load_json(file_path)` | `file_path: str` | `Dict` |
| `print_segments(segments, speaker_brackets=False, speaker_map=None)` | `segments: List[List[Dict]]` | `None` |
| `get_grouped_segments(words, language_code='eng', max_duration=15.0, big_pause_seconds=0.75, min_words_in_segment=2, skip_punctuation_only=False)` | `words: List[Dict]` | `List[List[Dict]]` |
| `segment_transcription(transcription, big_pause_seconds=0.75, min_words_in_segment=2, language_code=None, speaker_brackets=False, skip_punctuation_only=False)` | `transcription: Union[str, Dict]` | `List[Dict]` |
| `save_segments_as_srt(segments, filepath, speaker_brackets=False, speaker_map=None)` | `segments: List[List[Dict]]` | `None` |

### Extensibility

Custom sentence boundary rules or acronym handling can be achieved by
overriding `merge_on_sentence_boundary` or
`split_long_segments_on_sentence` and providing your own tokenizer or regular
expression. This allows adapting the aligner to specialized languages or
domain-specific abbreviations.

## How It Works
- **Initial Grouping:** Words are grouped by pauses and speaker changes.
- **Long Segment Splitting:** Any segment longer than 15 seconds is split at sentence boundaries using language-specific rules.
- **Acronym Handling:** Prevents sentence splits inside acronyms (e.g., B.M.W.).
- **Final Merging:** Segments are merged on sentence boundaries for natural output.

## Requirements
- Python 3.7+
- nltk==3.8.1
- NLTK requires the `punkt` tokenizer data (`python -m nltk.downloader punkt`).
- Tested on Linux and macOS with Python 3.7+. On minimal Docker images install
  build tools (e.g., `build-essential`) so that NLTK can compile its optional
  dependencies.

## Development
- To run the sample:
  ```bash
  python run_sample.py
  ```
- To run unit tests:
  ```bash
  python -m unittest test_aligner.py
  # or
  pytest
  ```
- To add dependencies, update `requirements.txt` and `setup.py`.

### Example Unit Test

You can test the API directly in your own unit tests:

```python
from aligner import segment_transcription

def test_segment_api():
    words = [
        {"text": "Hello", "start": 0.0, "end": 0.5, "speaker_id": "A"},
        {"text": "world", "start": 0.6, "end": 1.0, "speaker_id": "A"},
    ]
    segments = segment_transcription({"words": words})
    assert segments[0]["text"] == "Hello world"
```

## Docker Usage
If using Docker, add this to your Dockerfile after installing dependencies:
```dockerfile
RUN python -m nltk.downloader punkt
```

### Deployment Notes

The project supports Python 3.7 and above. Ensure the operating system has the
standard C++ runtime available (e.g., `libstdc++6` on Debian/Ubuntu). All tests
are run on Linux containers, but the code should work on any OS where NLTK can
be installed.

### Versioning

This project follows [semantic versioning](https://semver.org). Public
functions, including `segment_transcription`, may change only in a new major
version. Consult the changelog for details when upgrading.

## License
Copyright (c) 2025 TAC Labs. All rights reserved.
