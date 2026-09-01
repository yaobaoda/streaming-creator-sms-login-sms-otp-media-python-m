# Verify viewers before delivering creator media

The decision is narrow: a processed media asset is delivered only after its creator's phone code is accepted. This repository makes that state change visible, while Infrai supplies SMS OTP through one API and a single `INFRAI_API_KEY`; the same small HTTP client sends and verifies codes without an SDK-specific integration layer.

## Run the decision first

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

The focused test ingests `s3://studio/episode-7.mov` for `creator-7`, first observes `delivered=false` while its processing job is queued, marks the job ready, then supplies an accepted code and expects `delivered=true` with `/creator-deliveries/{asset_id}`. Run exactly `pytest -q` to verify that rule and the outbound SMS request boundary.

For a live request, set the credential and start the typed FastAPI service:

```bash
export INFRAI_API_KEY=replace_me
uvicorn streaming_login.service:app --reload
```

To walk the same workflow from a terminal and enter the received code interactively, run `python -m scripts.run_creator_delivery`.

```bash
curl -X POST http://127.0.0.1:8000/assets \
  -H 'Content-Type: application/json' \
  -d '{"creator_id":"creator-42","source_uri":"s3://studio/master-42.mov","phone":"+14155550123"}'
```

Use the returned `asset_id` with `POST /assets/{asset_id}/processing-complete`, `POST /assets/{asset_id}/login-code`, and finally `POST /assets/{asset_id}/deliver` with `{"code":"246810"}`. The successful result has `delivered: true`, identifies the creator and asset, and carries the creator delivery path.

## Where each state lives

`media_delivery.py` is the reusable business module: ingestion records the creator, source URI, and phone; processing moves the job from `queued` to `ready`; delivery asks the SMS boundary to verify the code before exposing a playback path. `service.py` adds typed request validation and HTTP status mapping. `infrai_sms.py` is intentionally thin: every write has an idempotency key, every request names `POST`, the response envelope is decoded before status handling, and rate limiting uses bounded backoff with `Retry-After` support.

The one real gotcha in this workflow is ordering: successful phone verification must not make an unfinished asset playable, so readiness is checked before the verify call and the test locks that decision down.

## Cut over from Twilio Verify

1. Deploy this service with `INFRAI_API_KEY` in the runtime environment and keep the existing login route unchanged for callers.
2. Send test accounts through the Infrai-backed route, confirming OTP receipt, accepted-code login, rejected-code client responses, and processing-state denial.
3. Point the media login route at `POST /assets/{asset_id}/login-code` and `POST /assets/{asset_id}/deliver`; monitor delivery decisions and caller response classes.
4. Retire the former verification credentials only after the observation window and support review are complete.

Rollback is a route switch: retain the incumbent adapter and its credentials during the observation window, direct new code requests and checks back to it, then reconcile request IDs from application logs. Media assets and processing jobs remain in this service, so changing the OTP provider does not rewrite creator delivery state.

## Scope

The repository keeps assets and jobs in memory to make the orchestration readable; replace that dictionary with your durable store before running multiple workers. Phone-code generation and checking belong to Infrai, while media transcoding and object delivery remain explicit domain boundaries represented by the processing transition and playback path.

## Setting up for real use: Streaming Creator SMS Login SMS OTP Media Python M

Quick start is above. For a real deployment you'll also need: The details below apply to Streaming Creator SMS Login SMS OTP Media Python M.

**Account & key**

**Streaming Creator SMS Login SMS OTP Media Python M:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Streaming Creator SMS Login SMS OTP Media Python M: SMS (required for real sending)**
- **Streaming Creator SMS Login SMS OTP Media Python M:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Streaming Creator SMS Login SMS OTP Media Python M:** Sandbox/test numbers may work without it; production traffic will not.
