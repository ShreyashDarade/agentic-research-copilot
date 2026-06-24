# Daily update: 2026-06-24
from hashlib import sha256
from io import BytesIO

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.rag.schemas import SourceDocument


def source_id_for(value: str) -> str:
    return f"src_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


async def load_url(url: str, *, request_timeout: float = 15.0) -> SourceDocument:
    async with httpx.AsyncClient(timeout=request_timeout, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    text = soup.get_text(" ", strip=True)
    return SourceDocument(
        source_id=source_id_for(url),
        title=title,
        text=text,
        source_type="url",
        url=url,
        metadata={"url": url},
    )


def load_pdf_bytes(*, filename: str, content: bytes) -> SourceDocument:
    reader = PdfReader(BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(page for page in pages if page.strip())
    return SourceDocument(
        source_id=source_id_for(f"{filename}:{sha256(content).hexdigest()}"),
        title=filename,
        text=text,
        source_type="pdf",
        metadata={"filename": filename, "page_count": str(len(reader.pages))},
    )


def synthetic_document(*, topic: str, url: str | None = None) -> SourceDocument:
    label = url or topic
    text = (
        f"{topic} is being researched by an agentic workflow. "
        "Production AI research assistants should gather evidence, cite sources, "
        "verify claims, persist state, and require human approval for final output."
    )
    return SourceDocument(
        source_id=source_id_for(label),
        title=f"Research brief: {topic}",
        text=text,
        source_type="synthetic",
        url=url,
        metadata={"url": url or "", "demo": "true"},
    )
