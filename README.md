# Sentence-Segmentation-Aligner

A Python tool for segmenting and aligning sentences in transcriptions, with speaker and timing information. Built for production use with AWS Lambda deployment, pip installation, and support for Python 3.9-3.13.

## Features
- **Smart Segmentation**: Groups words into segments based on pauses and speaker changes
- **Sentence-Aware**: Merges segments on sentence boundaries using a lightweight regex tokenizer
- **Acronym Protection**: Prevents sentence splits inside acronyms (e.g., B.M.W., A.B.S.)
- **Duration Control**: Splits segments longer than configurable duration at the nearest sentence boundary
- **Multiple Output Formats**: Console output, SRT subtitles, JSON, and API-friendly string output
- **Multi-Language Support**: Wide range of source and target languages with ISO 639-1/639-3 codes
- **Configurable Parameters**: Pause length, minimum words per segment, max duration, and more
- **Speaker Formatting**: Optional speaker label formatting with brackets (e.g., `- [Speaker 1]`)
- **Punctuation Handling**: Merges punctuation-only segments for cleaner output
- **Zero Dependencies**: Core functionality uses only Python standard library
- **AWS Lambda Ready**: Serverless deployment with enhanced regex compatibility
- **Production Ready**: Supports Python 3.9-3.13 with CI/CD testing
- **Pip Installable**: Available as a proper Python package with optional extras

## Installation

### Prerequisites
- Python 3.9+ (tested on Python 3.9-3.13)
- pip (package installer for Python)

### Option 1: Pip Installation (Recommended)
```bash
# Standard installation (zero dependencies)
pip install sentence-segmentation-aligner

# With AWS Lambda extras (enhanced regex compatibility)
pip install sentence-segmentation-aligner[lambda]

# Development installation with testing tools
pip install sentence-segmentation-aligner[dev]

# All optional dependencies
pip install sentence-segmentation-aligner[all]
```

### Option 2: Development Installation
```bash
# Clone the repository
git clone https://github.com/The-Africa-Channel/Sentence-Segmentation-Aligner.git
cd Sentence-Segmentation-Aligner

# Install in editable mode
pip install -e .

# Or with development dependencies
pip install -e .[dev]
```

### Option 3: Direct Usage
```bash
# Clone and run directly
git clone https://github.com/The-Africa-Channel/Sentence-Segmentation-Aligner.git
cd Sentence-Segmentation-Aligner
python aligner.py sample/transcription.json
```

### Installation Extras

- **`[lambda]`**: Includes `regex` package for enhanced compatibility in AWS Lambda environments
- **`[dev]`**: Includes testing dependencies (`pytest`, `unittest`)
- **`[all]`**: Includes all optional dependencies

## Usage

### Command Line
After installation, run the aligner on a transcription JSON file:
```bash
aligner sample/transcription.json
```

Key options:

- `--big-pause-seconds` – pause length that starts a new segment.
- `--min-words-in-segment` – minimum number of words in a segment. If the last segment is shorter than this, it will be merged with the previous segment. This helps avoid very short, unnatural segments at the end of the output.
- `--speaker-brackets` – prefix lines with `- [Speaker]` (e.g., `- [speaker_1]`).
- `--fix-orphaned-punctuation` – merge segments that contain only punctuation (e.g., '.', '!', '?') into the previous segment. This is enabled by default and results in cleaner, more natural output by ensuring punctuation is attached to the preceding words rather than appearing as a separate segment.
- `--max-duration` – maximum allowed segment duration in seconds before splitting at a sentence boundary. Segments longer than this will be split at the nearest sentence boundary. Default: 15.0.

### As a Script
You can also run the script directly:
```bash
python aligner.py sample/transcription.json
```

### Sample Data
A sample transcription file is provided in the `sample/` directory. The file must include a `language_code` key. Both ISO 639-3 codes (e.g., `"deu"`) and ISO 639-1 codes (e.g., `"de"`) are accepted.

### Sample Transcription JSON Format

The aligner expects a JSON file with a structure similar to the ElevenLabs transcription output. Here is a realistic example (truncated for brevity):

```json
{
  "language_code": "deu",
  "language_probability": 0.998885989189148,
  "text": "Nahezu alle Modelle der Marken BMW und BMW M stehen zur Verfügung. ...",
  "words": [
    {"text": "Nahezu", "start": 0.359, "end": 0.779, "speaker_id": "speaker_0"},
    {"text": "alle", "start": 0.839, "end": 1.039, "speaker_id": "speaker_0"},
    {"text": "Modelle", "start": 1.079, "end": 1.519, "speaker_id": "speaker_0"},
    {"text": "der", "start": 1.519, "end": 1.659, "speaker_id": "speaker_0"},
    {"text": "Marken", "start": 1.719, "end": 2.019, "speaker_id": "speaker_0"},
    {"text": "B.M.W.", "start": 2.099, "end": 2.619, "speaker_id": "speaker_0"},
    {"text": "und", "start": 2.659, "end": 2.839, "speaker_id": "speaker_0"},
    // ... more word objects ...
  ]
}
```

