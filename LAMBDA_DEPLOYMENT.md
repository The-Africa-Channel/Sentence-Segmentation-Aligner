# AWS Lambda Deployment Guide

This guide explains how to deploy the Sentence-Segmentation-Aligner to AWS Lambda.

## Installation Options

### Option 1: Standard Library Only (Recommended)
```bash
pip install sentence-segmentation-aligner
```

### Option 2: Enhanced Regex Support (For edge cases)
```bash
pip install sentence-segmentation-aligner[lambda]
```

## Lambda Layer Creation

### Method 1: Using Docker (Recommended)
```bash
# Create a Docker container to build the layer
docker run --rm -v $(pwd):/var/task lambci/lambda:build-python3.9 \
  pip install sentence-segmentation-aligner[lambda] -t /var/task/python/

# Zip the layer
zip -r lambda-layer.zip python/
```

### Method 2: Local Build (Linux/WSL)
```bash
mkdir -p lambda-layer/python
pip install sentence-segmentation-aligner[lambda] -t lambda-layer/python/
cd lambda-layer
zip -r ../lambda-layer.zip .
```

### Method 3: Using AWS SAM
Create a `template.yaml`:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  SentenceAlignerLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: sentence-aligner-layer
      Description: Sentence Segmentation Aligner
      ContentUri: lambda-layer/
      CompatibleRuntimes:
        - python3.9
        - python3.10
        - python3.11
        - python3.12
```

## Lambda Function Example

```python
import json
import aligner

def lambda_handler(event, context):
    """
    AWS Lambda function to process transcription data
    """
    try:
        # Parse input
        transcription_data = event.get('transcription', {})
        output_format = event.get('format', 'srt')
        max_duration = event.get('max_duration', 15.0)
        speaker_brackets = event.get('speaker_brackets', True)
        
        # Process transcription
        segments = aligner.segment_transcription(
            transcription_data, 
            max_duration=max_duration
        )
        
        if output_format.lower() == 'srt':
            result = aligner.save_segments_as_srt(
                segments,
                speaker_brackets=speaker_brackets,
                return_string=True
            )
        else:
            # Return segments as JSON
            result = json.dumps(segments, indent=2)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/plain' if output_format == 'srt' else 'application/json'
            },
            'body': result
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            })
        }
```

## Environment Variables

You can configure the following environment variables in your Lambda function:

- `DEFAULT_MAX_DURATION`: Default maximum segment duration (default: 15.0)
- `DEFAULT_LANGUAGE`: Default language code (default: "eng")

## Testing

Test your Lambda function locally:

```bash
# Run the compatibility test
python test_lambda_compatibility.py

# Test with sample data
python -c "
import json
from lambda_function import lambda_handler

event = {
    'transcription': {
        'words': [
            {'text': 'Hello', 'start': 0.0, 'end': 0.5},
            {'text': 'world.', 'start': 0.5, 'end': 1.0}
        ]
    },
    'format': 'srt'
}

result = lambda_handler(event, {})
print(json.dumps(result, indent=2))
"
```

## Troubleshooting

### Import Errors
If you get regex-related import errors:
1. Make sure you're using Python 3.9+ 
2. Install with the lambda extras: `pip install sentence-segmentation-aligner[lambda]`
3. Rebuild your Lambda layer

### Memory Issues
- Set Lambda memory to at least 256MB for typical transcriptions
- For large transcriptions (>1000 words), use 512MB or more

### Timeout Issues
- Set Lambda timeout to at least 30 seconds for typical use
- For large transcriptions, use 60-120 seconds

## Performance Tips

1. **Reuse Lambda containers**: Initialize the aligner module outside the handler function
2. **Use layers**: Include the package in a Lambda layer to reduce deployment size
3. **Optimize input**: Pre-filter unnecessary data before sending to Lambda
4. **Batch processing**: Process multiple transcriptions in a single Lambda invocation when possible

## Cost Optimization

- Use ARM64 architecture (Graviton2) for ~20% cost savings
- Right-size memory allocation based on your transcription sizes
- Consider using Lambda Provisioned Concurrency for consistent performance
