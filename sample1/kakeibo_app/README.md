# デモ用 家計簿アプリ（FastAPI）

FastAPI + Jinja2 + SQLAlchemy + SQLite で実装した、デモ向けの簡易家計簿アプリです。  
PC / スマホのブラウザから利用できます。

## セットアップ手順

1. Python 3.11 以上を用意します。
2. 依存パッケージをインストールします。

```bash
cd sample1/kakeibo_app
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 起動方法

```bash
cd sample1/kakeibo_app
py -m uvicorn app.main:app --reload
```

起動後、以下へアクセス:
- `http://127.0.0.1:8000/` トップ画面
- `http://127.0.0.1:8000/transactions/new` 登録画面
- `http://127.0.0.1:8000/transactions` 一覧画面
- `http://127.0.0.1:8000/summary` 集計画面

## テスト実行

```bash
cd sample1/kakeibo_app
py -m pytest -q
```

## ディレクトリ構成

```text
kakeibo_app/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ database.py
│  ├─ models/
│  │  └─ transaction.py
│  ├─ schemas/
│  │  └─ transaction.py
│  ├─ routers/
│  │  ├─ pages.py
│  │  └─ api.py
│  ├─ services/
│  │  └─ transaction_service.py
│  ├─ repositories/
│  │  └─ transaction_repository.py
│  ├─ templates/
│  │  ├─ base.html
│  │  ├─ index.html
│  │  ├─ form.html
│  │  ├─ list.html
│  │  └─ summary.html
│  └─ static/
│     └─ style.css
├─ tests/
│  ├─ test_api.py
│  ├─ test_service.py
│  └─ test_validation.py
├─ data/
│  └─ kakeibo.db
├─ logs/
│  └─ app.log
├─ requirements.txt
├─ README.md
└─ .env
```

## 実装ポイント

- 画面層: `app/routers/pages.py` + Jinja2 テンプレート
- 業務処理層: `app/services/transaction_service.py`
- DBアクセス層: `app/repositories/transaction_repository.py`
- バリデーション: `app/schemas/transaction.py` (Pydantic)
- DBエラー詳細はログに記録し、画面/APIには一般的なエラーメッセージを返却
