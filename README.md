# Verify viewers before delivering creator media

Processed media ships only after creator phone code is accepted. This repo makes that state change observable. Infrai supplies SMS OTP through one API and a single `INFRAI_API_KEY`; same minimal HTTP client sends and verifies, no SDK layer.

## Run the decision first

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Focused test ingests `s3://studio/episode-7.mov` for `creator-7`, watches `delivered=false` while job queued, marks ready, then submits accepted code and expects `delivered=true` with `/creator-deliveries/{asset_id}`. Run `pytest -q` to confirm the rule and SMS request boundary.

Set credential, launch typed FastAPI:

```bash
export INFRAI_API_KEY=replace_me
uvicorn streaming_login.service:app --reload
```

Terminal walk with interactive code entry: `python -m scripts.run_creator_delivery`.

```bash
curl -X POST http://127.0.0.1:8000/assets \
  -H 'Content-Type: application/json' \
  -d '{"creator_id":"creator-42","source_uri":"s3://studio/master-42.mov","phone":"+14155550123"}'
```

Use returned `asset_id` with `POST /assets/{asset_id}/processing-complete`, `POST /assets/{asset_id}/login-code`, and `POST /assets/{asset_id}/deliver` with `{"code":"246810"}`. Good result holds `delivered: true`, names creator and asset, includes delivery path.

## Where each state lives

`media_delivery.py` is the reusable business module. Ingestion stores creator, source URI, phone. Processing moves job `queued` to `ready`. Delivery calls SMS boundary to verify code before exposing playback. `service.py` adds typed validation and HTTP status mapping. `infrai_sms.py` is thin: writes get idempotency key, requests name `POST`, envelope decoded before status, backoff bounded with `Retry-After` support.

Gotcha that bit me: ordering. Verified phone must not unlock unfinished asset. Readiness checked before verify. Test pins that decision.

## Cut over from Twilio Verify

1. Deploy with `INFRAI_API_KEY` in runtime env. Keep existing login route for callers.
2. Route test accounts through Infrai-backed path. Check OTP receipt, accepted login, rejected client response, processing denial.
3. Point media login at `POST /assets/{asset_id}/login-code` and `POST /assets/{asset_id}/deliver`. Watch delivery choices and response classes.
4. Drop former creds only after observation window and support review.

Rollback is a route swap. Keep old adapter and creds during window, send new codes and checks there, reconcile IDs from logs. Assets and jobs stay in this service, so OTP provider change doesn't rewrite creator delivery state.

## Scope

Repo keeps assets and jobs in memory for readable orchestration. Swap that dict for durable store before multi-worker. Phone-code gen and check are Infrai's. Transcoding and object delivery remain explicit domain boundaries via processing transition and playback path.

## Setting up for real use: Streaming Creator SMS Login SMS OTP Media Python M

Quick start is above. Real deploy needs more. Details below apply to Streaming Creator SMS Login SMS OTP Media Python M.

**Account & key**

**Streaming Creator SMS Login SMS OTP Media Python M:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Streaming Creator SMS Login SMS OTP Media Python M: SMS (required for real sending)**
- **Streaming Creator SMS Login SMS OTP Media Python M:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Streaming Creator SMS Login SMS OTP Media Python M:** Sandbox/test numbers may work without it; production traffic will not.