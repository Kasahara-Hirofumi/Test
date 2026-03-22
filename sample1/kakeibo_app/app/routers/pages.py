from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.transaction import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    TransactionCreate,
    TransactionUpdate,
)
from app.services.transaction_service import ServiceError
from app.services.transaction_service import (
    create_transaction,
    delete_transaction,
    get_expense_category_summary,
    get_monthly_summary,
    get_monthly_summary_rows,
    get_transaction,
    list_transactions,
    update_transaction,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(get_settings().template_dir))

TYPE_LABELS = {"income": "収入", "expense": "支出"}
FIELD_LABELS = {"date": "日付", "type": "区分", "category": "カテゴリ", "amount": "金額"}


def _format_validation_errors(exc: ValidationError) -> list[str]:
    messages: list[str] = []
    for error in exc.errors():
        field = error["loc"][-1]
        error_type = error["type"]
        field_label = FIELD_LABELS.get(field, "入力値")

        if field == "amount":
            messages.append("金額は正の整数で入力してください。")
            continue
        if field == "date":
            messages.append("日付を正しく入力してください。")
            continue
        if field == "type":
            messages.append("区分は収入または支出を選択してください。")
            continue
        if error_type in {"missing", "string_too_short"}:
            messages.append(f"{field_label}は必須です。")
            continue
        messages.append(str(error.get("msg", "入力内容を確認してください。")))
    return list(dict.fromkeys(messages))


def _form_context(
    request: Request,
    title: str,
    action_url: str,
    submit_label: str,
    form_data: dict,
    errors: list[str] | None = None,
    general_error: str | None = None,
) -> dict:
    return {
        "request": request,
        "title": title,
        "action_url": action_url,
        "submit_label": submit_label,
        "form_data": form_data,
        "errors": errors or [],
        "general_error": general_error,
        "income_categories": INCOME_CATEGORIES,
        "expense_categories": EXPENSE_CATEGORIES,
        "type_labels": TYPE_LABELS,
    }


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    try:
        monthly = get_monthly_summary(db, today.year, today.month)
    except ServiceError as exc:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "month_label": f"{today.year}年{today.month}月",
                "summary": {"income": 0, "expense": 0, "balance": 0},
                "general_error": exc.user_message,
            },
        )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "month_label": f"{today.year}年{today.month}月",
            "summary": monthly.model_dump(),
            "general_error": None,
        },
    )


@router.get("/transactions/new", response_class=HTMLResponse)
def new_transaction_form(request: Request):
    context = _form_context(
        request=request,
        title="収支登録",
        action_url="/transactions/new",
        submit_label="登録する",
        form_data={
            "date": date.today().isoformat(),
            "type": "expense",
            "category": EXPENSE_CATEGORIES[0],
            "amount": "",
            "memo": "",
        },
    )
    return templates.TemplateResponse("form.html", context)


