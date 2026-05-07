# Harvest Slot Backend

Harvest Slot 백엔드는 과수농가 수확 예약·직배송 서비스를 위한 FastAPI + MySQL 기반 API 서버입니다.  
고객은 웹에서 상품과 수확 슬롯을 보고 예약/주문/반품을 진행하고, 점주는 관리 앱에서 상품·수확 슬롯·발주·신선도 검사·배송·반품을 처리합니다. 백엔드는 이 두 클라이언트와 MySQL 사이에서 인증, 상태 전이, 업무 규칙을 담당합니다.

현재 ML/DL 예측과 품질 판정, 결제는 실제 외부 연동이 아니라 Mock 기반입니다.

## 시스템 구성

```text
고객 웹(CUSTOMER)
  -> 백엔드 API(FastAPI, /api/v1)
  -> MySQL

점주 관리 앱(OWNER)
  -> 백엔드 API(FastAPI, /api/v1)
  -> MySQL

ML/DL / 결제
  -> 현재는 Mock 응답 및 Stub 로직 사용
```

## 빠른 시작

### 1. 가상환경 생성 및 활성화

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. `.env` 작성

`.env.example`을 참고해서 루트에 `.env` 파일을 생성합니다.

```powershell
Copy-Item .env.example .env
```

최소 확인 항목:

```env
APP_NAME=Harvest Slot API
API_V1_PREFIX=/api/v1
DEBUG=true

DATABASE_HOST=your-db-host
DATABASE_PORT=3306
DATABASE_USER=your-db-user
DATABASE_PASSWORD=your-db-password
DATABASE_NAME=harvest_slot_db
DATABASE_CHARSET=utf8mb4

JWT_SECRET_KEY=change-this-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 4. 서버 실행

로컬 전용 실행:

```bash
uvicorn backend.app.main:app --reload
```

다른 팀원이 내 PC 서버에 접속해야 하는 경우:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 접속 주소

- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health: `http://127.0.0.1:8000/api/v1/health`
- API Prefix: `/api/v1`

## 팀원 접속 방법

- 같은 PC에서 테스트할 때는 `127.0.0.1` 또는 `localhost`를 사용합니다.
- 다른 팀원이 내 PC에서 띄운 서버에 접속할 때는 `127.0.0.1`이 아니라 내 PC의 사설 IP를 사용해야 합니다.
- 예: 내 PC IP가 `192.168.0.15`면 Swagger 주소는 `http://192.168.0.15:8000/docs` 입니다.
- 외부 접속을 받으려면 반드시 아래 명령으로 실행해야 합니다.

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## 테스트 계정 및 인증

### 테스트 계정

| 역할 | 이메일 | 비밀번호 |
|---|---|---|
| CUSTOMER | `customer@test.com` | `demo1234!` |
| OWNER | `owner@test.com` | `demo1234!` |

### 인증 방식

- 인증이 필요한 API는 `Authorization: Bearer <token>` 헤더가 필요합니다.
- CUSTOMER API는 CUSTOMER 토큰으로 호출해야 합니다.
- OWNER API는 OWNER 토큰으로 호출해야 합니다.
- 권한이 다르면 `403 Forbidden`이 발생할 수 있습니다.

### Swagger Authorize 사용 방법

Swagger 상단 `Authorize`는 OAuth2 password flow를 사용하므로 `POST /api/v1/auth/token` 기준으로 동작합니다.

1. `POST /api/v1/auth/token` 또는 Swagger `Authorize`에서 로그인합니다.
2. `username`에는 이메일을 넣습니다.
3. `password`에는 비밀번호를 넣습니다.
4. 발급된 Bearer Token으로 인증이 필요한 API를 호출합니다.

참고:

- 웹/앱에서 직접 로그인할 때는 `POST /api/v1/auth/login`을 사용합니다.
- Swagger `Authorize`는 `POST /api/v1/auth/token`을 사용합니다.

## 공통 응답 형식

대부분의 API는 아래 공통 응답 구조를 사용합니다.

```json
{
  "data": {},
  "message": "success",
  "error": null
}
```

예외:

- `POST /api/v1/auth/token`은 OAuth2 표준 형태로 `{ "access_token": "...", "token_type": "bearer" }` 를 반환합니다.

## 사용자 웹팀 연동 API

