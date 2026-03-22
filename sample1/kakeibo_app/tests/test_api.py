import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    db_file = tmp_path / "api_test.db"
    app = create_app(database_url=f"sqlite:///{db_file}")
    with TestClient(app) as test_client:
        yield test_client


def test_api_register_transaction(client: TestClient):
    response = client.post(
        "/api/transactions",
        json={
            "date": "2026-03-10",
            "type": "income",
            "category": "給与",
            "amount": 250000,
            "memo": "給料日",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["amount"] == 250000


def test_api_edit_transaction(client: TestClient):
    created = client.post(
        "/api/transactions",
        json={
            "date": "2026-03-10",
            "type": "expense",
            "category": "食費",
            "amount": 1500,
            "memo": "",
        },
    ).json()
    response = client.put(
        f"/api/transactions/{created['id']}",
        json={
            "date": "2026-03-10",
            "type": "expense",
            "category": "日用品",
            "amount": 3000,
            "memo": "更新",
        },
    )
    assert response.status_code == 200
    assert response.json()["category"] == "日用品"


def test_api_delete_transaction(client: TestClient):
    created = client.post(
        "/api/transactions",
        json={
            "date": "2026-03-11",
            "type": "expense",
            "category": "通信費",
            "amount": 5000,
            "memo": None,
        },
    ).json()
    response = client.delete(f"/api/transactions/{created['id']}")
    assert response.status_code == 200
    assert response.json()["message"] == "削除しました。"


def test_api_summary_result(client: TestClient):
    client.post(
        "/api/transactions",
        json={
            "date": "2026-03-01",
            "type": "income",
            "category": "給与",
            "amount": 100000,
            "memo": None,
        },
    )
    client.post(
        "/api/transactions",
        json={
            "date": "2026-03-01",
            "type": "expense",
            "category": "食費",
            "amount": 1000,
            "memo": None,
        },
    )

    monthly = client.get("/api/summary/monthly", params={"year": 2026, "month": 3})
    category = client.get("/api/summary/category-expense")
    assert monthly.status_code == 200
    assert monthly.json() == {"income": 100000, "expense": 1000, "balance": 99000}
    assert category.status_code == 200
    assert category.json()[0]["category"] == "食費"
    assert category.json()[0]["total"] == 1000
