"""
Fills remaining gaps: product image upload/delete (Cloudinary), staff
self-service read endpoints (my-attendance/my-salary), GET /payments/:id,
and admin staff list/deactivate.
"""
import pytest
import io


class TestAdminProductImages:
    async def test_upload_image_success(self, client, admin, product):
        files = {"files": ("cake.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")}
        resp = await client.post(f"/admin/products/{product['_id']}/images", headers=admin["headers"], files=files)
        assert resp.status_code == 200
        assert len(resp.json()["data"]["images"]) == 1
        assert "public_id" in resp.json()["data"]["images"][0]

    async def test_upload_rejects_disallowed_content_type(self, client, admin, product):
        files = {"files": ("doc.pdf", io.BytesIO(b"fake-pdf-bytes"), "application/pdf")}
        resp = await client.post(f"/admin/products/{product['_id']}/images", headers=admin["headers"], files=files)
        assert resp.status_code == 400

    async def test_upload_exceeding_max_images_rejected(self, client, admin, product, db):
        # pre-fill with 6 images (assuming MAX_IMAGES_PER_PRODUCT == 6)
        existing = [{"url": f"https://x.com/{i}.jpg", "public_id": f"p{i}"} for i in range(6)]
        await db.products.update_one({"_id": product["_id"]}, {"$set": {"images": existing}})

        files = {"files": ("one_more.jpg", io.BytesIO(b"data"), "image/jpeg")}
        resp = await client.post(f"/admin/products/{product['_id']}/images", headers=admin["headers"], files=files)
        assert resp.status_code == 400

    async def test_delete_image(self, client, admin, product):
        files = {"files": ("cake.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")}
        upload = await client.post(f"/admin/products/{product['_id']}/images", headers=admin["headers"], files=files)
        public_id = upload.json()["data"]["images"][0]["public_id"]

        resp = await client.delete(f"/admin/products/{product['_id']}/images?public_id={public_id}", headers=admin["headers"])
        assert resp.status_code == 200
        assert len(resp.json()["data"]["images"]) == 0

    async def test_delete_nonexistent_image_404(self, client, admin, product):
        resp = await client.delete(f"/admin/products/{product['_id']}/images?public_id=ghost", headers=admin["headers"])
        assert resp.status_code == 404

    async def test_uploaded_image_visible_on_public_product_page(self, client, admin, product):
        files = {"files": ("cake.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")}
        await client.post(f"/admin/products/{product['_id']}/images", headers=admin["headers"], files=files)

        resp = await client.get(f"/products/{product['slug']}")
        assert len(resp.json()["data"]["images"]) == 1


class TestStaffSelfServiceReadEndpoints:
    async def test_my_attendance_reflects_own_clock_in(self, client, admin, delivery_staff):
        await client.post("/staff/clock-in", headers=delivery_staff["headers"], json={})
        resp = await client.get("/staff/my-attendance", headers=delivery_staff["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["present_days"] >= 1

    async def test_my_attendance_isolated_between_staff(self, client, delivery_staff, super_admin):
        # create a second rider directly through the API
        second = await client.post("/admin/staff", headers=super_admin["headers"], json={
            "name": "Second Rider", "email": "secondrider@test.com", "phone": "9700000001", "role": "delivery_staff",
        })
        temp_password = second.json()["data"]["temp_password"]
        login = await client.post("/auth/login", json={"identifier": "secondrider@test.com", "password": temp_password})
        second_rider_headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

        await client.post("/staff/clock-in", headers=delivery_staff["headers"], json={})
        # second rider never clocked in
        resp = await client.get("/staff/my-attendance", headers=second_rider_headers)
        assert resp.json()["data"]["present_days"] == 0

    async def test_my_salary_empty_for_new_staff(self, client, delivery_staff):
        resp = await client.get("/staff/my-salary", headers=delivery_staff["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["items"] == []

    async def test_my_salary_reflects_processed_month(self, client, super_admin, admin, delivery_staff, db):
        from bson import ObjectId
        await db.users.update_one({"_id": ObjectId(delivery_staff["id"])},
                                   {"$set": {"staff_details.monthly_salary": 20000}})
        from datetime import datetime
        month = datetime.utcnow().strftime("%Y-%m")
        await client.post(f"/admin/salary/process/{month}", headers=super_admin["headers"], json={})

        resp = await client.get("/staff/my-salary", headers=delivery_staff["headers"])
        assert any(s["month"] == month for s in resp.json()["data"]["items"])

    async def test_customer_cannot_access_staff_routes(self, client, customer):
        resp = await client.post("/staff/clock-in", headers=customer["headers"], json={})
        assert resp.status_code == 403

    async def test_clock_in_twice_rejected(self, client, delivery_staff):
        await client.post("/staff/clock-in", headers=delivery_staff["headers"], json={})
        resp = await client.post("/staff/clock-in", headers=delivery_staff["headers"], json={})
        assert resp.status_code == 409

    async def test_clock_out_success(self, client, delivery_staff):
        await client.post("/staff/clock-in", headers=delivery_staff["headers"], json={})
        resp = await client.post("/staff/clock-out", headers=delivery_staff["headers"], json={})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] in ("present", "half_day")


class TestGetPaymentByOrder:
    async def test_get_payment_for_own_order(self, client, customer, product, address):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        order = await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})
        order_id = order.json()["data"]["id"]
        await client.post("/payments/create", headers=customer["headers"], json={"order_id": order_id})

        resp = await client.get(f"/payments/{order_id}", headers=customer["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["order_id"] == order_id

    async def test_get_payment_no_payment_yet_404(self, client, customer, product, address):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        order = await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})
        order_id = order.json()["data"]["id"]

        resp = await client.get(f"/payments/{order_id}", headers=customer["headers"])
        assert resp.status_code == 404

    async def test_get_payment_cross_user_404(self, client, customer, second_customer, product, address):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        order = await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})
        order_id = order.json()["data"]["id"]
        await client.post("/payments/create", headers=customer["headers"], json={"order_id": order_id})

        resp = await client.get(f"/payments/{order_id}", headers=second_customer["headers"])
        assert resp.status_code == 404


class TestAdminStaffListAndDeactivate:
    async def test_list_filter_by_role(self, client, admin, delivery_staff):
        resp = await client.get("/admin/staff?role=delivery_staff", headers=admin["headers"])
        assert resp.status_code == 200
        assert all(s["role"] == "delivery_staff" for s in resp.json()["data"])

    async def test_deactivate_by_super_admin(self, client, super_admin, delivery_staff):
        resp = await client.delete(f"/admin/staff/{delivery_staff['id']}", headers=super_admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

    async def test_deactivated_staff_cannot_login(self, client, super_admin, delivery_staff, db):
        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(delivery_staff["id"])})
        await client.delete(f"/admin/staff/{delivery_staff['id']}", headers=super_admin["headers"])

        # deactivated staff's existing token should now be rejected on the next request
        resp = await client.get("/staff/my-attendance", headers=delivery_staff["headers"])
        assert resp.status_code == 401