고객 화면 흐름 기준으로 보면 아래 API부터 확인하면 됩니다.

| Method | Path | 화면/기능 |
|---|---|---|
| POST | `/api/v1/auth/login` | 로그인 화면 |
| GET | `/api/v1/me` | 로그인 후 내 정보 확인, 헤더/마이페이지 초기화 |
| GET | `/api/v1/products` | 상품 목록 화면 |
| GET | `/api/v1/products/{product_id}` | 상품 상세 화면 |
| GET | `/api/v1/products/{product_id}/slots` | 상품 상세 내 예약 가능 슬롯 조회 |
| POST | `/api/v1/reservations/preview` | 예약 전 금액/중량 미리보기 |
| POST | `/api/v1/reservations` | 예약하기 버튼 |
| GET | `/api/v1/me/reservations` | 내 예약 목록 화면 |
| POST | `/api/v1/orders/from-reservation` | 예약을 주문으로 전환 |
| GET | `/api/v1/me/orders` | 주문 목록 화면 |
| GET | `/api/v1/me/orders/{order_id}` | 주문 상세 화면 |
| POST | `/api/v1/payments/mock-approve` | 결제 완료 Mock 처리 |
| GET | `/api/v1/me/orders/{order_id}/shipment` | 배송 조회 화면 |
| POST | `/api/v1/returns` | 반품 요청 화면 |
| GET | `/api/v1/me/returns` | 반품 요청/처리 내역 화면 |

### 사용자 웹팀에서 먼저 보면 좋은 순서

1. `GET /api/v1/products`
2. `GET /api/v1/products/{product_id}`
3. `GET /api/v1/products/{product_id}/slots`
4. `POST /api/v1/reservations/preview`
5. `POST /api/v1/reservations`
6. `POST /api/v1/orders/from-reservation`
7. `POST /api/v1/payments/mock-approve`
8. `GET /api/v1/me/orders/{order_id}`
9. `GET /api/v1/me/orders/{order_id}/shipment`
10. `POST /api/v1/returns`

## 점주 앱팀 연동 API

점주 업무 흐름 기준으로 보면 아래 API를 순서대로 확인하면 됩니다.

| Method | Path | 화면/기능 |
|---|---|---|
| POST | `/api/v1/auth/login` | 로그인 화면 |
| GET | `/api/v1/me` | 로그인 후 내 정보 확인 |
| GET | `/api/v1/owner/dashboard` | 대시보드 요약 카드 |
| GET | `/api/v1/owner/farms/me` | 내 농가 정보 조회 화면 |
| PUT | `/api/v1/owner/farms/{farm_id}` | 농가 정보 수정 화면 |
| GET | `/api/v1/owner/products` | 상품 목록 관리 화면 |
| POST | `/api/v1/owner/products` | 상품 등록 화면 |
| GET | `/api/v1/owner/ml/predictions` | 수확 예측 이력 화면 |
| POST | `/api/v1/owner/ml/predictions` | 수확 예측 실행 버튼 |
| GET | `/api/v1/owner/harvest-slots` | 수확 슬롯 목록 화면 |
| POST | `/api/v1/owner/harvest-slots` | 수확 슬롯 생성 화면 |
| PUT | `/api/v1/owner/harvest-slots/{slot_id}` | 수확 슬롯 수정 화면 |
| PATCH | `/api/v1/owner/harvest-slots/{slot_id}/status` | 슬롯 공개/마감 상태 변경 |
| GET | `/api/v1/owner/orders` | 주문 목록 화면 |
| GET | `/api/v1/owner/procurements` | 발주 목록 화면 |
| PATCH | `/api/v1/owner/procurements/{procurement_id}/decision` | 발주 승인/부분승인/거절 버튼 |
| POST | `/api/v1/owner/quality-inspections` | 신선도 검사 등록 |
| GET | `/api/v1/owner/quality-inspections` | 신선도 검사 이력 화면 |
| POST | `/api/v1/owner/shipments` | 배송 등록 |
| PATCH | `/api/v1/owner/shipments/{shipment_id}/status` | 배송 상태 변경 |
| GET | `/api/v1/owner/returns` | 반품 요청 목록 화면 |
| PATCH | `/api/v1/owner/returns/{return_request_id}/decision` | 반품 승인/거절 및 환불 처리 |

### 점주 앱팀에서 먼저 보면 좋은 순서

