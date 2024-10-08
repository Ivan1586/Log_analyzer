.PHONY: all black_check isort_check mypy_check test clean start

all: black_check isort_check mypy_check test

black_check:
	@echo "From Makefile run black..."
	poetry run black src/log_analyzer.py

isort_check:
	@echo "From Makefile run isort..."
	poetry run isort .

mypy_check:
	@echo "From Makefile run mypy..."
	poetry run mypy src/log_analyzer.py

test:
	@echo "From Makefile run pytest..."
	poetry run pytest

clean:
	@echo "Cleaning..."
	rm -rf __pycache__
	rm -rf *.pyc

start:
	@echo "From Makefile start log_analyzer..."
	python3 src/log_analyzer.py
