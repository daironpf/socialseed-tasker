from __future__ import annotations
from fastapi import APIRouter, Header, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

webhook_router = APIRouter()


@webhook_router.post("/api/v1/webhooks/receive")
async def webhooks_receive(request: Request, x_signature: Optional[str] = Header(None)):
    try:
        raw_body = await request.body()
    except Exception:
        raw_body = b""
    wm = request.app.state.events
    subs = wm.list_subscriptions()
    if any(s.get("secret") for s in subs):
        if not x_signature:
            return JSONResponse(status_code=401, content={"status": "error", "error": "missing signature"})
        verified = False
        for s in subs:
            secret = s.get("secret")
            if not secret:
                continue
            if wm.verify_signature(secret, raw_body, x_signature):
                verified = True
                break
        if not verified:
            return JSONResponse(status_code=401, content={"status": "error", "error": "invalid signature"})
    try:
        event = wm.receive(raw_body, x_signature)
    except Exception as exc:
        return JSONResponse(status_code=400, content={"status": "error", "error": str(exc)})
    bus = request.app.state.events_bus
    delivery = request.app.state.delivery_worker
    bus.publish(event)
    for s in subs:
        if "*" in s.get("events", []) or event.type in s.get("events", []):
            headers = {"Content-Type": "application/json"}
            secret = s.get("secret")
            if secret:
                import hmac, hashlib
                mac = hmac.new(secret.encode("utf-8"), event.to_json().encode("utf-8"), hashlib.sha256)
                headers["X-Signature"] = "sha256=" + mac.hexdigest()
            delivery.enqueue_delivery(s["url"], event.to_json(), headers=headers)
    return {"status": "ok", "event_id": event.id}


@webhook_router.post("/api/v1/webhooks/subscriptions")
async def create_subscription(req: dict, request: Request):
    wm = request.app.state.events
    sub = wm.create_subscription(url=req.get("url"), events=req.get("events"), secret=req.get("secret"))
    return {"status": "ok", "subscription": sub}


@webhook_router.get("/api/v1/webhooks/subscriptions")
async def list_subscriptions(request: Request):
    wm = request.app.state.events
    return {"status": "ok", "subscriptions": wm.list_subscriptions()}


@webhook_router.delete("/api/v1/webhooks/subscriptions/{sid}")
async def delete_subscription(sid: str, request: Request):
    wm = request.app.state.events
    wm.delete_subscription(sid)
    return {"status": "ok"}
