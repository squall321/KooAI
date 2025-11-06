"""
Response compression utilities
"""

import gzip
import zlib
from typing import Union
import structlog

logger = structlog.get_logger(__name__)


def compress_response(
    data: Union[str, bytes],
    method: str = "gzip",
    level: int = 6,
) -> bytes:
    """
    Compress response data

    Args:
        data: Data to compress (string or bytes)
        method: Compression method ('gzip', 'zlib')
        level: Compression level (1-9, higher = better compression but slower)

    Returns:
        Compressed data

    Example:
        compressed = compress_response(json_string, method="gzip")
    """
    # Convert string to bytes if needed
    if isinstance(data, str):
        data = data.encode("utf-8")

    try:
        if method == "gzip":
            compressed = gzip.compress(data, compresslevel=level)
        elif method == "zlib":
            compressed = zlib.compress(data, level=level)
        else:
            raise ValueError(f"Unknown compression method: {method}")

        compression_ratio = len(data) / len(compressed) if compressed else 1.0

        logger.debug(
            "response_compressed",
            method=method,
            original_size=len(data),
            compressed_size=len(compressed),
            compression_ratio=compression_ratio,
        )

        return compressed

    except Exception as e:
        logger.warning("compression_failed", error=str(e))
        return data


def decompress_response(
    data: bytes,
    method: str = "gzip",
) -> bytes:
    """
    Decompress response data

    Args:
        data: Compressed data
        method: Compression method ('gzip', 'zlib')

    Returns:
        Decompressed data
    """
    try:
        if method == "gzip":
            decompressed = gzip.decompress(data)
        elif method == "zlib":
            decompressed = zlib.decompress(data)
        else:
            raise ValueError(f"Unknown compression method: {method}")

        logger.debug(
            "response_decompressed",
            method=method,
            compressed_size=len(data),
            decompressed_size=len(decompressed),
        )

        return decompressed

    except Exception as e:
        logger.warning("decompression_failed", error=str(e))
        return data


def should_compress(
    data: Union[str, bytes],
    min_size: int = 1024,
    content_type: str = "application/json",
) -> bool:
    """
    Determine if response should be compressed

    Args:
        data: Response data
        min_size: Minimum size in bytes to compress
        content_type: Response content type

    Returns:
        True if compression is recommended
    """
    # Check size threshold
    data_size = len(data) if isinstance(data, bytes) else len(data.encode("utf-8"))

    if data_size < min_size:
        return False

    # Check if content type is compressible
    compressible_types = [
        "application/json",
        "application/xml",
        "text/html",
        "text/plain",
        "text/css",
        "text/javascript",
        "application/javascript",
    ]

    for compressible in compressible_types:
        if compressible in content_type.lower():
            return True

    return False


class CompressionMiddleware:
    """
    Middleware for automatic response compression

    Example:
        app.add_middleware(CompressionMiddleware, min_size=1024)
    """

    def __init__(
        self,
        app,
        min_size: int = 1024,
        compression_level: int = 6,
    ):
        """
        Initialize compression middleware

        Args:
            app: ASGI application
            min_size: Minimum response size to compress
            compression_level: Compression level (1-9)
        """
        self.app = app
        self.min_size = min_size
        self.compression_level = compression_level

    async def __call__(self, scope, receive, send):
        """ASGI application call"""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Check if client accepts gzip
        headers = dict(scope.get("headers", []))
        accept_encoding = headers.get(b"accept-encoding", b"").decode("latin1")

        if "gzip" not in accept_encoding.lower():
            # Client doesn't support gzip
            return await self.app(scope, receive, send)

        # Wrap send to intercept responses
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Store response headers
                self.response_headers = list(message.get("headers", []))
                self.status_code = message.get("status", 200)

            elif message["type"] == "http.response.body":
                body = message.get("body", b"")

                if len(body) >= self.min_size:
                    # Compress response
                    compressed_body = gzip.compress(body, compresslevel=self.compression_level)

                    # Add compression headers
                    self.response_headers.append((b"content-encoding", b"gzip"))
                    self.response_headers.append(
                        (b"content-length", str(len(compressed_body)).encode())
                    )

                    # Send start message with updated headers
                    await send(
                        {
                            "type": "http.response.start",
                            "status": self.status_code,
                            "headers": self.response_headers,
                        }
                    )

                    # Send compressed body
                    await send(
                        {
                            "type": "http.response.body",
                            "body": compressed_body,
                            "more_body": message.get("more_body", False),
                        }
                    )

                    return

            # Pass through unchanged
            await send(message)

        await self.app(scope, receive, send_wrapper)
