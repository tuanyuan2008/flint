import sys
from pathlib import Path

# flake8: noqa: E402
import pytest
import pytest_asyncio

from section_detector import SectionDetector, Section

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class TestSectionDetector:
    """Test cases for the SectionDetector class"""

    @pytest_asyncio.fixture
    async def detector(self):
        """Create a detector instance for testing"""
        detector = SectionDetector()
        await detector.initialize()
        yield detector
        await detector.close()

    @pytest.mark.asyncio
    async def test_detect_sections_from_html(self, detector):
        """Test section detection from HTML content"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <header style="background: blue; padding: 20px;">
                <h1>Test Header</h1>
                <nav>Navigation</nav>
            </header>
            <main style="padding: 40px;">
                <h2>Main Content</h2>
                <p>This is the main content section with lots of text.</p>
            </main>
            <footer style="background: gray; padding: 20px;">
                <p>Copyright 2024</p>
            </footer>
        </body>
        </html>
        """

        sections = await detector.detect_sections(html_content)

        assert len(sections) > 0
        assert all(isinstance(section, Section) for section in sections)

        # Check that we have different section types
        section_types = [section.type for section in sections]
        assert len(set(section_types)) > 1

    @pytest.mark.asyncio
    async def test_section_html_reconstruction(self, detector):
        """Test that sections can reconstruct their HTML"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <div style="padding: 20px; background: red;">
                <h1>Test Section</h1>
                <p>This is a test section.</p>
            </div>
        </body>
        </html>
        """

        sections = await detector.detect_sections(html_content)

        for section in sections:
            html = section.get_html()
            assert html is not None
            assert len(html) > 0
            assert "<" in html  # Should contain HTML tags

    @pytest.mark.asyncio
    async def test_section_classification(self, detector):
        """Test that sections are properly classified"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <header style="padding: 20px;">
                <h1>Header</h1>
                <nav>Navigation</nav>
            </header>
            <section style="padding: 40px; height: 400px;">
                <h2>Hero Section</h2>
                <img src="hero.jpg" alt="Hero">
            </section>
            <aside style="width: 200px; height: 600px;">
                <h3>Sidebar</h3>
                <ul><li>Link 1</li></ul>
            </aside>
            <footer style="padding: 20px;">
                <p>Copyright 2024</p>
            </footer>
        </body>
        </html>
        """

        sections = await detector.detect_sections(html_content)

        # Check that we have expected section types
        section_types = [section.type for section in sections]

        # Should have header, hero, sidebar, footer, or content sections
        expected_types = ["header", "hero", "sidebar", "footer", "content", "section"]
        for section_type in section_types:
            assert section_type in expected_types

    @pytest.mark.asyncio
    async def test_section_metadata(self, detector):
        """Test that sections have proper metadata"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <div style="padding: 20px;">
                <h1>Test Section</h1>
                <p>This is a test section with an image.</p>
                <img src="test.jpg" alt="Test">
            </div>
        </body>
        </html>
        """

        sections = await detector.detect_sections(html_content)

        for section in sections:
            assert hasattr(section, "id")
            assert hasattr(section, "type")
            assert hasattr(section, "content")
            assert hasattr(section, "bounds")
            assert hasattr(section, "metadata")
            assert hasattr(section, "html_elements")

            # Check metadata fields
            assert "hasImages" in section.metadata
            assert "hasVideos" in section.metadata
            assert "elementCount" in section.metadata

            # Check bounds
            assert "top" in section.bounds
            assert "left" in section.bounds
            assert "width" in section.bounds
            assert "height" in section.bounds

    @pytest.mark.asyncio
    async def test_section_bounds(self, detector):
        """Test that sections have valid bounds"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <div style="padding: 20px;">
                <h1>Test Section</h1>
                <p>This is a test section.</p>
            </div>
        </body>
        </html>
        """

        sections = await detector.detect_sections(html_content)

        for section in sections:
            bounds = section.bounds

            # Bounds should be positive numbers
            assert bounds["top"] >= 0
            assert bounds["left"] >= 0
            assert bounds["width"] > 0
            assert bounds["height"] > 0

    @pytest.mark.asyncio
    async def test_empty_html(self, detector):
        """Test handling of empty HTML"""
        html_content = "<!DOCTYPE html><html><body></body></html>"

        sections = await detector.detect_sections(html_content)

        # Should handle empty HTML gracefully
        assert isinstance(sections, list)

    @pytest.mark.asyncio
    async def test_complex_layout(self, detector):
        """Test detection in complex layouts"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .header { background: blue; padding: 20px; }
                .hero { background: gray; padding: 40px; height: 300px; }
                .content { padding: 20px; }
                .sidebar { width: 200px; height: 500px; background: lightgray; }
                .footer { background: darkgray; padding: 20px; }
            </style>
        </head>
        <body>
            <header class="header">
                <h1>Header</h1>
                <nav>Navigation</nav>
            </header>
            <section class="hero">
                <h2>Hero Section</h2>
                <img src="hero.jpg" alt="Hero">
            </section>
            <div style="display: flex;">
                <main class="content">
                    <h3>Main Content</h3>
                    <p>This is the main content area with lots of text content.</p>
                </main>
                <aside class="sidebar">
                    <h4>Sidebar</h4>
                    <ul><li>Link 1</li><li>Link 2</li></ul>
                </aside>
            </div>
            <footer class="footer">
                <p>Copyright 2024</p>
            </footer>
        </body>
        </html>
        """

        sections = await detector.detect_sections(html_content)

        assert len(sections) > 0

        # Check that sections are ordered properly (top to bottom)
        for i in range(len(sections) - 1):
            assert sections[i].bounds["top"] <= sections[i + 1].bounds["top"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
