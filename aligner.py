import json
import re
from typing import List, Dict, Union, Optional


# Constants
BIG_PAUSE_SECONDS = 2.0
MIN_WORDS_IN_SEGMENT = 2

# Basic sentence tokenizer to avoid heavy dependencies
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+")


def simple_sentence_tokenize(text: str) -> List[str]:
    """Lightweight sentence tokenizer using regex."""
    sentences = SENTENCE_SPLIT_RE.split(text)
    return [s.strip() for s in sentences if s.strip()]


# Map ISO 639-1 codes to ISO 639-3 for convenience
ISO1_TO_ISO3 = {
    "en": "eng",
    "es": "spa",
    "pt": "por",
    "fr": "fra",
    "de": "deu",
    "it": "ita",
    "nl": "nld",
    "zh": "cmn",
    "ko": "kor",
    "ar": "ara",
    "hi": "hin",
    "bn": "ben",
    "ta": "tam",
    "te": "tel",
    "mr": "mar",
    "gu": "guj",
    "kn": "kan",
    "pa": "pan",
    "ml": "mal",
    "ur": "urd",
}


def normalize_language_code(code: str) -> str:
    """
    Normalize a language code to ISO 639-3 format.

    Args:
        code: A 2-letter (ISO 639-1) or 3-letter (ISO 639-3) language code.

    Returns:
        The corresponding 3-letter ISO 639-3 code, or 'eng' if not recognized.
    """
    if not code:
        return "eng"
    code = code.lower()
    if len(code) == 2:
        return ISO1_TO_ISO3.get(code, "eng")
    return code


def initial_grouping(
    words: List[Dict],
    big_pause_seconds: float = BIG_PAUSE_SECONDS,
    min_words_in_segment: int = MIN_WORDS_IN_SEGMENT,
) -> List[List[Dict]]:
    """
    Group words into segments based on pauses and speaker changes.

    Args:
        words: List of word dicts, each with 'text', 'start', 'end', and 'speaker_id'.
        big_pause_seconds: Pause (in seconds) that triggers a new segment if exceeded between words.
        min_words_in_segment: Minimum number of words in a segment; if the last segment is too short, it is merged with the previous one.

    Returns:
        List of segments, where each segment is a list of word dicts.
    """

    segments = []
    if not words:
        return segments
    current_segment = [words[0]]
    current_speaker = words[0].get("speaker_id", "speaker_0")

    for word in words[1:]:
        word_speaker = word.get("speaker_id", "speaker_0")
        time_gap = word["start"] - current_segment[-1]["end"]

        # FIXED: Speaker change ALWAYS triggers new segment, regardless of timing
        if word_speaker != current_speaker:
            segments.append(current_segment)
            current_segment = [word]
            current_speaker = word_speaker
        # Only check temporal proximity for SAME speaker
        elif time_gap > big_pause_seconds:
            segments.append(current_segment)
            current_segment = [word]
        else:
            current_segment.append(word)

    segments.append(current_segment)

    # Ensure no segments are too short, but don't merge different speakers
    if len(segments[-1]) < min_words_in_segment and len(segments) > 1:
        # Only merge if speakers are the same
        last_speaker = segments[-1][0].get("speaker_id", "speaker_0")
        prev_speaker = segments[-2][-1].get("speaker_id", "speaker_0")
        if last_speaker == prev_speaker:
            segments[-2].extend(segments.pop())

    return segments


