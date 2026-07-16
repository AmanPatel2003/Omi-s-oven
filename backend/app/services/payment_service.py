# import hmac
# import hashlib
# import razorpay
# from datetime import datetime
# from typing import Optional
# from bson import ObjectId

# from app.core.config import settings
# from app.core.exceptions import NotFoundException, BadRequestException, UnauthorizedException, ForbiddenException

# client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# def _to_object_id(id_str: str, label: str = "id"):
#     try:
#         return ObjectId(id_str)
#     except Exception:
#         raise BadRequestException(f"Invalid {label}")


# def _out(doc: dict) -> dict:
#     doc["id"] = str(doc.pop("_id"))
#     return doc


# # ── CREATE RAZORPAY ORDER ─────────────────────────────────────
# async def create_payment(db, user_id: str, order_id: str) -> dict:
#     order = await db.orders.find_one({
#         "_id": _to_object_id(order_id, "order id"),
#         "user_id": user_id,
#     })
#     if not order:
#         raise NotFoundException("Order not found")

#     if order["payment_status"] == "paid":
#         raise BadRequestException("This order has already been paid for")

#     # reuse an existing pending payment for this order instead of creating duplicates
#     existing = await db.payments.find_one({"order_id": order_id, "status": {"$in": ["created", "authorized"]}})
#     if existing:
#         return {
#             "razorpay_order_id": existing["razorpay_order_id"],
#             "amount": int(existing["amount"] * 100),
#             "currency": existing["currency"],
#             "razorpay_key_id": settings.RAZORPAY_KEY_ID,
#             "order_id": order_id,
#         }

#     amount_paise = int(round(order["total"] * 100))  # Razorpay always works in the smallest currency unit

#     rzp_order = client.order.create({
#         "amount": amount_paise,
#         "currency": "INR",
#         "receipt": order["order_number"],
#         "notes": {"order_id": order_id, "user_id": user_id},
#     })

#     now = datetime.utcnow()
#     payment_doc = {
#         "order_id": order_id,
#         "razorpay_order_id": rzp_order["id"],
#         "razorpay_payment_id": None,
#         "razorpay_signature": None,
#         "amount": order["total"],
#         "currency": "INR",
#         "status": "created",
#         "method": None,
#         "refund_id": None,
#         "refund_status": None,
#         "refund_amount": None,
#         "refund_reason": None,
#         "raw_webhook_events": [],
#         "created_at": now,
#         "updated_at": now,
#     }
#     await db.payments.insert_one(payment_doc)

#     return {
#         "razorpay_order_id": rzp_order["id"],
#         "amount": amount_paise,
#         "currency": "INR",
#         "razorpay_key_id": settings.RAZORPAY_KEY_ID,
#         "order_id": order_id,
#     }


# # ── VERIFY PAYMENT (client-side confirmation, not the source of truth) ──
# async def verify_payment(
#     db,
#     user_id: str,
#     razorpay_order_id: str,
#     razorpay_payment_id: str,
#     razorpay_signature: str,
# ) -> dict:
#     payment = await db.payments.find_one({"razorpay_order_id": razorpay_order_id})
#     if not payment:
#         raise NotFoundException("Payment record not found")

#     order = await db.orders.find_one({"_id": ObjectId(payment["order_id"]), "user_id": user_id})
#     if not order:
#         raise NotFoundException("Order not found")

#     # HMAC SHA256 over "order_id|payment_id" using the key SECRET (never the key id)
#     body = f"{razorpay_order_id}|{razorpay_payment_id}"
#     expected_signature = hmac.new(
#         key=settings.RAZORPAY_KEY_SECRET.encode(),
#         msg=body.encode(),
#         digestmod=hashlib.sha256,
#     ).hexdigest()

#     if not hmac.compare_digest(expected_signature, razorpay_signature):
#         await db.payments.update_one(
#             {"_id": payment["_id"]},
#             {"$set": {"status": "failed", "updated_at": datetime.utcnow()}},
#         )
#         raise BadRequestException("Payment verification failed — signature mismatch")

#     # Signature is valid, but DO NOT mark order as paid here — that's the webhook's job.
#     # This just reflects the client-observed success back to the frontend immediately.
#     await db.payments.update_one(
#         {"_id": payment["_id"]},
#         {"$set": {
#             "razorpay_payment_id": razorpay_payment_id,
#             "razorpay_signature": razorpay_signature,
#             "status": "authorized",
#             "updated_at": datetime.utcnow(),
#         }},
#     )

#     return {"verified": True, "order_id": payment["order_id"]}


