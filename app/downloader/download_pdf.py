import os
import curl_cffi
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TextColumn,
)


def download_pdf_from_url(
    pdf_url: str, save_path: str = "temp_pdfs/sample.pdf"
) -> None:
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    response = curl_cffi.requests.get(
        pdf_url, impersonate="chrome", stream=True, timeout=300
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
        task = progress.add_task("Downloading PDF", total=total_size)
        with open(save_path, "wb") as pdf_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    pdf_file.write(chunk)
                    progress.update(task, advance=len(chunk))

    print(f"✅ Saved to {save_path}")


if __name__ == "__main__":
    sample_pdf_url = (
        "http://arxiv.org/pdf/2301.12597"
    )
    download_pdf_from_url(sample_pdf_url)
