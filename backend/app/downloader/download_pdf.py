import os
import time
from dataclasses import dataclass
from curl_cffi import AsyncSession, CurlError
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TextColumn,
)


@dataclass
class DownloadOutcome:
    pdf_bytes: bytes | None
    error: str | None = None
    is_network_error: bool = False
    error_code: int | None = None


async def download_pdf_from_url(
    session: AsyncSession,
    pdf_url: str,
    filename: str = "sample.pdf",
    output_dir: str = "temp_pdfs",
    save_to_file: bool = True,
) -> DownloadOutcome:
    if not pdf_url:
        return DownloadOutcome(
            pdf_bytes=None,
            error="Missing PDF URL",
            is_network_error=False,
        )

    save_path = os.path.join(output_dir, filename)
    try:
        if save_to_file:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

        headers = {
            "Referer": "https://google.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        response = await session.get(
            pdf_url,
            headers=headers,
            impersonate="chrome",
            stream=True,
            timeout=600,
            allow_redirects=True,
        )
        response.raise_for_status()

        total_size = int(response.headers.get("Content-Length", 0))

        # Rich progress bar setup
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),  # Shows downloaded / total bytes
            TransferSpeedColumn(),  # Shows speed
            TimeRemainingColumn(),  # Shows ETA
        )

        with progress:
            task = progress.add_task(f"Downloading {filename}", total=total_size)

            start_time = time.time()
            downloaded_bytes = 0
            aborted = False
            chunks: list[bytes] = []

            target_file = open(save_path, "wb") if save_to_file else None
            try:
                async for chunk in response.aiter_content(chunk_size=1024 * 1024):
                    if chunk:
                        chunks.append(chunk)
                        if target_file:
                            target_file.write(chunk)
                        chunk_len = len(chunk)
                        progress.update(task, advance=chunk_len)
                        downloaded_bytes += chunk_len

                    # Speed limit check
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 10:
                        average_speed_kbps = (downloaded_bytes / 1024) / elapsed_time
                        if average_speed_kbps < 100:
                            print(
                                f"[Warning] Skipping {filename}: Average speed too slow ({average_speed_kbps:.2f} KB/s)"
                            )
                            aborted = True
                            break
            finally:
                if target_file:
                    target_file.close()

            if aborted:
                if save_to_file and os.path.exists(save_path):
                    os.remove(save_path)
                return DownloadOutcome(
                    pdf_bytes=None,
                    error=f"Download aborted due to slow transfer for {filename}",
                    is_network_error=True,
                )

        pdf_bytes = b"".join(chunks)
        if not pdf_bytes:
            return DownloadOutcome(
                pdf_bytes=None,
                error=f"Empty response body for {filename}",
                is_network_error=False,
            )

        if save_to_file:
            print(f"Saved to {save_path}")

        return DownloadOutcome(pdf_bytes=pdf_bytes)
    except CurlError as ce:
        print(f"Curl error for file {filename} ({ce.code}): {ce}")
        error_text = f"Curl error {ce.code}: {ce}"
        return DownloadOutcome(
            pdf_bytes=None,
            error=error_text,
            is_network_error=True,
            error_code=ce.code,
        )
    except Exception as e:
        print(f"Failed to download {pdf_url}: {e}")
        error_text = str(e)
        lowered = error_text.lower()
        looks_network_related = any(
            token in lowered
            for token in (
                "timeout",
                "connection",
                "network",
                "tls",
                "ssl",
                "dns",
                "refused",
                "unreachable",
            )
        )
        return DownloadOutcome(
            pdf_bytes=None,
            error=error_text,
            is_network_error=looks_network_related,
        )
