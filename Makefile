PYTHON ?= python3
PYTHONPATH := src

.PHONY: setup demo test lint clean

setup:
	@$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 11), sys.version'
	@mkdir -p artifacts

demo: setup
	@PYTHONPATH="$(PYTHONPATH)" $(PYTHON) -m portfolio_proof report --examples examples --out artifacts/report.md
	@echo "Wrote artifacts/report.md"

test: setup
	@PYTHONPATH="$(PYTHONPATH)" $(PYTHON) -m unittest discover -s tests -p "test_*.py" -q

lint:
	@$(PYTHON) -m compileall -q src tests scripts
	@PYTHONPATH="$(PYTHONPATH)" $(PYTHON) -m portfolio_proof validate --examples examples

clean:
	@rm -rf artifacts
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
