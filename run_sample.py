import os
import sys
import subprocess

# Path to the aligner script and sample transcription file
ALIGNER_SCRIPT = os.path.join(os.path.dirname(__file__), "aligner.py")
SAMPLE_JSON = os.path.join(os.path.dirname(__file__), "sample", "transcription.json")

if not os.path.exists(ALIGNER_SCRIPT):
    print(f"Error: aligner.py not found at {ALIGNER_SCRIPT}")
    sys.exit(1)

if not os.path.exists(SAMPLE_JSON):
    print(f"Error: transcription.json not found at {SAMPLE_JSON}")
    sys.exit(1)

# Run the aligner script with the sample transcription file
try:
    result = subprocess.run(
        [sys.executable, ALIGNER_SCRIPT, SAMPLE_JSON],
        cwd=os.path.dirname(__file__),
        check=True,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("Error running aligner.py:")
    print(e.stderr)
    sys.exit(1)
