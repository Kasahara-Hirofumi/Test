from datetime import date

import pytest

from app.database import SessionLocal, init_db, init_engine
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.transaction_service import (
    create_transaction,
    delete_transaction,
    get_expense_category_summary,
    get_monthly_summary,
    list_transactions,
    update_transaction,
)


@pytest.fixture
def db_session(tmp_path):
    db_file = tmp_path / "service_test.db"
    init_engine(f"sqlite:///{db_file}")
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_register_transaction(db_session):
    payload = TransactionCreate(
        date=date(2026, 3, 1),
        type="income",
        category="給与",
        amount=300000,
        memo="3月給与",
    )
    created = create_transaction(db_session, payload)
    assert created.id > 0
    assert created.category == "給与"
    assert created.amount == 300000


def test_edit_transaction(db_session):
    created = create_transaction(
        db_session,
        TransactionCreate(
            date=date(2026, 3, 5),
            type="expense",
            category="食費",
            amount=1200,
            memo=None,
        ),
    )
    updated = update_transaction(
        db_session,
        created.id,
        TransactionUpdate(
            date=date(2026, 3, 5),
            type="expense",
            category="日用品",
            amount=2000,
            memo="編集後",
        ),
    )
    assert updated is not None
    assert updated.category == "日用品"
    assert updated.amount == 2000


def test_delete_transaction(db_session):
    created = create_transaction(
        db_session,
        TransactionCreate(
            date=date(2026, 3, 6),
            type="expense",
            category="交通費",
            amount=800,
            memo=None,
        ),
    )
    deleted = delete_transaction(db_session, created.id)
    assert deleted is True
    assert len(list_transactions(db_session)) == 0


def test_summary_result(db_session):
    create_transaction(
        db_session,
        TransactionCreate(
            date=date(2026, 3, 1),
            type="income",
            category="給与",
            amount=100000,
            memo=None,
        ),
    )
    create_transaction(
        db_session,
        TransactionCreate(
            date=date(2026, 3, 2),
            type="expense",
            category="食費",
            amount=1200,
            memo=None,
        ),
    )
    create_transaction(
        db_session,
        TransactionCreate(
            date=date(2026, 3, 2),
            type="expense",
            category="交通費",
            amount=800,
            memo=None,
        ),
    )

    monthly = get_monthly_summary(db_session, 2026, 3)
    categories = get_expense_category_summary(db_session)

    assert monthly.income == 100000
    assert monthly.expense == 2000
    assert monthly.balance == 98000
    assert {item.category: item.total for item in categories} == {"食費": 1200, "交通費": 800}
