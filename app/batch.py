"""Batch receipt processing — parallel OCR with progress tracking."""
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC
from typing import Any

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class BatchJob:
    """Tracks state of a batch processing job."""
    job_id: str
    status: str                 # "queued" | "processing" | "completed" | "failed"
    total: int
    completed: int = 0
    failed: int = 0
    results: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    webhook_url: str | None = None

    @property
    def progress(self) -> float:
        """Completion percentage (0.0 to 1.0)."""
        return (self.completed + self.failed) / self.total if self.total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API responses."""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "progress": self.progress,
            "results": self.results,
            "errors": self.errors,
            "created_at": self.created_at,
            "webhook_url": self.webhook_url,
        }


# ---------------------------------------------------------------------------
# Processor
# ---------------------------------------------------------------------------

class BatchProcessor:
    """Parallel receipt OCR processor with progress tracking.

    Uses ThreadPoolExecutor for CPU-bound OCR work.
    Reports progress via callback or polling.
    """

    def __init__(
        self,
        *,
        max_workers: int = 4,
        progress_callback: Callable[[BatchJob], None] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        max_workers:
            Maximum parallel OCR threads. Default 4.
        progress_callback:
            Called after each item completes. Useful for WebSocket updates.
        """
        self._max_workers = max_workers
        self._progress_callback = progress_callback

    async def process_batch(
        self,
        items: list[bytes | str],  # raw image bytes or URLs
        *,
        lang: str | None = None,
        webhook_url: str | None = None,
        job_id: str | None = None,
    ) -> BatchJob:
        """Process a batch of receipt images in parallel.

        Parameters
        ----------
        items:
            List of image bytes or public URLs.
        lang:
            Language override (None = auto-detect per receipt).
        webhook_url:
            Optional POST callback on completion.
        job_id:
            Optional pre-allocated job id. When provided, the job is updated
            in-place so callers that already created a job (api_v2) can poll
            the SAME id. When omitted, a fresh id is generated.

        Returns
        -------
        BatchJob
            Job object with progress tracking and results.
        """
        import uuid
        from datetime import datetime

        from app.ocr import parse_receipt

        if job_id is not None:
            job = _batch_jobs.get(job_id)
            if job is None:
                job = BatchJob(
                    job_id=job_id,
                    status="processing",
                    total=len(items),
                    created_at=datetime.now(UTC).isoformat(),
                    webhook_url=webhook_url,
                )
                _batch_jobs[job_id] = job
            else:
                job.status = "processing"
                job.total = len(items)
        else:
            job_id = str(uuid.uuid4())
            job = BatchJob(
                job_id=job_id,
                status="processing",
                total=len(items),
                created_at=datetime.now(UTC).isoformat(),
                webhook_url=webhook_url,
            )
            _batch_jobs[job_id] = job

        def _process_one(idx: int, item: bytes | str) -> dict[str, Any]:
            try:
                if isinstance(item, str):
                    from app.security import fetch_image_bytes

                    img_bytes = fetch_image_bytes(item)
                else:
                    img_bytes = item
                parsed = parse_receipt(img_bytes, lang=lang)
                return {
                    "index": idx,
                    "vendor": parsed.merchant,
                    "total": parsed.total,
                    "date": parsed.date,
                    "currency": parsed.currency,
                    "line_items": [
                        {"name": it.name, "price": it.price} for it in parsed.items
                    ],
                    "error": None,
                }
            except Exception as exc:
                return {
                    "index": idx,
                    "vendor": None,
                    "total": None,
                    "date": None,
                    "currency": None,
                    "line_items": [],
                    "error": str(exc),
                }

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = [
                loop.run_in_executor(pool, _process_one, i, item)
                for i, item in enumerate(items)
            ]
            for future in asyncio.as_completed(futures):
                result = await future
                idx = result["index"]
                if result["error"]:
                    job.failed += 1
                    job.errors.append({"index": idx, "error": result["error"]})
                else:
                    job.completed += 1
                job.results.append(result)
                if self._progress_callback:
                    self._progress_callback(job)

        job.status = "completed"
        return job

    def get_job(self, job_id: str) -> BatchJob | None:
        """Retrieve a batch job by ID for progress polling."""
        return _batch_jobs.get(job_id)

    def list_jobs(self) -> list[BatchJob]:
        """List all batch jobs with their current status."""
        return list(_batch_jobs.values())


# Module-level job store
_batch_jobs: dict[str, BatchJob] = {}
_batch_executor = ThreadPoolExecutor(max_workers=4)