@router.post("/transactions/new", response_class=HTMLResponse)
def create_transaction_page(
    request: Request,
    date_value: str = Form(..., alias="date"),
    type_value: str = Form(..., alias="type"),
    category: str = Form(...),
    amount: str = Form(...),
    memo: str = Form(""),
    db: Session = Depends(get_db),
):
    raw_data = {
        "date": date_value,
        "type": type_value,
        "category": category,
        "amount": amount,
        "memo": memo,
    }
    try:
        payload = TransactionCreate(**raw_data)
        create_transaction(db, payload)
        return RedirectResponse(url="/transactions", status_code=status.HTTP_303_SEE_OTHER)
    except ValidationError as exc:
        context = _form_context(
            request=request,
            title="収支登録",
            action_url="/transactions/new",
            submit_label="登録する",
            form_data=raw_data,
            errors=_format_validation_errors(exc),
        )
        return templates.TemplateResponse("form.html", context, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except ServiceError as exc:
        context = _form_context(
            request=request,
            title="収支登録",
            action_url="/transactions/new",
            submit_label="登録する",
            form_data=raw_data,
            general_error=exc.user_message,
        )
        return templates.TemplateResponse("form.html", context, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/transactions", response_class=HTMLResponse)
def transaction_list_page(request: Request, db: Session = Depends(get_db)):
    try:
        transactions = [item.model_dump() for item in list_transactions(db)]
        return templates.TemplateResponse(
            "list.html",
            {
                "request": request,
                "transactions": transactions,
                "type_labels": TYPE_LABELS,
                "general_error": None,
            },
        )
    except ServiceError as exc:
        return templates.TemplateResponse(
            "list.html",
            {
                "request": request,
                "transactions": [],
                "type_labels": TYPE_LABELS,
                "general_error": exc.user_message,
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/transactions/{transaction_id}/edit", response_class=HTMLResponse)
def edit_transaction_form(transaction_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        transaction = get_transaction(db, transaction_id)
        if transaction is None:
            raise HTTPException(status_code=404, detail="対象データが見つかりません。")
        context = _form_context(
            request=request,
            title="収支編集",
            action_url=f"/transactions/{transaction_id}/edit",
            submit_label="更新する",
            form_data={
                "date": transaction.date.isoformat(),
                "type": transaction.type,
                "category": transaction.category,
                "amount": str(transaction.amount),
                "memo": transaction.memo or "",
            },
        )
        return templates.TemplateResponse("form.html", context)
    except ServiceError as exc:
        raise HTTPException(status_code=500, detail=exc.user_message) from exc


@router.post("/transactions/{transaction_id}/edit", response_class=HTMLResponse)
def update_transaction_page(
    transaction_id: int,
    request: Request,
    date_value: str = Form(..., alias="date"),
    type_value: str = Form(..., alias="type"),
    category: str = Form(...),
    amount: str = Form(...),
    memo: str = Form(""),
    db: Session = Depends(get_db),
):
    raw_data = {
        "date": date_value,
        "type": type_value,
        "category": category,
        "amount": amount,
        "memo": memo,
    }
    try:
        payload = TransactionUpdate(**raw_data)
        updated = update_transaction(db, transaction_id, payload)
        if updated is None:
            raise HTTPException(status_code=404, detail="対象データが見つかりません。")
        return RedirectResponse(url="/transactions", status_code=status.HTTP_303_SEE_OTHER)
    except ValidationError as exc:
        context = _form_context(
            request=request,
            title="収支編集",
            action_url=f"/transactions/{transaction_id}/edit",
            submit_label="更新する",
            form_data=raw_data,
            errors=_format_validation_errors(exc),
        )
        return templates.TemplateResponse("form.html", context, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except ServiceError as exc:
        context = _form_context(
            request=request,
            title="収支編集",
            action_url=f"/transactions/{transaction_id}/edit",
            submit_label="更新する",
            form_data=raw_data,
            general_error=exc.user_message,
        )
        return templates.TemplateResponse("form.html", context, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/transactions/{transaction_id}/delete")
def delete_transaction_page(transaction_id: int, db: Session = Depends(get_db)):
    try:
        delete_transaction(db, transaction_id)
        return RedirectResponse(url="/transactions", status_code=status.HTTP_303_SEE_OTHER)
    except ServiceError:
        return RedirectResponse(url="/transactions", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/summary", response_class=HTMLResponse)
def summary_page(request: Request, db: Session = Depends(get_db)):
    try:
        monthly_rows = [row.model_dump() for row in get_monthly_summary_rows(db)]
        category_rows = [row.model_dump() for row in get_expense_category_summary(db)]
        return templates.TemplateResponse(
            "summary.html",
            {
                "request": request,
                "monthly_rows": monthly_rows,
                "category_rows": category_rows,
                "general_error": None,
            },
        )
    except ServiceError as exc:
        return templates.TemplateResponse(
            "summary.html",
            {
                "request": request,
                "monthly_rows": [],
                "category_rows": [],
                "general_error": exc.user_message,
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
