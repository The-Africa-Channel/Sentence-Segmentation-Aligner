"""
Filter utilities for the TranscriptionValidation module.
"""

import re
from typing import List, Dict, Any


# Simple logger replacement
class SimpleLogger:
    def debug(self, msg, *args):
        pass

    def info(self, msg, *args):
        print(f"INFO: {msg % args}" if args else f"INFO: {msg}")

    def warning(self, msg, *args):
        print(f"WARNING: {msg % args}" if args else f"WARNING: {msg}")


logger = SimpleLogger()


def contains_meaningful_words(text: str) -> bool:
    """
    Check if text contains meaningful words (not just punctuation, symbols, or non-word characters).

    Args:
        text: The text to check

    Returns:
        bool: True if text contains at least one meaningful word, False otherwise
    """
    if not text or not isinstance(text, str):
        return False

    # Remove common speaker tags and brackets first
    cleaned_text = re.sub(r"-\s*\[[^\]]+\]\s*", "", text)
    cleaned_text = re.sub(r"\[[^\]]+\]\s*", "", cleaned_text)
    cleaned_text = re.sub(r"\([^)]*\)", "", cleaned_text)

    # Remove HTML tags
    cleaned_text = re.sub(r"<[^>]*>", "", cleaned_text)

    # Find all sequences of word characters (letters, digits, apostrophes)
    # This regex matches words that contain at least one letter or digit
    words = re.findall(r"\b\w*[a-zA-Z0-9]\w*\b", cleaned_text)

    # Check if we have at least one meaningful word (length > 1 or single letters/digits)
    meaningful_words = [word for word in words if len(word) >= 1 and not word.isspace()]

    if not meaningful_words:
        logger.debug(f"Text contains no meaningful words: '{text}'")
        return False
    # Additional check: if text is only common filler sounds or non-words
    filler_patterns = [
        r"^\.+$",  # Only dots
        r"^-+$",  # Only dashes
        r"^\*+$",  # Only asterisks
        r"^_+$",  # Only underscores
        r"^[,.;:!?]+$",  # Only punctuation
        r"^[^\w\s]+$",  # Only non-word, non-space characters
    ]

    text_lower = cleaned_text.lower().strip()
    for pattern in filler_patterns:
        if re.match(pattern, text_lower):
            logger.debug(f"Text matches filler pattern {pattern}: '{text}'")
            return False

    return True


def filter_aligner_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter aligner segments to remove those with non-meaningful content.

    Args:
        segments: List of aligner segment dictionaries

    Returns:
        List of filtered segments with meaningful content only
    """
    if not segments:
        return segments

    filtered_segments = []
    removed_count = 0

    for i, segment in enumerate(segments):
        if not isinstance(segment, dict):
            logger.warning(f"Segment {i} is not a dictionary, skipping")
            continue

        text = segment.get("text", "")

        if not text:
            logger.debug(f"Segment {i} has no text content, removing")
            removed_count += 1
            continue

        # Check if text contains meaningful words
        if contains_meaningful_words(text):
            filtered_segments.append(segment)
        else:
            logger.info(
                f"Removing aligner segment {i} with non-meaningful text: '{text}'"
            )
            removed_count += 1

    if removed_count > 0:
        logger.info(
            f"Filtered out {removed_count} aligner segments with non-meaningful content. "
            f"Remaining: {len(filtered_segments)}/{len(segments)}"
        )

    return filtered_segments
