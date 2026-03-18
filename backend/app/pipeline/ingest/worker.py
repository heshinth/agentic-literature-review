import asyncio

from curl_cffi import AsyncSession

from app.downloader.download_pdf import download_pdf_from_url
from app.downloader.unpaywall import get_oa_status
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

    doi = paper_data.get("doi_id")

    # Start with Semantic Scholar OA URL, then try Unpaywall DOI fallback URLs.
    candidate_urls: list[str] = []
    seen_urls: set[str] = set()

    url = paper_data.get("open_access_url")
    if isinstance(url, str) and url.strip():
        cleaned = url.strip()
        candidate_urls.append(cleaned)
        seen_urls.add(cleaned)

    if isinstance(doi, str) and doi.strip():
        try:
            fallback_urls = await asyncio.to_thread(get_oa_status, doi.strip())
            for fallback in fallback_urls:
                if fallback not in seen_urls:
                    candidate_urls.append(fallback)
                    seen_urls.add(fallback)
            if fallback_urls:
                logger.info(
                    "Unpaywall fallback discovered %s candidate URL(s) for %s",
                    len(fallback_urls),
                    paper_id,
                )
        except Exception as e:
            logger.warning(
                "Unpaywall lookup failed for %s (doi=%s): %s",
                paper_id,
                doi,
                e,
            )

    if not candidate_urls:
        return {
            "paper_id": paper_id,
            "title": title,
            "status": "missing_open_access_url",
            "text": "",
        }

    async with semaphore:
        logger.info(f"Downloading and extracting: {paper_id} | {title}")
        pdf_bytes = None
        for candidate_url in candidate_urls:
            pdf_bytes = await download_pdf_from_url(
                session=session,
                pdf_url=candidate_url,
                filename=f"{paper_id}.pdf",
                save_to_file=False,
            )
            if pdf_bytes:
                break

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
