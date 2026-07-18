"""
Tests for /admin/staff/*, /admin/attendance/*, /admin/salary/*.
"""
import pytest
from datetime import datetime, timedelta


class TestStaffCreation:
    async def test_temp_password_actually_logs_in(self, client, super_admin):
        resp = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "New Rider", "email": "temppw@test.com", "phone": "9800000001", "role": "delivery_staff",
        })
        temp_password = resp.json()["data"]["temp_password"]

        login = await client.post("/auth/login", json={"identifier": "temppw@test.com", "password": temp_password})
        assert login.status_code == 200

    async def test_duplicate_email_rejected(self, client, super_admin):
        payload = {"name": "A", "email": "dupstaff@test.com", "phone": "9800000002", "role": "admin"}
        await client.post("/admin/staff", headers=super_admin["headers"], json=payload)
        payload["phone"] = "9800000003"
        resp = await client.post("/admin/staff", headers=super_admin["headers"], json=payload)
        assert resp.status_code == 409

    async def test_invalid_role_rejected(self, client, super_admin):
        resp = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "A", "email": "badrole@test.com", "phone": "9800000004", "role": "customer",
        })
        assert resp.status_code == 422


class TestStaffDetail:
    async def test_get_staff_shows_this_month_attendance_summary(self, client, super_admin, admin):
        create = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "Rider Detail", "email": "riderdetail@test.com", "phone": "9800000005", "role": "delivery_staff",
        })
        staff_id = create.json()["data"]["staff"]["id"]

        resp = await client.get(f"/admin/staff/{staff_id}", headers=admin["headers"])
        assert resp.status_code == 200
        assert "attendance_this_month" in resp.json()["data"]

    async def test_update_staff_details(self, client, super_admin, admin):
        create = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "Update Me", "email": "updateme@test.com", "phone": "9800000006", "role": "admin",
        })
        staff_id = create.json()["data"]["staff"]["id"]

        resp = await client.put(f"/admin/staff/{staff_id}", headers=admin["headers"], json={"designation": "Senior Admin"})
        assert resp.status_code == 200
        assert resp.json()["data"]["designation"] == "Senior Admin"


class TestAttendanceClockInOut:
    async def _create_staff(self, client, super_admin, email="attstaff@test.com", phone="9800000010"):
        create = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "Attendance Staff", "email": email, "phone": phone, "role": "delivery_staff",
        })
        return create.json()["data"]["staff"]["id"]

    async def test_clock_in_success(self, client, admin, super_admin):
        staff_id = await self._create_staff(client, super_admin)
        resp = await client.post("/admin/attendance/clock-in", headers=admin["headers"], json={"staff_id": staff_id})
        assert resp.status_code == 200

    async def test_double_clock_in_same_day_rejected(self, client, admin, super_admin):
        staff_id = await self._create_staff(client, super_admin, "double@test.com", "9800000011")
        await client.post("/admin/attendance/clock-in", headers=admin["headers"], json={"staff_id": staff_id})
        resp = await client.post("/admin/attendance/clock-in", headers=admin["headers"], json={"staff_id": staff_id})
        assert resp.status_code == 409

    async def test_clock_out_before_clock_in_rejected(self, client, admin, super_admin):
        staff_id = await self._create_staff(client, super_admin, "noclock@test.com", "9800000012")
        resp = await client.post("/admin/attendance/clock-out", headers=admin["headers"], json={"staff_id": staff_id})
        assert resp.status_code == 400

    async def test_clock_out_computes_hours(self, client, admin, super_admin, db):
        staff_id = await self._create_staff(client, super_admin, "hours@test.com", "9800000013")
        past_check_in = (datetime.utcnow() - timedelta(hours=6)).isoformat()
        await client.post("/admin/attendance/clock-in", headers=admin["headers"],
                           json={"staff_id": staff_id, "check_in": past_check_in})
        resp = await client.post("/admin/attendance/clock-out", headers=admin["headers"], json={"staff_id": staff_id})
        assert resp.status_code == 200
        assert resp.json()["data"]["hours_worked"] >= 5.9

    async def test_under_four_hours_marked_half_day(self, client, admin, super_admin):
        staff_id = await self._create_staff(client, super_admin, "halfday@test.com", "9800000014")
        past_check_in = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        await client.post("/admin/attendance/clock-in", headers=admin["headers"],
                           json={"staff_id": staff_id, "check_in": past_check_in})
        resp = await client.post("/admin/attendance/clock-out", headers=admin["headers"], json={"staff_id": staff_id})
        assert resp.json()["data"]["status"] == "half_day"


class TestAttendanceCorrectionAndLeave:
    async def test_edit_attendance_marks_corrected(self, client, admin, super_admin):
        create = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "Correction Staff", "email": "correction@test.com", "phone": "9800000015", "role": "delivery_staff",
        })
        staff_id = create.json()["data"]["staff"]["id"]
        clock_in = await client.post("/admin/attendance/clock-in", headers=admin["headers"], json={"staff_id": staff_id})
        record_id = clock_in.json()["data"]["id"]

        resp = await client.put(f"/admin/attendance/{record_id}", headers=admin["headers"],
                                 json={"status": "absent"})
        assert resp.status_code == 200
        assert resp.json()["data"]["is_corrected"] is True

    async def test_mark_leave_creates_one_record_per_day(self, client, admin, super_admin):
        create = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "Leave Staff", "email": "leave@test.com", "phone": "9800000016", "role": "delivery_staff",
        })
        staff_id = create.json()["data"]["staff"]["id"]

        today = datetime.utcnow()
        date_from = today.strftime("%Y-%m-%d")
        date_to = (today + timedelta(days=2)).strftime("%Y-%m-%d")

        resp = await client.post("/admin/attendance/mark-leave", headers=admin["headers"], json={
            "staff_id": staff_id, "date_from": date_from, "date_to": date_to,
        })
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 3
        assert all(r["status"] == "leave" for r in resp.json()["data"])


