from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


def list_transactions(db: Session) -> list[Transaction]:
    stmt = select(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc())
    return list(db.execute(stmt).scalars().all())


def get_transaction_by_id(db: Session, transaction_id: int) -> Transaction | None:
    return db.get(Transaction, transaction_id)


def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    transaction = Transaction(**payload.model_dump())
    db.add(transaction)
    return transaction


def update_transaction(
    db: Session,
    transaction: Transaction,
    payload: TransactionUpdate,
) -> Transaction:
    for key, value in payload.model_dump().items():
        setattr(transaction, key, value)
    db.add(transaction)
    return transaction


def delete_transaction(db: Session, transaction: Transaction) -> None:
    db.delete(transaction)


def get_monthly_summary(db: Session, year: int, month: int) -> dict[str, int]:
    month_start = date(year, month, 1)
    month_end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    period_condition = (Transaction.date >= month_start) & (Transaction.date < month_end)

    income_stmt = (
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.type == "income")
        .where(period_condition)
    )
    expense_stmt = (
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.type == "expense")
        .where(period_condition)
    )
    income = int(db.scalar(income_stmt) or 0)
    expense = int(db.scalar(expense_stmt) or 0)
    return {"income": income, "expense": expense, "balance": income - expense}


def get_monthly_summary_rows(db: Session) -> list[dict[str, int | str]]:
    month_key = func.strftime("%Y-%m", Transaction.date)
    income_expr = func.sum(case((Transaction.type == "income", Transaction.amount), else_=0))
    expense_expr = func.sum(case((Transaction.type == "expense", Transaction.amount), else_=0))
    stmt = (
        select(
            month_key.label("month"),
            income_expr.label("income"),
            expense_expr.label("expense"),
        )
        .group_by(month_key)
        .order_by(month_key.desc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "month": row.month,
            "income": int(row.income or 0),
            "expense": int(row.expense or 0),
            "balance": int((row.income or 0) - (row.expense or 0)),
        }
        for row in rows
    ]


def get_expense_category_summary(db: Session) -> list[dict[str, int | str]]:
    stmt = (
        select(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .where(Transaction.type == "expense")
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc(), Transaction.category.asc())
    )
    rows = db.execute(stmt).all()
    return [{"category": row.category, "total": int(row.total or 0)} for row in rows]
