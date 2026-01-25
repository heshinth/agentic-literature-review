import os
from curl_cffi import AsyncSession , CurlError
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TextColumn,
)


async def download_pdf_from_url(
    session: AsyncSession, pdf_url: str, filename: str = "sample.pdf"
) -> None:
    if not pdf_url:
        return

    save_path = f"temp_pdfs/{filename}"
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        headers = {
            "Referer": "https://google.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        response = await session.get(
            pdf_url, headers=headers, impersonate="chrome", stream=True, timeout=300
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
            with open(save_path, "wb") as pdf_file:
                async for chunk in response.aiter_content(chunk_size=1024 * 1024):
                    if chunk:
                        pdf_file.write(chunk)
                        progress.update(task, advance=len(chunk))

        print(f"Saved to {save_path}")
    except CurlError as ce:
        print(f"Curl error for file {filename} ({ce.code}): {ce}")
    except Exception as e:
        print(f"Failed to download {pdf_url}: {e}")