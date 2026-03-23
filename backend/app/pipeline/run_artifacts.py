import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def generate_run_id(prefix: str = "run") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short = uuid4().hex[:8]
    return f"{prefix}_{ts}_{short}"


def save_run_manifest(
    manifest: dict,
    logger,
    run_id: str,
    output_dir: str = "logs/manifests",
) -> str:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    output_path = out_dir / f"{run_id}.json"
    output_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Run manifest saved to %s", output_path)
    return str(output_path)