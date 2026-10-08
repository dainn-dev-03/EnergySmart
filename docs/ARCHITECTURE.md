# EnergySmart — Kiến trúc hệ thống

Website quản lý và phân tích tiêu thụ điện năng cho tòa nhà (dữ liệu điện được giả lập; trợ lý hỏi đáp dùng Gemini, chưa có ML/dự báo hoặc IoT).

## 1. Tổng quan

```text
Browser (http://localhost:3000)
   │
   ▼
frontend · Next.js App Router · TypeScript strict · giao diện tiếng Việt      :3000
   │  middleware.ts   chặn route khi chưa có token → /login
   │  app/(main)/*    dashboard, CRUD, analytics, alerts, reports, chat
   │  components/     layout · charts (Recharts) · forms (React Hook Form + Zod)
   │  hooks/          TanStack Query: cache, loading, refetch
   │  lib/api.ts      axios: gắn Bearer JWT, bóc envelope, xử lý 401
   │
   │  REST/JSON  /api/v1/*   Authorization: Bearer <JWT>
   ▼
backend · FastAPI · Python ≥ 3.12                                              :8000
   │  api/routes      HTTP + phân quyền (Depends)
   │  schemas         Pydantic: validate input, định dạng output
   │  services        business logic: cost, analytics, alert, report, Gemini chat tools
   │  repositories    truy vấn SQLAlchemy: CRUD + aggregate
   │  core            config · DB session · JWT · exception handlers
   │  seed/ alembic/  dữ liệu giả lập · migration
   │
   │  SQLAlchemy 2.1 + psycopg 3
   ▼
PostgreSQL (dữ liệu điện, users)                                               :5432
MongoDB (metadata hội thoại, các lượt chat)                                    :27017
```

Chatbot là trợ lý Gemini hỗ trợ kiến thức phổ thông và dữ liệu năng lượng EnergySmart. Với kiến thức phổ thông, trả lời dựa trên kiến thức sẵn có của mô hình và nêu rõ không có tra cứu Internet/thông tin thời gian thực; với dữ liệu vận hành, agent dùng các công cụ analytics trong allowlist, hỏi lại khi thiếu thông tin và không bịa số liệu. Agent điều phối theo vòng bounded plan → act → observe → re-plan (tối đa 4 vòng gọi tool). `ChatService` xác thực tham số và gọi `AnalyticsService`, không cho phép model tạo SQL hoặc truy cập database trực tiếp. Phản hồi cuối được gửi cho giao diện theo Server-Sent Events (SSE): token văn bản và payload trực quan hóa được phát riêng. KPI, bảng và các hiển thị phân tích được dựng từ kết quả công cụ analytics thực tế, không trích số từ Markdown; payload trực quan hóa lưu cùng message trợ lý trong MongoDB để còn hiển thị ở lịch sử chat. Lượt chat chỉ được ghi sau khi sinh hoàn tất. API key chỉ nằm trong `backend/.env`. Conversation metadata được lưu trong MongoDB `chat_conversations`; mỗi cặp user/model được lưu thành một turn document trong `chat_turns`, với hai message con chứa role/content và payload trực quan hóa tùy chọn ở message trợ lý. Cả hai collection có `user_id` lấy từ JWT đã xác thực; mỗi truy vấn và thao tác đều lọc theo owner. PostgreSQL vẫn là nguồn xác thực user và dữ liệu điện. Cần chạy MongoDB để sử dụng chat; cấu hình `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_TIMEOUT_MS`, `MONGODB_URI`, `MONGODB_DATABASE` và `MONGODB_TIMEOUT_MS`.

Project chạy hoàn toàn local, không dùng Docker. PostgreSQL do người dùng tự cài và tự tạo database; backend đọc thông tin kết nối từ `backend/.env`.

### Luồng xử lý request

```text
Router (api/routes)  →  Schema (Pydantic)  →  Service  →  Repository  →  SQLAlchemy  →  PostgreSQL
```

