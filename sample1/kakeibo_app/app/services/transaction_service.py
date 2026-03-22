import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories import transaction_repository
from app.schemas.transaction import (
    CategorySummary,
    MonthlySummary,
    MonthlySummaryRow,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)

logger = logging.getLogger(__name__)
GENERIC_ERROR_MESSAGE = "処理中にエラーが発生しました。時間をおいて再度お試しください。"


class ServiceError(Exception):
    def __init__(self, user_message: str = GENERIC_ERROR_MESSAGE):
        super().__init__(user_message)
        self.user_message = user_message


def list_transactions(db: Session) -> list[TransactionRead]:
    try:
        transactions = transaction_repository.list_transactions(db)
        return [TransactionRead.model_validate(item) for item in transactions]
    except SQLAlchemyError as exc:
        logger.exception("Failed to list transactions: %s", exc)
        raise ServiceError() from exc


def get_transaction(db: Session, transaction_id: int) -> TransactionRead | None:
    try:
        transaction = transaction_repository.get_transaction_by_id(db, transaction_id)
        if transaction is None:
            return None
        return TransactionRead.model_validate(transaction)
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch transaction(id=%s): %s", transaction_id, exc)
        raise ServiceError() from exc


def create_transaction(db: Session, payload: TransactionCreate) -> TransactionRead:
    try:
        transaction = transaction_repository.create_transaction(db, payload)
        db.commit()
        db.refresh(transaction)
        return TransactionRead.model_validate(transaction)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to create transaction: %s", exc)
        raise ServiceError() from exc


def update_transaction(
    db: Session,
    transaction_id: int,
    payload: TransactionUpdate,
) -> TransactionRead | None:
    try:
        transaction = transaction_repository.get_transaction_by_id(db, transaction_id)
        if transaction is None:
            return None
        updated = transaction_repository.update_transaction(db, transaction, payload)
        db.commit()
        db.refresh(updated)
        return TransactionRead.model_validate(updated)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to update transaction(id=%s): %s", transaction_id, exc)
        raise ServiceError() from exc


def delete_transaction(db: Session, transaction_id: int) -> bool:
    try:
        transaction = transaction_repository.get_transaction_by_id(db, transaction_id)
        if transaction is None:
            return False
        transaction_repository.delete_transaction(db, transaction)
        db.commit()
        return True
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to delete transaction(id=%s): %s", transaction_id, exc)
        raise ServiceError() from exc


def get_monthly_summary(db: Session, year: int, month: int) -> MonthlySummary:
    try:
        summary = transaction_repository.get_monthly_summary(db, year, month)
        return MonthlySummary(**summary)
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch monthly summary(year=%s, month=%s): %s", year, month, exc)
        raise ServiceError() from exc


def get_monthly_summary_rows(db: Session) -> list[MonthlySummaryRow]:
    try:
        rows = transaction_repository.get_monthly_summary_rows(db)
        return [MonthlySummaryRow(**row) for row in rows]
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch monthly summary rows: %s", exc)
        raise ServiceError() from exc


def get_expense_category_summary(db: Session) -> list[CategorySummary]:
    try:
        rows = transaction_repository.get_expense_category_summary(db)
        return [CategorySummary(**row) for row in rows]
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch category summary: %s", exc)
        raise ServiceError() from exc
