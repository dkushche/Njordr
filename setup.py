from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="njordr",
    version="1.2",
    author="roothazard",
    description="Njordr telegram broker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dkushche/Njordr",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.5.3",
    ],
)
