from streaming_login.media_delivery import MediaDeliveryWorkflow


class AcceptedSms:
    def __init__(self) -> None:
        self.sent_to = ""
        self.verified = False

    def request_code(self, phone: str, request_id: str) -> object:
        self.sent_to = phone
        return {"accepted": True}

    def verify_code(self, phone: str, code: str, request_id: str) -> object:
        self.verified = True
        return {"verified": True}


def test_creator_delivery_requires_ready_asset_and_verified_code() -> None:
    sms = AcceptedSms()
    workflow = MediaDeliveryWorkflow(sms)
    asset = workflow.ingest("creator-7", "s3://studio/episode-7.mov", "+14155550123")

    early = workflow.verify_and_deliver(asset.asset_id, "246810")
    assert early.delivered is False
    assert sms.verified is False

    workflow.complete_processing(asset.asset_id)
    workflow.send_login_code(asset.asset_id)
    delivered = workflow.verify_and_deliver(asset.asset_id, "246810")

    assert sms.sent_to == "+14155550123"
    assert sms.verified is True
    assert delivered.delivered is True
    assert delivered.playback_path == f"/creator-deliveries/{asset.asset_id}"

