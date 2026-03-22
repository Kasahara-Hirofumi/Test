from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

INCOME_CATEGORIES = ["給与", "賞与", "臨時収入"]
EXPENSE_CATEGORIES = ["食費", "日用品", "交通費", "娯楽", "通信費", "その他"]
CATEGORY_MAP = {
    "income": INCOME_CATEGORIES,
    "expense": EXPENSE_CATEGORIES,
}


class TransactionBase(BaseModel):
    date: date
    type: Literal["income", "expense"]
    category: str = Field(min_length=1, max_length=50)
    amount: int = Field(gt=0)
    memo: str | None = Field(default=None, max_length=255)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str, info: ValidationInfo) -> str:
        tx_type = info.data.get("type")
        if tx_type and value not in CATEGORY_MAP[tx_type]:
            raise ValueError("カテゴリが区分に一致していません。")
        return value

    @field_validator("memo")
    @classmethod
    def normalize_memo(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonthlySummary(BaseModel):
    income: int
    expense: int
    balance: int


class MonthlySummaryRow(MonthlySummary):
    month: str


class CategorySummary(BaseModel):
    category: str
    total: int
