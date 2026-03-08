import time
import pymupdf  # fitz


def sanitize_text_for_db(text: str) -> str:
    if not text:
        return ""

    cleaned = text.replace("\x00", "")
    cleaned = "".join(
        ch for ch in cleaned if (ch == "\n" or ch == "\t" or ord(ch) >= 32)
    )
    return cleaned


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
