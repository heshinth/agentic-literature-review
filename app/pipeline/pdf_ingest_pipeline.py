import asyncio
import os
from typing import Any

from curl_cffi import AsyncSession

from database import crud
from database.crud import add_paper, get_paper_by_id, update_paper_status
from database.db_config import SessionLocal
from downloader.download_pdf import download_pdf_from_url
from utils.pdf_extractor import extract_pdf_bytes_by_column


async def process_papers(papers: list[dict[str, Any]], logger) -> dict[str, int]:
    if not papers:
        logger.warning("No papers found.")
        return {
            "added_new": 0,
            "already_in_db": 0,
            "already_extracted": 0,
            "missing_paper_id": 0,
            "missing_open_access_url": 0,
            "download_failed": 0,
            "extract_empty": 0,
            "stored_text": 0,
        }

    concurrency = int(os.getenv("PIPELINE_CONCURRENCY", "5"))
    semaphore = asyncio.Semaphore(concurrency)

    async def download_and_extract_one(
        session: AsyncSession, paper_data: dict[str, Any]
    ):
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

    summary = {
        "added_new": 0,
        "already_in_db": 0,
        "already_extracted": 0,
        "missing_paper_id": 0,
        "missing_open_access_url": 0,
        "download_failed": 0,
        "extract_empty": 0,
        "stored_text": 0,
    }

    with SessionLocal() as db:
        for paper_data in papers:
            inserted = add_paper(db, paper_data)
            title = paper_data.get("title", "Unknown title")
            if inserted:
                logger.info(f"Added paper: {inserted.title} ({inserted.year})")
                summary["added_new"] += 1
            else:
                logger.info(f"Skipped insert (already in database): {title}")
                summary["already_in_db"] += 1

        papers_to_process: list[dict[str, Any]] = []
        for paper_data in papers:
            paper_id = paper_data.get("paper_id")
            title = paper_data.get("title", "Unknown title")
            if not paper_id:
                logger.warning(f"Skipped pipeline item (missing paper_id): {title}")
                summary["missing_paper_id"] += 1
                continue

            db_paper = get_paper_by_id(db, paper_id)
            if not db_paper:
                logger.warning(
                    f"Skipped {paper_id} | {title}: not found in database after insert step"
                )
                continue

            if db_paper.is_extracted:
                logger.info(
                    f"Skipped {paper_id} | {title}: already extracted in database"
                )
                summary["already_extracted"] += 1
                continue

            papers_to_process.append(paper_data)

        if not papers_to_process:
            logger.info("No papers need download/extraction.")
            return summary

        async with AsyncSession() as session:
            tasks = [
                download_and_extract_one(session, paper_data)
                for paper_data in papers_to_process
            ]
            pipeline_results = await asyncio.gather(*tasks)

        for item in pipeline_results:
            if not item:
                continue

            paper_id = item["paper_id"]
            title = item.get("title", "Unknown title")
            status = item.get("status")

            if status == "missing_paper_id":
                logger.warning(f"Skipped pipeline item (missing paper_id): {title}")
                summary["missing_paper_id"] += 1
                continue

            if status == "missing_open_access_url":
                logger.warning(f"Skipped {paper_id} | {title}: missing open access URL")
                summary["missing_open_access_url"] += 1
                continue

            if status == "download_failed":
                logger.warning(f"Skipped {paper_id} | {title}: download failed")
                summary["download_failed"] += 1
                continue

            update_paper_status(db, paper_id, {"is_downloaded": True})

            extracted_text = item["text"]
            if not extracted_text.strip():
                logger.warning(
                    f"Skipped {paper_id} | {title}: extract produced empty text"
                )
                summary["extract_empty"] += 1
                continue

            crud.add_paper_text(db, paper_id, extracted_text)
            update_paper_status(db, paper_id, {"is_extracted": True})
            logger.info(f"Stored extracted text for {paper_id} | {title}")
            summary["stored_text"] += 1

    return summary