def merge_on_sentence_boundary(
    segments: List[List[Dict]], language_code: str = "eng"
) -> List[List[Dict]]:
    """
    Merge segments on sentence boundaries using simple tokenization.
    Handles acronyms and abbreviations to avoid incorrect splits.
    CRITICAL: Never merge segments from different speakers.
    CRITICAL: Never merge segments that were separated by big pauses.

    Args:
        segments: List of segments (each a list of word dicts).
        language_code: ISO 639-3 language code for language-specific abbreviations.

    Returns:
        List of merged segments split at sentence boundaries.
    """
    import re
    import string

    merged_segments: List[List[Dict]] = []
    
    # Process each segment independently - don't merge across big pause boundaries
    for segment in segments:
        if not segment:
            continue
            
        # Each segment from initial_grouping should be processed independently
        # This preserves big pause separations while still handling sentence boundaries within segments
        text = " ".join(w["text"] for w in segment)
        
        # Patterns and placeholders for acronym/abbreviation handling
        acronym_pattern = re.compile(r"((?:[A-ZÄÖÜ]\.){2,})", re.UNICODE)
        ACRONYM_PLACEHOLDER = "__ACRONYM__"

        # Language-specific abbreviation lists
        ABBR_LISTS = {
            "eng": ["Mr", "Mrs", "Ms", "Dr", "Prof", "Sr", "Jr", "etc"],
            "spa": ["Sr", "Sra", "Srta", "Dr", "Lic", "Ing", "etc"],
            "fra": ["M", "Mme", "Mlle", "Dr", "Pr", "Me", "etc"],
            "deu": ["Hr", "Fr", "Dr", "Prof", "etc", "bzw", "z. B"],
            "ita": ["Sig", r"Sig\.ra", r"Sig\.na", "Dott", "Prof", "Avv", "etc"],
            "por": ["Sr", "Sra", "Dout", "Prof", "Dr", "etc"],
        }
        abbrs = ABBR_LISTS.get(language_code, ABBR_LISTS["eng"])
        abbr_pattern = re.compile(
            r"\b(?:" + "|".join(re.escape(a) for a in abbrs) + r")\.", re.UNICODE
        )
        ABBR_PLACEHOLDER = "__ABBR__"

        def replace_acronyms(text: str) -> str:
            return acronym_pattern.sub(
                lambda m: m.group(1).replace(".", ACRONYM_PLACEHOLDER), text
            )

        def replace_abbrs(text: str) -> str:
            return abbr_pattern.sub(
                lambda m: m.group(0).replace(".", ABBR_PLACEHOLDER), text
            )

        def restore_placeholders(text: str) -> str:
            return text.replace(ACRONYM_PLACEHOLDER, ".").replace(ABBR_PLACEHOLDER, ".")

        # Protect acronyms and abbreviations, then tokenize
        safe = replace_abbrs(replace_acronyms(text))
        sentences = simple_sentence_tokenize(safe)
        sentences = [restore_placeholders(s) for s in sentences]

        # If this segment contains multiple sentences, split it
        if len(sentences) > 1:
            word_iter = iter(segment)
            sentence_idx = 0
            
            for sentence in sentences:
                current_words = []
                current_text = ""
                
                # Collect words for this sentence
                for word in word_iter:
                    if current_text and word["text"] not in string.punctuation:
                        current_text += " "
                    current_text += word["text"]
                    current_words.append(word)
                    
                    # Check if we've completed this sentence
                    if replace_abbrs(replace_acronyms(current_text.strip())) == sentence.strip():
                        merged_segments.append(current_words)
                        current_text = ""
                        current_words = []
                        break
                
                # Handle any remaining words in the last sentence
                if current_words:
                    merged_segments.append(current_words)
        else:
            # Single sentence or incomplete sentence - keep as is
            merged_segments.append(segment)

    return merged_segments


def split_long_segments_on_sentence(
    segments: List[List[Dict]], max_duration: float = 60.0, language_code: str = "eng"
) -> List[List[Dict]]:
    """
    Split any segment longer than max_duration at the nearest sentence boundary.
    Handles acronyms to avoid incorrect sentence splits.

    Args:
        segments: List of segments (each a list of word dicts).
        max_duration: Maximum allowed segment duration in seconds.
        language_code: ISO 639-3 language code for sentence tokenization.

    Returns:
        List of segments, split so that no segment exceeds max_duration.
    """
    import string
    import re

    # Use the same acronym handling as merge_on_sentence_boundary
    acronym_pattern = re.compile(r"((?:[A-ZÄÖÜ]\.){2,})", re.UNICODE)
    ACRONYM_PLACEHOLDER = "__ACRONYM__"

    def replace_acronyms(text):
        return acronym_pattern.sub(
            lambda m: m.group(1).replace(".", ACRONYM_PLACEHOLDER), text
        )

    def restore_acronyms(text):
        return text.replace(ACRONYM_PLACEHOLDER, ".")

    new_segments = []
    for segment in segments:
        start = segment[0]["start"]
        end = segment[-1]["end"]
        duration = end - start
        if duration <= max_duration:
            new_segments.append(segment)
            continue
        # Split at sentence boundaries
        texts = " ".join([w["text"] for w in segment])
        safe_texts = replace_acronyms(texts)
        sentences = simple_sentence_tokenize(safe_texts)
        sentences = [restore_acronyms(s) for s in sentences]
        # Now, walk through words and split at sentence boundaries
        word_iter = iter(segment)
        current_text = ""
        current_words = []
        sentence_idx = 0
        for word in word_iter:
            if current_text and word["text"] not in string.punctuation:
                current_text += " "
            current_text += word["text"]
            current_words.append(word)
            if (
                sentence_idx < len(sentences)
                and replace_acronyms(current_text.strip())
                == sentences[sentence_idx].strip()
            ):
                new_segments.append(current_words)
                current_words = []
                current_text = ""
                sentence_idx += 1
        if current_words:
            new_segments.append(current_words)
    return new_segments


