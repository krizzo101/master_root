from setuptools import setup, find_packages

setup(
    name="asea_factory",
    version="0.1.0",
    description="SDLC Automation Factory",
    author="Autonomous Agent",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "pydantic",
        "pyyaml",
        "argparse",
        "arango",
        "redis",
        "openai",
        "langchain",
        "langgraph",
        "fastapi",
        "uvicorn",
        "pytest",
        "prometheus-client",
        "grafana-api",
    ],
    entry_points={
        "console_scripts": [
            "asea=asea_factory.cli.cli:main",
        ],
    },
    include_package_data=True,
    python_requires=">=3.11",
)
