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
python -m app.seed.seed_database        # tài khoản + tòa nhà demo + 90 ngày dữ liệu điện theo giờ
uvicorn app.main:app --reload           # http://localhost:8000/docs
```

Tài khoản demo (lấy từ biến `SEED_*` trong `.env`):

| Username | Mật khẩu | Role |
|---|---|---|
| admin | admin123 | ADMIN |
| manager | demo123 | MANAGER |
| viewer | demo123 | VIEWER |

### Dữ liệu giả lập

- **Lần chạy đầu:** tạo 1 tòa nhà, 10 tầng, 50 phòng, 50 công tơ, 2 mức giá điện và khoảng 106.000 bản ghi theo giờ cho 90 ngày (mất khoảng 7 giây).
- **Các lần chạy sau:** chỉ bổ sung dữ liệu đến giờ hiện tại. Nên chạy lại trước mỗi buổi demo để luôn có số liệu "hôm nay".
- `--reset`: xóa dữ liệu demo rồi tạo lại; tài khoản người dùng được giữ nguyên. `--days N`: đổi số ngày lịch sử.
- **Đặc điểm dữ liệu:**
  - Có giờ cao điểm (9–11h, 14–15h), cuối tuần thấp hơn và ảnh hưởng theo mùa.
  - Khoảng 3% số ngày có bất thường.
  - Cố định cho demo: M003 hôm qua tăng gấp 2,3 lần; tầng 3 tăng khoảng 25% trong 7 ngày gần nhất; 2 công tơ INACTIVE, 2 công tơ MAINTENANCE.
- **Cảnh báo:** seed tự chạy phát hiện tiêu thụ bất thường cho toàn bộ dữ liệu. Chỉ cảnh báo của 3 ngày gần nhất còn mở; các cảnh báo cũ hơn được đánh dấu đã xử lý.
- Dữ liệu tái lập được nhờ `SEED_RANDOM_SEED`.

Dùng Swagger: gọi `POST /api/v1/auth/login`, copy `data.access_token`, bấm **Authorize** rồi dán token vào.

Kiểm tra code:

```powershell
ruff check . ; ruff format --check . ; mypy app tests ; pytest
```

`pytest` dùng database riêng `POSTGRES_TEST_DB` (mặc định `energy_management_test`). Database này bị xóa và tạo lại bảng mỗi lần chạy test; nếu chưa có, pytest sẽ tự tạo.
