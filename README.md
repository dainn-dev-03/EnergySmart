# EnergySmart

Website quản lý và phân tích tiêu thụ điện năng cho tòa nhà.
Thiết kế chi tiết: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

> Đang phát triển theo từng phase. README đầy đủ sẽ hoàn thiện ở phase cuối.

## Backend (FastAPI)

Yêu cầu: Python ≥ 3.12 và PostgreSQL đang chạy trên máy.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt

Copy-Item .env.example .env             # macOS/Linux: cp .env.example .env
# Sửa .env: POSTGRES_* (hoặc DATABASE_URL) và JWT_SECRET_KEY (>= 32 ký tự)

alembic upgrade head                    # tạo bảng
python -m app.seed.seed_database        # tạo tài khoản demo (chạy lại nhiều lần không bị trùng)
uvicorn app.main:app --reload           # http://localhost:8000/docs
```

Tài khoản demo (lấy từ biến `SEED_*` trong `.env`):

| Username | Mật khẩu | Role |
|---|---|---|
| admin | admin123 | ADMIN |
| manager | demo123 | MANAGER |
| viewer | demo123 | VIEWER |

Dùng Swagger: gọi `POST /api/v1/auth/login`, copy `data.access_token`, bấm **Authorize** rồi dán token vào.

Kiểm tra code:

```powershell
ruff check . ; ruff format --check . ; mypy app tests ; pytest
```

`pytest` dùng database riêng `POSTGRES_TEST_DB` (mặc định `energy_management_test`). Database này bị xóa và tạo lại bảng mỗi lần chạy test; nếu chưa có, pytest sẽ tự tạo.