- `language_code`: (string) ISO 639-1 or 639-3 code for the language.
- `language_probability`: (float, optional) Confidence score for language detection.
- `text`: (string) The full transcript as a single string.
- `words`: (list) Each word is a dictionary with:
  - `text`: (string) The word or punctuation.
  - `start`: (float) Start time in seconds.
  - `end`: (float) End time in seconds.
  - `speaker_id`: (string) Speaker label or ID.

This format matches the output of ElevenLabs and similar transcription APIs. The aligner requires all four fields for each word in the `words` list.

### Output Format

When using the `--speaker-brackets` option, each segment will be printed as:

```
Segment N: - [speaker_X] (start-end)
text...
```

This preserves the speaker label in brackets as in the JSON, with a hyphen at the front.

### Example SRT Output

When you generate an SRT file using the aligner, the output will look like this:

```
1
00:00:00,359 --> 00:00:08,698
- [speaker_0] Nahezu alle Modelle der Marken B.M.W. und B.M.W. M stehen zur Verfügung. Vom 2er bis hin zum M High-Performance-Modell.

2
00:00:12,319 --> 00:00:14,679
- [speaker_0] Los geht's auf einem kleinen Rundkurs.

3
00:00:15,898 --> 00:00:17,940
- [speaker_0] Was ist der erste Eindruck des Profis?

4
00:00:23,699 --> 00:00:32,139
- [speaker_1] Wenn ich jetzt nicht wüsste, dass es ein Turbomotor ist, hat er für mich eigentlich die Eigenschaften wie ein Saugmotor.

5
00:00:32,478 --> 00:00:36,639
- [speaker_1] Sprich, je mehr Drehzahler, desto mehr Leistung gibt er frei.

6
00:00:37,179 --> 00:00:41,158
- [speaker_1] Von dem her hätte ich erwartet, dass er unter raus ein bisschen spritziger ist.

7
00:00:41,200 --> 00:00:45,459
- [speaker_1] Wenn ich das mit meinem1er M Coupé vergleiche, der ist unter raus doch viel früher da.
```

Each segment includes the segment number, start and end timestamps, and the speaker label with a hyphen prefix, followed by the segment text.

### Python Example: SRT Generation

You can generate an SRT file using the Python API as follows:

```python
from aligner import segment_transcription, save_segments_as_srt, get_grouped_segments
import os
import json

SAMPLE_JSON = os.path.join(os.path.dirname(__file__), "sample", "transcription.json")
SRT_PATH = os.path.join(os.path.dirname(__file__), "sample", "transcription.srt")

# Segment the transcription (flat output for printing)
segments = segment_transcription(
    SAMPLE_JSON,
    speaker_brackets=True,
    max_duration=15.0,
    big_pause_seconds=0.75,
    min_words_in_segment=2,
)

# Print segments (optional)
for i, seg in enumerate(segments, 1):
    print(f"Segment {i}: {seg['speaker']} ({seg['start']:.2f}-{seg['end']:.2f})\n{seg['text']}\n")

# For SRT, re-segment as list of lists of word dicts
with open(SAMPLE_JSON, "r", encoding="utf-8") as f:
    words = json.load(f)["words"]
segments_for_srt = get_grouped_segments(
    words,
    max_duration=15.0,
    big_pause_seconds=0.75,
    min_words_in_segment=2,
)
save_segments_as_srt(segments_for_srt, SRT_PATH, speaker_brackets=True)
print(f"SRT file saved to: {SRT_PATH}")
```

This will create an SRT file with the format shown above.

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
    max_duration=10.0,  # Example: set duration to size of segment that it will find a breakpoint in punctuation. 
    language_code="en",
    speaker_brackets=True,
    # fix_orphaned_punctuation is True by default
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

## AWS Lambda Deployment

This package is designed for AWS Lambda deployment with enhanced serverless compatibility. The core package has zero dependencies and uses the Python standard library for maximum compatibility.

### Quick Lambda Setup

1. **Install with Lambda extras:**
   ```bash
   pip install sentence-segmentation-aligner[lambda]
   ```

2. **Use the provided Lambda function template:**
   ```python
   from aligner import segment_transcription, save_segments_as_srt, get_grouped_segments
   import json
   
   def lambda_handler(event, context):
       try:
           # Extract transcription from event
           transcription = event.get('transcription')
           output_format = event.get('format', 'segments')  # 'segments', 'srt', 'grouped'
           
           # Segment the transcription
           segments = segment_transcription(
               transcription,
               big_pause_seconds=event.get('big_pause_seconds', 0.75),
               min_words_in_segment=event.get('min_words_in_segment', 2),
               max_duration=event.get('max_duration', 15.0),
               speaker_brackets=event.get('speaker_brackets', True)
           )
           
           if output_format == 'srt':
               # Generate SRT string for API response
               grouped_segments = get_grouped_segments(
                   transcription['words'],
                   max_duration=event.get('max_duration', 15.0),
                   big_pause_seconds=event.get('big_pause_seconds', 0.75),
                   min_words_in_segment=event.get('min_words_in_segment', 2)
               )
               srt_content = save_segments_as_srt(
                   grouped_segments, 
                   speaker_brackets=event.get('speaker_brackets', True),
                   return_string=True
               )
               return {
                   'statusCode': 200,
                   'body': json.dumps({
                       'format': 'srt',
                       'content': srt_content,
                       'segment_count': len(grouped_segments)
                   })
               }
           
           return {
               'statusCode': 200,
               'body': json.dumps({
                   'format': output_format,
                   'segments': segments,
                   'segment_count': len(segments)
               })
           }
           
       except Exception as e:
           return {
               'statusCode': 400,
               'body': json.dumps({'error': str(e)})
           }
   ```

