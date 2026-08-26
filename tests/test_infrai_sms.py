import httpx

from streaming_login.infrai_sms import InfraiSmsClient


def test_sms_boundary_decodes_envelope_and_sends_idempotency_key() -> None:
    observed: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed.append(request)
        return httpx.Response(200, json={"ok": True, "data": {"accepted": True}})

    client = InfraiSmsClient(api_key="test-key", transport=httpx.MockTransport(handler))
    result = client.request_code("+14155550123", "login-send:asset-7")

    assert result == {"accepted": True}
    assert observed[0].method == "POST"
    assert observed[0].url.path == "/v1/sms/otp"
    assert observed[0].headers["Idempotency-Key"] == "login-send:asset-7"

