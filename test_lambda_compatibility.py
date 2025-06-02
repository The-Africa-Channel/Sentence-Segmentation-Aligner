"""
Test script to verify AWS Lambda compatibility
"""

import sys
import os

# Add the current directory to path to import aligner
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_lambda_compatibility():
    """Test that aligner works in a Lambda-like environment"""
    try:
        import aligner

        print(f"✓ Successfully imported aligner module")
        # Test data similar to what might come from a Lambda event
        test_data = {
            "words": [
                {"text": "Hello", "start": 0.0, "end": 0.5, "speaker_id": "Speaker1"},
                {"text": "world.", "start": 0.5, "end": 1.0, "speaker_id": "Speaker1"},
                {"text": "How", "start": 2.0, "end": 2.3, "speaker_id": "Speaker1"},
                {"text": "are", "start": 2.3, "end": 2.5, "speaker_id": "Speaker1"},
                {"text": "you?", "start": 2.5, "end": 3.0, "speaker_id": "Speaker1"},
            ]
        }  # Test segmentation
        segments = aligner.segment_transcription(test_data)
        print(f"✓ Segmentation successful: {len(segments)} segments created")
        # For SRT generation, we need to use get_grouped_segments instead
        grouped_segments = aligner.get_grouped_segments(
            test_data["words"], max_duration=15.0
        )

        # Test SRT generation
        srt_content = aligner.save_segments_as_srt(grouped_segments, return_string=True)
        print(f"✓ SRT generation successful: {len(srt_content)} characters")

        # Test with speakers
        test_data_with_speakers = {
            "words": [
                {"text": "Hello", "start": 0.0, "end": 0.5, "speaker_id": "Speaker1"},
                {"text": "world.", "start": 0.5, "end": 1.0, "speaker_id": "Speaker1"},
                {"text": "Hi", "start": 2.0, "end": 2.2, "speaker_id": "Speaker2"},
                {"text": "there!", "start": 2.2, "end": 2.8, "speaker_id": "Speaker2"},
            ]
        }

        segments_with_speakers = aligner.segment_transcription(test_data_with_speakers)
        grouped_segments_with_speakers = aligner.get_grouped_segments(
            test_data_with_speakers["words"], max_duration=15.0
        )
        srt_with_speakers = aligner.save_segments_as_srt(
            grouped_segments_with_speakers, speaker_brackets=True, return_string=True
        )
        print(f"✓ Speaker-aware processing successful")

        print("\n✅ All Lambda compatibility tests passed!")
        return True

    except Exception as e:
        print(f"❌ Lambda compatibility test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_lambda_compatibility()
    sys.exit(0 if success else 1)
