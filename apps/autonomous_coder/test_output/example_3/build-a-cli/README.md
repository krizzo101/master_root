# build-a-cli CLI

Command-line tool built with Typer

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python cli.py --help
python cli.py hello --name "User"
python cli.py list-items --limit 20
python cli.py process input.txt -o output.txt -v
```

## Development

```bash
pip install -e .
```

## Building

```bash
python setup.py sdist bdist_wheel
```
