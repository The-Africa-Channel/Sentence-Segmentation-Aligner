"""
SRT Generation Tool - Replicates process_elevenlabs_format_transcript logic
VERSION: 2025-06-18

This module generates SRT files using the exact same logic as process_elevenlabs_format_transcript
to ensure identical output between systems.
"""

import json
import os
import sys
import re

# Import from local aligner module
try:
    from aligner import segment_transcription
except ImportError:
    # Fallback for different import scenarios
    current_dir = os.path.dirname(__file__)
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    from aligner import segment_transcription

# Import subtitle filters
try:
    from subtitle_filters import filter_aligner_segments
except ImportError:
    print("Warning: subtitle_filters not found, using basic filtering")

    def filter_aligner_segments(segments):
        """Basic fallback filtering - only removes punctuation-only segments"""
        filtered = []
        for segment in segments:
            text = segment.get("text", "").strip()
            # Only remove if text is purely punctuation/whitespace
            if text and not re.match(r"^[^\w\s]*$", text):
                filtered.append(segment)
        return filtered


# Exact GROUPING_CONFIG from the other system
GROUPING_CONFIG = {
    "big_pause_seconds": 1.0,
    "min_words_in_segment": 2,
    "max_duration": 15.0,
    "speaker_brackets": True,
    "skip_punctuation_only": True,
}


