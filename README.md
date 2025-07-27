# Section Detector

A Python-based tool to identify visual sections in web pages using browser-based analysis. This solution addresses the challenge of breaking down complex web pages into manageable sections for AI processing.

## Problem Statement

When working with websites and AI, raw HTML/CSS/JS can be too large to fit into modern foundational models' context windows. This tool helps break down web pages into sections that can be processed individually, making them more manageable for AI applications.

## Features

- **Visual-First Analysis**: Uses browser rendering to understand actual layout
- **Smart Section Detection**: Identifies sections based on whitespace separation and visual cues
- **HTML Reconstruction**: Each section contains the original HTML elements
- **Multiple Input Methods**: Works with URLs, HTML files, or direct HTML content
- **REST API**: FastAPI-based HTTP endpoints for integration
- **CLI Tool**: Command-line interface for quick testing
- **Comprehensive Testing**: Full test suite with pytest
- **Automatic Environment**: Uses direnv for seamless development setup
- **Fast Setup**: Only installs Chromium browser (not all browsers)
- **All-in-One Dependencies**: Single requirements.txt with both production and development tools

## Quick Start

### Option 1: Using direnv (Recommended)

1. Install direnv:
```bash
# macOS
brew install direnv

# Ubuntu/Debian
sudo apt-get install direnv

# Or download from https://direnv.net/
```

2. Clone and setup:
```bash
git clone <repository-url>
cd flint-section-detector
direnv allow  # This will automatically create venv and install dependencies
```

3. Run a demo:
```bash
make demo
```

### Option 2: Manual Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd flint-section-detector
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Chromium browser (faster than all browsers):
```bash
playwright install chromium
```

## Development Commands

The project includes a comprehensive Makefile for common tasks:

```bash
make help          # Show all available commands
make install       # Setup environment and install dependencies
make test          # Run all tests
make test-html     # Test with example HTML file
make test-url      # Test with example URL
make run-api       # Start the FastAPI server
make run-cli       # Run CLI with example
make demo          # Run a quick demo
make dev           # Start development server with auto-reload
make clean         # Clean up generated files
make format        # Format code with black
make lint          # Lint code with flake8
make check         # Run format, lint, and tests
```

## Usage

### Command Line Interface

Analyze a website by URL:
```bash
python src/cli.py --url https://example.com
```

Analyze an HTML file:
```bash
python src/cli.py --file examples/example.html
```

Output as JSON:
```bash
python src/cli.py --url https://example.com --output json
```

Save section HTML to files:
```bash
python src/cli.py --url https://example.com --save-html sections/
```

### REST API

Start the server:
```bash
python src/api.py
# or
make run-api
```

The API will be available at `http://localhost:8000`

#### Endpoints

**Detect sections from URL:**
```bash
POST /api/detect-sections
Content-Type: application/json

{
  "url": "https://example.com"
}
```

**Analyze HTML content directly:**
```bash
POST /api/analyze-html
Content-Type: application/json

{
  "html": "<html>...</html>"
}
```

**Health check:**
```bash
GET /health
```

**API documentation:**
```bash
GET /docs
```

### Example Response

```json
{
  "url": "https://example.com",
  "sections": [
    {
      "id": 1,
      "type": "header",
      "content": "Website Header Navigation Menu",
      "bounds": {
        "top": 0,
        "left": 0,
        "width": 1200,
        "height": 80
      },
      "metadata": {
        "hasImages": false,
        "hasVideos": false,
        "elementCount": 5
      },
      "html": "<header class=\"header\">...</header>"
    }
  ],
  "total_sections": 5,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## How It Works

### Visual-First Analysis

1. **Browser Rendering**: Uses Playwright with Chromium to render HTML exactly as a user sees it
2. **Element Analysis**: Captures computed styles, positions, and layout information
3. **Visual Separation**: Detects sections based on:
   - Vertical spacing between elements (>20px threshold)
   - Background color changes
   - Border lines and dividers
   - Content density variations

### Section Detection Algorithm

1. **Element Filtering**: Identifies elements with significant content (text, images, videos)
2. **Visual Grouping**: Groups elements based on proximity and styling
3. **Section Classification**: Categorizes sections as header, hero, content, sidebar, footer
4. **HTML Reconstruction**: Preserves original HTML elements for each section

### Key Heuristics

- **Whitespace Threshold**: 20px minimum separation between sections
- **Size Filtering**: Sections must be at least 30px tall and 100px wide
- **Content Requirements**: Sections must have meaningful content
- **Styling Analysis**: Considers margins, padding, backgrounds, and borders

## Testing

Run the test suite:
```bash
make test
# or
pytest tests/ -v
```

Test with a specific example:
```bash
make test-html
# or
python src/cli.py --file examples/example.html
```

## API Documentation

### POST /api/detect-sections

Detects sections from a live website URL.

**Request Body:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "sections": [...],
  "total_sections": 5,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### POST /api/analyze-html

Analyzes HTML content directly.

**Request Body:**
```json
{
  "html": "<html>...</html>"
}
```

**Response:**
```json
{
  "sections": [...],
  "total_sections": 3,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## Section Types

- **header**: Navigation and site branding (typically at top)
- **hero**: Large banner sections with images/videos
- **content**: Main text content areas
- **sidebar**: Narrow side panels
- **footer**: Bottom sections with links and copyright
- **section**: Generic sections that don't fit other categories

## Technical Approach

### Why Browser-Based Analysis?

1. **Visual Accuracy**: Sees the page exactly as users do
2. **CSS Understanding**: Handles complex layouts, flexbox, grid
3. **JavaScript Support**: Processes dynamic content
4. **Real Positioning**: Gets actual rendered positions and sizes

### HTML Reconstruction

Each section preserves the original HTML elements, allowing you to:
- Reconstruct the original page from sections
- Process sections independently
- Maintain styling and functionality
- Extract clean, reusable components

## Performance Characteristics

- **Speed**: ~2-5 seconds per website analysis
- **Accuracy**: Excellent section boundary detection
- **Reliability**: Handles various website structures
- **Scalability**: Stateless API design
- **Setup Speed**: Only installs Chromium (not all browsers)

## Dependencies

- **Playwright**: Browser automation for rendering and layout analysis (Chromium only)
- **FastAPI**: Modern web framework for API development
- **Pydantic**: Data validation and serialization
- **Pytest**: Testing framework
- **Uvicorn**: ASGI server
- **Development Tools**: black (formatting), flake8 (linting), mypy (type checking), pre-commit (git hooks)

## Development Setup

The project includes all development tools in the main requirements.txt:

- **black**: Code formatting
- **flake8**: Code linting
- **pytest-cov**: Test coverage
- **mypy**: Type checking
- **pre-commit**: Git hooks

All tools are automatically installed with `pip install -r requirements.txt`.

## Future Improvements

- **Machine Learning**: Train models on labeled section data
- **Semantic Analysis**: Use NLP to understand section content
- **Mobile Support**: Better handling of responsive layouts
- **Performance**: Caching and parallel processing
- **More Section Types**: Product grids, testimonials, forms

## License

MIT License - see LICENSE file for details. 