from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.transaction import (
    CategorySummary,
    MonthlySummary,
    MonthlySummaryRow,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from app.services.transaction_service import ServiceError
from app.services.transaction_service import (
    create_transaction,
    delete_transaction,
    get_expense_category_summary,
    get_monthly_summary,
    get_monthly_summary_rows,
    list_transactions,
    update_transaction,
)

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/transactions", response_model=list[TransactionRead])
def list_api_transactions(db: Session = Depends(get_db)):
    try:
        return list_transactions(db)
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.user_message) from exc


@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_api_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    try:
        return create_transaction(db, payload)
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.user_message) from exc


@router.put("/transactions/{transaction_id}", response_model=TransactionRead)
def update_api_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
):
    try:
        updated = update_transaction(db, transaction_id, payload)
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="対象データが見つかりません。")
        return updated
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.user_message) from exc


@router.delete("/transactions/{transaction_id}")
def delete_api_transaction(transaction_id: int, db: Session = Depends(get_db)):
    try:
        deleted = delete_transaction(db, transaction_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="対象データが見つかりません。")
        return {"message": "削除しました。"}
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.user_message) from exc


@router.get("/summary/monthly", response_model=MonthlySummary)
def monthly_summary_api(year: int, month: int, db: Session = Depends(get_db)):
    try:
        return get_monthly_summary(db, year, month)
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.user_message) from exc


@router.get("/summary/monthly/all", response_model=list[MonthlySummaryRow])
def monthly_summary_all_api(db: Session = Depends(get_db)):
    try:
        return get_monthly_summary_rows(db)
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.user_message) from exc


@router.get("/summary/category-expense", response_model=list[CategorySummary])
def category_expense_summary_api(db: Session = Depends(get_db)):
    try:
        return get_expense_category_summary(db)
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.user_message) from exc
