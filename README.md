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
- Optional speaker label formatting with brackets
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
- `--speaker-brackets` – prefix SRT lines with `[Speaker]`.
- `--skip-punctuation-only` – remove segments that contain only punctuation.

### As a Script
You can also run the script directly:
```bash
python aligner.py sample/transcription.json
```

### Sample Data
A sample transcription file is provided in the `sample/` directory. The file must include a `language_code` key. Both ISO 639-3 codes (e.g., `"deu"`) and ISO 639-1 codes (e.g., `"de"`) are accepted.

## How It Works
- **Initial Grouping:** Words are grouped by pauses and speaker changes.
- **Long Segment Splitting:** Any segment longer than 15 seconds is split at sentence boundaries using language-specific rules.
- **Acronym Handling:** Prevents sentence splits inside acronyms (e.g., B.M.W.).
- **Final Merging:** Segments are merged on sentence boundaries for natural output.

## Requirements
- Python 3.7+
- nltk==3.8.1

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

## Docker Usage
If using Docker, add this to your Dockerfile after installing dependencies:
```dockerfile
RUN python -m nltk.downloader punkt
```

## License
Copyright (c) 2025 TAC Labs. All rights reserved.
