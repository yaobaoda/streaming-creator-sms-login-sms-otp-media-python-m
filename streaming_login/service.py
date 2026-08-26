from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .infrai_sms import InfraiError, InfraiSmsClient
from .media_delivery import MediaDeliveryWorkflow


class AssetIngestRequest(BaseModel):
    creator_id: str = Field(min_length=1)
    source_uri: str = Field(min_length=1)
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")


class VerifyLoginRequest(BaseModel):
    code: str = Field(pattern=r"^\d{4,10}$")


def create_app(workflow: MediaDeliveryWorkflow | None = None) -> FastAPI:
    media = workflow or MediaDeliveryWorkflow(InfraiSmsClient())
    app = FastAPI(title="Streaming creator delivery")

    def upstream_error(exc: InfraiError) -> HTTPException:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        return HTTPException(status_code=status, detail=exc.detail)

    @app.post("/assets", status_code=201)
    def ingest(body: AssetIngestRequest) -> dict[str, str]:
        asset = media.ingest(body.creator_id, body.source_uri, body.phone)
        return {"asset_id": asset.asset_id, "job_state": asset.job_state.value}

    @app.post("/assets/{asset_id}/processing-complete")
    def processing_complete(asset_id: str) -> dict[str, str]:
        try:
            asset = media.complete_processing(asset_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="asset not found") from exc
        return {"asset_id": asset.asset_id, "job_state": asset.job_state.value}

    @app.post("/assets/{asset_id}/login-code", status_code=202)
    def send_login_code(asset_id: str) -> dict[str, str]:
        try:
            media.send_login_code(asset_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="asset not found") from exc
        except InfraiError as exc:
            raise upstream_error(exc) from exc
        return {"asset_id": asset_id, "login_code": "sent"}

    @app.post("/assets/{asset_id}/deliver")
    def deliver(asset_id: str, body: VerifyLoginRequest) -> dict[str, str | bool]:
        try:
            decision = media.verify_and_deliver(asset_id, body.code)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="asset not found") from exc
        except InfraiError as exc:
            raise upstream_error(exc) from exc
        return {
            "delivered": decision.delivered,
            "asset_id": decision.asset_id,
            "creator_id": decision.creator_id,
            "playback_path": decision.playback_path,
        }

    return app


app = create_app()