def merge_punctuation_only_segments(segments: List[List[Dict]]) -> List[List[Dict]]:
    """
    Move punctuation-only segments to the end of the previous segment, instead of removing them.

    Args:
        segments: List of segments (each a list of word dicts).

    Returns:
        Cleaned list of segments with punctuation-only segments appended to the previous segment.
    """
    import string

    cleaned = []
    for seg in segments:
        text = "".join(w["text"] for w in seg)
        if all(ch in string.punctuation for ch in text):
            if cleaned:
                cleaned[-1].extend(seg)
            # If no previous segment, keep as is (edge case)
            else:
                cleaned.append(seg)
        else:
            cleaned.append(seg)
    return cleaned


def load_json(file_path: str) -> Dict:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Dictionary with the loaded JSON data.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_segments(
    segments: List[List[Dict]],
    speaker_brackets: bool = False,
    speaker_map: Optional[Dict[str, str]] = None,
) -> None:
    """
    Pretty-print segments with speaker, time, and text.

    Args:
        segments: List of segments (each a list of word dicts).
        speaker_brackets: If True, prefix each segment with '- [Speaker]'.
        speaker_map: Optional mapping to rename speaker IDs.
    """

    for i, segment in enumerate(segments, 1):
        text = " ".join(word["text"] for word in segment)
        start = segment[0]["start"]
        end = segment[-1]["end"]
        speaker = segment[0]["speaker_id"]
        if speaker_map:
            speaker = speaker_map.get(speaker, speaker)
        if speaker_brackets:
            label = f"- [{speaker}]"
        else:
            label = speaker
        print(f"Segment {i}: {label} ({start:.2f}-{end:.2f})\n{text}\n")


def get_grouped_segments(
    words: List[Dict],
    language_code: str = "eng",
    max_duration: float = 60.0,
    big_pause_seconds: float = BIG_PAUSE_SECONDS,
    min_words_in_segment: int = MIN_WORDS_IN_SEGMENT,
    skip_punctuation_only: bool = False,
) -> List[List[Dict]]:
    """
    Return grouped segments using the aligner logic (pauses, speaker, sentence, duration, punctuation).

    Args:
        words: List of word dicts, each with 'text', 'start', 'end', and 'speaker_id'.
        language_code: ISO 639-3 or 639-1 language code for sentence tokenization.
        max_duration: Maximum allowed segment duration in seconds.
        big_pause_seconds: Pause (in seconds) that triggers a new segment if exceeded between words.
        min_words_in_segment: Minimum number of words in a segment.
        skip_punctuation_only: If True, remove segments that contain only punctuation.

    Returns:
        List of grouped segments (each a list of word dicts).
    """

    lang_code = normalize_language_code(language_code)

    initial_segments = initial_grouping(
        words,
        big_pause_seconds=big_pause_seconds,
        min_words_in_segment=min_words_in_segment,
    )
    split_segments = split_long_segments_on_sentence(
        initial_segments, max_duration=max_duration, language_code=lang_code
    )
    final_segments = merge_on_sentence_boundary(split_segments, language_code=lang_code)
    if skip_punctuation_only:
        final_segments = merge_punctuation_only_segments(final_segments)
    return final_segments