Router không chứa business logic. Service ném `AppError` (`NotFoundError`, `ConflictError`, …); exception handler chuyển chúng thành error envelope.

### Quyết định kỹ thuật

| Hạng mục | Lựa chọn | Lý do |
|---|---|---|
| ORM | SQLAlchemy 2.1 **sync**, typed `Mapped[]` | Đơn giản và ít lỗi hơn async; FastAPI tự chạy endpoint sync trong threadpool |
| Driver | psycopg 3 (`postgresql+psycopg://`) | |
| JWT / hash | PyJWT (HS256) + `pwdlib[argon2]` | passlib không còn được bảo trì |
| Enum | `VARCHAR` + `CHECK` (không dùng native PG enum) | Thêm giá trị không cần `ALTER TYPE` |
| Thời gian | `TIMESTAMPTZ`; mọi kết nối DB chạy ở UTC (`-c timezone=UTC`) nên API luôn trả thời gian UTC (`...Z`); gom nhóm và lọc ngày theo `APP_TIMEZONE=Asia/Ho_Chi_Minh` | Kết quả không phụ thuộc cấu hình TimeZone của PostgreSQL server; "hôm nay", "tháng này" tính theo giờ Việt Nam |
| Test | pytest + TestClient trên DB PostgreSQL riêng (`POSTGRES_TEST_DB`) | Query dùng hàm thời gian đặc thù của PostgreSQL |
| Swagger auth | `HTTPBearer` | Login → copy token → Authorize |
| FE auth | JWT trong cookie `es_token` (SameSite=Lax, 8h) + header Bearer | Middleware đọc cookie để chặn route; 401 → về `/login` |
| Ngôn ngữ | Giao diện và `message` của API bằng tiếng Việt; code bằng tiếng Anh | Số và tiền định dạng `vi-VN` |

## 2. Database

```text
buildings
  └─1:N─ floors            UQ (building_id, floor_number)
           └─1:N─ rooms
                    └─1:N─ meters
                             ├─1:N─ electricity_usages   UQ (meter_id, recorded_at)
                             └─1:N─ alerts               UQ (meter_id, alert_type, usage_date)

users                (độc lập: xác thực / phân quyền ADMIN | MANAGER | VIEWER)
electricity_prices   (độc lập: usage.cost = kwh × đơn giá hiệu lực tại recorded_at)
```

- `electricity_usages`: mỗi dòng là điện năng tiêu thụ **trong 1 giờ** bắt đầu từ `recorded_at`, không phải chỉ số cộng dồn của công tơ. `cost` được tính khi ghi và không tính lại khi đổi giá.
- `alerts.usage_date` (bổ sung ngoài spec): ngày được đánh giá, giúp chạy phát hiện lại không tạo trùng.
- **Quy tắc xóa**: cấp cha còn cấp con → `RESTRICT` (API trả 409). Xóa công tơ → `CASCADE` xóa usage và alert của công tơ đó.
- **Index**: `uq_electricity_usages_meter_id_recorded_at` (cột đầu là `meter_id`, đồng thời là index cho `meter_id`), `ix_electricity_usages_recorded_at`, `ix_alerts_meter_id`, `ix_alerts_created_at`, `ix_alerts_is_resolved`, `ix_rooms_floor_id`, `ix_meters_room_id`, `ix_electricity_prices_effective_from`.
- Tên constraint/index theo naming convention trong `app/core/database.py` để migration ổn định.

## 3. API

Prefix `/api/v1`. Mọi endpoint trừ `/auth/login` và `/health` cần `Authorization: Bearer <token>`.

**Response envelope**

```json
{ "success": true,  "message": "Thành công", "data": {} }
{ "success": true,  "message": "Thành công", "data": [], "pagination": { "page": 1, "page_size": 20, "total": 100, "total_pages": 5 } }
{ "success": false, "message": "Dữ liệu không hợp lệ", "error": { "code": "VALIDATION_ERROR", "details": [{ "field": "code", "message": "Trường này là bắt buộc" }] } }
```

