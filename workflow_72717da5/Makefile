.PHONY: install test run
install:
	pip install -r requirements.txt

test:
	pytest -q

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
