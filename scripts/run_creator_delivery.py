from streaming_login.infrai_sms import InfraiSmsClient
from streaming_login.media_delivery import MediaDeliveryWorkflow


def main() -> None:
    phone = input("Creator phone in E.164 format: ").strip()
    workflow = MediaDeliveryWorkflow(InfraiSmsClient())
    asset = workflow.ingest("creator-42", "s3://studio/master-42.mov", phone)
    print({"asset_id": asset.asset_id, "job_state": asset.job_state.value})
    workflow.complete_processing(asset.asset_id)
    workflow.send_login_code(asset.asset_id)
    code = input("SMS code: ").strip()
    decision = workflow.verify_and_deliver(asset.asset_id, code)
    print(decision)


if __name__ == "__main__":
    main()
