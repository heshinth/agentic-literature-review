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
    candidate_urls: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    url = paper_data.get("open_access_url")
    if isinstance(url, str) and url.strip():
        cleaned = url.strip()
        candidate_urls.append({"url": cleaned, "source": "semantic_scholar"})
        seen_urls.add(cleaned)

    if isinstance(doi, str) and doi.strip():
        try:
            fallback_urls = await asyncio.to_thread(get_oa_status, doi.strip())
            for fallback in fallback_urls:
                if fallback not in seen_urls:
                    candidate_urls.append({"url": fallback, "source": "unpaywall"})
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
        successful_source = ""
        successful_url = ""
        attempt_errors: list[dict[str, str | int | bool]] = []
        network_errors: list[str] = []
        for candidate in candidate_urls:
            candidate_url = candidate["url"]
            source = candidate["source"]
            logger.info(
                "Download attempt for %s from source=%s url=%s",
                paper_id,
                source,
                candidate_url,
            )
            download_outcome = await download_pdf_from_url(
                session=session,
                pdf_url=candidate_url,
                filename=f"{paper_id}.pdf",
                save_to_file=False,
            )
            pdf_bytes = download_outcome.pdf_bytes

            if download_outcome.error:
                attempt_error: dict[str, str | int | bool] = {
                    "source": source,
                    "url": candidate_url,
                    "error": download_outcome.error,
                    "is_network_error": download_outcome.is_network_error,
                }
                if download_outcome.error_code is not None:
                    attempt_error["error_code"] = download_outcome.error_code
                attempt_errors.append(attempt_error)

                if download_outcome.is_network_error:
                    network_errors.append(
                        f"{paper_id} via {source}: {download_outcome.error}"
                    )

            if pdf_bytes:
                successful_source = source
                successful_url = candidate_url
                logger.info(
                    "Download succeeded for %s using source=%s",
                    paper_id,
                    source,
                )
                break

        if not pdf_bytes:
            return {
                "paper_id": paper_id,
                "title": title,
                "status": "download_failed",
                "text": "",
                "attempt_errors": attempt_errors,
                "network_errors": network_errors,
            }

        extracted_text = await asyncio.to_thread(
            extract_pdf_bytes_by_column, pdf_bytes, paper_id
        )
        return {
            "paper_id": paper_id,
            "title": title,
            "status": "downloaded_and_extracted",
            "download_source": successful_source,
            "download_url": successful_url,
            "text": extracted_text or "",
        }
