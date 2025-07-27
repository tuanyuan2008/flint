from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Browser, Page
from section import Section


class SectionDetector:
    """Detects visual sections in web pages using browser-based analysis"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright: Optional[Any] = None

    async def initialize(self):
        """Initialize the browser for analysis"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

    async def close(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def detect_sections(self, html_content: str) -> List[Section]:
        """
        Detect sections in HTML content using visual analysis

        Args:
            html_content: Raw HTML string to analyze

        Returns:
            List of Section objects
        """
        if not self.browser:
            await self.initialize()

        if self.browser is None:
            raise RuntimeError("Failed to initialize browser")

        page = await self.browser.new_page()

        try:
            # Set the HTML content and wait for it to render
            await page.set_content(html_content)
            await page.wait_for_load_state("networkidle")

            # Analyze the page structure
            sections_data = await self._analyze_page_structure(page)

            # Convert to Section objects
            sections = self._create_section_objects(sections_data)

            return sections

        finally:
            await page.close()

    async def detect_sections_from_url(self, url: str) -> List[Section]:
        """
        Detect sections from a live URL

        Args:
            url: URL to analyze

        Returns:
            List of Section objects
        """
        if not self.browser:
            await self.initialize()

        if self.browser is None:
            raise RuntimeError("Failed to initialize browser")

        page = await self.browser.new_page()

        try:
            # Navigate to the URL
            await page.goto(url, wait_until="networkidle")

            # Analyze the page structure
            sections_data = await self._analyze_page_structure(page)

            # Convert to Section objects
            sections = self._create_section_objects(sections_data)

            return sections

        finally:
            await page.close()

    async def _analyze_page_structure(self, page: Page) -> List[Dict]:
        """Analyze the page structure to identify sections"""

        # Get all elements with their computed styles and positions
        elements_data = await page.evaluate(
            """
            () => {
                const elements = document.querySelectorAll('*');
                return Array.from(elements).map(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    
                    return {
                        tagName: el.tagName.toLowerCase(),
                        textContent: el.textContent.trim(),
                        outerHTML: el.outerHTML,
                        rect: {
                            top: rect.top,
                            left: rect.left,
                            width: rect.width,
                            height: rect.height,
                            bottom: rect.bottom,
                            right: rect.right
                        },
                        styles: {
                            backgroundColor: style.backgroundColor,
                            marginTop: parseInt(style.marginTop),
                            marginBottom: parseInt(style.marginBottom),
                            paddingTop: parseInt(style.paddingTop),
                            paddingBottom: parseInt(style.paddingBottom),
                            borderTop: style.borderTop,
                            borderBottom: style.borderBottom,
                            display: style.display,
                            visibility: style.visibility,
                            position: style.position
                        },
                        hasImages: el.querySelector('img') !== null,
                        hasVideos: el.querySelector('video, iframe') !== null
                    };
                }).filter(el =>
                    el.rect.width > 50 &&
                    el.rect.height > 50 &&
                    el.styles.display !== 'none' &&
                    el.styles.visibility !== 'hidden' &&
                    (el.textContent.length > 0 || el.hasImages || el.hasVideos)
                );
            }
        """
        )

        # Group elements into sections based on visual separation
        sections = self._group_elements_into_sections(elements_data)

        return sections

    def _group_elements_into_sections(self, elements: List[Dict]) -> List[Dict]:
        """Group elements into sections based on visual separation"""
        if not elements:
            return []

        # Filter out very small or insignificant elements first
        significant_elements = []
        for element in elements:
            rect = element["rect"]

            # Skip very small elements (likely decorative)
            if rect["width"] < 80 or rect["height"] < 40:
                continue

            # Skip elements with very little content
            if (
                not element["textContent"].strip()
                and not element["hasImages"]
                and not element["hasVideos"]
            ):
                continue

            # Skip elements that are likely just containers without meaningful content
            if (
                len(element["textContent"].strip()) < 10
                and not element["hasImages"]
                and not element["hasVideos"]
            ):
                continue

            significant_elements.append(element)

        if not significant_elements:
            return []

        # Sort elements by vertical position (top to bottom)
        sorted_elements = sorted(significant_elements, key=lambda x: x["rect"]["top"])

        sections = []
        current_section: Optional[Dict[str, Any]] = None

        for element in sorted_elements:
            rect = element["rect"]

            # Check if this element should start a new section
            should_start_new_section = False

            if current_section is None:
                should_start_new_section = True
            else:
                # Check for significant vertical gap (whitespace)
                current_bottom = (
                    current_section["bounds"]["top"] + current_section["bounds"]["height"]
                )
                gap = rect["top"] - current_bottom

                # Start new section if there's significant gap (> 100px) or if element is very different
                if gap > 100:
                    should_start_new_section = True
                elif gap > 50:
                    # Check if this element is significantly different from current section
                    current_center = (
                        current_section["bounds"]["left"] + current_section["bounds"]["width"] / 2
                    )
                    element_center = rect["left"] + rect["width"] / 2
                    horizontal_distance = abs(current_center - element_center)

                    # If element is far from current section center, start new section
                    if (
                        horizontal_distance
                        > max(rect["width"], current_section["bounds"]["width"]) * 0.4
                    ):
                        should_start_new_section = True

                # Also check if this element has significantly different content type
                current_has_media = current_section["hasImages"] or current_section["hasVideos"]
                element_has_media = element["hasImages"] or element["hasVideos"]

                if current_has_media != element_has_media and (
                    element["textContent"].strip() or element_has_media
                ):
                    should_start_new_section = True

                # Check for significant styling differences that suggest section boundaries
                if self._has_significant_styling(element.get("styles", {})):
                    should_start_new_section = True

            if should_start_new_section:
                # Save current section if it has meaningful content
                if current_section is not None and current_section.get("elementCount", 0) > 0:
                    # Only add sections with substantial content
                    content = current_section.get("content", "")
                    has_images = current_section.get("hasImages", False)
                    has_videos = current_section.get("hasVideos", False)
                    if len(content.strip()) > 30 or has_images or has_videos:
                        sections.append(current_section)

                # Start new section
                current_section = {
                    "id": len(sections) + 1,
                    "bounds": {
                        "top": rect["top"],
                        "left": rect["left"],
                        "width": rect["width"],
                        "height": rect["height"],
                    },
                    "elements": [element["outerHTML"]],
                    "elementCount": 1,
                    "content": element["textContent"].strip(),
                    "hasImages": element["hasImages"],
                    "hasVideos": element["hasVideos"],
                }
            else:
                # Add to current section
                if current_section is not None:
                    # Only add substantial elements
                    if (
                        rect["width"] > 80
                        and rect["height"] > 40
                        and (
                            element["textContent"].strip()
                            or element["hasImages"]
                            or element["hasVideos"]
                        )
                    ):

                        # Check if this element is already in the section to avoid duplicates
                        element_html = element["outerHTML"]
                        if element_html not in current_section["elements"]:
                            current_section["elements"].append(element_html)
                            current_section["elementCount"] += 1

                            # Update section bounds to include this element
                            current_section["bounds"]["top"] = min(
                                current_section["bounds"]["top"], rect["top"]
                            )
                            current_section["bounds"]["left"] = min(
                                current_section["bounds"]["left"], rect["left"]
                            )
                            current_section["bounds"]["width"] = max(
                                current_section["bounds"]["width"],
                                rect["left"] + rect["width"] - current_section["bounds"]["left"],
                            )
                            current_section["bounds"]["height"] = max(
                                current_section["bounds"]["height"],
                                rect["top"] + rect["height"] - current_section["bounds"]["top"],
                            )

                            # Update content
                            if element["textContent"].strip():
                                current_section["content"] += " " + element["textContent"].strip()
                            current_section["hasImages"] = (
                                current_section["hasImages"] or element["hasImages"]
                            )
                            current_section["hasVideos"] = (
                                current_section["hasVideos"] or element["hasVideos"]
                            )

        # Add final section
        if current_section is not None and current_section["elementCount"] > 0:
            # Only add sections with substantial content
            if (
                len(current_section["content"].strip()) > 30
                or current_section["hasImages"]
                or current_section["hasVideos"]
            ):
                sections.append(current_section)

        # Post-process: merge very close sections and remove duplicates
        return self._merge_close_sections(sections)

    def _merge_close_sections(self, sections: List[Dict]) -> List[Dict]:
        """Merge sections that are very close to each other"""
        if len(sections) <= 1:
            return sections

        merged = []
        i = 0

        while i < len(sections):
            current = sections[i]
            merged_section = current.copy()

            # Look ahead for sections that should be merged
            j = i + 1
            while j < len(sections):
                next_section = sections[j]

                # Check if sections are very close vertically
                current_bottom = current["bounds"]["top"] + current["bounds"]["height"]
                gap = next_section["bounds"]["top"] - current_bottom

                # Merge if gap is small (< 30px) and sections are similar
                if gap < 30:
                    # Merge the sections
                    merged_section["bounds"]["height"] = (
                        next_section["bounds"]["top"]
                        + next_section["bounds"]["height"]
                        - merged_section["bounds"]["top"]
                    )
                    merged_section["bounds"]["width"] = max(
                        merged_section["bounds"]["width"], next_section["bounds"]["width"]
                    )

                    # TODO: how to validly merge HTML elements?
                    merged_section["elements"] += next_section["elements"]
                    merged_section["elementCount"] = len(merged_section["elements"])
                    merged_section["content"] += " " + next_section["content"]
                    merged_section["hasImages"] = (
                        merged_section["hasImages"] or next_section["hasImages"]
                    )
                    merged_section["hasVideos"] = (
                        merged_section["hasVideos"] or next_section["hasVideos"]
                    )

                    j += 1
                else:
                    break

            merged.append(merged_section)
            i = j

        return merged

    def _has_significant_styling(self, styles: Dict) -> bool:
        """Detect if element has styling that suggests section separation"""
        return (
            styles["marginTop"] > 20
            or styles["marginBottom"] > 20
            or styles["paddingTop"] > 20
            or styles["paddingBottom"] > 20
            or styles["backgroundColor"] not in ["rgba(0, 0, 0, 0)", "transparent"]
            or styles["borderTop"] != "0px none"
            or styles["borderBottom"] != "0px none"
        )

    def _has_border_separator(self, styles: Dict) -> bool:
        """Detect border lines that indicate section separation"""
        border_top = styles["borderTop"]
        border_bottom = styles["borderBottom"]

        # Look for solid borders with significant thickness
        return (
            "solid" in border_top
            and any(color in border_top.lower() for color in ["red", "#ff0000", "rgb(255,0,0)"])
            or "solid" in border_bottom
            and any(color in border_bottom.lower() for color in ["red", "#ff0000", "rgb(255,0,0)"])
        )

    def _create_section_objects(self, sections_data: List[Dict]) -> List[Section]:
        """Convert section data to Section objects"""
        section_objects = []

        for i, section_data in enumerate(sections_data):
            # Filter out sections that are too small or have no content
            if (
                section_data["bounds"]["height"] < 30
                or section_data["bounds"]["width"] < 100
                or (
                    len(section_data["content"].strip()) < 10
                    and not section_data.get("hasImages", False)
                    and not section_data.get("hasVideos", False)
                )
            ):
                continue

            section = Section(
                id=i + 1,
                type=self._classify_section(section_data),
                content=section_data["content"][:200],
                html_elements=section_data["elements"],
                bounds=section_data["bounds"],
                metadata={
                    "hasImages": section_data.get("hasImages", False),
                    "hasVideos": section_data.get("hasVideos", False),
                    "elementCount": section_data.get("elementCount", 0),
                },
            )
            section_objects.append(section)

        return section_objects

    def _classify_section(self, section_data: Dict) -> str:
        """Determine section type based on content and position"""
        text = section_data["content"].lower()
        bounds = section_data["bounds"]

        # Header detection
        if bounds["top"] < 200 and any(
            word in text for word in ["menu", "nav", "header", "navigation"]
        ):
            return "header"

        # Footer detection
        if any(word in text for word in ["footer", "copyright", "privacy", "terms"]):
            return "footer"

        # Hero section detection
        if bounds["height"] > 300 and (section_data["hasImages"] or section_data["hasVideos"]):
            return "hero"

        # Content section
        if len(section_data["content"]) > 100:
            return "content"

        # Sidebar detection
        if bounds["width"] < 300 and bounds["height"] > 500:
            return "sidebar"

        return "section"
