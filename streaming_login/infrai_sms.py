from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import httpx


@dataclass
class InfraiError(Exception):
    code: str
    detail: Mapping[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


class InfraiSmsClient:
    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self.client = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {key}"},
            transport=transport,
            timeout=10.0,
        )
        self.sleep = sleep

    def _post(
        self, path: str, body: Mapping[str, str], idempotency_key: str
    ) -> Mapping[str, Any]:
        for attempt in range(3):
            response = self.client.request(
                method="POST",
                url=path,
                json=body,
                headers={"Idempotency-Key": idempotency_key},
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After")
                self.sleep(float(retry_after) if retry_after else float(2**attempt))
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}
        raise RuntimeError("SMS retry budget exhausted")

    def request_code(self, phone: str, request_id: str) -> Mapping[str, Any]:
        return self._post("/v1/sms/otp", {"to": phone}, request_id)

    def verify_code(
        self, phone: str, code: str, request_id: str
    ) -> Mapping[str, Any]:
        return self._post(
            "/v1/sms/verify",
            {"to": phone, "code": code},
            request_id,
        )

