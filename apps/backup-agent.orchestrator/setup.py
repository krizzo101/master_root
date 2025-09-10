from setuptools import find_packages, setup

setup(
    name="agent-orchestrator",
    version="1.0.0",
    description="Production-ready multi-agent orchestration framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.3.0",
        "watchdog>=3.0.0",
        "aiofiles>=23.0.0",
        "pydantic>=2.0.0",
        "websockets>=12.0",
        "aiohttp>=3.9.0",
        "psycopg2-binary>=2.9.0",
        "requests>=2.31.0",
        "redis>=4.5.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
