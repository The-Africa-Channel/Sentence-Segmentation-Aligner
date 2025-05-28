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
        self.assertEqual(len(segments), 4)


if __name__ == "__main__":
    unittest.main()
