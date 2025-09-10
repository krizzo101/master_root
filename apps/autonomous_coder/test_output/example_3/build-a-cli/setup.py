from setuptools import setup, find_packages

setup(
    name="build-a-cli",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "build-a-cli=cli:app",
        ],
    },
    python_requires=">=3.8",
)
