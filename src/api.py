from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uvicorn

from section_detector import SectionDetector

app = FastAPI(
    title="Section Detector API",
    description="Detect visual sections in web pages using a browser-based analysis",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize section detector
detector = SectionDetector()


class URLRequest(BaseModel):
    url: str


class HTMLRequest(BaseModel):
    html: str


class SectionResponse(BaseModel):
    id: int
    type: str
    content: str
    bounds: Dict[str, int]
    metadata: Dict[str, Any]
    html: str


class DetectionResponse(BaseModel):
    url: Optional[str] = None
    sections: List[SectionResponse]
    total_sections: int
    timestamp: str


@app.on_event("startup")
async def startup_event():
    """Initialize the section detector on startup"""
    await detector.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await detector.close()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Section Detector API is running",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/detect-sections", response_model=DetectionResponse)
async def detect_sections_from_url(request: URLRequest):
    """
    Detect sections from a live URL

    Args:
        request: URLRequest containing the URL to analyze

    Returns:
        DetectionResponse with detected sections
    """
    try:
        print(f"Analyzing sections for URL: {request.url}")

        sections = await detector.detect_sections_from_url(request.url)

        # Convert sections to response format
        section_responses = []
        for section in sections:
            section_response = SectionResponse(
                id=section.id,
                type=section.type,
                content=section.content,
                bounds=section.bounds,
                metadata=section.metadata,
                html=section.get_html(),
            )
            section_responses.append(section_response)

        return DetectionResponse(
            url=request.url,
            sections=section_responses,
            total_sections=len(sections),
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        print(f"Error detecting sections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to detect sections: {str(e)}")


@app.post("/api/analyze-html", response_model=DetectionResponse)
async def analyze_html_content(request: HTMLRequest):
    """
    Analyze HTML content directly

    Args:
        request: HTMLRequest containing the HTML content

    Returns:
        DetectionResponse with detected sections
    """
    try:
        print(f"Analyzing HTML content ({len(request.html)} characters)")

        sections = await detector.detect_sections(request.html)

        # Convert sections to response format
        section_responses = []
        for section in sections:
            section_response = SectionResponse(
                id=section.id,
                type=section.type,
                content=section.content,
                bounds=section.bounds,
                metadata=section.metadata,
                html=section.get_html(),
            )
            section_responses.append(section_response)

        return DetectionResponse(
            sections=section_responses,
            total_sections=len(sections),
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        print(f"Error analyzing HTML: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze HTML: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get API statistics and endpoint information"""
    return {
        "endpoints": {
            "/api/detect-sections": "POST - Detect sections from URL",
            "/api/analyze-html": "POST - Analyze HTML content directly",
            "/health": "GET - Health check",
            "/api/stats": "GET - API statistics",
        },
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
