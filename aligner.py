import json
import nltk
from typing import List, Dict
from nltk.tokenize import sent_tokenize

# Ensure you have the tokenizer downloaded
nltk.download("punkt")

BIG_PAUSE_SECONDS = 0.75
MIN_WORDS_IN_SEGMENT = 2

# Map ISO 639-3 codes to NLTK language names for supported languages
ISO_TO_NLTK_LANG = {
    "eng": "english",
    "spa": "spanish",
    "por": "portuguese",
    "fra": "french",
    "deu": "german",
    "ita": "italian",
    "nld": "dutch",
    "cmn": "chinese",
    "kor": "korean",
    "ara": "arabic",
    "hin": "english",  # Hindi not natively supported by NLTK, fallback to English
    "ben": "english",  # Bengali fallback
    "tam": "english",  # Tamil fallback
    "tel": "english",  # Telugu fallback
    "mar": "english",  # Marathi fallback
    "guj": "english",  # Gujarati fallback
    "kan": "english",  # Kannada fallback
    "pan": "english",  # Punjabi fallback
    "mal": "english",  # Malayalam fallback
    "urd": "english",  # Urdu fallback
}


def initial_grouping(words: List[Dict]) -> List[List[Dict]]:
    segments = []
    current_segment = [words[0]]

    for word in words[1:]:
        if (
            word["start"] - current_segment[-1]["end"] > BIG_PAUSE_SECONDS
            or word["speaker_id"] != current_segment[-1]["speaker_id"]
        ):
            segments.append(current_segment)
            current_segment = [word]
        else:
            current_segment.append(word)
    segments.append(current_segment)

    # Ensure no segments are too short
    if len(segments[-1]) < MIN_WORDS_IN_SEGMENT and len(segments) > 1:
        segments[-2].extend(segments.pop())

    return segments


def merge_on_sentence_boundary(
    segments: List[List[Dict]], language_code: str = "eng"
) -> List[List[Dict]]:
    import re
    import string

    merged_segments = []
    buffer_segment = []

    # Unicode-aware regex for acronyms (e.g., B.M.W., A.B.S.)
    acronym_pattern = re.compile(r"((?:[A-ZÄÖÜ]\.){2,})", re.UNICODE)
    ACRONYM_PLACEHOLDER = "__ACRONYM__"

    def replace_acronyms(text):
        return acronym_pattern.sub(
            lambda m: m.group(1).replace(".", ACRONYM_PLACEHOLDER), text
        )

    def restore_acronyms(text):
        return text.replace(ACRONYM_PLACEHOLDER, ".")

    # Get NLTK language name
    nltk_lang = ISO_TO_NLTK_LANG.get(language_code, "english")

    for segment in segments:
        buffer_segment.extend(segment)
        texts = " ".join([w["text"] for w in buffer_segment])
        safe_texts = replace_acronyms(texts)
        sentences = sent_tokenize(safe_texts, language=nltk_lang)
        sentences = [restore_acronyms(s) for s in sentences]

        if len(sentences) > 1:
            finalized_text = " ".join(sentences[:-1])
            finalized_words = []
            word_iter = iter(buffer_segment)
            current_text = ""

            for word in word_iter:
                # Join with space or punctuation as appropriate
                if current_text and word["text"] not in string.punctuation:
                    current_text += " "
                current_text += word["text"]
                finalized_words.append(word)
                if replace_acronyms(current_text.strip()) == finalized_text.strip():
                    break

            merged_segments.append(finalized_words)
            buffer_segment = list(word_iter)

    if buffer_segment:
        merged_segments.append(buffer_segment)

    return merged_segments


def split_long_segments_on_sentence(
    segments: List[List[Dict]], max_duration: float = 15.0, language_code: str = "eng"
) -> List[List[Dict]]:
    from nltk.tokenize import sent_tokenize
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

    nltk_lang = ISO_TO_NLTK_LANG.get(language_code, "english")
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
        sentences = sent_tokenize(safe_texts, language=nltk_lang)
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


def load_json(file_path: str) -> Dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_segments(segments: List[List[Dict]]):
    for i, segment in enumerate(segments, 1):
        text = " ".join(word["text"] for word in segment)
        start = segment[0]["start"]
        end = segment[-1]["end"]
        speaker = segment[0]["speaker_id"]
        print(f"Segment {i}: [{speaker}] ({start:.2f}-{end:.2f})\n{text}\n")


def get_grouped_segments(words: List[Dict], language_code: str = "eng", max_duration: float = 15.0) -> List[List[Dict]]:
    """
    Returns grouped segments (list of list of word dicts) using the aligner logic.
    """
    initial_segments = initial_grouping(words)
    split_segments = split_long_segments_on_sentence(initial_segments, max_duration=max_duration, language_code=language_code)
    final_segments = merge_on_sentence_boundary(split_segments, language_code=language_code)
    return final_segments


def save_segments_as_srt(segments: List[List[Dict]], filepath: str):
    """
    Save segments as an SRT file.
    """
    def format_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    with open(filepath, "w", encoding="utf-8") as f:
        for idx, segment in enumerate(segments, 1):
            start = format_time(segment[0]['start'])
            end = format_time(segment[-1]['end'])
            text = " ".join(w['text'] for w in segment)
            f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")


# Add a main() function for pip install entry point


def main():
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
    args = parser.parse_args()

    transcription = load_json(args.transcription_json)
    words = transcription["words"]
    language_code = transcription.get("language_code", "eng")
    initial_segments = initial_grouping(words)
    split_segments = split_long_segments_on_sentence(
        initial_segments, max_duration=15.0, language_code=language_code
    )
    final_segments = merge_on_sentence_boundary(
        split_segments, language_code=language_code
    )
    print_segments(final_segments)


if __name__ == "__main__":
    main()
