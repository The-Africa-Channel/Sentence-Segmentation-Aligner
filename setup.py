from setuptools import setup, find_packages

setup(
    name="sentence-segmentation-aligner",
    version="0.1.0",
    description="A tool for segmenting and aligning sentences in transcriptions.",
    author="Chris Eckman",
    packages=find_packages(),
    py_modules=["aligner"],
    install_requires=["nltk==3.8.1"],
    entry_points={"console_scripts": ["aligner=aligner:main"]},
    include_package_data=True,
    python_requires=">=3.7",
)
