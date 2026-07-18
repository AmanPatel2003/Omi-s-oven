"""
Tests for /admin/categories/*, including main-category / subcategory hierarchy.
"""
import pytest


class TestBasicCategoryCRUD:
    async def test_create_category(self, client, admin):
        resp = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Cookies", "slug": "cookies",
        })
        assert resp.status_code == 200

    async def test_duplicate_slug_rejected(self, client, admin, category):
        resp = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Dup", "slug": category["slug"],
        })
        assert resp.status_code == 409

    async def test_slug_change_cascades_to_products(self, client, admin, category, product, db):
        resp = await client.put(f"/admin/categories/{category['_id']}", headers=admin["headers"], json={
            "slug": "celebration-cakes",
        })
        assert resp.status_code == 200

        updated_product = await db.products.find_one({"_id": product["_id"]})
        assert updated_product["category"] == "celebration-cakes"

    async def test_reorder_categories(self, client, admin, category, db):
        second = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Pastries", "slug": "pastries", "sort_order": 2,
        })
        second_id = second.json()["data"]["id"]

        resp = await client.put("/admin/categories/reorder", headers=admin["headers"], json={
            "items": [{"id": str(category["_id"]), "sort_order": 5}, {"id": second_id, "sort_order": 1}],
        })
        assert resp.status_code == 200

    async def test_reorder_duplicate_ids_rejected(self, client, admin, category):
        resp = await client.put("/admin/categories/reorder", headers=admin["headers"], json={
            "items": [
                {"id": str(category["_id"]), "sort_order": 1},
                {"id": str(category["_id"]), "sort_order": 2},
            ],
        })
        assert resp.status_code == 422


class TestDeleteBehavior:
    async def test_delete_empty_category_hard_deletes(self, client, admin, db):
        create = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Empty Cat", "slug": "empty-cat",
        })
        category_id = create.json()["data"]["id"]

        resp = await client.delete(f"/admin/categories/{category_id}", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

        gone = await db.categories.find_one({"slug": "empty-cat"})
        assert gone is None

    async def test_delete_category_with_products_soft_deletes(self, client, admin, category, product, db):
        resp = await client.delete(f"/admin/categories/{category['_id']}", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is False
        assert resp.json()["data"]["deactivated"] is True

        still_exists = await db.categories.find_one({"_id": category["_id"]})
        assert still_exists is not None
        assert still_exists["is_active"] is False

    async def test_force_delete_with_products_hard_deletes_anyway(self, client, admin, category, product, db):
        resp = await client.delete(f"/admin/categories/{category['_id']}?force=true", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True


class TestSubcategoryHierarchy:
    async def _create_main(self, client, admin, name="Cakes", slug="cakes-main"):
        resp = await client.post("/admin/categories", headers=admin["headers"], json={"name": name, "slug": slug})
        return resp.json()["data"]["id"]

    async def test_create_subcategory_with_parent(self, client, admin):
        main_id = await self._create_main(client, admin)
        resp = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Wedding Cake", "slug": "wedding-cake", "parent_id": main_id,
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["parent_id"] == main_id
        assert resp.json()["data"]["parent_name"] == "Cakes"

    async def test_cannot_nest_subcategory_under_subcategory(self, client, admin):
        main_id = await self._create_main(client, admin)
        sub = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Wedding Cake", "slug": "wedding-cake-2", "parent_id": main_id,
        })
        sub_id = sub.json()["data"]["id"]

        resp = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Tiered Wedding Cake", "slug": "tiered-wedding-cake", "parent_id": sub_id,
        })
        assert resp.status_code == 400

    async def test_category_cannot_be_its_own_parent(self, client, admin):
        main_id = await self._create_main(client, admin, "Cakes B", "cakes-b")
        resp = await client.put(f"/admin/categories/{main_id}", headers=admin["headers"], json={"parent_id": main_id})
        assert resp.status_code == 400

    async def test_category_with_children_cannot_become_a_subcategory(self, client, admin):
        main_id = await self._create_main(client, admin, "Cakes C", "cakes-c")
        await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Birthday Cake", "slug": "birthday-cake-c", "parent_id": main_id,
        })
        other_main = await self._create_main(client, admin, "Sandwiches", "sandwiches")

        resp = await client.put(f"/admin/categories/{main_id}", headers=admin["headers"], json={"parent_id": other_main})
        assert resp.status_code == 400

    async def test_invalid_parent_id_rejected(self, client, admin):
        resp = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Orphan", "slug": "orphan-sub", "parent_id": "000000000000000000000000",
        })
        assert resp.status_code == 400

    async def test_list_categories_nests_subcategories(self, client, admin):
        main_id = await self._create_main(client, admin, "Cakes D", "cakes-d")
        await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Birthday Cake D", "slug": "birthday-cake-d", "parent_id": main_id,
        })

        resp = await client.get("/admin/categories", headers=admin["headers"])
        main_row = next(c for c in resp.json()["data"] if c["id"] == main_id)
        assert any(s["slug"] == "birthday-cake-d" for s in main_row["subcategories"])

    async def test_delete_main_category_with_subcategories_blocked(self, client, admin):
        main_id = await self._create_main(client, admin, "Cakes E", "cakes-e")
        await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Birthday Cake E", "slug": "birthday-cake-e", "parent_id": main_id,
        })
        resp = await client.delete(f"/admin/categories/{main_id}", headers=admin["headers"])
        assert resp.status_code == 400


class TestPublicSubcategoryBehavior:
    async def test_main_category_products_include_subcategory_products(self, client, admin, db):
        main = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Cakes F", "slug": "cakes-f",
        })
        main_id = main.json()["data"]["id"]
        sub = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Wedding Cake F", "slug": "wedding-cake-f", "parent_id": main_id,
        })

        await client.post("/admin/products", headers=admin["headers"], json={
            "name": "Elegant Wedding Cake", "slug": "elegant-wedding-cake",
            "description": "3-tier", "category": "wedding-cake-f", "price": 3000, "stock": 5,
        })

        resp = await client.get("/categories/cakes-f")
        assert resp.status_code == 200
        product_slugs = [p["slug"] for p in resp.json()["data"]["products"]["items"]]
        assert "elegant-wedding-cake" in product_slugs

    async def test_subcategory_page_shows_only_its_own_products(self, client, admin):
        main = await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Cakes G", "slug": "cakes-g",
        })
        main_id = main.json()["data"]["id"]
        await client.post("/admin/categories", headers=admin["headers"], json={
            "name": "Birthday Cake G", "slug": "birthday-cake-g", "parent_id": main_id,
        })
        await client.post("/admin/products", headers=admin["headers"], json={
            "name": "Direct Cakes G Product", "slug": "direct-cakes-g-product",
            "description": "x", "category": "cakes-g", "price": 500, "stock": 5,
        })
        await client.post("/admin/products", headers=admin["headers"], json={
            "name": "Birthday G Product", "slug": "birthday-g-product",
            "description": "x", "category": "birthday-cake-g", "price": 500, "stock": 5,
        })

        resp = await client.get("/categories/birthday-cake-g")
        product_slugs = [p["slug"] for p in resp.json()["data"]["products"]["items"]]
        assert "birthday-g-product" in product_slugs
        assert "direct-cakes-g-product" not in product_slugs