def segment_transcription(
    transcription: Union[str, Dict],
    *,
    big_pause_seconds: float = BIG_PAUSE_SECONDS,
    min_words_in_segment: int = MIN_WORDS_IN_SEGMENT,
    max_duration: float = 60.0,
    language_code: Optional[str] = None,
    speaker_brackets: bool = False,
    skip_punctuation_only: bool = False,
) -> List[Dict]:
    """Segment a transcription JSON and return clean segment dictionaries.

    Args:
        transcription: Either a path to a transcription JSON file or a parsed
            transcription dictionary. The dictionary must contain a ``words``
            list with ``text``, ``start``, ``end`` and ``speaker_id`` fields.
        big_pause_seconds: Pause in seconds that triggers a new segment.
        min_words_in_segment: Minimum number of words required per segment.
        max_duration: Maximum allowed segment duration in seconds.
        language_code: Language code override. If ``None`` the value from the
            transcription is used.
        speaker_brackets: If ``True``, speaker labels in the returned segments
            are formatted as ``- [Speaker]``.
        skip_punctuation_only: Remove segments that contain only punctuation.

    Returns:
        A list of dictionaries with ``speaker``, ``start``, ``end`` and ``text``
        keys.

    Raises:
        ValueError: If the input is malformed or missing required fields.
    """

    if isinstance(transcription, str):
        transcription = load_json(transcription)
    elif not isinstance(transcription, dict):
        raise ValueError("transcription must be a dict or file path")

    if "words" not in transcription or not isinstance(transcription["words"], list):
        raise ValueError("transcription missing required 'words' list")

    words = transcription["words"]
    required_fields = {"text", "start", "end", "speaker_id"}
    for w in words:
        if not required_fields.issubset(w):
            raise ValueError("each word must contain text, start, end and speaker_id")

    lang = language_code or transcription.get("language_code", "eng")

    grouped = get_grouped_segments(
        words,
        language_code=lang,
        big_pause_seconds=big_pause_seconds,
        min_words_in_segment=min_words_in_segment,
        max_duration=max_duration,
        skip_punctuation_only=skip_punctuation_only,
    )

    results: List[Dict] = []
    for seg in grouped:
        speaker = seg[0]["speaker_id"]
        if speaker_brackets:
            speaker = f"- [{speaker}]"
        results.append(
            {
                "speaker": speaker,
                "start": seg[0]["start"],
                "end": seg[-1]["end"],
                "text": " ".join(w["text"] for w in seg),
            }
        )

    return results


def normalize_speaker_id(speaker_id: str) -> str:
    """
    Normalize speaker IDs to the standard "Speaker N" format.

    Args:
        speaker_id: Raw speaker ID (e.g., "spk1", "speaker_1", "SPEAKER_01")

    Returns:
        Normalized speaker ID (e.g., "Speaker 1")
    """
    if not speaker_id:
        return "Speaker 1"

    # Remove common prefixes and clean up
    cleaned = speaker_id.lower()

    # Handle various patterns
    patterns_to_remove = ["spk", "speaker", "speaker_", "spk_"]
    for pattern in patterns_to_remove:
        if cleaned.startswith(pattern):
            cleaned = cleaned[len(pattern) :]
            break

    # Extract numeric part
    import re

    match = re.search(r"(\d+)", cleaned)
    if match:
        num = int(match.group(1))
        # Convert 0-based numbering to 1-based for speaker_N format
        # but keep 1-based numbering as-is for spk_N format
        if speaker_id.lower().startswith("speaker_"):
            # This is 0-based (speaker_0, speaker_1) -> convert to 1-based
            num += 1
        elif num == 0:
            # Handle edge case where other formats use 0
            num = 1
        return f"Speaker {num}"

    # Fallback: if no number found, assume Speaker 1
    return "Speaker 1"


