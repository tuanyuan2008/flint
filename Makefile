.PHONY: help install test run-api run-cli clean

help: ## Show this help message
	@echo "Section Detector - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies and setup environment
	@echo "Setting up development environment..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@echo "Installing dependencies..."
	@source venv/bin/activate && pip install -r requirements.txt
	@echo "Installing Chromium browser..."
	@source venv/bin/activate && playwright install chromium
	@echo "Setup complete!"

test: ## Run tests
	@echo "Running tests..."
	@source venv/bin/activate && python -m pytest tests/ -v

test-html: ## Test with example HTML file
	@echo "Testing with example HTML..."
	@source venv/bin/activate && python src/cli.py --file examples/example.html

test-url: ## Test with example URL
	@echo "Testing with example URL..."
	@source venv/bin/activate && python src/cli.py --url https://example.com

run-api: ## Start the FastAPI server
	@echo "Starting API server..."
	@source venv/bin/activate && python src/api.py

run-cli: ## Run CLI with example
	@echo "Running CLI example..."
	@source venv/bin/activate && python src/cli.py --url https://example.com

demo: ## Run a quick demo
	@echo "Running demo..."
	@source venv/bin/activate && python src/cli.py --file examples/example.html --output json

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	@rm -rf sections/
	@rm -rf output/
	@rm -rf __pycache__/
	@rm -rf src/__pycache__/
	@rm -rf tests/__pycache__/
	@find . -name "*.pyc" -delete
	@echo "Cleanup complete!"

dev: ## Start development mode (API + auto-reload)
	@echo "Starting development server..."
	@source venv/bin/activate && uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

format: ## Format code with black
	@echo "Formatting code..."
	@source venv/bin/activate && black src/ tests/

lint: ## Lint code with flake8
	@echo "Linting code..."
	@source venv/bin/activate && flake8 src/ tests/

check: format lint test ## Run all checks (format, lint, test)

package: ## Create distribution package
	@echo "Creating package..."
	@mkdir -p dist
	@tar -czf dist/flint-section-detector.tar.gz --exclude=venv --exclude=.git --exclude=__pycache__ --exclude=*.pyc .
	@echo "Package created: dist/flint-section-detector.tar.gz" 