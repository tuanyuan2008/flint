from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class Section:
    """Represents a detected section in a web page"""

    id: int
    type: str  # header, content, sidebar, footer, hero, etc.
    content: str  # text content
    html_elements: List[str]  # original HTML elements
    bounds: Dict[str, int]  # position and size
    metadata: Dict[str, Any]  # additional info

    def get_html(self) -> str:
        """Reconstruct the HTML for this section"""
        if not self.html_elements:
            return ""

        html_parts = [
            f'<div class="section section-{self.type}" data-section-id="{self.id}">'
        ]
        html_parts.extend(self.html_elements)
        html_parts.append("</div>")
        return "\n".join(html_parts)

    def get_clean_html(self) -> str:
        """Get HTML with proper indentation and structure"""
        if not self.html_elements:
            return ""

        html_parts = [
            f'<div class="section section-{self.type}" data-section-id="{self.id}">'
        ]
        html_parts.extend(self.html_elements)
        html_parts.append("</div>")

        return self._format_html(html_parts)

    def _format_html(self, elements: List[str]) -> str:
        """Format HTML with proper indentation"""
        formatted = []
        indent_level = 0

        for element in elements:
            if element.strip().startswith("</"):
                indent_level -= 1

            formatted.append("  " * max(0, indent_level) + element.strip())

            if (
                element.strip().startswith("<")
                and not element.strip().startswith("</")
                and not element.strip().endswith("/>")
            ):
                indent_level += 1

        return "\n".join(formatted)
