.PHONY: install setup clean test tree docs

.DEFAULT_GOAL := setup

SHELL := /bin/bash

PROFILE_NAME := "DEFAULT"

install:
	@CURRENT_OS=$$(uname -s); \
	echo "Current OS: $$CURRENT_OS"; \
	if [ "$$CURRENT_OS" = "Darwin" ]; then \
		echo "Verifying if Homebrew is installed..."; \
		which brew > /dev/null || (echo "Homebrew is not installed. Installing Homebrew..." && /bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"); \
		echo "Installing tools..."; \
		for tool in git uv; do \
			if ! command -v $$tool >/dev/null 2>&1; then \
				echo "Installing $$tool..."; \
				brew install $$tool; \
			else \
				echo "$$tool is already installed. Skipping."; \
			fi; \
		done; \
	elif [ "$$CURRENT_OS" = "Linux" ]; then \
		echo "Installing tools..."; \
		if ! command -v git >/dev/null 2>&1; then \
				echo "Installing git..."; \
				sudo apt update && sudo apt install -y git; \
			else \
				echo "git is already installed. Skipping."; \
			fi; \
		if ! command -v uv >/dev/null 2>&1; then \
			echo "Installing uv..."; \
			curl -LsSf https://astral.sh/uv/install.sh | sh; \
			echo "Sourcing ~/.bashrc to update shell environment..."; \
			source ~/.bashrc || true; \
			echo "Continuing even if sourcing ~/.bashrc failed..."; \
		else \
			echo "uv is already installed. Skipping."; \
		fi; \
	else \
		echo "Unsupported OS. Currently supported kernels are either Darwin (macOS) or Linux (ubuntu22.04)."; \
		exit 1; \
	fi; \

	echo "Setting up Python..."; \
	uv python install || true; \
	echo "All tools installed successfully."

setup:
	@echo "Installing tools..."
	@{ \
		output=$$($(MAKE) install 2>&1); \
		exit_code=$$?; \
		if [ $$exit_code -ne 0 ]; then \
			echo "$$output"; \
			exit $$exit_code; \
		fi; \
	}
	@echo "All tools installed successfully."
	@echo "Setting up the project..."

	@uv sync;

	@if [ ! -d ".git" ]; then \
		echo "Setting up git..."; \
		git init -b main > /dev/null; \
	fi

	@echo "Setting up pre-commit..."
	@. .venv/bin/activate
	@.venv/bin/pre-commit install --hook-type pre-commit --hook-type commit-msg

	@echo "Setup completed successfully!"

clean:
	@echo "Uninstalling local packages..."
	@rm -rf uv.lock
	@
	@uv sync

	@echo -e "Cleaning up project artifacts..."
	@find . \( \
		-name ".pytest_cache" -o \
		-name ".mypy_cache" -o \
		-name ".ruff_cache" -o \
		-name "dist" -o \
		-name "__pycache__" -o \
		-name ".ipynb_checkpoints" \) \
		-type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".coverage" -type f -delete 2>/dev/null || true

	@echo "Cleanup completed."
	@reset

test:
	@echo "Running tests..."
	@. .venv/bin/activate

	@uv build
	@uv sync
	@uv run pytest -v tests --cov=src --cov-report=term

deploy: deploy_dev



tree:
	@echo "Generating project tree..."
	@tree -I '.venv|__pycache__|archive|scratch|.databricks|.ruff_cache|.mypy_cache|.pytest_cache|.git|htmlcov|site|dist|.DS_Store|fixtures' -a

docs:
	@echo "Running tests and generating coverage data..."
	@. .venv/bin/activate
	@uv run pytest -v tests --cov=src --junitxml=docs/tests/coverage/pytest_coverage.xml
	# @uv run coverage xml -o docs/tests/coverage/coverage.xml
	@echo "Generating HTML documentation..."
	@uv run pdoc --html src/extractor -o docs/api --force
	# @uv run pdoc --html tests -o docs/api --force
	@uv run mkdocs serve
