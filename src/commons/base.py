import urllib
import urllib.parse
from base64 import b64encode
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from hashlib import sha256
from secrets import token_urlsafe

from httpx import AsyncClient


class ApiClientBase:
    @asynccontextmanager
    async def _get_client(
        self,
        proxy: str | None = None,
    ) -> AsyncGenerator[AsyncClient]:
        client = AsyncClient(
            proxy=proxy if proxy else None,
        )
        yield client

    def _generate_pkce_pair(self) -> tuple[str, str]:
        verifier: str = token_urlsafe(64)

        challenge: str = (
            b64encode(sha256(verifier.encode("utf-8")).digest())
            .decode("ascii")
            .replace("+", "-")
            .replace("/", "_")
            .rstrip("=")
        )
        return verifier, challenge

    def _generate_redirect_uri(
        self,
        scope: str,
        client_code: str,
        redirect_uri: str,
        state: str,
        code_challenge,
        auth_url: str,
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": client_code,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        auth_url = f"{auth_url}?{urllib.parse.urlencode(params)}"
        return auth_url