1. `GET /api/v1/owner/dashboard`
2. `GET /api/v1/owner/products`
3. `POST /api/v1/owner/ml/predictions`
4. `POST /api/v1/owner/harvest-slots`
5. `GET /api/v1/owner/procurements`
6. `PATCH /api/v1/owner/procurements/{procurement_id}/decision`
7. `POST /api/v1/owner/quality-inspections`
8. `POST /api/v1/owner/shipments`
9. `PATCH /api/v1/owner/shipments/{shipment_id}/status`
10. `GET /api/v1/owner/returns`
11. `PATCH /api/v1/owner/returns/{return_request_id}/decision`

## 핵심 E2E 테스트 흐름

Swagger에서 핵심 연동 흐름을 검증할 때는 아래 순서대로 보면 됩니다.

### CUSTOMER

1. `POST /api/v1/reservations`
2. `GET /api/v1/me/reservations`
3. `POST /api/v1/orders/from-reservation`
4. `POST /api/v1/payments/mock-approve`

### OWNER

5. `GET /api/v1/owner/procurements`
6. `PATCH /api/v1/owner/procurements/{procurement_id}/decision`
7. `POST /api/v1/owner/quality-inspections`
8. `POST /api/v1/owner/shipments`
9. `PATCH /api/v1/owner/shipments/{shipment_id}/status`

### CUSTOMER

10. `GET /api/v1/me/orders/{order_id}/shipment`
11. `POST /api/v1/returns`
12. `GET /api/v1/me/returns`

### OWNER

13. `GET /api/v1/owner/returns`
14. `PATCH /api/v1/owner/returns/{return_request_id}/decision`

### CUSTOMER

15. `GET /api/v1/me/orders/{order_id}`
16. `GET /api/v1/me/returns`

## 자주 헷갈리는 요청 Body 필드명

Swagger 기준으로 자주 실수하는 부분입니다.

### 배송 등록

- `tracking_number`가 아니라 `tracking_no`를 사용합니다.
- `shipped_package_count`, `shipped_kg`는 필수입니다.
- `POST /api/v1/owner/shipments` 요청 바디에는 `shipment_status` 필드가 없습니다.
- 생성 시 서버가 내부적으로 `shipment_status=SHIPPED`로 처리합니다.

실제 요청 예시:

```json
{
  "order_id": 1,
  "carrier_name": "CJ대한통운",
  "tracking_no": "1234567890",
  "shipped_package_count": 2,
  "shipped_kg": 10
}
```

### 반품 요청

- `return_reason`이 아니라 `reason_code`를 사용합니다.
- `requested_amount`는 필수입니다.
- 상세 사유 필드는 `return_detail`이 아니라 `reason_detail`입니다.

실제 요청 예시:

```json
{
  "order_id": 1,
  "reason_code": "QUALITY_ISSUE",
  "requested_amount": 78000,
  "reason_detail": "상품 품질 문제로 반품 요청합니다."
}
```

### 신선도 검사

- `image_url`은 필수입니다.
- 현재 `POST /api/v1/owner/quality-inspections` 요청 바디는 모델 결과 전체를 받지 않습니다.
- `model_grade`, `freshness_score`, `color_score`, `roundness_score`, `bruise_probability`, `model_decision`은 응답에서 서버가 Mock 값으로 채워줍니다.

실제 요청 예시:

```json
{
  "procurement_item_id": 1,
  "image_url": "/mock/quality/apple_sample_001.jpg",
  "owner_confirmed_grade": "A",
  "owner_decision": "PASS"
}
```

### Mock 결제 승인

- `POST /api/v1/payments/mock-approve`는 `order_id`와 `idempotency_key`가 필요합니다.

실제 요청 예시:

```json
{
  "order_id": 1,
  "idempotency_key": "payment-order-1-try-1"
}
```

## 상태값 정리

프론트에서 화면 분기할 때는 아래 실제 코드 기준 상태값을 사용하면 됩니다.

### `reservation_status`

| 값 | 설명 |
|---|---|
| `RESERVED` | 예약 생성 완료 |
| `ORDERED` | 예약이 주문으로 전환됨 |
| `EXPIRED` | 예약 만료 |
| `CANCELED` | 예약 취소 |

### `order_status`

