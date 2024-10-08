.PHONY: all black_check isort_check mypy_check test clean start flake8_check

all: black_check isort_check mypy_check flake8_check test

black_check:
	@echo "From Makefile run black..."
	poetry run black src/log_analyzer.py

isort_check:
	@echo "From Makefile run isort..."
	poetry run isort src/log_analyzer.py

mypy_check:
	@echo "From Makefile run mypy..."
	poetry run mypy src/log_analyzer.py

flake8_check:
	@echo "From Makefile run flake8..."
	poetry run flake8 src/log_analyzer.py

test:
	@echo "From Makefile run pytest..."
	poetry run pytest tests/test_nginx_log_file.py

clean:
	@echo "Cleaning..."
	rm -rf __pycache__
	rm -rf *.pyc

start:
	@echo "From Makefile start log_analyzer..."
	python3 src/log_analyzer.py
