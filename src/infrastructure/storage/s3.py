"""
S3 storage adapter (AWS S3 and compatible services)
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator, BinaryIO, Optional

from .base import (
    FileMetadata,
    PresignedUrl,
    StorageBackend,
    UploadResult,
)

if TYPE_CHECKING:
    import aioboto3
else:
    try:
        import aioboto3
    except ImportError:
        aioboto3 = None  # type: ignore


class S3StorageBackend(StorageBackend):
    """
    S3 storage adapter

    AWS S3 및 호환 서비스 (MinIO, DigitalOcean Spaces 등)를 지원합니다.
    """

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        use_ssl: bool = True,
    ):
        """
        Args:
            bucket_name: S3 버킷 이름
            region: AWS 리전
            endpoint_url: 커스텀 엔드포인트 URL (MinIO 등)
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            use_ssl: SSL 사용 여부
        """
        if aioboto3 is None:
            raise ImportError(
                "aioboto3 is required for S3 storage. " "Install it with: pip install aioboto3"
            )

        self.bucket_name = bucket_name
        self.region = region
        self.endpoint_url = endpoint_url
        self.use_ssl = use_ssl

        # Create session
        self.session = aioboto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )

    def _get_client_kwargs(self) -> dict[str, Any]:
        """Get S3 client kwargs"""
        kwargs: dict[str, Any] = {
            "use_ssl": self.use_ssl,
        }
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        return kwargs

    async def upload(
        self,
        file: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> UploadResult:
        """파일 업로드"""
        content = file.read()
        size = len(content)

        extra_args = {
            "ContentType": content_type,
        }
        if metadata:
            extra_args["Metadata"] = metadata

        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            response = await s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                **extra_args,
            )

        return UploadResult(
            key=key,
            size=size,
            etag=response.get("ETag", "").strip('"'),
        )

    async def upload_multipart(
        self,
        file: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
        part_size: int = 5 * 1024 * 1024,
        metadata: Optional[dict[str, str]] = None,
    ) -> UploadResult:
        """멀티파트 업로드"""
        extra_args = {
            "ContentType": content_type,
        }
        if metadata:
            extra_args["Metadata"] = metadata

        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            # Initiate multipart upload
            response = await s3.create_multipart_upload(
                Bucket=self.bucket_name, Key=key, **extra_args
            )
            upload_id = response["UploadId"]

            parts = []
            part_number = 1
            total_size = 0

            try:
                while True:
                    chunk = file.read(part_size)
                    if not chunk:
                        break

                    # Upload part
                    part_response = await s3.upload_part(
                        Bucket=self.bucket_name,
                        Key=key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=chunk,
                    )

                    parts.append(
                        {
                            "PartNumber": part_number,
                            "ETag": part_response["ETag"],
                        }
                    )
                    part_number += 1
                    total_size += len(chunk)

                # Complete multipart upload
                complete_response = await s3.complete_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )

                return UploadResult(
                    key=key,
                    size=total_size,
                    etag=complete_response.get("ETag", "").strip('"'),
                )

            except Exception as e:
                # Abort multipart upload on error
                await s3.abort_multipart_upload(
                    Bucket=self.bucket_name, Key=key, UploadId=upload_id
                )
                raise e

    async def download(self, key: str) -> bytes:
        """파일 다운로드"""
        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            response = await s3.get_object(Bucket=self.bucket_name, Key=key)
            async with response["Body"] as stream:
                return await stream.read()

    async def download_to_file(self, key: str, destination: Path) -> None:
        """파일을 로컬 파일로 다운로드"""
        destination.parent.mkdir(parents=True, exist_ok=True)

        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            await s3.download_file(self.bucket_name, key, str(destination))

    async def download_stream(self, key: str, chunk_size: int = 8192) -> AsyncIterator[bytes]:
        """파일을 스트림으로 다운로드"""
        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            response = await s3.get_object(Bucket=self.bucket_name, Key=key)
            async with response["Body"] as stream:
                while True:
                    chunk = await stream.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

    async def delete(self, key: str) -> None:
        """파일 삭제"""
        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            await s3.delete_object(Bucket=self.bucket_name, Key=key)

    async def delete_many(self, keys: list[str]) -> None:
        """여러 파일 삭제"""
        if not keys:
            return

        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            # S3 allows deleting up to 1000 objects at once
            batch_size = 1000
            for i in range(0, len(keys), batch_size):
                batch = keys[i : i + batch_size]
                await s3.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={
                        "Objects": [{"Key": key} for key in batch],
                        "Quiet": True,
                    },
                )

    async def exists(self, key: str) -> bool:
        """파일 존재 여부 확인"""
        try:
            async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
                await s3.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

    async def get_metadata(self, key: str) -> FileMetadata:
        """파일 메타데이터 조회"""
        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            response = await s3.head_object(Bucket=self.bucket_name, Key=key)

        return FileMetadata(
            key=key,
            size=response["ContentLength"],
            content_type=response.get("ContentType", "application/octet-stream"),
            etag=response.get("ETag", "").strip('"'),
            last_modified=response.get("LastModified"),
            custom_metadata=response.get("Metadata"),
        )

    async def list_files(self, prefix: str = "", max_results: int = 1000) -> list[FileMetadata]:
        """파일 목록 조회"""
        files = []

        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                PaginationConfig={"MaxItems": max_results},
            ):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        files.append(
                            FileMetadata(
                                key=obj["Key"],
                                size=obj["Size"],
                                content_type="application/octet-stream",  # Not in listing
                                etag=obj.get("ETag", "").strip('"'),
                                last_modified=obj.get("LastModified"),
                            )
                        )

        return files

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> PresignedUrl:
        """Presigned URL 생성"""
        # Map HTTP method to S3 operation
        operation_map = {
            "GET": "get_object",
            "PUT": "put_object",
            "DELETE": "delete_object",
        }
        client_method = operation_map.get(method.upper(), "get_object")

        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            url = await s3.generate_presigned_url(
                ClientMethod=client_method,
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )

        return PresignedUrl(
            url=url,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            method=method,
        )

    async def copy(self, source_key: str, destination_key: str) -> None:
        """파일 복사"""
        async with self.session.client("s3", **self._get_client_kwargs()) as s3:  # type: ignore
            copy_source = {"Bucket": self.bucket_name, "Key": source_key}
            await s3.copy_object(
                Bucket=self.bucket_name,
                CopySource=copy_source,
                Key=destination_key,
            )

    async def move(self, source_key: str, destination_key: str) -> None:
        """파일 이동"""
        await self.copy(source_key, destination_key)
        await self.delete(source_key)

    async def get_size(self, key: str) -> int:
        """파일 크기 조회"""
        metadata = await self.get_metadata(key)
        return metadata.size

    async def cleanup_old_files(self, prefix: str, days: int) -> int:
        """오래된 파일 정리"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

        files = await self.list_files(prefix=prefix)
        old_files = [f.key for f in files if f.last_modified and f.last_modified < cutoff_time]

        if old_files:
            await self.delete_many(old_files)

        return len(old_files)


# MinIO는 S3 호환이므로 별칭으로 제공
MinIOStorageBackend = S3StorageBackend
