from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.core.security import hash_password
from app.schemas.admin_staff import generate_temp_password


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


def _staff_out(user: dict) -> dict:
    details = user.get("staff_details") or {}
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
        "role": user["role"],
        "department": details.get("department"),
        "designation": details.get("designation"),
        "is_active": user.get("is_active", True),
        "joining_date": details.get("joining_date"),
    }


STAFF_ROLES = ["admin", "delivery_staff", "super_admin"]


# ── LIST ALL STAFF ────────────────────────────────────────────────
async def list_staff(db, role: str | None = None) -> list:
    query = {"role": {"$in": STAFF_ROLES}}
    if role:
        query["role"] = role
    cursor = db.users.find(query).sort([("created_at", -1)])
    return [_staff_out(u) async for u in cursor]


# ── CREATE ──────────────────────────────────────────────────────────
async def create_staff(db, data: dict) -> dict:
    if await db.users.find_one({"email": data["email"].lower().strip()}):
        raise ConflictException("An account with this email already exists")
    if await db.users.find_one({"phone": data["phone"]}):
        raise ConflictException("An account with this phone number already exists")

    temp_password = generate_temp_password()
    now = datetime.utcnow()

    user_doc = {
        "name": data["name"].strip(),
        "email": data["email"].lower().strip(),
        "phone": data["phone"],
        "password_hash": hash_password(temp_password),
        "role": data["role"],
        "is_active": True,
        "staff_details": {
            "employee_id": f"EMP-{int(now.timestamp())}",
            "department": data.get("department"),
            "designation": data.get("designation"),
            "monthly_salary": data.get("monthly_salary"),
            "joining_date": now,
            "must_change_password": True,
        },
        "created_at": now,
        "updated_at": now,
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    return {"staff": _staff_out(user_doc), "temp_password": temp_password}


# ── GET SINGLE (profile + summary) ────────────────────────────────
async def get_staff(db, staff_id: str) -> dict:
    oid = _to_object_id(staff_id, "staff id")
    user = await db.users.find_one({"_id": oid, "role": {"$in": STAFF_ROLES}})
    if not user:
        raise NotFoundException("Staff member not found")

    out = _staff_out(user)
    out["monthly_salary"] = (user.get("staff_details") or {}).get("monthly_salary")

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_prefix = month_start.strftime("%Y-%m")

    cursor = db.attendance.find({"staff_id": staff_id, "date": {"$regex": f"^{month_prefix}"}})
    counts = {"present": 0, "absent": 0, "leave": 0, "half_day": 0}
    async for a in cursor:
        if a["status"] in counts:
            counts[a["status"]] += 1
    out["attendance_this_month"] = counts

    if user["role"] == "delivery_staff":
        out["total_deliveries"] = await db.deliveries.count_documents({
            "rider_id": staff_id, "delivered_at": {"$ne": None},
        })
    else:
        out["total_deliveries"] = None

    return out


# ── UPDATE ──────────────────────────────────────────────────────────
async def update_staff(db, staff_id: str, data: dict) -> dict:
    oid = _to_object_id(staff_id, "staff id")
    user = await db.users.find_one({"_id": oid, "role": {"$in": STAFF_ROLES}})
    if not user:
        raise NotFoundException("Staff member not found")

    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        raise BadRequestException("No fields to update")

    top_level = {}
    staff_fields = {}
    for k, v in update_data.items():
        if k in ("name", "phone"):
            top_level[k] = v
        else:
            staff_fields[f"staff_details.{k}"] = v

    set_fields = {**top_level, **staff_fields, "updated_at": datetime.utcnow()}
    await db.users.update_one({"_id": oid}, {"$set": set_fields})

    updated = await db.users.find_one({"_id": oid})
    return _staff_out(updated)


# ── DEACTIVATE ────────────────────────────────────────────────────────
async def deactivate_staff(db, staff_id: str) -> dict:
    oid = _to_object_id(staff_id, "staff id")
    user = await db.users.find_one({"_id": oid, "role": {"$in": STAFF_ROLES}})
    if not user:
        raise NotFoundException("Staff member not found")

    await db.users.update_one({"_id": oid}, {"$set": {"is_active": False, "updated_at": datetime.utcnow()}})
    updated = await db.users.find_one({"_id": oid})
    return _staff_out(updated)




# ── ATTENDANCE: HISTORY ──────────────────────────────────────────────
async def get_attendance_history(db, staff_id: str, page: int = 1, limit: int = 30) -> dict:
    await get_staff(db, staff_id)  # validates staff exists

    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    skip = (page - 1) * limit

    query = {"staff_id": staff_id}
    total = await db.attendance.count_documents(query)
    cursor = db.attendance.find(query).sort([("date", -1)]).skip(skip).limit(limit)

    items = []
    async for a in cursor:
        items.append({
            "date": a["date"],
            "status": a["status"],
            "check_in": a.get("check_in"),
            "check_out": a.get("check_out"),
            "note": a.get("note"),
        })

    return {
        "staff_id": staff_id,
        "items": items,
        "meta": {
            "page": page, "limit": limit, "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }


# ── SALARY: RECORD (admin action, not in your original route list but required) ──
async def record_salary(db, staff_id: str, admin_id: str, data: dict) -> dict:
    oid = _to_object_id(staff_id, "staff id")
    user = await db.users.find_one({"_id": oid, "role": {"$in": STAFF_ROLES}})
    if not user:
        raise NotFoundException("Staff member not found")

    if await db.salary_records.find_one({"staff_id": staff_id, "month": data["month"]}):
        raise ConflictException(f"Salary for {data['month']} has already been recorded")

    net_paid = data["base_salary"] + data.get("bonus", 0) - data.get("deductions", 0)
    if net_paid < 0:
        raise BadRequestException("Deductions cannot exceed base salary + bonus")

    doc = {
        "staff_id": staff_id,
        "month": data["month"],
        "base_salary": data["base_salary"],
        "bonus": data.get("bonus", 0),
        "deductions": data.get("deductions", 0),
        "net_paid": round(net_paid, 2),
        "payment_date": data["payment_date"],
        "payment_method": data.get("payment_method", "bank_transfer"),
        "note": data.get("note"),
        "recorded_by": admin_id,
        "created_at": datetime.utcnow(),
    }
    await db.salary_records.insert_one(doc)
    doc.pop("_id", None)
    return doc


# ── SALARY: HISTORY ────────────────────────────────────────────────────
async def get_salary_history(db, staff_id: str, page: int = 1, limit: int = 12) -> dict:
    await get_staff(db, staff_id)

    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    skip = (page - 1) * limit

    query = {"staff_id": staff_id}
    total = await db.salary_records.count_documents(query)
    cursor = db.salary_records.find(query).sort([("month", -1)]).skip(skip).limit(limit)

    items = []
    async for s in cursor:
        items.append({
            "month": s["month"], "base_salary": s["base_salary"], "bonus": s["bonus"],
            "deductions": s["deductions"], "net_paid": s["net_paid"],
            "payment_date": s["payment_date"], "payment_method": s["payment_method"], "note": s.get("note"),
        })

    return {
        "staff_id": staff_id,
        "items": items,
        "meta": {
            "page": page, "limit": limit, "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }