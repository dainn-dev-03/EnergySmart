# EnergySmart

Website quản lý và phân tích tiêu thụ điện năng cho tòa nhà: quản lý tòa nhà, tầng, phòng và công tơ; dữ liệu điện theo giờ; dashboard; phân tích; cảnh báo tiêu thụ bất thường; báo cáo xuất CSV.

> Phiên bản BASE (đồ án). Chưa có Machine Learning/AI, chưa kết nối công tơ thật hay IoT/MQTT. Dữ liệu điện được **giả lập** bằng lệnh seed.

Mục lục:
1. [Giới thiệu](#1-giới-thiệu)
2. [Kiến trúc](#2-kiến-trúc)
3. [Công nghệ](#3-công-nghệ)
4. [Cấu trúc thư mục](#4-cấu-trúc-thư-mục)
5. [Biến môi trường](#5-biến-môi-trường)
6. [Cài đặt](#6-cài-đặt)
7. [Docker](#7-docker)
8. [Migration cơ sở dữ liệu](#8-migration-cơ-sở-dữ-liệu)
9. [Dữ liệu giả lập (seed)](#9-dữ-liệu-giả-lập-seed)
10. [Chạy backend](#10-chạy-backend)
11. [Chạy frontend](#11-chạy-frontend)
12. [Tài liệu API](#12-tài-liệu-api)
13. [Tài khoản mặc định](#13-tài-khoản-mặc-định)

Phụ lục: [Kiểm thử](#kiểm-thử) · [Kịch bản demo](#kịch-bản-demo) · [Xử lý sự cố](#xử-lý-sự-cố) · [Hướng phát triển](#hướng-phát-triển)

---

## 1. Giới thiệu

Mô hình dữ liệu: **Tòa nhà → Tầng → Phòng → Công tơ → Dữ liệu điện năng** (theo giờ). Ngoài ra có **Bảng giá điện** để tính chi phí và **Cảnh báo** cho các ngày tiêu thụ bất thường.

| Chức năng | Mô tả |
|---|---|
| Đăng nhập, phân quyền | JWT. Role ADMIN, MANAGER, VIEWER: mọi role đều xem được; ADMIN/MANAGER được thêm/sửa/xóa; chỉ ADMIN được sửa bảng giá |
| Quản lý danh mục | Tòa nhà, tầng, phòng, công tơ: thêm/sửa/xóa, tìm kiếm, lọc, sắp xếp, phân trang. Không xóa được cấp cha khi còn cấp con |
| Dữ liệu điện | Điện năng tiêu thụ **trong từng giờ** của mỗi công tơ. Chi phí tự tính = kWh × đơn giá có hiệu lực vào ngày ghi |
| Dashboard | Tiêu thụ hôm nay, tháng này, chi phí, công tơ hoạt động, số cảnh báo; biểu đồ theo ngày, tháng, tầng và chi phí; tình trạng từng tầng |
| Phân tích | So sánh ngày/tuần/tháng với kỳ trước (cùng khoảng thời gian đã trôi qua), biểu đồ tải theo giờ (giờ cao điểm), tiêu thụ theo tầng/phòng |
| Cảnh báo | Ngày tiêu thụ ≥ 1,2 / 1,5 / 2 lần mức trung bình 14 ngày cùng loại → INFO / WARNING / CRITICAL; đánh dấu đã xử lý |
| Báo cáo | Gom theo tầng, phòng hoặc công tơ trong một khoảng ngày; xuất CSV mở được bằng Excel |

Toàn bộ giao diện bằng tiếng Việt; số, tiền và ngày định dạng theo vi-VN; thời gian tính theo giờ Việt Nam.

## 2. Kiến trúc

```text
Trình duyệt ──► Frontend: Next.js (:3000)
                  │  REST/JSON  /api/v1/*   Authorization: Bearer <JWT>
                  ▼
                Backend: FastAPI (:8000)
                  Router → Schema (Pydantic) → Service → Repository → SQLAlchemy
                  ▼
                PostgreSQL (:5432)
```

- **Backend chia lớp rõ ràng.** Router chỉ nhận request và trả response. Business logic (tính chi phí, phát hiện bất thường, phân tích) nằm ở service; mọi câu SQL nằm ở repository.
- **Frontend gọi API từ trình duyệt** bằng axios + TanStack Query. Khu vực cần đăng nhập được bảo vệ ở hai lớp: `proxy.ts` (kiểm tra cookie) và `AuthGate` (gọi `/auth/me`). Backend kiểm tra JWT trên mọi request.
- **Thời gian lưu dạng UTC.** Mọi kết nối DB chạy ở UTC; việc gom theo ngày/tháng và lọc ngày dùng giờ Việt Nam (`APP_TIMEZONE`).

Thiết kế chi tiết (ERD, quy ước API, thuật toán cảnh báo, dữ liệu giả lập): [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 3. Công nghệ

| Phần | Công nghệ |
|---|---|
| Backend | Python ≥ 3.12, FastAPI, SQLAlchemy 2.1, Alembic, Pydantic v2, PyJWT, pwdlib (Argon2), psycopg 3 |
| Cơ sở dữ liệu | PostgreSQL (đã kiểm tra với PostgreSQL 18) |
| Frontend | Next.js 16 (App Router, TypeScript strict), Tailwind CSS v4, shadcn/ui (Radix), TanStack Query, axios, React Hook Form, Zod, Recharts |
| Chất lượng code | pytest, ruff, mypy (strict), ESLint, `tsc --noEmit` |

## 4. Cấu trúc thư mục

```text
EnergySmart/
├── backend/
│   ├── app/
│   │   ├── main.py              # tạo FastAPI app: CORS, exception handlers, router
│   │   ├── core/                # config, database, security (JWT, hash), dependencies, exceptions, timezone
│   │   ├── models/              # SQLAlchemy: user, building, floor, room, meter, electricity_usage, electricity_price, alert
│   │   ├── schemas/             # Pydantic: input/output và envelope phản hồi
│   │   ├── repositories/        # truy vấn SQL (CRUD + aggregate cho analytics)
│   │   ├── services/            # business logic (CRUD, auth, analytics, dashboard, alert, report)
│   │   ├── api/routes/          # REST endpoints /api/v1/*
│   │   └── seed/                # dữ liệu giả lập: master data, usage_simulator, seed_database (CLI)
│   ├── alembic/                 # migration (versions/20261007_0001_initial_schema.py)
│   ├── tests/                   # pytest (106 test)
│   ├── requirements.txt         # thư viện runtime
│   ├── requirements-dev.txt     # + pytest, ruff, mypy
│   ├── pyproject.toml           # cấu hình ruff / mypy / pytest
│   └── .env.example
├── frontend/
│   ├── app/                     # Next.js App Router: /login và nhóm (main) với các trang
│   ├── components/
│   │   ├── auth/                # AuthGate
│   │   ├── layout/              # sidebar, header, menu người dùng
│   │   ├── views/               # màn hình của từng trang
│   │   ├── forms/               # form + field dùng chung, date picker
│   │   ├── data-table/          # bảng, phân trang, tìm kiếm, bộ lọc
│   │   ├── charts/              # biểu đồ + chế độ xem dạng bảng
│   │   ├── dashboard/           # thẻ số liệu, nhãn mức độ cảnh báo
│   │   └── ui/                  # shadcn/ui
│   ├── hooks/                   # use-resource, use-entity-form, use-list-state, ...
│   ├── lib/                     # api (axios), auth, format (vi-VN), resources, labels
│   ├── types/                   # kiểu dữ liệu khớp với API
│   ├── proxy.ts                 # chặn route khi chưa đăng nhập (middleware của Next.js 16)
│   └── .env.example
└── docs/ARCHITECTURE.md
```

## 5. Biến môi trường

Không commit file `.env` hay `.env.local`. Hãy sao chép từ file `.env.example` tương ứng.

**Backend** (`backend/.env`):

| Biến | Bắt buộc | Mặc định | Ý nghĩa |
|---|:-:|---|---|
| `POSTGRES_HOST`, `POSTGRES_PORT` | | `localhost`, `5432` | Máy chủ PostgreSQL |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | ✓* | | Database và tài khoản |
| `DATABASE_URL` | ✓* | | Dùng thay cho bộ `POSTGRES_*`, ví dụ `postgresql+psycopg://user:pass@localhost:5432/energy_management` |
| `POSTGRES_TEST_DB` | | `energy_management_test` | Database riêng cho pytest. Các bảng của DB này bị xóa và tạo lại mỗi lần test |
| `DATABASE_CONNECT_TIMEOUT_SECONDS` | | `5` | Thời gian chờ kết nối DB |
| `JWT_SECRET_KEY` | ✓ | | **Tối thiểu 32 ký tự**; ngắn hơn thì app không khởi động |
| `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | | `HS256`, `480` | Thuật toán và thời hạn token (phút) |
| `CORS_ORIGINS` | | `http://localhost:3000` | Các origin frontend được phép, ngăn cách bằng dấu phẩy |
| `APP_TIMEZONE` | | `Asia/Ho_Chi_Minh` | Múi giờ dùng để tính "ngày" và "tháng" |
| `DEBUG` | | `false` | Log chi tiết |
| `ALERT_RATIO_INFO`, `ALERT_RATIO_WARNING`, `ALERT_RATIO_CRITICAL` | | `1.2`, `1.5`, `2.0` | Ngưỡng cảnh báo |
| `ALERT_BASELINE_DAYS`, `ALERT_MIN_REFERENCE_DAYS` | | `14`, `3` | Số ngày tham chiếu khi tính mức trung bình |
| `SEED_ADMIN_USERNAME`, `SEED_ADMIN_PASSWORD`, `SEED_ADMIN_EMAIL` | ✓ (khi seed) | | Tài khoản admin do lệnh seed tạo |
| `SEED_DEMO_PASSWORD` | | | Mật khẩu của 2 tài khoản `manager` và `viewer`; bỏ trống thì không tạo |
| `SEED_DAYS`, `SEED_RANDOM_SEED` | | `90`, `42` | Số ngày dữ liệu giả lập và random seed |

\* Cần **hoặc** `DATABASE_URL` **hoặc** `POSTGRES_DB` + `POSTGRES_USER` (+ `POSTGRES_PASSWORD`).

Tạo `JWT_SECRET_KEY`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**Frontend** (`frontend/.env.local`):

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | URL của API. Giá trị được **nhúng vào bundle lúc build**: đổi giá trị thì phải build lại |

## 6. Cài đặt

Yêu cầu: **Python ≥ 3.12**, **Node.js ≥ 20**, **PostgreSQL** đang chạy trên máy, và khoảng 1 GB ổ đĩa cho thư viện.

**Bước 1: tạo database** (dùng psql hoặc pgAdmin, với user có quyền tạo DB):

```sql
CREATE DATABASE energy_management;
-- Không bắt buộc: pytest tự tạo DB test nếu user có quyền CREATEDB
CREATE DATABASE energy_management_test;
```

**Bước 2: cài backend.** Các lệnh dưới đây dùng PowerShell trên Windows; trên macOS/Linux dùng các lệnh trong phần chú thích.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt     # chỉ để chạy app thì dùng requirements.txt

Copy-Item .env.example .env             # macOS/Linux: cp .env.example .env
# Mở .env: điền POSTGRES_PASSWORD (và các POSTGRES_* khác nếu cần), đặt JWT_SECRET_KEY >= 32 ký tự
```

**Bước 3: cài frontend.**

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local       # macOS/Linux: cp .env.example .env.local
```

## 7. Docker

Dự án **chạy trực tiếp trên máy, không dùng Docker**; đây là quyết định của nhóm phát triển. Toàn bộ cấu hình kết nối nằm trong `backend/.env`, nên muốn đóng gói bằng Docker sau này chỉ cần thêm Dockerfile, không phải sửa code.

## 8. Migration cơ sở dữ liệu

Chạy trong thư mục `backend` (venv đã kích hoạt):

```powershell
alembic upgrade head        # tạo/cập nhật toàn bộ bảng
alembic current             # xem phiên bản hiện tại (0001)
alembic check               # kiểm tra models và migration có khớp nhau không
alembic downgrade base      # xóa toàn bộ bảng (cẩn thận)
```

Khi thay đổi model, tạo migration mới bằng `alembic revision --autogenerate -m "mo ta thay doi"`, đọc lại file sinh ra trong `alembic/versions/`, rồi chạy `alembic upgrade head`.

> `alembic/env.py` có hook `render_item` để khắc phục một chỗ chưa tương thích giữa Alembic 1.20 và SQLAlchemy 2.1. Nếu thiếu hook này, cột enum sẽ bị sinh trùng CHECK constraint.

## 9. Dữ liệu giả lập (seed)

```powershell
python -m app.seed.seed_database            # lần đầu: tạo đầy đủ; các lần sau: bổ sung dữ liệu đến giờ hiện tại
python -m app.seed.seed_database --reset    # xóa dữ liệu demo rồi tạo lại (giữ tài khoản người dùng)
python -m app.seed.seed_database --days 30  # số ngày lịch sử khi tạo mới
```

Lần đầu, lệnh tạo các dữ liệu sau (mất khoảng 7 giây):

- **Tài khoản:** `admin`, `manager`, `viewer` (xem [mục 13](#13-tài-khoản-mặc-định)).
- **Tòa nhà:** EnergySmart Tower (`ES-01`) gồm 10 tầng và 50 phòng: tầng 1 là sảnh và dịch vụ, tầng 2–9 là văn phòng, tầng 10 là kỹ thuật.
- **Công tơ:** 50 công tơ `M001`–`M050`, gồm 46 ACTIVE, 2 MAINTENANCE và 2 INACTIVE.
- **Bảng giá:** 2 mức (2.500 và 2.650 VND/kWh); mức mới áp dụng từ ngày 1 của tháng trước.
- **Dữ liệu điện:** khoảng **106.000 bản ghi theo giờ** trong 90 ngày, với các đặc điểm:
  - giờ cao điểm 9–11h và 14–15h, nghỉ trưa giảm, ban đêm thấp;
  - cuối tuần thấp hơn ngày thường (trừ phòng máy chủ);
  - tiêu thụ thay đổi theo mùa (điều hòa chạy nhiều nhất vào giữa tháng 7);
  - khoảng 3% số ngày có bất thường.
- **Sự kiện cố định để demo:**
  - công tơ **M003 hôm qua tăng khoảng 2,3 lần** (cảnh báo CRITICAL);
  - **M017 tăng khoảng 1,6 lần** cách đây 2 ngày (WARNING);
  - **tầng 3 tăng khoảng 25%** trong 7 ngày gần nhất.
- **Cảnh báo:** khoảng 300 cảnh báo lịch sử. Chỉ các cảnh báo của 3 ngày gần nhất còn **chưa xử lý**.

Dữ liệu tái lập được: cùng `SEED_RANDOM_SEED` thì cho cùng số liệu. **Trước mỗi buổi demo, chạy lại lệnh seed** để bổ sung dữ liệu tới giờ hiện tại, như vậy dashboard luôn có số liệu "hôm nay".

## 10. Chạy backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000/api/v1
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Kiểm tra trạng thái: http://localhost:8000/health

## 11. Chạy frontend

Backend phải đang chạy.

```powershell
cd frontend
npm run dev                  # chế độ phát triển: http://localhost:3000
# hoặc bản production:
npm run build
npm run start                # http://localhost:3000
```

## 12. Tài liệu API

Tài liệu tương tác đầy đủ có tại **Swagger** (http://localhost:8000/docs). Cách thử API trên Swagger: gọi `POST /api/v1/auth/login`, copy `data.access_token`, bấm **Authorize** và dán token vào.

**Định dạng phản hồi:**

```json
{ "success": true,  "message": "Thành công", "data": { } }
{ "success": true,  "message": "Thành công", "data": [ ], "pagination": { "page": 1, "page_size": 20, "total": 100, "total_pages": 5 } }
{ "success": false, "message": "Dữ liệu không hợp lệ", "error": { "code": "VALIDATION_ERROR", "details": [ { "field": "code", "message": "Trường này là bắt buộc" } ] } }
```

| HTTP | `error.code` |
|---|---|
| 401 | `UNAUTHORIZED`, `INVALID_CREDENTIALS`, `INVALID_TOKEN`, `TOKEN_EXPIRED` |
| 403 | `FORBIDDEN`, `ACCOUNT_DISABLED` |
| 404 | `NOT_FOUND` |
| 409 | `CONFLICT` (trùng mã, còn bản ghi con, khoảng giá chồng nhau, …) |
| 422 | `VALIDATION_ERROR`, `PRICE_NOT_FOUND` |
| 503 | `DATABASE_UNAVAILABLE` |

**Các endpoint** (52 endpoint, tiền tố `/api/v1`):

| Nhóm | Endpoint |
|---|---|
| Hệ thống | `GET /health` (không có tiền tố) |
| Auth | `POST /auth/login` · `GET /auth/me` |
| Tòa nhà | `GET/POST /buildings` · `GET/PUT/DELETE /buildings/{id}` |
| Tầng | `GET/POST /floors` · `GET/PUT/DELETE /floors/{id}` |
| Phòng | `GET/POST /rooms` · `GET/PUT/DELETE /rooms/{id}` |
| Công tơ | `GET/POST /meters` · `GET/PUT/DELETE /meters/{id}` |
| Dữ liệu điện | `GET/POST /electricity-usages` · `GET/PUT/DELETE /electricity-usages/{id}` |
| Bảng giá | `GET/POST /electricity-prices` · `GET/PUT/DELETE /electricity-prices/{id}` (ghi: chỉ ADMIN) |
| Dashboard | `GET /dashboard/summary`, `/daily`, `/monthly`, `/by-floor`, `/by-room`, `/cost` |
| Phân tích | `GET /analytics/daily`, `/monthly`, `/hourly`, `/by-floor`, `/by-room`, `/comparison` |
| Cảnh báo | `GET /alerts` · `GET /alerts/{id}` · `POST /alerts/{id}/resolve` · `POST /alerts/detect?date=` |
| Báo cáo | `GET /reports/consumption?group_by=floor\|room\|meter` · `GET /reports/consumption/export` (CSV) |

**Tham số danh sách:**
- Chung cho mọi danh sách: `page`, `page_size` (≤ 100), `search`, `sort_by`, `sort_order` (`asc`/`desc`).
- Lọc theo cây phân cấp: `building_id`, `floor_id`, `room_id`, `meter_id`.
- Lọc theo ngày (ngày theo giờ Việt Nam, bao gồm cả hai đầu): `from_date`, `to_date`.

Ví dụ dùng curl:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['data']['access_token'])")
curl -s http://localhost:8000/api/v1/dashboard/summary -H "Authorization: Bearer $TOKEN"
```

## 13. Tài khoản mặc định

Tài khoản được tạo bởi lệnh seed, lấy từ các biến `SEED_*` trong `backend/.env`:

| Username | Mật khẩu | Role | Quyền |
|---|---|---|---|
| `admin` | `admin123` | ADMIN | Toàn quyền, kể cả bảng giá điện |
| `manager` | `demo123` | MANAGER | Thêm/sửa/xóa dữ liệu, xử lý cảnh báo |
| `viewer` | `demo123` | VIEWER | Chỉ xem |

> Đây là tài khoản demo. Hãy đổi các giá trị `SEED_*` và `JWT_SECRET_KEY` trước khi dùng ở môi trường thật.

---

## Kiểm thử

```powershell
# Backend (trong thư mục backend, venv đã kích hoạt)
ruff check . ; ruff format --check . ; mypy app tests ; pytest

# Frontend (trong thư mục frontend)
npm run lint ; npm run typecheck ; npm run build
```

- **Backend có 106 test**, chạy trên DB `POSTGRES_TEST_DB` (khác DB chính), mỗi test được rollback. Các test bao phủ: auth, CRUD của 6 resource, quy tắc xóa và constraint, dashboard, analytics, cảnh báo, báo cáo/CSV, bộ mô phỏng và lệnh seed.
- Pytest **từ chối chạy** nếu `POSTGRES_TEST_DB` trùng với DB chính, để không xóa nhầm dữ liệu.

## Kịch bản demo

1. Chạy `python -m app.seed.seed_database` để dữ liệu được cập nhật tới giờ hiện tại, sau đó bật backend và frontend.
2. Mở http://localhost:3000. Trang tự chuyển tới **Đăng nhập**; đăng nhập bằng `admin` / `admin123`.
3. **Dashboard:**
   - thẻ tiêu thụ hôm nay và tháng này, kèm % so với cùng giờ kỳ trước;
   - biểu đồ 30 ngày (thấy rõ cuối tuần thấp hơn);
   - biểu đồ theo tầng (tầng 3 cao bất thường);
   - phần cảnh báo: ⚠ "Tầng 3 tăng …%" và cảnh báo **Nghiêm trọng** của M003.
4. **Tầng → Phòng → Công tơ:** lọc công tơ theo trạng thái *Bảo trì*; thử xóa một tầng còn phòng (hệ thống chặn kèm lý do).
5. **Dữ liệu điện:** lọc theo công tơ M003 và hôm qua để thấy các giờ tăng vọt; mở tab **Bảng giá điện**.
6. **Phân tích:** biểu đồ tải theo giờ (2 đỉnh 9–11h và 14–15h; cuối tuần thấp); so sánh ngày, tuần, tháng.
7. **Cảnh báo:** đánh dấu một cảnh báo là *Đã xử lý*, rồi quay lại Dashboard để thấy số cảnh báo giảm.
8. **Báo cáo:** chuyển *Theo phòng* rồi bấm **Xuất CSV**.
9. Đăng xuất, đăng nhập bằng `viewer` / `demo123`: các nút thêm, sửa, xóa đều bị ẩn.

## Xử lý sự cố

| Triệu chứng | Nguyên nhân / cách xử lý |
|---|---|
| `JWT_SECRET_KEY must be at least 32 characters` | Đặt `JWT_SECRET_KEY` dài ít nhất 32 ký tự trong `backend/.env` |
| `Database is not configured` | Thiếu `DATABASE_URL` hoặc `POSTGRES_DB` + `POSTGRES_USER` trong `backend/.env` |
| `database "energy_management" does not exist` | Chưa tạo DB: xem [mục 6, bước 1](#6-cài-đặt) |
| `/health` trả 503 `DATABASE_UNAVAILABLE` | PostgreSQL chưa chạy hoặc sai host/port/mật khẩu |
| Frontend báo "Không kết nối được máy chủ" | Backend chưa chạy ở cổng 8000, hoặc `NEXT_PUBLIC_API_URL` sai. Nhớ build lại frontend sau khi đổi biến này |
| Lỗi CORS trong console trình duyệt | Thêm origin của frontend vào `CORS_ORIGINS` rồi khởi động lại backend |
| Dashboard "hôm nay" bằng 0 | Dữ liệu seed đã cũ: chạy lại `python -m app.seed.seed_database` |
| `Chưa có bảng giá điện áp dụng cho ngày …` | Ngày ghi dữ liệu nằm ngoài mọi khoảng hiệu lực: thêm bảng giá ở tab *Bảng giá điện* (ADMIN) |
| Cổng 5432/3000/8000 đã bị chiếm | Đổi `POSTGRES_PORT`; với các cổng khác dùng `uvicorn ... --port` hoặc `npm run dev -- -p` (nhớ cập nhật `CORS_ORIGINS` và `NEXT_PUBLIC_API_URL`) |

## Hướng phát triển

- **Dự báo tiêu thụ và phát hiện bất thường bằng Machine Learning**, thay cho ngưỡng cố định.
- **Thu thập dữ liệu thật** từ công tơ thông minh qua MQTT/IoT, thay cho dữ liệu giả lập.
- **Giá điện bậc thang hoặc theo khung giờ** (cao điểm, bình thường, thấp điểm) theo biểu giá EVN.
- **Quản lý người dùng trên giao diện**, refresh token, cookie httpOnly.
- **Thông báo cảnh báo** qua email hoặc chat; job tự động chạy phát hiện cảnh báo mỗi ngày.
