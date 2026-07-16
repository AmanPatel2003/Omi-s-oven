from datetime import datetime, timedelta
from bson import ObjectId

from app.core.exceptions import BadRequestException
from app.core.notification_providers import PROVIDER_MAP


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


# ── RESOLVE TARGET AUDIENCE ──────────────────────────────────────────
async def _resolve_targets(db, customer_ids: list[str] | None, segment: dict | None, exclude_inactive: bool = True) -> list[dict]:
    if customer_ids:
        oids = []
        for cid in customer_ids:
            try:
                oids.append(ObjectId(cid))
            except Exception:
                continue
        query = {"_id": {"$in": oids}, "role": "customer"}
        if exclude_inactive:
            query["is_active"] = True
        cursor = db.users.find(query)
        return await cursor.to_list(length=None)

    # segment-based or full broadcast
    query = {"role": "customer"}
    if exclude_inactive:
        query["is_active"] = True

    if segment:
        if segment.get("inactive_days"):
            cutoff = datetime.utcnow() - timedelta(days=segment["inactive_days"])
            recent_orderers = await db.orders.distinct("user_id", {"created_at": {"$gte": cutoff}})
            recent_orderer_oids = []
            for uid in recent_orderers:
                try:
                    recent_orderer_oids.append(ObjectId(uid))
                except Exception:
                    continue
            query["_id"] = {"$nin": recent_orderer_oids}

        if segment.get("min_lifetime_orders"):
            active_user_ids = await db.orders.aggregate([
                {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gte": segment["min_lifetime_orders"]}}},
            ]).to_list(length=None)
            qualifying_ids = []
            for r in active_user_ids:
                try:
                    qualifying_ids.append(ObjectId(r["_id"]))
                except Exception:
                    continue
            query["_id"] = {"$in": qualifying_ids} if "_id" not in query else {
                "$in": list(set(query["_id"].get("$in", [])) & set(qualifying_ids))
            }

    cursor = db.users.find(query)
    customers = await cursor.to_list(length=None)

    if segment and segment.get("loyalty_tier"):
        from app.core.config import TIERS
        target_tier = next((t for t in TIERS if t["name"] == segment["loyalty_tier"]), None)
        if target_tier:
            filtered = []
            for c in customers:
                reward = await db.rewards.find_one({"user_id": str(c["_id"])})
                lifetime = reward["lifetime_points"] if reward else 0
                current_tier = TIERS[0]["name"]
                for t in TIERS:
                    if lifetime >= t["min_lifetime_points"]:
                        current_tier = t["name"]
                if current_tier == segment["loyalty_tier"]:
                    filtered.append(c)
            customers = filtered

    return customers


def _get_channel_preference_key(channel: str) -> str:
    return channel  # matches keys already used in notification_preferences: email/sms/whatsapp


# ── SEND (targeted) ────────────────────────────────────────────────────
async def send_notification(db, admin_id: str, channel: str, customer_ids: list[str] | None,
                             segment: dict | None, subject: str | None, message: str) -> dict:
    if not customer_ids and not segment:
        raise BadRequestException("Provide either customer_ids or a segment filter")
    if channel == "email" and not subject:
        raise BadRequestException("subject is required for email campaigns")

    targets = await _resolve_targets(db, customer_ids, segment, exclude_inactive=True)
    return await _run_campaign(db, admin_id, "targeted", channel, subject, message, targets, segment)


# ── BROADCAST (all customers) ────────────────────────────────────────────
async def broadcast_notification(db, admin_id: str, channel: str, subject: str | None,
                                  message: str, exclude_inactive: bool) -> dict:
    if channel == "email" and not subject:
        raise BadRequestException("subject is required for email campaigns")

    targets = await _resolve_targets(db, None, None, exclude_inactive=exclude_inactive)
    return await _run_campaign(db, admin_id, "broadcast", channel, subject, message, targets, None)


# ── SHARED SEND LOOP ──────────────────────────────────────────────────
async def _run_campaign(db, admin_id: str, campaign_type: str, channel: str,
                         subject: str | None, message: str, targets: list[dict], segment: dict | None) -> dict:
    now = datetime.utcnow()
    campaign_doc = {
        "type": campaign_type,
        "channel": channel,
        "subject": subject,
        "message": message,
        "segment": segment,
        "target_count": len(targets),
        "sent_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "status": "in_progress",
        "sent_by": admin_id,
        "created_at": now,
        "completed_at": None,
    }
    result = await db.campaigns.insert_one(campaign_doc)
    campaign_id = result.inserted_id

    provider_fn = PROVIDER_MAP[channel]
    pref_key = _get_channel_preference_key(channel)

    sent_count = 0
    failed_count = 0
    skipped_count = 0
    provider_configured = True

    for customer in targets:
        prefs = customer.get("notification_preferences", {"email": True, "sms": True, "whatsapp": False})
        if not prefs.get(pref_key, True):
            skipped_count += 1
            continue

        contact = customer["email"] if channel == "email" else customer["phone"]
        if channel == "email":
            send_result = await provider_fn(to=contact, subject=subject, body=message)
        else:
            send_result = await provider_fn(to=contact, message=message)

        if send_result["success"]:
            sent_count += 1
        else:
            failed_count += 1
            provider_configured = False   # provider stub always fails — surfaces this clearly in the response

    await db.campaigns.update_one(
        {"_id": campaign_id},
        {"$set": {
            "sent_count": sent_count, "failed_count": failed_count, "skipped_count": skipped_count,
            "status": "completed", "completed_at": datetime.utcnow(),
        }},
    )

    updated = await db.campaigns.find_one({"_id": campaign_id})
    out = _out(updated)
    out["provider_configured"] = provider_configured
    if not provider_configured:
        out["warning"] = (
            f"No {channel} provider is configured — {failed_count} message(s) were NOT actually delivered. "
            f"This campaign was logged for audit purposes only. Wire a real provider in "
            f"app/core/notification_providers.py to enable real sending."
        )
    return out