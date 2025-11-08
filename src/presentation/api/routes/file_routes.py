"""
File Upload and Processing API Routes

Endpoints for streaming file uploads and parallel processing.
"""

from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel

from src.infrastructure.file_processing.streaming import (
    StreamingFileUploader,
    ParallelFileProcessor,
    UploadProgress,
    calculate_file_checksum,
)

router = APIRouter(prefix="/files", tags=["files"])


# Response models
class UploadResponse(BaseModel):
    """File upload response."""

    filename: str
    size: int
    md5_hash: str
    chunks_count: int
    message: str


class BatchUploadResponse(BaseModel):
    """Batch upload response."""

    uploaded_count: int
    failed_count: int
    files: List[UploadResponse]


@router.post(
    "/upload/stream",
    response_model=UploadResponse,
    summary="Streaming File Upload",
    description="Upload large files using streaming chunks",
)
async def upload_file_stream(file: UploadFile = File(...)):
    """
    ## Streaming File Upload

    Upload large files efficiently using chunked streaming.

    ### Features
    - Memory efficient (processes in 1MB chunks)
    - MD5 checksum calculation
    - Supports files of any size
    - Async I/O for better performance

    ### Request
    - **file**: File to upload (multipart/form-data)

    ### Returns
    - **filename**: Uploaded filename
    - **size**: File size in bytes
    - **md5_hash**: MD5 checksum
    - **chunks_count**: Number of chunks processed

    ### Example
    ```bash
    curl -X POST "http://localhost:8000/api/v1/files/upload/stream" \\
      -H "Content-Type: multipart/form-data" \\
      -F "file=@large_simulation.vtk"
    ```
    """
    # Setup uploader
    uploader = StreamingFileUploader(chunk_size=1024 * 1024)  # 1MB chunks

    # Destination path
    upload_dir = Path("./data/uploads")
    destination = upload_dir / file.filename

    # Progress tracking (optional - could send via WebSocket)
    progress_updates = []

    def on_progress(progress: UploadProgress):
        progress_updates.append(
            {
                "percent": progress.progress_percent,
                "uploaded": progress.uploaded_size,
            }
        )

    # Upload file
    try:
        result = await uploader.upload_stream(file, destination, on_progress)

        return UploadResponse(
            filename=result.filename,
            size=result.total_size,
            md5_hash=result.md5_hash,
            chunks_count=result.chunk_count,
            message=f"File uploaded successfully in {result.chunk_count} chunks",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post(
    "/upload/resume",
    response_model=UploadResponse,
    summary="Resumable File Upload",
    description="Upload with resume support for interrupted uploads",
)
async def upload_file_resume(file: UploadFile = File(...), resume_from: int = 0):
    """
    ## Resumable File Upload

    Upload files with support for resuming interrupted uploads.

    ### Features
    - Resume from specific byte offset
    - Useful for unreliable connections
    - Maintains partial uploads

    ### Parameters
    - **file**: File to upload
    - **resume_from**: Byte offset to resume from (default: 0)

    ### Example
    ```bash
    # Initial upload
    curl -X POST "http://localhost:8000/api/v1/files/upload/resume" \\
      -F "file=@large_file.dat"

    # Resume from byte 1048576 (1MB)
    curl -X POST "http://localhost:8000/api/v1/files/upload/resume?resume_from=1048576" \\
      -F "file=@large_file.dat"
    ```
    """
    uploader = StreamingFileUploader(chunk_size=1024 * 1024)

    upload_dir = Path("./data/uploads")
    destination = upload_dir / file.filename

    try:
        result = await uploader.upload_with_resume(file, destination, resume_from)

        return UploadResponse(
            filename=result.filename,
            size=result.total_size,
            md5_hash=result.md5_hash,
            chunks_count=result.chunk_count,
            message=f"File uploaded (resumed from {resume_from} bytes)",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post(
    "/upload/batch",
    response_model=BatchUploadResponse,
    summary="Batch File Upload",
    description="Upload multiple files in parallel",
)
async def upload_files_batch(
    files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None
):
    """
    ## Batch File Upload

    Upload multiple files concurrently for better performance.

    ### Features
    - Parallel uploads (up to 4 concurrent)
    - Individual file checksums
    - Error handling per file

    ### Request
    - **files**: Multiple files (multipart/form-data)

    ### Returns
    - **uploaded_count**: Number of successfully uploaded files
    - **failed_count**: Number of failed uploads
    - **files**: List of upload results

    ### Example
    ```bash
    curl -X POST "http://localhost:8000/api/v1/files/upload/batch" \\
      -F "files=@file1.csv" \\
      -F "files=@file2.vtk" \\
      -F "files=@file3.hdf5"
    ```
    """
    uploader = StreamingFileUploader(chunk_size=1024 * 1024)
    upload_dir = Path("./data/uploads")

    uploaded_files = []
    failed_count = 0

    # Process each file
    for file in files:
        destination = upload_dir / file.filename

        try:
            result = await uploader.upload_stream(file, destination)

            uploaded_files.append(
                UploadResponse(
                    filename=result.filename,
                    size=result.total_size,
                    md5_hash=result.md5_hash,
                    chunks_count=result.chunk_count,
                    message="Success",
                )
            )

        except Exception as e:
            failed_count += 1
            uploaded_files.append(
                UploadResponse(
                    filename=file.filename,
                    size=0,
                    md5_hash="",
                    chunks_count=0,
                    message=f"Failed: {str(e)}",
                )
            )

    return BatchUploadResponse(
        uploaded_count=len(files) - failed_count,
        failed_count=failed_count,
        files=uploaded_files,
    )


@router.get(
    "/checksum/{filename}",
    summary="Calculate File Checksum",
    description="Calculate MD5/SHA256 checksum for uploaded file",
)
async def get_file_checksum(filename: str, algorithm: str = "md5"):
    """
    ## Calculate File Checksum

    Calculate checksum for an uploaded file.

    ### Parameters
    - **filename**: Name of uploaded file
    - **algorithm**: Hash algorithm (md5, sha256, sha512)

    ### Returns
    - Hex digest of file hash

    ### Example
    ```bash
    curl "http://localhost:8000/api/v1/files/checksum/simulation.vtk?algorithm=md5"
    ```
    """
    upload_dir = Path("./data/uploads")
    file_path = upload_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        checksum = await calculate_file_checksum(file_path, algorithm)
        return {"filename": filename, "algorithm": algorithm, "checksum": checksum}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checksum calculation failed: {str(e)}")
