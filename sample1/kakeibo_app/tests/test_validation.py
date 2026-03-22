import pytest
from pydantic import ValidationError

from app.schemas.transaction import TransactionCreate


def valid_payload() -> dict:
    return {
        "date": "2026-03-14",
        "type": "expense",
        "category": "食費",
        "amount": 1200,
        "memo": "ランチ",
    }


def test_amount_must_be_positive_integer():
    data = valid_payload()
    data["amount"] = 0
    with pytest.raises(ValidationError):
        TransactionCreate(**data)


def test_date_must_be_valid():
    data = valid_payload()
    data["date"] = "2026-02-30"
    with pytest.raises(ValidationError):
        TransactionCreate(**data)


def test_type_must_be_income_or_expense():
    data = valid_payload()
    data["type"] = "other"
    with pytest.raises(ValidationError):
        TransactionCreate(**data)


def test_required_fields_must_exist():
    data = valid_payload()
    data.pop("category")
    with pytest.raises(ValidationError):
        TransactionCreate(**data)
