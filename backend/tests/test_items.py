from fastapi import status

def test_create_item(client, auth_headers):
    response = client.post(
        "/items",
        headers=auth_headers,
        json={
            "name": "Milk",
            "category_id": 1, # Assuming seeding worked, ID 1 exists
            "unit": "L",
            "current_quantity": 1.0,
            "minimum_quantity": 2.0,
            "acquisition_difficulty": 0,
            "usage_period": "weekly"
        }
    )
    if response.status_code != 200:
        # If category 1 doesn't exist (seeding failed?), create it first
        cat_res = client.post("/categories", headers=auth_headers, json={"name": "TestCat", "icon": "T", "color": "#000"})
        cat_id = cat_res.json()["id"]
        response = client.post(
            "/items",
            headers=auth_headers,
            json={
                "name": "Milk",
                "category_id": cat_id,
                "unit": "L",
                "current_quantity": 1.0,
                "minimum_quantity": 2.0,
                "acquisition_difficulty": 0,
                "usage_period": "weekly"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Milk"
    assert data["current_quantity"] == 1.0

def test_read_items(client, auth_headers):
    response = client.get("/items", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_item(client, auth_headers):
    # Create first
    cat_res = client.post("/categories", headers=auth_headers, json={"name": "TestCatUpdates", "icon": "T", "color": "#000"})
    cat_id = cat_res.json()["id"]
    
    create_res = client.post(
        "/items",
        headers=auth_headers,
        json={
            "name": "Bread",
            "category_id": cat_id,
            "unit": "un",
            "current_quantity": 1.0,
            "minimum_quantity": 1.0
        }
    )
    item_id = create_res.json()["id"]
    
    # Update
    response = client.put(
        f"/items/{item_id}",
        headers=auth_headers,
        json={"current_quantity": 2.0, "name": "Sourdough Bread"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_quantity"] == 2.0
    assert data["name"] == "Sourdough Bread"

def test_delete_item(client, auth_headers):
    # Create first
    cat_res = client.post("/categories", headers=auth_headers, json={"name": "TestCatDel", "icon": "T", "color": "#000"})
    cat_id = cat_res.json()["id"]
    
    create_res = client.post(
        "/items",
        headers=auth_headers,
        json={
            "name": "Water",
            "category_id": cat_id,
            "unit": "L",
            "current_quantity": 5.0,
            "minimum_quantity": 2.0
        }
    )
    item_id = create_res.json()["id"]
    
    # Delete
    del_res = client.delete(f"/items/{item_id}", headers=auth_headers)
    assert del_res.status_code == 200
    
    # Verify gone
    get_res = client.get(f"/items/{item_id}", headers=auth_headers)
    assert get_res.status_code == 404
