import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="Text-Summarizer",
    version="1.0.0",
    author="DevSourcerer04",
    author_email="builder4107@gmail.com",
    description="Inference-only text summarization app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
)
