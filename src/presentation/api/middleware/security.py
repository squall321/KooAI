"""
보안 헤더 미들웨어

보안 관련 HTTP 헤더를 자동으로 추가합니다.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    보안 헤더 추가 미들웨어

    추가하는 헤더:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: HTTPS 강제
    - Content-Security-Policy: XSS 방지
    - X-Permitted-Cross-Domain-Policies: crossdomain.xml 제어
    """

    async def dispatch(self, request: Request, call_next):
        """요청 처리 및 보안 헤더 추가"""
        response: Response = await call_next(request)

        # X-Content-Type-Options
        # MIME 타입 스니핑 방지
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options
        # 클릭재킹(Clickjacking) 공격 방지
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection
        # 구형 브라우저의 XSS 필터 활성화
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security (HSTS)
        # HTTPS 강제 사용 (프로덕션 환경에서 HTTPS 사용 시)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content-Security-Policy (CSP)
        # XSS 공격 방지를 위한 컨텐츠 보안 정책
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        # X-Permitted-Cross-Domain-Policies
        # Adobe Flash/PDF의 cross-domain 요청 제어
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Referrer-Policy
        # Referer 헤더 정보 제어
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Remove server header (보안상 서버 정보 숨김)
        if "Server" in response.headers:
            del response.headers["Server"]

        # Remove X-Powered-By header (보안상 기술 스택 정보 숨김)
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        return response
