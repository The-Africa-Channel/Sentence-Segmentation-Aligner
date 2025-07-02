import unittest
from aligner import (
    initial_grouping,
    merge_on_sentence_boundary,
    get_grouped_segments,
)


class TestAligner(unittest.TestCase):
    def setUp(self):
        self.words = [
            {"text": "Hello", "start": 0.0, "end": 0.5, "speaker_id": "A"},
            {"text": "world.", "start": 0.6, "end": 1.0, "speaker_id": "A"},
            {"text": "How", "start": 4.0, "end": 4.2, "speaker_id": "A"},  # Big pause
            {"text": "are", "start": 4.3, "end": 4.5, "speaker_id": "A"},
            {"text": "you?", "start": 4.6, "end": 5.0, "speaker_id": "A"},
            {
                "text": "I",
                "start": 5.1,
                "end": 5.2,
                "speaker_id": "B",
            },  # Speaker change
            {"text": "am", "start": 5.3, "end": 5.4, "speaker_id": "B"},
            {"text": "fine.", "start": 5.5, "end": 6.0, "speaker_id": "B"},
        ]

    def test_initial_grouping(self):
        segments = initial_grouping(self.words)
        self.assertEqual(len(segments), 3)
        self.assertEqual([w["text"] for w in segments[0]], ["Hello", "world."])
        self.assertEqual([w["text"] for w in segments[1]], ["How", "are", "you?"])
        self.assertEqual([w["text"] for w in segments[2]], ["I", "am", "fine."])

    def test_merge_on_sentence_boundary(self):
        segments = initial_grouping(self.words)
        merged = merge_on_sentence_boundary(segments)
        # Should still be 3 segments, as each is a sentence
        self.assertEqual(len(merged), 3)
        self.assertEqual(" ".join(w["text"] for w in merged[0]), "Hello world.")
        self.assertEqual(" ".join(w["text"] for w in merged[1]), "How are you?")
        self.assertEqual(" ".join(w["text"] for w in merged[2]), "I am fine.")

    def test_custom_parameters(self):
        segments = get_grouped_segments(
            self.words,
            big_pause_seconds=0.1,
            min_words_in_segment=1,
            skip_punctuation_only=True,
        )
        self.assertEqual(len(segments), 3)

    def test_overlapping_speakers_not_combined(self):
        """Test that overlapping speakers are never combined into the same segment."""
        # Create overlapping speech scenario
        overlapping_words = [
            {"text": "This", "start": 0.0, "end": 0.3, "speaker_id": "A"},
            {"text": "is", "start": 0.4, "end": 0.6, "speaker_id": "A"},
            {"text": "speaker", "start": 0.7, "end": 1.0, "speaker_id": "A"},
            {"text": "A", "start": 1.1, "end": 1.3, "speaker_id": "A"},
            {"text": "speaking.", "start": 1.4, "end": 2.0, "speaker_id": "A"},
            # Speaker B interrupts/overlaps during A's speech
            {"text": "Wait,", "start": 1.5, "end": 1.8, "speaker_id": "B"},
            {"text": "I", "start": 1.9, "end": 2.0, "speaker_id": "B"},
            {"text": "disagree.", "start": 2.1, "end": 2.8, "speaker_id": "B"},
            # Speaker A continues after B
            {"text": "Let", "start": 3.0, "end": 3.2, "speaker_id": "A"},
            {"text": "me", "start": 3.3, "end": 3.5, "speaker_id": "A"},
            {"text": "finish.", "start": 3.6, "end": 4.0, "speaker_id": "A"},
        ]

        # Test initial grouping preserves speaker separation
        segments = initial_grouping(overlapping_words)

        # Verify no segment contains multiple speakers
        for i, segment in enumerate(segments):
            speakers_in_segment = set(w.get("speaker_id") for w in segment)
            self.assertEqual(
                len(speakers_in_segment),
                1,
                f"Segment {i} contains multiple speakers: {speakers_in_segment}. "
                f"Words: {[w['text'] for w in segment]}",
            )

        # Test merge_on_sentence_boundary also preserves speaker separation
        merged_segments = merge_on_sentence_boundary(segments)

        # Verify no merged segment contains multiple speakers
        for i, segment in enumerate(merged_segments):
            speakers_in_segment = set(w.get("speaker_id") for w in segment)
            self.assertEqual(
                len(speakers_in_segment),
                1,
                f"Merged segment {i} contains multiple speakers: {speakers_in_segment}. "
                f"Words: {[w['text'] for w in segment]}",
            )

        # Test full pipeline with get_grouped_segments
        final_segments = get_grouped_segments(overlapping_words)

        # Verify final result maintains speaker separation
        for i, segment in enumerate(final_segments):
            speakers_in_segment = set(w.get("speaker_id") for w in segment)
            self.assertEqual(
                len(speakers_in_segment),
                1,
                f"Final segment {i} contains multiple speakers: {speakers_in_segment}. "
                f"Words: {[w['text'] for w in segment]}",
            )

        # Verify we have segments from both speakers
        all_speakers = set()
        for segment in final_segments:
            all_speakers.update(w.get("speaker_id") for w in segment)
        self.assertIn(
            "A", all_speakers, "Speaker A should be present in final segments"
        )
        self.assertIn(
            "B", all_speakers, "Speaker B should be present in final segments"
        )

    def test_rapid_speaker_alternation(self):
        """Test rapid speaker changes are handled correctly without combining speakers."""
        rapid_alternation_words = [
            {"text": "Hello", "start": 0.0, "end": 0.5, "speaker_id": "A"},
            {"text": "Hi", "start": 0.6, "end": 0.8, "speaker_id": "B"},
            {"text": "there.", "start": 0.9, "end": 1.2, "speaker_id": "A"},
            {"text": "How", "start": 1.3, "end": 1.5, "speaker_id": "B"},
            {"text": "are", "start": 1.6, "end": 1.8, "speaker_id": "A"},
            {"text": "you?", "start": 1.9, "end": 2.2, "speaker_id": "B"},
        ]

        segments = get_grouped_segments(rapid_alternation_words)

        # Each word should be in its own segment due to speaker changes
        for segment in segments:
            speakers_in_segment = set(w.get("speaker_id") for w in segment)
            self.assertEqual(
                len(speakers_in_segment),
                1,
                f"Segment contains multiple speakers: {speakers_in_segment}",
            )

    def test_simultaneous_speech_different_timestamps(self):
        """Test simultaneous speech with overlapping timestamps."""
        simultaneous_words = [
            {"text": "I", "start": 0.0, "end": 0.2, "speaker_id": "A"},
            {"text": "think", "start": 0.3, "end": 0.6, "speaker_id": "A"},
            {"text": "we", "start": 0.7, "end": 0.9, "speaker_id": "A"},
            {"text": "should", "start": 1.0, "end": 1.3, "speaker_id": "A"},
            # Speaker B talks over A - same timeframe
            {
                "text": "No,",
                "start": 0.8,
                "end": 1.0,
                "speaker_id": "B",
            },  # Overlaps with "we"
            {
                "text": "wait!",
                "start": 1.1,
                "end": 1.4,
                "speaker_id": "B",
            },  # Overlaps with "should"
            # A continues
            {"text": "go", "start": 1.5, "end": 1.7, "speaker_id": "A"},
            {"text": "now.", "start": 1.8, "end": 2.0, "speaker_id": "A"},
        ]

        segments = get_grouped_segments(simultaneous_words)

        # Verify speaker separation is maintained
        for i, segment in enumerate(segments):
            speakers_in_segment = set(w.get("speaker_id") for w in segment)
            self.assertEqual(
                len(speakers_in_segment),
                1,
                f"Segment {i} has mixed speakers: {speakers_in_segment}. "
                f"Text: '{' '.join(w['text'] for w in segment)}'",
            )


if __name__ == "__main__":
    unittest.main()
