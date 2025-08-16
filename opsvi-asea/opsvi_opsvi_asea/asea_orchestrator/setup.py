from setuptools import setup, find_packages

setup(
    name="asea_orchestrator",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "celery",
        "requests",
        # Add other dependencies here as needed
    ],
    entry_points={
        "console_scripts": [
            "asea-run-workflow=asea_orchestrator.scripts.run_qa_workflow:main",
        ],
    },
)