def save_segments_as_srt(
    segments: List[List[Dict]],
    filepath: str,
    speaker_brackets: bool = False,
    speaker_map: Union[Dict[str, str], None] = None,
    normalize_speakers: bool = True,
) -> None:
    """
    Save segments as an SRT subtitle file.

    Args:
        segments: List of segments (each a list of word dicts).
        filepath: Path to the output SRT file.
        speaker_brackets: If True, prefix each segment with '[Speaker]' in the SRT.
        speaker_map: Optional mapping to rename speaker IDs.
        normalize_speakers: If True, normalize speaker IDs to "Speaker N" format.
    """

    def format_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    # If normalizing speakers, create a consistent mapping for all unique speaker IDs
    if normalize_speakers and not speaker_map:
        # Collect all unique speaker IDs from segments
        unique_speakers = set()
        for segment in segments:
            if segment:  # Ensure segment is not empty
                speaker_id = segment[0].get("speaker_id")
                if speaker_id:
                    unique_speakers.add(speaker_id)

        # Sort unique speakers for consistent mapping
        sorted_speakers = sorted(unique_speakers)
        # Create mapping from raw speaker IDs to normalized Speaker N format
        speaker_map = {}
        for i, speaker_id in enumerate(sorted_speakers, 1):
            speaker_map[speaker_id] = f"Speaker {i}"

    with open(filepath, "w", encoding="utf-8") as f:
        for idx, segment in enumerate(segments, 1):
            start = format_time(segment[0]["start"])
            end = format_time(segment[-1]["end"])

            # Clean text by removing null characters and normalizing whitespace
            raw_text = " ".join(w["text"] for w in segment)
            text = raw_text.replace("\x00", "").strip()
            if not text:
                continue  # Skip empty segments

            speaker = segment[0].get("speaker_id", "unknown")

            # Apply speaker mapping if available
            if speaker_map:
                speaker = speaker_map.get(speaker, speaker)
            # Apply individual normalization if no speaker map exists and normalization is requested
            elif normalize_speakers:
                speaker = normalize_speaker_id(speaker)

            if speaker_brackets:
                label = f"- [{speaker}] "
            else:
                label = f"[{speaker}] "
            f.write(f"{idx}\n{start} --> {end}\n{label}{text}\n\n")


# Add a main() function for pip install entry point


def main():
    """
    Command-line entry point for running the aligner on a transcription JSON file.
    Parses arguments, loads data, runs segmentation, and prints results.
    """

    import argparse

    parser = argparse.ArgumentParser(
        description="Run sentence segmentation aligner on a transcription JSON file."
    )
    parser.add_argument(
        "transcription_json",
        nargs="?",
        default="transcription.json",
        help="Path to transcription JSON file",
    )
    parser.add_argument(
        "--big-pause-seconds",
        type=float,
        default=BIG_PAUSE_SECONDS,
        help="Pause length to start a new segment",
    )
    parser.add_argument(
        "--min-words-in-segment",
        type=int,
        default=MIN_WORDS_IN_SEGMENT,
        help="Minimum number of words in a segment",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=60.0,
        help="Maximum allowed segment duration in seconds before splitting at a sentence boundary",
    )
    parser.add_argument(
        "--speaker-brackets",
        action="store_true",
        help="Include speaker label in brackets in output",
    )
    parser.add_argument(
        "--fix-orphaned-punctuation",
        action="store_true",
        help="Merge segments that contain only punctuation into the previous segment (default behavior)",
    )
    args = parser.parse_args()

    transcription = load_json(args.transcription_json)
    words = transcription["words"]
    language_code = transcription.get("language_code", "eng")
    segments = get_grouped_segments(
        words,
        language_code=language_code,
        big_pause_seconds=args.big_pause_seconds,
        min_words_in_segment=args.min_words_in_segment,
        max_duration=args.max_duration,
        skip_punctuation_only=args.fix_orphaned_punctuation,
    )
    print_segments(
        segments,
        speaker_brackets=args.speaker_brackets,
    )


if __name__ == "__main__":
    main()


def validate_speaker_purity(segments: List[List[Dict]]) -> bool:
    """
    Validate that no segment contains words from multiple speakers.

    Args:
        segments: List of segments (each a list of word dicts).

    Returns:
        True if all segments contain only single speakers, False otherwise.
    """
    all_pure = True

    for i, segment in enumerate(segments):
        if not segment:
            continue

        speakers = set(w.get("speaker_id") for w in segment)
        if len(speakers) > 1:
            all_pure = False
            print(f"❌ MIXED SPEAKERS in Segment {i + 1}: {speakers}")
            text = " ".join(w["text"] for w in segment)
            print(f"   Text: '{text}'")
            print("   Word-by-word breakdown:")
            for j, word in enumerate(segment):
                print(f"     {j + 1:2d}. [{word.get('speaker_id')}] '{word['text']}'")
        else:
            speaker = list(speakers)[0] if speakers else "None"
            print(f"✅ Single speaker in Segment {i + 1}: {speaker}")

    return all_pure
