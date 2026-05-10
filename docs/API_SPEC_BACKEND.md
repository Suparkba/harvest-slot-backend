# API_SPEC_BACKEND

## 공통

모든 API Base URL은 `/api/v1` 이고 응답 형식은 아래 공통 구조를 따른다.

```json
{
  "data": {},
  "message": "success",
  "error": null
}
```

## 공통 API

| Method | Path | 설계서 일치 여부 | 비고 |
|---|---|---|---|
| GET | `/api/v1/health` | 구현 추가 | Health Check |
| GET | `/api/v1/health/db` | 구현 추가 | DB Health Check |
| POST | `/api/v1/auth/customers/signup` | 일치 | Mock 이메일 인증 코드 반환 |
| POST | `/api/v1/auth/owners/signup` | 일치 | Mock 이메일 인증 코드 반환 |
| POST | `/api/v1/auth/email/resend` | 일치 | Mock 재발송 |
| POST | `/api/v1/auth/email/verify` | 일치 | 코드 검증 후 `accounts.email_verified=true` |
| POST | `/api/v1/auth/login` | 일치 | JWT 발급 |
| GET | `/api/v1/me` | 일치 | 현재 계정 정보 |

회원가입 예시:

```json
{
  "email": "customer@test.com",
  "password": "pass1234!",
  "name": "홍길동",
  "phone": "010-1111-2222"
}
```

## 사용자 예약 웹 API

| Method | Path | 설계서 일치 여부 | 비고 |
|---|---|---|---|
| GET | `/api/v1/products?featured=true` | 일치 | OPEN 슬롯 보유 상품 우선 |
| GET | `/api/v1/products` | 일치 | `fruit_type` 필터 지원 |
| GET | `/api/v1/products/{product_id}` | 일치 | 농장 정보 포함 |
| GET | `/api/v1/products/{product_id}/slots` | 일치 | `available_kg` 계산 포함 |
| GET | `/api/v1/farms/{farm_id}` | 일치 | 공개 조회 |
| POST | `/api/v1/reservations/preview` | 일치 | DB 저장 없이 계산 |
| POST | `/api/v1/reservations` | 일치 | 트랜잭션 처리 |
| GET | `/api/v1/me/reservations` | 일치 | 고객 예약 목록 |
| POST | `/api/v1/orders/from-reservation` | 일치 | 예약을 주문으로 전환 |
| GET | `/api/v1/me/orders` | 일치 | 고객 주문 목록 |
| GET | `/api/v1/me/orders/{order_id}` | 일치 | 결제/발주/배송/반품 포함 |
| POST | `/api/v1/payments/mock-approve` | 일치 | Mock 승인 |
| GET | `/api/v1/me/orders/{order_id}/payments` | 일치 | 주문 결제 목록 |
| GET | `/api/v1/me/orders/{order_id}/shipment` | 일치 | 배송 정보 |
| POST | `/api/v1/returns` | 일치 | 배송 완료 주문만 가능 |
| GET | `/api/v1/me/returns` | 일치 | 고객 반품 목록 |

예약 생성 예시:

```json
{
  "items": [
    {
      "slot_id": 12,
      "package_count": 2
    }
  ]
}
```

## 점주 앱 API

| Method | Path | 설계서/화면정의 일치 여부 | 비고 |
|---|---|---|---|
| GET | `/api/v1/owner/dashboard` | 화면정의 기준 구현 | 열린 슬롯/발주/선별 대기/배송 준비/반품 요청 |
| GET | `/api/v1/owner/farms/me` | 일치 | 내 농장 목록 |
| PUT | `/api/v1/owner/farms/{farm_id}` | 일치 | 농장 수정 |
| GET | `/api/v1/owner/products` | 일치 | 상품 목록 |
| POST | `/api/v1/owner/products` | 일치 | 상품 등록 |
| PUT | `/api/v1/owner/products/{product_id}` | 일치 | 상품 수정 |
| PATCH | `/api/v1/owner/products/{product_id}/status` | 일치 | 상품 상태 변경 |
| POST | `/api/v1/owner/ml/predictions` | 일치 | Mock ML 예측 |
| GET | `/api/v1/owner/ml/predictions` | 일치 | 예측 이력 |
| GET | `/api/v1/owner/ml/predictions/{prediction_id}` | 일치 | 예측 상세 |
| GET | `/api/v1/owner/harvest-slots` | 일치 | 점주 슬롯 목록 |
| POST | `/api/v1/owner/harvest-slots` | 일치 | 슬롯 생성 |
| PUT | `/api/v1/owner/harvest-slots/{slot_id}` | 일치 | 슬롯 수정 |
| PATCH | `/api/v1/owner/harvest-slots/{slot_id}/status` | 일치 | 슬롯 상태 변경 |
| GET | `/api/v1/owner/reservations` | 일치 | 점주 예약 목록 |
| GET | `/api/v1/owner/orders` | 일치 | 점주 주문 목록 |
| GET | `/api/v1/owner/procurements` | 일치 | 발주 목록 |
| GET | `/api/v1/owner/procurements/{procurement_id}` | 일치 | 발주 상세 |
| PATCH | `/api/v1/owner/procurements/{procurement_id}/decision` | 일치 | 승인/부분승인/거절 |
| POST | `/api/v1/owner/quality-inspections` | 일치 | Mock DL 검사 |
| GET | `/api/v1/owner/quality-inspections` | 일치 | 검사 이력 |
| POST | `/api/v1/owner/shipments` | 일치 | 배송 등록 |
| PATCH | `/api/v1/owner/shipments/{shipment_id}/status` | 일치 | 배송 상태 변경 |
| GET | `/api/v1/owner/returns` | 일치 | 반품 목록 |
| PATCH | `/api/v1/owner/returns/{return_request_id}/decision` | 일치 | 반품 승인/거절 및 환불 |
| GET | `/api/v1/owner/profile` | 화면정의 기준 구현 | 점주 프로필 조회 |
| PUT | `/api/v1/owner/profile` | 화면정의 기준 구현 | 점주 프로필 수정 |

ML 예측 응답 예시:

```json
{
  "data": {
    "prediction_id": 10,
    "predicted_harvest_start": "2026-10-12",
    "predicted_harvest_end": "2026-10-18",
    "estimated_yield_kg": 420.0,
    "suggested_reservable_min_kg": 260.0,
    "suggested_reservable_max_kg": 320.0,
    "recommended_price": 5500,
    "confidence": 0.78,
    "safety_factor": 0.75,
    "warning_message": "기상과 생육 상황에 따라 점주 확정값을 조정하세요.",
    "model_version": "rf-apple-harvest-v1"
  },
  "message": "success",
  "error": null
}
```

## Swagger Test Order

1. `POST /api/v1/auth/login`
   - Web/app JSON login endpoint
   - Request body:

```json
{
  "email": "owner@test.com",
  "password": "demo1234!"
}
```

   - Response shape:

```json
{
  "data": {
    "access_token": "...",
    "token_type": "bearer",
    "role": "OWNER"
  },
  "message": "success",
  "error": null
}
```

2. `POST /api/v1/auth/token`
   - Swagger `Authorize` OAuth2 password flow endpoint
   - Form fields:
     - `username`: service email
     - `password`: account password
   - Response shape:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

3. `GET /api/v1/me`
   - After `Authorize`, call this endpoint with `Bearer <token>` to verify authentication
