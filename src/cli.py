#!/usr/bin/env python3

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict

from section_detector import SectionDetector
from section import Section


async def analyze_url(detector: SectionDetector, url: str) -> List[Section]:
    """Analyze sections from a URL"""
    print(f"Analyzing sections for URL: {url}")
    print("Please wait...\n")

    sections = await detector.detect_sections_from_url(url)
    return sections


async def analyze_html_file(detector: SectionDetector, file_path: str) -> List[Section]:
    """Analyze sections from an HTML file"""
    print(f"Analyzing sections for HTML file: {file_path}")
    print("Please wait...\n")

    # Read the HTML file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        sys.exit(1)

    sections = await detector.detect_sections(html_content)
    return sections


def print_sections(sections: List[Section], output_format: str = "text"):
    """Print sections in the specified format"""

    if output_format == "json":
        # Output as JSON
        sections_data = []
        for section in sections:
            sections_data.append(
                {
                    "id": section.id,
                    "type": section.type,
                    "content": section.content,
                    "bounds": section.bounds,
                    "metadata": section.metadata,
                    "html": section.get_html(),
                }
            )

        print(json.dumps({"sections": sections_data, "total_sections": len(sections)}, indent=2))

    else:
        # Output as formatted text
        print(f"Found {len(sections)} sections:\n")

        for section in sections:
            print(f"   Section {section.id} ({section.type}):")
            print(f"   Content: {section.content[:100]}...")
            print(
                f"   Layout: {section.bounds['width']}x{section.bounds['height']} at ({section.bounds['left']}, {section.bounds['top']})"
            )
            print(f"   Elements: {section.metadata['elementCount']}")
            print(f"   Images: {'Yes' if section.metadata['hasImages'] else 'No'}")
            print(f"   Videos: {'Yes' if section.metadata['hasVideos'] else 'No'}")
            print("")

        # Summary
        type_counts: Dict[str, int] = {}
        for section in sections:
            type_counts[section.type] = type_counts.get(section.type, 0) + 1

        print("Summary:")
        for section_type, count in type_counts.items():
            print(f"   {section_type}: {count}")


async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Section Detector - Detect visual sections in web pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --url https://example.com
  python cli.py --file example.html
  python cli.py --url https://example.com --output json
        """,
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--url", help="URL to analyze")
    input_group.add_argument("--file", help="HTML file to analyze")

    # Output options
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument("--save-html", help="Save each section's HTML to the specified directory")

    args = parser.parse_args()

    # Initialize detector
    detector = SectionDetector()

    try:
        await detector.initialize()

        # Analyze based on input type
        if args.url:
            sections = await analyze_url(detector, args.url)
        else:
            sections = await analyze_html_file(detector, args.file)

        # Print results
        print_sections(sections, args.output)

        # Save HTML if requested
        if args.save_html:
            save_dir = Path(args.save_html)
            save_dir.mkdir(exist_ok=True)

            print(f"\nSaving section HTML to: {save_dir}")
            for section in sections:
                filename = save_dir / f"section_{section.id}_{section.type}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(section.get_clean_html())
                print(f"   Saved: {filename}")

    except KeyboardInterrupt:
        print("\n Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    finally:
        await detector.close()


if __name__ == "__main__":
    asyncio.run(main())
