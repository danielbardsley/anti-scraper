from __future__ import annotations

from fastapi import Request

from proof_of_work_api.config.app_settings import AppSettings


class ClientIpResolver:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def resolve(self, request: Request) -> str:
        direct_ip = request.client.host if request.client else "unknown"
        if direct_ip in self._settings.trusted_proxy_ips:
            forwarded = request.headers.get(self._settings.forwarded_for_header)
            if forwarded:
                first = forwarded.split(",")[0].strip()
                if first:
                    return first
        return direct_ip