3. **For detailed deployment instructions, see [LAMBDA_DEPLOYMENT.md](LAMBDA_DEPLOYMENT.md)**

### Lambda Features

- **Zero Dependencies**: Core functionality works without external packages
- **Enhanced Regex**: Automatic fallback to `regex` package if standard `re` module limitations are encountered
- **String Output**: `save_segments_as_srt()` supports `return_string=True` for API responses
- **Error Handling**: Comprehensive error handling for serverless environments
- **Small Package Size**: Minimal footprint for fast Lambda cold starts

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
| `segment_transcription(transcription, big_pause_seconds=0.75, min_words_in_segment=2, max_duration=15.0, language_code=None, speaker_brackets=False, skip_punctuation_only=False)` | `transcription: Union[str, Dict]` | `List[Dict]` |
| `save_segments_as_srt(segments, filepath=None, speaker_brackets=False, speaker_map=None, return_string=False)` | `segments: List[List[Dict]]` | `None or str` |

#### Parameter Details

- **min_words_in_segment**: Controls the minimum number of words required in each segment. If the last segment after grouping is shorter than this value, it will be merged with the previous segment. This prevents the output from ending with a fragment or a single word.
- **fix_orphaned_punctuation / merge_punctuation_only_segments**: If enabled (default), any segment that contains only punctuation marks (such as '.', '!', '?', etc.) will be merged with the previous segment. This is useful for producing cleaner output, especially when punctuation tokens are separated from words in the input. This behavior is now the default.
- **max_duration**: Controls the maximum allowed segment duration in seconds. If a segment is longer than this value, it will be split at the nearest sentence boundary. Default is 15.0 seconds.
- **return_string**: (save_segments_as_srt only) When True, returns the SRT content as a string instead of writing to a file. Useful for API responses and Lambda functions.
- **language_code**: ISO 639-1 or 639-3 language code for sentence boundary detection. Automatically detected from transcription if not provided.

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
- Python 3.9+ (tested on Python 3.9, 3.10, 3.11, 3.12, 3.13)
- Zero required dependencies (uses Python standard library)
- Optional: `regex` package for enhanced Lambda compatibility
- Tested on Linux, macOS, and Windows

## Continuous Integration
This project uses GitHub Actions for automated testing across multiple Python versions:
- **Python Versions**: 3.9, 3.10, 3.11, 3.12, 3.13
- **Test Coverage**: Standard functionality and AWS Lambda compatibility
- **Platforms**: Linux (Ubuntu latest)

See [`.github/workflows/test.yml`](.github/workflows/test.yml) for the full CI configuration.

## Development

### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test files
python -m unittest test_aligner.py
python -m unittest test_lambda_compatibility.py

# Run with coverage
pytest --cov=aligner
```

### Running the Sample
```bash
python run_sample.py
```

### Testing Lambda Compatibility
```bash
# Test Lambda-specific functionality
python test_lambda_compatibility.py
```

### Adding Dependencies
- For core functionality: Update both `requirements.txt` and `setup.py`
- For optional extras: Update `setup.py` extras_require section
- Maintain zero-dependency core for maximum compatibility

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
If using Docker, simply copy the project files and install the package:
```dockerfile
RUN pip install -e .
```

### Deployment Notes

This project supports Python 3.9+ and is tested across all versions from 3.9 to 3.13. The core functionality has zero dependencies and uses only the Python standard library for maximum compatibility.

**Key Compatibility Features:**
- **Zero Dependencies**: Core functionality works with standard library only
- **Enhanced Regex**: Automatic fallback to `regex` package for complex patterns in Lambda environments
- **Cross-Platform**: Tested on Linux, macOS, and Windows
- **Serverless Ready**: Optimized for AWS Lambda with small package size and fast cold starts

**Production Deployment:**
- Use `pip install sentence-segmentation-aligner` for standard deployments
- Use `pip install sentence-segmentation-aligner[lambda]` for AWS Lambda
- Docker deployments work with any Python 3.9+ base image

### Versioning

This project follows [semantic versioning](https://semver.org). Public
functions, including `segment_transcription`, may change only in a new major
version. Consult the changelog for details when upgrading.

## Additional Documentation

- **[LAMBDA_DEPLOYMENT.md](LAMBDA_DEPLOYMENT.md)**: Comprehensive AWS Lambda deployment guide with step-by-step instructions, deployment packages, and troubleshooting
- **[UPDATE_SUMMARY.md](UPDATE_SUMMARY.md)**: Detailed summary of recent improvements and enhancements to the project

## License
Copyright (c) 2025 TAC Labs. All rights reserved.