| HTTP | `error.code` |
|---|---|
| 401 | `UNAUTHORIZED` (thiếu token), `INVALID_CREDENTIALS`, `INVALID_TOKEN`, `TOKEN_EXPIRED` |
| 403 | `FORBIDDEN`, `ACCOUNT_DISABLED` |
| 404 | `NOT_FOUND` |
| 409 | `CONFLICT` |
| 422 | `VALIDATION_ERROR`, `PRICE_NOT_FOUND`, `BUSINESS_RULE_VIOLATION` |
| 503 | `DATABASE_UNAVAILABLE`, `SERVICE_UNAVAILABLE` |
| 500 | `INTERNAL_ERROR` |

**Xác thực**: JWT HS256 (`sub` = user id, `role`, `exp` mặc định 8 giờ). `JWT_SECRET_KEY` bắt buộc dài ít nhất 32 ký tự. Mật khẩu được hash bằng Argon2. Username không phân biệt hoa thường. Mỗi request đều đọc lại user từ DB, nên tài khoản bị khóa sẽ mất quyền truy cập ngay.

**Phân quyền** (dependency `CurrentUser`, `AdminOrManager`, `AdminOnly`): mọi role đều xem được (GET). ADMIN và MANAGER được tạo/sửa/xóa dữ liệu, resolve alert và chạy detect. Chỉ ADMIN được ghi bảng giá điện.

| Nhóm | Endpoint |
|---|---|
| Hệ thống | `GET /health`, `GET /docs`, `GET /redoc` |
| Auth | `POST /auth/login`, `GET /auth/me` |
| CRUD | `buildings`, `floors`, `rooms`, `meters`, `electricity-usages`, `electricity-prices`: `GET` list (page, page_size, search, sort_by, sort_order + filter), `GET /{id}`, `POST`, `PUT /{id}`, `DELETE /{id}` |
| Dashboard | `GET /dashboard/summary`, `/daily`, `/monthly`, `/by-floor`, `/by-room`, `/cost` |
| Analytics | `GET /analytics/daily`, `/monthly`, `/hourly`, `/by-floor`, `/by-room`, `/comparison` |
| Alerts | `GET /alerts`, `POST /alerts/{id}/resolve`, `POST /alerts/detect` |
| Reports | `GET /reports/consumption`, `GET /reports/consumption/export` (CSV) |
| Chat | `GET /chat/conversations`, `POST /chat/conversations`, `GET /chat/conversations/{id}`, `DELETE /chat/conversations/{id}`, `POST /chat/conversations/{id}/messages` (JWT) |

Conversation được gắn với `user_id`; list/detail/delete chỉ truy cập conversation của user hiện tại. MongoDB lưu message history thành từng turn user + model; khi gọi Gemini, backend lấy tối đa 2 turn gần nhất (4 message trước đó, cộng câu hỏi hiện tại thành tối đa 5 message) và giới hạn prompt ở 24.000 ký tự, ưu tiên giữ trọn các cặp user/model. Frontend chỉ gửi conversation ID và câu hỏi hiện tại; backend tự tải lịch sử từ MongoDB để tránh tin vào history do client cung cấp. Luồng agent: kiểm tra quyền sở hữu → nạp ngữ cảnh → phân loại phạm vi/thiếu thông tin → gọi các tool analytics allowlist khi cần → đánh giá kết quả và lặp có giới hạn → stream câu trả lời hoặc câu hỏi làm rõ → lưu turn hoàn tất. Với câu hỏi phân tích rộng, agent ưu tiên lấy tổng quan, dữ liệu theo tầng và top phòng để giao diện hiển thị biểu đồ/bảng; chỉ các loại dữ liệu thực sự được tool trả về mới được dựng. Hội thoại mới là bản nháp trên frontend; chỉ tạo document conversation sau khi agent trả lời hoàn tất. Endpoint gửi message phản hồi dạng SSE với các event `token`, `visualization` (nếu công cụ trả dữ liệu phân tích), `done` hoặc `error`; payload visualization lưu kèm message trợ lý. Xóa conversation sẽ xóa các turn tương ứng. Nếu MongoDB hoặc Gemini không sẵn sàng trước khi bắt đầu stream, API trả `503 SERVICE_UNAVAILABLE`.

