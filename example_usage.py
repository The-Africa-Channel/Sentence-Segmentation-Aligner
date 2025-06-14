# Example: Using the aligner as an installed pip package

from aligner import segment_transcription, save_segments_as_srt
from aligner import get_grouped_segments
import os
import json

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
    print(
        f"Segment {i}: {seg['speaker']} ({seg['start']:.2f}-{seg['end']:.2f})\n{seg['text']}\n"
    )

# Save as SRT (subtitle) file
SRT_PATH = os.path.join(os.path.dirname(__file__), "sample", "transcription.srt")
# The save_segments_as_srt function expects a list of lists of word dicts, so we need to load the words and re-segment
with open(SAMPLE_JSON, "r", encoding="utf-8") as f:
    words = json.load(f)["words"]


segments_for_srt = get_grouped_segments(
    words,
    max_duration=15.0,
    big_pause_seconds=0.75,
    min_words_in_segment=2,
    # fix_orphaned_punctuation is True by default
)
save_segments_as_srt(segments_for_srt, SRT_PATH, speaker_brackets=True)
print(f"SRT file saved to: {SRT_PATH}")
# Optionally, print the SRT file contents
with open(SRT_PATH, "r", encoding="utf-8") as f:
    print("\nSRT Output:\n" + f.read())