# # ── WEBHOOK (authoritative — Razorpay server calling us directly) ────
# async def handle_webhook(db, raw_body: bytes, signature: str) -> dict:
#     expected_signature = hmac.new(
#         key=settings.RAZORPAY_WEBHOOK_SECRET.encode(),
#         msg=raw_body,
#         digestmod=hashlib.sha256,
#     ).hexdigest()

#     if not hmac.compare_digest(expected_signature, signature):
#         raise UnauthorizedException("Invalid webhook signature")

#     import json
#     payload = json.loads(raw_body)
#     event = payload.get("event")
#     entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

#     razorpay_order_id = entity.get("order_id")
#     razorpay_payment_id = entity.get("id")

#     if not razorpay_order_id:
#         return {"handled": False, "reason": "no order_id in payload"}

#     payment = await db.payments.find_one({"razorpay_order_id": razorpay_order_id})
#     if not payment:
#         return {"handled": False, "reason": "payment record not found"}

#     # idempotency guard — Razorpay may send the same webhook more than once
#     already_processed = any(
#         e.get("event") == event and e.get("payment_id") == razorpay_payment_id
#         for e in payment.get("raw_webhook_events", [])
#     )
#     if already_processed:
#         return {"handled": True, "duplicate": True}

#     now = datetime.utcnow()

#     if event == "payment.captured":
#         await db.payments.update_one(
#             {"_id": payment["_id"]},
#             {
#                 "$set": {
#                     "razorpay_payment_id": razorpay_payment_id,
#                     "status": "captured",
#                     "method": entity.get("method"),
#                     "updated_at": now,
#                 },
#                 "$push": {"raw_webhook_events": {"event": event, "payment_id": razorpay_payment_id, "at": now}},
#             },
#         )
#         await db.orders.update_one(
#             {"_id": ObjectId(payment["order_id"])},
#             {"$set": {
#                 "payment_status": "paid",
#                 "status": "confirmed",
#                 "updated_at": now,
#             },
#             "$push": {"status_history": {"status": "confirmed", "timestamp": now, "note": "Payment received"}}},
#         )

#     elif event == "payment.failed":
#         await db.payments.update_one(
#             {"_id": payment["_id"]},
#             {
#                 "$set": {"status": "failed", "updated_at": now},
#                 "$push": {"raw_webhook_events": {"event": event, "payment_id": razorpay_payment_id, "at": now}},
#             },
#         )
#         await db.orders.update_one(
#             {"_id": ObjectId(payment["order_id"])},
#             {"$set": {"payment_status": "failed", "updated_at": now}},
#         )

#     return {"handled": True, "event": event}


# # ── GET PAYMENT DETAILS ────────────────────────────────────────
# async def get_payment(db, user_id: str, order_id: str) -> dict:
#     order = await db.orders.find_one({"_id": _to_object_id(order_id, "order id"), "user_id": user_id})
#     if not order:
#         raise NotFoundException("Order not found")

#     payment = await db.payments.find_one({"order_id": order_id})
#     if not payment:
#         raise NotFoundException("No payment found for this order")

#     return _out(payment)


# # ── REFUND (admin-gated) ────────────────────────────────────────
# async def request_refund(
#     db,
#     requesting_user: dict,
#     order_id: str,
#     amount: Optional[float],
#     reason: Optional[str],
# ) -> dict:
#     if requesting_user.get("role") != "admin":
#         raise ForbiddenException("Only admins can process refunds")

#     order = await db.orders.find_one({"_id": _to_object_id(order_id, "order id")})
#     if not order:
#         raise NotFoundException("Order not found")

#     payment = await db.payments.find_one({"order_id": order_id, "status": "captured"})
#     if not payment:
#         raise BadRequestException("No captured payment found for this order")

#     if payment.get("refund_status") == "processed":
#         raise BadRequestException("This payment has already been refunded")

#     refund_amount = amount or payment["amount"]
#     if refund_amount > payment["amount"]:
#         raise BadRequestException("Refund amount cannot exceed the paid amount")

#     rzp_refund = client.payment.refund(payment["razorpay_payment_id"], {
#         "amount": int(round(refund_amount * 100)),
#         "notes": {"reason": reason or "Refund requested"},
#     })

#     now = datetime.utcnow()
#     await db.payments.update_one(
#         {"_id": payment["_id"]},
#         {"$set": {
#             "refund_id": rzp_refund["id"],
#             "refund_status": "processed",
#             "refund_amount": refund_amount,
#             "refund_reason": reason,
#             "status": "refunded",
#             "updated_at": now,
#         }},
#     )
#     await db.orders.update_one(
#         {"_id": order["_id"]},
#         {"$set": {"payment_status": "refunded", "updated_at": now}},
#     )

#     payment = await db.payments.find_one({"_id": payment["_id"]})
#     return _out(payment)