**Quy ước CRUD**
- PUT là cập nhật toàn bộ, gửi đủ các trường giống POST. POST trả về 201; DELETE trả về 200 kèm `data: null`.
- `sort_by` chỉ nhận các giá trị được liệt kê trên Swagger. `search` không phân biệt hoa thường, và các ký tự `%` `_` được hiểu theo nghĩa đen.
- Mã (`code`, `meter_code`) được tự động bỏ khoảng trắng và chuyển sang chữ in hoa.
- Số thập phân (`kwh`, `cost`, `area`, `price_per_kwh`, …) được trả về dạng số JSON.
- Response có kèm thông tin tham chiếu lồng nhau, ví dụ `meter.room.floor.building`, để frontend hiển thị tên mà không cần gọi thêm API.
- Lỗi theo từng field:
  - `422 VALIDATION_ERROR` khi id cấp cha không tồn tại, ví dụ `{"field": "building_id", "message": "Tòa nhà không tồn tại"}`.
  - `409 CONFLICT` khi trùng dữ liệu, ví dụ `{"field": "code", ...}`.
- Electricity usage:
  - `recorded_at` phải là đầu giờ và không được ở tương lai; nếu không ghi múi giờ thì hiểu là giờ Việt Nam.
  - `cost` không nhận từ client mà được tính bằng `kwh × đơn giá có hiệu lực`; không có bảng giá thì trả `422 PRICE_NOT_FOUND`.
- Bảng giá điện: các khoảng hiệu lực không được chồng lên nhau (trùng thì trả 409); chỉ ADMIN được ghi.

| Endpoint list | Filter | `sort_by` (mặc định) |
|---|---|---|
| `/buildings` | `search` (name, code, address) | **code**, name, created_at |
| `/floors` | `building_id`, `search` | **floor_number**, name, created_at |
| `/rooms` | `floor_id`, `building_id`, `search` | **code**, name, area, created_at |
| `/meters` | `room_id`, `floor_id`, `building_id`, `status`, `meter_type`, `search` | **meter_code**, name, status, installation_date, created_at |
| `/electricity-usages` | `meter_id`, `room_id`, `floor_id`, `building_id`, `from_date`, `to_date` (ngày giờ Việt Nam, bao gồm cả hai đầu) | **recorded_at desc**, kwh, cost |
| `/electricity-prices` | `active_on`, `search` | **effective_from desc**, price_per_kwh, name |

### Dashboard & Analytics

Dashboard và Analytics dùng chung `AnalyticsRepository`: mọi phép gom nhóm chạy bằng SQL, theo giờ Việt Nam, và không bao giờ tính quá thời điểm hiện tại.

| Endpoint | Ý nghĩa |
|---|---|
| `/dashboard/summary` | Tổng kWh hôm nay; tổng kWh và chi phí từ đầu tháng; số công tơ ACTIVE; số cảnh báo chưa xử lý |
| `/dashboard/daily?days=30`, `/dashboard/monthly?months=12`, `/dashboard/cost?months=6` | Chuỗi số liệu, ngày/tháng trống được điền 0 |
| `/dashboard/by-floor` | 7 ngày gần nhất so với 7 ngày trước đó; tăng ≥ 20% thì `status = WARNING` |
| `/dashboard/by-room?limit=10` | Các phòng tiêu thụ nhiều nhất từ đầu tháng, kèm tỷ trọng % |
| `/analytics/daily`, `/monthly`, `/hourly`, `/by-floor`, `/by-room` | Lọc theo `from_date`/`to_date` (mặc định 30 ngày; riêng `/monthly` là 12 tháng) và theo cây phân cấp. `/hourly` trả kWh trung bình mỗi ngày tại từng giờ, tách ngày thường và cuối tuần |
| `/analytics/comparison` | `period=day\|week\|month` (tuần bắt đầu từ thứ Hai) hoặc `current_from`/`current_to`. Kỳ trước được lấy với **cùng khoảng thời gian đã trôi qua** |

