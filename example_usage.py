# Example: Using the aligner as an installed pip package

from aligner import segment_transcription
import os

# Path to the sample transcription file
SAMPLE_JSON = os.path.join(os.path.dirname(__file__), "sample", "transcription.json")

# Run segmentation with typical options
segments = segment_transcription(
    SAMPLE_JSON,
    speaker_brackets=True,
    max_duration=15.0,  # or any other value you want
    big_pause_seconds=0.75,
    min_words_in_segment=2,
    # fix_orphaned_punctuation is True by default
)

# Print the results
for i, seg in enumerate(segments, 1):
    print(f"Segment {i}: {seg['speaker']} ({seg['start']:.2f}-{seg['end']:.2f})\n{seg['text']}\n")
