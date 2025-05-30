from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sentence-segmentation-aligner",
    version="0.1.0",
    description="A tool for segmenting and aligning sentences in transcriptions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Chris Eckman",
    url="https://github.com/chriseckman/Sentence-Segmentation-Aligner",
    packages=find_packages(),
    py_modules=["aligner"],    install_requires=[
        # Standard library only - no required dependencies
    ],
    extras_require={
        "lambda": [
            "regex>=2022.1.18",  # Enhanced regex for AWS Lambda compatibility
        ],
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
        ],
        "all": [
            "regex>=2022.1.18",
            "pytest>=6.0", 
            "pytest-cov>=2.10",
        ],
    },
    entry_points={"console_scripts": ["aligner=aligner:main"]},
    include_package_data=True,
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    keywords="transcription segmentation alignment speech nlp",
)
