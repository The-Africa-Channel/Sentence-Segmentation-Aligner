"""
Example AWS Lambda function for sentence segmentation and alignment
"""

import json
import aligner


def lambda_handler(event, context):
    """
    AWS Lambda function to process transcription data

    Expected event structure:
    {
        "transcription": {
            "words": [
                {"text": "word", "start": 0.0, "end": 0.5, "speaker_id": "Speaker1"},
                ...
            ]
        },
        "format": "srt",  # or "json"
        "max_duration": 15.0,
        "speaker_brackets": true,
        "big_pause_seconds": 0.75,
        "min_words_in_segment": 2
    }
    """
    try:
        # Parse input parameters
        transcription_data = event.get("transcription", {})
        output_format = event.get("format", "srt").lower()
        max_duration = event.get("max_duration", 15.0)
        speaker_brackets = event.get("speaker_brackets", True)
        big_pause_seconds = event.get("big_pause_seconds", 0.75)
        min_words_in_segment = event.get("min_words_in_segment", 2)

        # Validate input
        if not transcription_data.get("words"):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "Missing or empty words array in transcription"}
                ),
            }

        # Process transcription
        if output_format == "srt":
            # For SRT output, use get_grouped_segments
            segments = aligner.get_grouped_segments(
                transcription_data["words"],
                max_duration=max_duration,
                big_pause_seconds=big_pause_seconds,
                min_words_in_segment=min_words_in_segment,
            )

            result = aligner.save_segments_as_srt(
                segments, speaker_brackets=speaker_brackets, return_string=True
            )
            content_type = "text/plain"

        else:
            # For JSON output, use segment_transcription (flat format)
            segments = aligner.segment_transcription(
                transcription_data,
                max_duration=max_duration,
                big_pause_seconds=big_pause_seconds,
                min_words_in_segment=min_words_in_segment,
                speaker_brackets=speaker_brackets,
            )

            result = json.dumps(segments, indent=2)
            content_type = "application/json"

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": content_type,
                "Access-Control-Allow-Origin": "*",  # For CORS if needed
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
            },
            "body": result,
        }

    except ValueError as e:
        # Handle validation errors
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": f"Validation error: {str(e)}", "type": "ValidationError"}
            ),
        }

    except Exception as e:
        # Handle unexpected errors
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": f"Internal server error: {str(e)}", "type": type(e).__name__}
            ),
        }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "transcription": {
            "words": [
                {"text": "Hello", "start": 0.0, "end": 0.5, "speaker_id": "Speaker1"},
                {"text": "world.", "start": 0.5, "end": 1.0, "speaker_id": "Speaker1"},
                {"text": "How", "start": 2.0, "end": 2.3, "speaker_id": "Speaker2"},
                {"text": "are", "start": 2.3, "end": 2.5, "speaker_id": "Speaker2"},
                {"text": "you?", "start": 2.5, "end": 3.0, "speaker_id": "Speaker2"},
            ]
        },
        "format": "srt",
        "speaker_brackets": True,
    }

    result = lambda_handler(test_event, {})
    print("Status Code:", result["statusCode"])
    print("Content Type:", result["headers"]["Content-Type"])
    print("Body:")
    print(result["body"])
