from fastapi import status

def test_read_seeded_categories(client, auth_headers):
    # Depending on startup event, seeded categories might exist
    response = client.get("/categories", headers=auth_headers)
    assert response.status_code == 200
    categories = response.json()
    # Check for some default categories like "Alimentos"
    names = [c["name"] for c in categories]
    # Note: Startup event behavior in Valid TestClient strongly depends on app lifespan handling
    # If not triggered, list might be empty. But TestClient usually runs startup.
    # However, since we drop tables after each test, startup only runs ONCE per Client instantiation?
    # Our client fixture yields a TestClient.
    # If startup logic is idempotent, it's fine.
    
    # Actually, with TestClient, startup events run on entering the context manager.
    # Our fixture: `with TestClient(app) as c: yield c`
    # So startup runs when fixture starts.
    # But `db_session` fixture creates tables FRESH for each test.
    # If `client` fixture is scope="function", it re-starts for each test, so re-seeds.
    # So "Alimentos" should be there.
    assert "Alimentos" in names

def test_create_category(client, auth_headers):
    response = client.post(
        "/categories",
        headers=auth_headers,
        json={"name": "New Category", "icon": "🆕", "color": "#000000"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Category"
    assert data["id"] is not None

def test_create_duplicate_category(client, auth_headers):
    # First create
    client.post(
        "/categories",
        headers=auth_headers,
        json={"name": "Unique Cat", "icon": "🐈", "color": "#111111"}
    )
    # Second create
    response = client.post(
        "/categories",
        headers=auth_headers,
        json={"name": "Unique Cat", "icon": "🐈", "color": "#111111"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Category already exists"
