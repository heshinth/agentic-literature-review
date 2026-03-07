import os
import time
from pathlib import Path
import pymupdf  # fitz
from sqlalchemy.orm import Session
from database import crud, db_config


def sanitize_text_for_db(text: str) -> str:
    if not text:
        return ""

    cleaned = text.replace("\x00", "")
    cleaned = "".join(
        ch for ch in cleaned if (ch == "\n" or ch == "\t" or ord(ch) >= 32)
    )
    return cleaned


def extract_pdf_by_column(pdf_path: str) -> str:
    """
    Extracts text from a PDF prioritizing a two-column layout.
    Returns the concatenated full text from all pages.
    """
    start_time = time.time()
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
        return ""

    full_text_pages = []

    for page_num, page in enumerate(doc, 1):
        W = page.rect.width
        try:
            blocks = page.get_text("blocks")  # Raw blocks, no sort yet
        except Exception:
            continue

        # Filter: Text only (type=0) and not empty
        text_blocks = [b for b in blocks if len(b) > 6 and b[6] == 0 and b[4].strip()]
        if not text_blocks:
            continue

        # Split into Spanners (Headers) and Columns
        span_blocks = []
        col_blocks = []

        for b in text_blocks:
            # If block width > 60% of page width, it's a spanner (Header/Title)
            if (b[2] - b[0]) > (W * 0.6):
                span_blocks.append(b)
            else:
                col_blocks.append(b)

        # Sort Spanners by Y (vertical)
        span_blocks.sort(key=lambda b: b[1])

        # Sort Columns: Primary Key = Column (Left vs Right), Secondary = Y
        # We assume Left Column is where x0 < W/2
        col_blocks.sort(key=lambda b: (1 if b[0] > W / 2 else 0, b[1]))

        # Reassemble: Header Spans -> Columns -> Footer Spans
        # Simple heuristic: Top 30% are headers, Bottom 30% are footers
        headers = [b for b in span_blocks if b[1] < page.rect.height * 0.3]
        footers = [b for b in span_blocks if b[1] >= page.rect.height * 0.3]

        page_content = []
        # Add Headers
        page_content.extend([b[4].strip() for b in headers])
        # Add Columns (Sorted Left->Right)
        page_content.extend([b[4].strip() for b in col_blocks])
        # Add Footers
        page_content.extend([b[4].strip() for b in footers])

        full_text_pages.append("\n".join(page_content))

    doc.close()
    print(f"Extracted {pdf_path} in {time.time() - start_time:.2f}s")

    # Return as a single continuous string
    return sanitize_text_for_db("\n\n".join(full_text_pages))


def extract_pdf_bytes_by_column(pdf_bytes: bytes, paper_id: str = "in-memory") -> str:
    """
    Extracts text from in-memory PDF bytes prioritizing a two-column layout.
    Returns the concatenated full text from all pages.
    """
    start_time = time.time()
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        print(f"Error opening in-memory PDF for {paper_id}: {e}")
        return ""

    full_text_pages = []

    for page_num, page in enumerate(doc, 1):
        W = page.rect.width
        try:
            blocks = page.get_text("blocks")
        except Exception:
            continue

        text_blocks = [b for b in blocks if len(b) > 6 and b[6] == 0 and b[4].strip()]
        if not text_blocks:
            continue

        span_blocks = []
        col_blocks = []

        for b in text_blocks:
            if (b[2] - b[0]) > (W * 0.6):
                span_blocks.append(b)
            else:
                col_blocks.append(b)

        span_blocks.sort(key=lambda b: b[1])
        col_blocks.sort(key=lambda b: (1 if b[0] > W / 2 else 0, b[1]))

        headers = [b for b in span_blocks if b[1] < page.rect.height * 0.3]
        footers = [b for b in span_blocks if b[1] >= page.rect.height * 0.3]

        page_content = []
        page_content.extend([b[4].strip() for b in headers])
        page_content.extend([b[4].strip() for b in col_blocks])
        page_content.extend([b[4].strip() for b in footers])

        full_text_pages.append("\n".join(page_content))

    doc.close()
    print(f"Extracted {paper_id} from bytes in {time.time() - start_time:.2f}s")
    return sanitize_text_for_db("\n\n".join(full_text_pages))


def process_unextracted_pdfs(db: Session | None = None):
    """Reads unextracted PDFs from DB, extracts text, and saves to DB."""
    own_session = db is None
    if own_session:
        db = db_config.SessionLocal()

    base_dir = Path(__file__).resolve().parents[2] / "temp_pdfs"

    # First, let's sync our local files to the DB: mark any PDFs we have as downloaded.
    print(f"Scanning {base_dir} for existing PDFs...")
    if not base_dir.exists():
        print("No temp_pdfs directory found yet.")
        if own_session:
            db.close()
        return

    existing_pdfs = [f for f in os.listdir(base_dir) if f.endswith(".pdf")]
    for pdf_file in existing_pdfs:
        paper_id = pdf_file.replace(".pdf", "")
        # Simple DB update to set is_downloaded = True for existing files
        crud.update_paper_status(db, paper_id, {"is_downloaded": True})

    # Get papers that are downloaded but not yet extracted
    papers = crud.get_papers_needing_extraction(db)

    if not papers:
        print("No new PDFs to extract.")
        if own_session:
            db.close()
        return

    print(f"Found {len(papers)} PDFs to extract.")

    for paper in papers:
        pdf_path = os.path.join(str(base_dir), f"{paper.paper_id}.pdf")

        if not os.path.exists(pdf_path):
            print(f"Warning: PDF file missing for {paper.paper_id} at {pdf_path}")
            continue

        print(f"Extracting {paper.paper_id}...")
        text = extract_pdf_by_column(pdf_path)

        if text.strip():
            # Save the text in Postgres
            crud.add_paper_text(db, paper.paper_id, text)
            # Mark as extracted
            crud.update_paper_status(db, paper.paper_id, {"is_extracted": True})
            print(f"Successfully extracted and saved {paper.paper_id}")
        else:
            print(f"Warning: No text found in {paper.paper_id}")

    if own_session:
        db.close()


if __name__ == "__main__":
    process_unextracted_pdfs()