## 4. Logic nghiệp vụ

**Comparison**: `percentage_change = (current − previous) / previous × 100`. Kỳ trước có cùng độ dài với kỳ hiện tại; nếu `previous = 0` thì trả `null`.

**Alert** (theo từng công tơ ACTIVE, từng ngày theo giờ Việt Nam):

```text
actual   = tổng kWh của ngày D
baseline = trung bình kWh/ngày trong 14 ngày trước D, chỉ tính các ngày cùng loại (ngày thường / cuối tuần)
ratio    = actual / baseline          (bỏ qua nếu có ít hơn 3 ngày tham chiếu)
ratio ≥ 2.0 → CRITICAL · ≥ 1.5 → WARNING · ≥ 1.2 → INFO
```

Một số chi tiết triển khai:
- Ngưỡng nằm trong config (`ALERT_RATIO_*`, `ALERT_BASELINE_DAYS`, `ALERT_MIN_REFERENCE_DAYS`).
- Chỉ đánh giá những ngày đã kết thúc. Mỗi lần phát hiện chỉ cần 1 truy vấn SQL cho cả khoảng ngày.
- Insert dùng `ON CONFLICT DO NOTHING` trên `(meter_id, alert_type, usage_date)`, nên chạy lại không tạo trùng.
- `created_at` của cảnh báo là thời điểm ngày đó kết thúc.
- `threshold_value` = ngưỡng tham chiếu × 1,2; `actual_value` = kWh thực tế của ngày.

**API**
- `POST /alerts/detect?date=` (ADMIN/MANAGER): phát hiện cho một ngày, mặc định là hôm qua.
- `POST /alerts/{id}/resolve` (ADMIN/MANAGER): đánh dấu đã xử lý; nếu cảnh báo đã được xử lý trước đó thì trả 409.
- `GET /alerts`: lọc theo `is_resolved`, `severity`, cây phân cấp và khoảng `usage_date`.

**Seed**
- Lệnh seed tự chạy phát hiện cho toàn bộ dữ liệu vừa sinh.
- Lần seed đầu: cảnh báo cũ hơn 3 ngày được đánh dấu đã xử lý (khoảng 296 cảnh báo, chỉ khoảng 9 cái còn mở).

**Reports**
- `GET /reports/consumption?group_by=floor|room|meter`: mặc định tính từ đầu tháng tới hôm nay.
- `GET /reports/consumption/export`: trả cùng dữ liệu dạng CSV UTF-8 có BOM (Excel hiển thị đúng tiếng Việt), kèm dòng "Tổng cộng". Tên file có dạng `bao-cao-dien-nang_<nhóm>_<từ>-<đến>.csv`.

**Dữ liệu giả lập**: 1 tòa nhà, 10 tầng, 50 phòng, 50 công tơ, dữ liệu theo giờ trong 90 ngày (~108.000 dòng). Có giờ cao điểm, cuối tuần thấp hơn, một số ngày bất thường. Random seed cố định để tái lập được; `--top-up` bổ sung dữ liệu đến thời điểm hiện tại.

## 5. Lộ trình

| Phase | Nội dung | Trạng thái |
|---|---|---|
| P1 | Kiến trúc | ✅ |
| P2 | Backend base, models, Alembic migration | ✅ |
| P3 | Authentication (JWT, phân quyền) | ✅ |
| P4 | CRUD API | ✅ |
| P5 | Seed dữ liệu giả lập | ✅ |
| P6 | Dashboard + Analytics API | ✅ |
| P7 | Alerts + Reports API | ✅ |
| P8 | Frontend base (layout, login, API client) | ✅ |
| P9 | Các trang frontend, kết nối API thật | ✅ |
| P10 | README hoàn chỉnh, kiểm tra toàn bộ từ bản clone sạch | ✅ |