def normalize_speaker_id(speaker_id: str) -> str:
    """
    Normalize speaker IDs to the standard "Speaker N" format.
    Replicates the logic from aligner.py
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
    match = re.search(r"(\d+)", cleaned)
    if match:
        num = int(match.group(1))
        # Convert 0-based numbering to 1-based for speaker_N format
        if speaker_id.lower().startswith("speaker_"):
            # This is 0-based (speaker_0, speaker_1) -> convert to 1-based
            num += 1
        elif num == 0:
            # Handle edge case where other formats use 0
            num = 1
        return f"Speaker {num}"

    # Fallback: if no number found, assume Speaker 1
    return "Speaker 1"


def format_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def clean_text_spacing(text: str) -> str:
    """Clean up text formatting issues - fix multiple spaces."""
    return re.sub(r"\s+", " ", text.strip())


def expand_acronyms(text: str) -> str:
    """
    Expand acronyms in a string (e.g., 'NASA' -> 'N.A.S.A.').
    Only expands all-caps words of 2+ letters not already containing periods.
    EXACT COPY from production code.
    """

    def repl(match):
        return ".".join(match.group(0)) + "."

    return re.sub(r"\b([A-Z]{2,})(?=(?:'s|'s)?\b)", repl, text)


def clean_transcription_data(transcript):
    """
    Clean and preprocess transcription data exactly like production system.
    """
    import copy

    # Deep copy to avoid modifying the original
    cleaned = copy.deepcopy(transcript)

    # Step 1: Normalize speaker IDs (0-based to 1-based)
    if "words" in cleaned:
        for word in cleaned["words"]:
            speaker_id = word.get("speaker_id")
            if isinstance(speaker_id, str) and "_" in speaker_id:
                try:
                    num = int(speaker_id.split("_")[1]) + 1
                    word["speaker_id"] = f"speaker_{num}"
                except ValueError:
                    pass

    # Step 2: Expand acronyms and clean text in words
    if "words" in cleaned:
        for word in cleaned["words"]:
            if "text" in word and isinstance(word["text"], str):
                # Remove null characters
                word["text"] = word["text"].replace("\x00", "")
                # Expand acronyms
                word["text"] = expand_acronyms(word["text"])

    return cleaned


def fix_word_spacing_issues(text: str) -> str:
    """
    Fix common word spacing issues from transcription APIs.
    Handles cases like "meinem1er" -> "meinem 1er"
    """
    # Pattern to match letter followed immediately by digit
    # Insert space between letter and digit (e.g., "meinem1er" -> "meinem 1er")
    text = re.sub(r"([a-zA-ZäöüßÄÖÜ])(\d)", r"\1 \2", text)

    # Pattern to match digit followed immediately by letter (for cases like "1erM")
    # Insert space between digit and letter
    text = re.sub(r"(\d)([a-zA-ZäöüßÄÖÜ])", r"\1 \2", text)

    # Clean up any double spaces that might have been created
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def generate_srt_from_transcript(
    transcript_path: str,
    output_path: str = None,
    max_duration: float = None,
    big_pause_seconds: float = None,
    min_words_in_segment: int = None,
    speaker_brackets: bool = None,
    normalize_speakers: bool = True,
    debug: bool = False,
) -> str:
    """
    Generate SRT file from ElevenLabs format transcript using the exact same logic
    as the production system.

    Args:
        transcript_path: Path to the JSON transcript file
        output_path: Path for output SRT file (optional, auto-generated if None)
        max_duration: Maximum segment duration before splitting (uses GROUPING_CONFIG if None)
        big_pause_seconds: Pause threshold for new segments (uses GROUPING_CONFIG if None)
        min_words_in_segment: Minimum words per segment (uses GROUPING_CONFIG if None)
        speaker_brackets: Whether to use "- [Speaker]" format (uses GROUPING_CONFIG if None)
        normalize_speakers: Whether to normalize speaker IDs
        debug: Whether to print debugging information

    Returns:
        str: Path to the generated SRT file
    """

    # Use GROUPING_CONFIG defaults if not specified
    if max_duration is None:
        max_duration = GROUPING_CONFIG["max_duration"]
    if big_pause_seconds is None:
        big_pause_seconds = GROUPING_CONFIG["big_pause_seconds"]
    if min_words_in_segment is None:
        min_words_in_segment = GROUPING_CONFIG["min_words_in_segment"]
    if speaker_brackets is None:
        speaker_brackets = GROUPING_CONFIG["speaker_brackets"]

    # Load transcript
    with open(transcript_path, "r", encoding="utf-8") as f:
        raw_transcript = json.load(f)

    if "words" not in raw_transcript:
        raise ValueError("Transcript must contain 'words' array (ElevenLabs format)")

    print(
        f"Processing ElevenLabs format transcript with {len(raw_transcript['words'])} words"
    )

    # CRITICAL: Clean and preprocess the transcript data exactly like production
    transcript = clean_transcription_data(raw_transcript)

    if debug:
        print("Using parameters:")
        print(f"  max_duration: {max_duration}")
        print(f"  big_pause_seconds: {big_pause_seconds}")
        print(f"  min_words_in_segment: {min_words_in_segment}")
        print(f"  speaker_brackets: {speaker_brackets}")
        print(f"  skip_punctuation_only: {GROUPING_CONFIG['skip_punctuation_only']}")
        print(f"After cleaning: {len(transcript['words'])} words")

    # Step 1: Get grouped segments using production logic
    # Remove speaker_brackets from grouping_kwargs (not supported by get_grouped_segments)
    grouping_kwargs = {
        k: v for k, v in GROUPING_CONFIG.items() if k != "speaker_brackets"
    }

    # Import get_grouped_segments from aligner (used in production)
    try:
        from aligner import get_grouped_segments

        # Use the exact production method
        words = transcript.get("words", [])
        speech_segments = get_grouped_segments(
            words,
            language_code=transcript.get("language_code", "en"),
            **grouping_kwargs,
        )

        print(f"get_grouped_segments returned {len(speech_segments)} segments")

    except ImportError:
        print(
            "Warning: get_grouped_segments not found, using segment_transcription fallback"
        )
        # Fallback to segment_transcription
        aligner_segments = segment_transcription(
            transcript,
            max_duration=max_duration,
            big_pause_seconds=big_pause_seconds,
            min_words_in_segment=min_words_in_segment,
            speaker_brackets=False,
            skip_punctuation_only=GROUPING_CONFIG["skip_punctuation_only"],
            language_code=transcript.get("language_code", "en"),
        )

        # Convert to speech_segments format (list of word lists)
        speech_segments = []
        for seg in aligner_segments:
            # Need to reconstruct word lists from segment data
            # This is a limitation but let's make it work
            print(
                "Warning: Using fallback mode - segment boundaries may differ from production"
            )

        speech_segments = []

    # Step 2: Convert speech segments to the format expected by save_segments_as_srt
    # This matches the production logic for final segment processing
    final_segments = []

    for segment in speech_segments:
        # Handle different segment formats (list vs dict)
        if isinstance(segment, list):
            seg_words = segment
        else:
            seg_words = segment.get("words", [])

        if not seg_words:
            continue  # Apply comprehensive text cleaning like production
        cleaned_words = []
        for word in seg_words:
            if isinstance(word, dict) and "text" in word:
                cleaned_text = word["text"]
                if isinstance(cleaned_text, str):
                    # Remove null characters, normalize whitespace, clean up punctuation spacing
                    cleaned_text = re.sub(
                        r"\x00+", "", cleaned_text
                    )  # Remove null chars
                    cleaned_text = re.sub(
                        r"\s+", " ", cleaned_text
                    )  # Normalize whitespace
                    cleaned_text = re.sub(
                        r"\s+([,.!?;:])", r"\1", cleaned_text
                    )  # Fix punctuation spacing
                    cleaned_text = re.sub(
                        r"([,.!?;:])\s*([,.!?;:])", r"\1\2", cleaned_text
                    )  # Remove space between punctuation

                    # Fix word spacing issues (e.g., "meinem1er" -> "meinem 1er")
                    cleaned_text = fix_word_spacing_issues(cleaned_text)
                    cleaned_text = cleaned_text.strip()

                    if cleaned_text:  # Only include non-empty words
                        word_copy = word.copy()
                        word_copy["text"] = cleaned_text
                        cleaned_words.append(word_copy)

        if cleaned_words:  # Only add segments with valid words
            final_segments.append(cleaned_words)

    print(f"Final segments after cleaning: {len(final_segments)} segments")

    if debug:
        print("\nFinal segments for SRT generation:")
        for i, seg in enumerate(final_segments[:10]):  # Show first 10
            if seg:
                start_time = seg[0]["start"]
                end_time = seg[-1]["end"]
                text = " ".join(w["text"] for w in seg)
                speaker = seg[0].get("speaker_id", "speaker_0")
                print(
                    f"  {i + 1}: {start_time:.3f}-{end_time:.3f} [{speaker}] {text[:60]}..."
                )

    # Step 3: Generate output path if not provided
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(transcript_path))[0]
        output_dir = os.path.dirname(transcript_path)
        output_path = os.path.join(output_dir, f"{base_name}.srt")

    # Step 4: Use aligner's save_segments_as_srt function exactly like production
    try:
        from aligner import save_segments_as_srt

        save_segments_as_srt(
            final_segments,
            output_path,
            speaker_brackets=speaker_brackets,
            speaker_map=None,
            normalize_speakers=normalize_speakers,
        )

        print(f"SRT file generated using save_segments_as_srt: {output_path}")
        print(f"Total segments written: {len(final_segments)}")

    except ImportError:
        print("Warning: save_segments_as_srt not found, using fallback SRT generation")
        # Fallback to manual SRT generation
        with open(output_path, "w", encoding="utf-8") as f:
            for idx, segment in enumerate(final_segments, 1):
                if not segment:
                    continue

                # Extract timing and text
                start_time = format_time(segment[0]["start"])
                end_time = format_time(segment[-1]["end"])
                text = " ".join(w["text"] for w in segment)
                text = clean_text_spacing(text)

                # Handle speaker formatting
                speaker = segment[0].get("speaker_id", "speaker_0")

                # Apply speaker normalization if requested
                if normalize_speakers:
                    speaker = normalize_speaker_id(speaker)

                # Apply speaker bracket formatting
                if speaker_brackets:
                    speaker_label = f"- [{speaker}] "
                else:
                    speaker_label = f"[{speaker}] "

                # Write SRT entry
                f.write(f"{idx}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{speaker_label}{text}\n\n")

        print(f"SRT file generated using fallback method: {output_path}")
        print(f"Total segments written: {len(final_segments)}")

    return output_path


def main():
    """Command line interface for SRT generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate SRT file from ElevenLabs transcript using process_elevenlabs_format_transcript logic"
    )
    parser.add_argument(
        "transcript_json", help="Path to ElevenLabs format JSON transcript file"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output SRT file path (default: same directory as input with .srt extension)",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=15.0,
        help="Maximum segment duration in seconds (default: 15.0)",
    )
    parser.add_argument(
        "--big-pause-seconds",
        type=float,
        default=1.0,
        help="Pause threshold for new segments in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--min-words-in-segment",
        type=int,
        default=2,
        help="Minimum words per segment (default: 2)",
    )
    parser.add_argument(
        "--no-speaker-brackets",
        action="store_true",
        help="Don't use '- [Speaker]' format (use '[Speaker]' instead)",
    )
    parser.add_argument(
        "--no-normalize-speakers",
        action="store_true",
        help="Don't normalize speaker IDs (keep original speaker_0, speaker_1, etc.)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print detailed debugging information",
    )

    args = parser.parse_args()

    try:
        output_path = generate_srt_from_transcript(
            transcript_path=args.transcript_json,
            output_path=args.output,
            max_duration=args.max_duration,
            big_pause_seconds=args.big_pause_seconds,
            min_words_in_segment=args.min_words_in_segment,
            speaker_brackets=not args.no_speaker_brackets,
            normalize_speakers=not args.no_normalize_speakers,
            debug=args.debug,
        )
        print(f"\n✅ Success! SRT file saved to: {output_path}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