| 값 | 설명 |
|---|---|
| `PAYMENT_PENDING` | 결제 전 |
| `PAID` | 결제 완료 |
| `PROCUREMENT_REQUESTED` | 발주 요청됨 |
| `PROCUREMENT_APPROVED` | 발주 승인 |
| `PROCUREMENT_PARTIAL_APPROVED` | 발주 부분승인 |
| `PROCUREMENT_REJECTED` | 발주 거절 |
| `QUALITY_CHECKING` | 품질 검사 단계 |
| `READY_TO_SHIP` | 배송 준비 |
| `SHIPPED` | 배송중 |
| `DELIVERED` | 배송 완료 |
| `RETURN_REQUESTED` | 반품 요청됨 |
| `REFUNDED` | 환불 완료 |
| `CANCELED` | 주문 취소 |

### `procurement_status`

| 값 | 설명 |
|---|---|
| `REQUESTED` | 발주 요청 |
| `APPROVED` | 발주 승인 |
| `PARTIAL_APPROVED` | 발주 부분승인 |
| `REJECTED` | 발주 거절 |

주의:

- 코드상 실제 값은 `PARTIAL_APPROVED`입니다.
- `PARTIALLY_APPROVED`가 아닙니다.

### `shipment_status`

| 값 | 설명 |
|---|---|
| `READY` | 배송 준비 |
| `SHIPPED` | 배송중 |
| `DELIVERED` | 배송 완료 |

### `return_status`

| 값 | 설명 |
|---|---|
| `REQUESTED` | 반품 요청 접수 |
| `APPROVED` | 반품 승인 |
| `REJECTED` | 반품 거절 |
| `REFUNDED` | 환불 완료 |

### `refund_status`

| 값 | 설명 |
|---|---|
| `REQUESTED` | 환불 요청 생성 |
| `COMPLETED` | 환불 완료 |
| `FAILED` | 환불 실패 |

### `payment_status`

| 값 | 설명 |
|---|---|
| `REQUESTED` | 결제 요청 생성 |
| `APPROVED` | 결제 승인 |
| `FAILED` | 결제 실패 |
| `CANCELED` | 결제 취소 |
| `REFUNDED` | 환불 완료 |

## 프론트 연동 시 주의사항

- CUSTOMER API는 CUSTOMER 토큰으로 호출합니다.
- OWNER API는 OWNER 토큰으로 호출합니다.
- 역할이 맞지 않으면 `403`이 날 수 있습니다.
- `422 Unprocessable Entity`는 요청 Body 필드 누락, 타입 오류, 필드명 오타일 가능성이 큽니다.
- `400 Bad Request`는 비즈니스 규칙 위반일 가능성이 큽니다.
  예: 이미 반품 요청 존재, 이미 처리된 반품, 이미 배송 존재
- `500 Internal Server Error`는 백엔드 수정 대상입니다.
- Swagger에서 먼저 동일 요청을 재현해보고, Swagger도 실패하면 프론트 코드보다 백엔드/데이터 상태를 먼저 확인하는 편이 빠릅니다.

## 문서 레포 참고

- 참고 문서 레포: `smart_docs`
- GitHub: `https://github.com/AI-MegaStudy/smart_docs.git`
- 백엔드 작업 시 참고 문서 기준: `../smart_docs/00_harvest_slot_docs_v3_2`
- `smart_docs`는 참고용 문서 레포입니다.
- 실제 백엔드 코드 수정은 현재 레포(`harvest-slot-backend`)에서만 진행합니다.

## 팀 협업 안내

- 프론트/앱 팀원은 먼저 Swagger에서 실제 요청/응답을 확인한 뒤 화면에 연동합니다.
- 필요한 응답 필드가 부족하면 백엔드 담당자에게 요청합니다.
- 요청 Body가 헷갈리면 Swagger Schema를 가장 먼저 확인합니다.
- `.env` 파일은 공유하거나 GitHub에 올리지 않습니다.
- 테스트 데이터는 NAS MySQL을 같이 쓰는 경우 ID가 계속 증가할 수 있습니다.

## 팀원이 가장 먼저 확인할 위치

1. `http://127.0.0.1:8000/docs`
2. 이 README의 `사용자 웹팀 연동 API`, `점주 앱팀 연동 API`
3. 이 README의 `자주 헷갈리는 요청 Body 필드명`
4. 이 README의 `핵심 E2E 테스트 흐름`
