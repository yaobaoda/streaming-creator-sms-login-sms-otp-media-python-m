from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import uuid4


class SmsVerifier(Protocol):
    def request_code(self, phone: str, request_id: str) -> object:
        raise AssertionError("protocol method")

    def verify_code(self, phone: str, code: str, request_id: str) -> object:
        raise AssertionError("protocol method")


class JobState(StrEnum):
    QUEUED = "queued"
    READY = "ready"


@dataclass
class MediaAsset:
    asset_id: str
    creator_id: str
    source_uri: str
    phone: str
    job_state: JobState = JobState.QUEUED


@dataclass(frozen=True)
class DeliveryDecision:
    delivered: bool
    asset_id: str
    creator_id: str
    playback_path: str


class MediaDeliveryWorkflow:
    def __init__(self, sms: SmsVerifier) -> None:
        self.sms = sms
        self.assets: dict[str, MediaAsset] = {}

    def ingest(self, creator_id: str, source_uri: str, phone: str) -> MediaAsset:
        asset = MediaAsset(str(uuid4()), creator_id, source_uri, phone)
        self.assets[asset.asset_id] = asset
        return asset

    def complete_processing(self, asset_id: str) -> MediaAsset:
        asset = self.assets[asset_id]
        asset.job_state = JobState.READY
        return asset

    def send_login_code(self, asset_id: str) -> None:
        asset = self.assets[asset_id]
        self.sms.request_code(asset.phone, f"login-send:{asset.asset_id}")

    def verify_and_deliver(self, asset_id: str, code: str) -> DeliveryDecision:
        asset = self.assets[asset_id]
        if asset.job_state is not JobState.READY:
            return DeliveryDecision(False, asset.asset_id, asset.creator_id, "")
        self.sms.verify_code(asset.phone, code, f"login-verify:{asset.asset_id}:{code}")
        return DeliveryDecision(
            True,
            asset.asset_id,
            asset.creator_id,
            f"/creator-deliveries/{asset.asset_id}",
        )