class TestTodayAndReport:
    async def test_today_status_buckets_correctly(self, client, admin, super_admin):
        create = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "Today Staff", "email": "today@test.com", "phone": "9800000017", "role": "delivery_staff",
        })
        staff_id = create.json()["data"]["staff"]["id"]
        await client.post("/admin/attendance/clock-in", headers=admin["headers"], json={"staff_id": staff_id})

        resp = await client.get("/admin/attendance/today", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["present_count"] >= 1

    async def test_monthly_report_grid_shape(self, client, admin, super_admin):
        month = datetime.utcnow().strftime("%Y-%m")
        resp = await client.get(f"/admin/attendance/report?month={month}", headers=admin["headers"])
        assert resp.status_code == 200
        assert "rows" in resp.json()["data"]

    async def test_export_returns_excel(self, client, admin):
        month = datetime.utcnow().strftime("%Y-%m")
        resp = await client.get(f"/admin/attendance/export?month={month}", headers=admin["headers"])
        assert resp.status_code == 200
        assert "spreadsheet" in resp.headers["content-type"]


class TestSalaryCalculation:
    async def _staff_with_salary(self, client, super_admin, admin, salary=30000, email="salarystaff@test.com", phone="9800000020"):
        create = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "Salary Staff", "email": email, "phone": phone, "role": "delivery_staff",
            "monthly_salary": salary,
        })
        return create.json()["data"]["staff"]["id"]

    async def test_calculate_skips_staff_with_no_salary_configured(self, client, admin, super_admin):
        create = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "No Salary", "email": "nosalary@test.com", "phone": "9800000021", "role": "delivery_staff",
        })
        month = datetime.utcnow().strftime("%Y-%m")
        resp = await client.get(f"/admin/salary/calculate/{month}", headers=admin["headers"])
        assert resp.status_code == 200
        staff_id = create.json()["data"]["staff"]["id"]
        assert not any(i["staff_id"] == staff_id for i in resp.json()["data"]["items"])

    async def test_single_staff_breakdown(self, client, admin, super_admin):
        staff_id = await self._staff_with_salary(client, super_admin, admin)
        month = datetime.utcnow().strftime("%Y-%m")
        resp = await client.get(f"/admin/salary/{staff_id}/{month}", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["base_salary"] == 30000

    async def test_process_month_is_idempotent(self, client, super_admin, admin):
        staff_id = await self._staff_with_salary(client, super_admin, admin, email="idempotent@test.com", phone="9800000022")
        month = datetime.utcnow().strftime("%Y-%m")

        first = await client.post(f"/admin/salary/process/{month}", headers=super_admin["headers"], json={})
        second = await client.post(f"/admin/salary/process/{month}", headers=super_admin["headers"], json={})

        assert first.status_code == 200
        assert second.json()["data"]["skipped_count"] >= 1

    async def test_process_with_force_reprocesses(self, client, super_admin, admin):
        staff_id = await self._staff_with_salary(client, super_admin, admin, email="force@test.com", phone="9800000023")
        month = datetime.utcnow().strftime("%Y-%m")

        await client.post(f"/admin/salary/process/{month}", headers=super_admin["headers"], json={})
        resp = await client.post(f"/admin/salary/process/{month}", headers=super_admin["headers"], json={"force": True})
        assert resp.json()["data"]["skipped_count"] == 0

    async def test_regular_admin_cannot_process_salary(self, client, admin):
        month = datetime.utcnow().strftime("%Y-%m")
        resp = await client.post(f"/admin/salary/process/{month}", headers=admin["headers"], json={})
        assert resp.status_code == 403

    async def test_generate_slip_returns_pdf_but_no_real_email(self, client, super_admin, admin):
        staff_id = await self._staff_with_salary(client, super_admin, admin, email="slip@test.com", phone="9800000024")
        resp = await client.post(f"/admin/salary/{staff_id}/slip", headers=admin["headers"], json={"email_to_staff": True})
        assert resp.status_code == 200
        assert resp.json()["data"]["pdf_generated"] is True
        assert resp.json()["data"]["email_sent"] is False   # provider is a stub — must reflect this honestly

    async def test_export_all_salaries_excel(self, client, admin):
        month = datetime.utcnow().strftime("%Y-%m")
        resp = await client.get(f"/admin/salary/export/{month}", headers=admin["headers"])
        assert resp.status_code == 200
        assert "spreadsheet" in resp.headers["content-type"]

    async def test_invalid_month_format_rejected(self, client, admin):
        resp = await client.get("/admin/salary/calculate/2026-7", headers=admin["headers"])
        assert resp.status_code == 400