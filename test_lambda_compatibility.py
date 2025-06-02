"""
Test script to verify AWS Lambda compatibility
"""

import sys
import os
import tempfile

# Add the current directory to path to import aligner
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the functions we need to test
from aligner import segment_transcription, get_grouped_segments, save_segments_as_srt


def test_lambda_compatibility():
    """Test that the aligner works in AWS Lambda-like environments."""
    import tempfile
    import os

    # Test data with proper speaker_id fields
    test_data = {
        "language_code": "eng",
        "words": [
            {"text": "Hello", "start": 0.0, "end": 0.5, "speaker_id": "speaker_0"},
            {"text": "world", "start": 0.6, "end": 1.0, "speaker_id": "speaker_0"},
            {"text": ".", "start": 1.0, "end": 1.1, "speaker_id": "speaker_0"},
            {"text": "How", "start": 4.0, "end": 4.2, "speaker_id": "speaker_1"},
            {"text": "are", "start": 4.3, "end": 4.5, "speaker_id": "speaker_1"},
            {"text": "you", "start": 4.6, "end": 5.0, "speaker_id": "speaker_1"},
            {"text": "?", "start": 5.0, "end": 5.1, "speaker_id": "speaker_1"},
        ],
    }

    # Test segment_transcription function
    segments = segment_transcription(
        test_data,
        big_pause_seconds=1.0,
        min_words_in_segment=2,
        speaker_brackets=True,
        skip_punctuation_only=True,
    )

    # Use assert statements instead of returning True
    assert len(segments) > 0, "Should produce at least one segment"
    assert segments[0]["speaker"] == "- [speaker_0]", (
        f"Expected '- [speaker_0]', got '{segments[0]['speaker']}'"
    )
    assert "text" in segments[0], "Segments should have 'text' field"
    assert "start" in segments[0], "Segments should have 'start' field"
    assert "end" in segments[0], "Segments should have 'end' field"

    # Test SRT generation functionality
    grouped_segments = get_grouped_segments(
        test_data["words"],
        big_pause_seconds=1.0,
        min_words_in_segment=2,
        skip_punctuation_only=True,
    )

    assert len(grouped_segments) > 0, "Should produce grouped segments"

    # Test SRT file generation
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".srt", delete=False, encoding="utf-8"
    ) as tmp_file:
        srt_path = tmp_file.name

    try:
        # Generate SRT file
        save_segments_as_srt(grouped_segments, srt_path, speaker_brackets=True)

        # Verify SRT file was created and has content
        assert os.path.exists(srt_path), "SRT file should be created"

        with open(srt_path, "r", encoding="utf-8") as f:
            srt_content = f.read()

        assert len(srt_content) > 0, "SRT file should have content"
        assert "- [Speaker 1]" in srt_content, (
            "SRT should contain speaker labels with hyphens"
        )

        print("✅ Lambda compatibility test passed!")
        print(f"Generated {len(segments)} segments")
        print(f"SRT file size: {len(srt_content)} characters")

    finally:
        # Clean up temporary file
        if os.path.exists(srt_path):
            os.unlink(srt_path)


if __name__ == "__main__":
    test_lambda_compatibility()
