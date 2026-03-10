import asyncio

from curl_cffi import AsyncSession

from app.downloader.download_pdf import download_pdf_from_url
from app.utils.pdf_extractor import extract_pdf_bytes_by_column


async def download_and_extract_one(
    session: AsyncSession,
    paper_data: dict,
    logger,
    semaphore: asyncio.Semaphore,
) -> dict:
    paper_id = paper_data.get("paper_id")
    title = paper_data.get("title", "Unknown title")

    if not paper_id:
        return {
            "paper_id": "unknown",
            "title": title,
            "status": "missing_paper_id",
            "text": "",
        }

    url = paper_data.get("open_access_url")
    if not url:
        return {
            "paper_id": paper_id,
            "title": title,
            "status": "missing_open_access_url",
            "text": "",
        }

    async with semaphore:
        logger.info(f"Downloading and extracting: {paper_id} | {title}")
        pdf_bytes = await download_pdf_from_url(
            session=session,
            pdf_url=url,
            filename=f"{paper_id}.pdf",
            save_to_file=False,
        )

        if not pdf_bytes:
            return {
                "paper_id": paper_id,
                "title": title,
                "status": "download_failed",
                "text": "",
            }

        extracted_text = await asyncio.to_thread(
            extract_pdf_bytes_by_column, pdf_bytes, paper_id
        )
        return {
            "paper_id": paper_id,
            "title": title,
            "status": "downloaded_and_extracted",
            "text": extracted_text or "",
        }
