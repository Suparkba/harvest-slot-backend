# Harvest Slot Backend

## 프로젝트 개요

**Harvest Slot Backend**는 FastAPI, MySQL 기반 과수농가 수확 예약·직배송 플랫폼 백엔드 API 서버입니다.

서비스 흐름:

```text
상품 등록
→ ML 예측 보조
→ 점주 수확 슬롯 확정
→ 고객 예약
→ 주문 생성
→ Mock 결제 승인
→ 발주 생성
→ 점주 발주 승인/부분승인/거절
→ DL 신선도 검사
→ 배송 등록
→ 반품 요청
→ Mock 환불 처리
```

공통 API prefix:

```text
/api/v1
```

공통 응답 구조:

```json
{
  "data": {},
  "message": "success",
  "error": null
}
```

역할:

```text
CUSTOMER
OWNER
```

주요 기능:

- CUSTOMER / OWNER 인증 및 권한 분리
- 이메일 인증
- 상품 / 수확 슬롯 / 예약 / 주문 / 결제
- 발주 / 품질검사 / 배송 / 반품 / 환불
- NAS 이미지 업로드 및 이미지 CRUD
- 외부 DL API / ngrok 기반 신선도 검사 연동
- Swagger 기반 API 문서 제공

## 실행 방법

로컬 Swagger 확인용:

```powershell
cd C:\Users\zzwls\Desktop\teamProject\harvest-slot-backend\harvest-slot-backend
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.app.main:app --reload
```

팀원 접속용:

```powershell
cd C:\Users\zzwls\Desktop\teamProject\harvest-slot-backend\harvest-slot-backend
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

팀원 접속 주소:

```text
Swagger:
http://<서버_PC_IP>:8000/docs

API Base URL:
http://<서버_PC_IP>:8000/api/v1
```

주의:

- `<서버_PC_IP>`는 서버를 실행하는 사람의 IPv4 주소입니다.
- 학원 / 집 / 와이파이에 따라 IP가 바뀔 수 있습니다.
- `127.0.0.1`은 자기 PC 기준이라 팀원 PC / 휴대폰에서는 접속할 수 없습니다.

Windows IPv4 확인:

```powershell
ipconfig
```

## 환경변수

`.env.example`을 복사해서 `.env`를 만들고, 실제 값은 각자 로컬 / 서버 환경에 맞게 채웁니다.

주의:

- 실제 `.env`는 GitHub에 올리지 않습니다.
- 실제 DB 비밀번호, SMTP 비밀번호, NAS 관련 민감 정보는 `.env`에만 저장합니다.
- `.env.example`은 팀원 공유용 예시 파일입니다.

이미지 / NAS 관련:

```env
IMAGE_UPLOAD_URL=https://cheng80.myqnapcloud.com/upload_image.php
IMAGE_UPLOAD_TIMEOUT_SECONDS=20
IMAGE_DEFAULT_PRODUCT_SUBFOLDER=products
IMAGE_DEFAULT_QUALITY_SUBFOLDER=quality-inspections
IMAGE_ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,webp
IMAGE_MAX_SIZE_MB=5
```

DL 신선도 검사 관련:

```env
DL_QUALITY_ENABLED=false
DL_QUALITY_API_URL=
DL_QUALITY_TIMEOUT_SECONDS=60
```

실제 DL 연동 시:

```env
DL_QUALITY_ENABLED=true
DL_QUALITY_API_URL=https://xxxx.ngrok-free.app/owner/quality-inspections
DL_QUALITY_TIMEOUT_SECONDS=60
```

이메일 인증 관련:

```env
EMAIL_VERIFICATION_REQUIRED=false
EMAIL_VERIFICATION_EXPIRE_MINUTES=5
EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=60
EMAIL_VERIFICATION_MAX_ATTEMPTS=5
EMAIL_DEV_MODE=true
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
SMTP_USE_TLS=true
```

주의:

- `EMAIL_DEV_MODE=false`에서는 인증번호가 응답에 노출되면 안 됩니다.
- 실제 SMTP 비밀번호는 `.env`에만 저장합니다.

## 테스트 실행 방법

기본 테스트:

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -v tests
```

최근 기준 테스트 결과:

```text
74 passed, 3 skipped, 0 failed
```

기본 pytest는 실제 NAS, SMTP, DL 서버에 의존하지 않고 mock / monkeypatch 기반으로 통과해야 합니다.

Live E2E 테스트:

```powershell
$env:RUN_LIVE_API_TESTS="true"
$env:BASE_URL="http://127.0.0.1:8000/api/v1"
pytest -v tests/test_live_e2e_api.py
```

Live Image 테스트:

```powershell
$env:RUN_LIVE_IMAGE_TESTS="true"
pytest -v tests/test_live_image_api.py
```

Live DL 테스트:

```powershell
$env:RUN_LIVE_DL_TESTS="true"
$env:DL_QUALITY_ENABLED="true"
$env:DL_QUALITY_API_URL="https://xxxx.ngrok-free.app/owner/quality-inspections"
pytest -v tests/test_live_dl_quality_api.py
```

주의:

- Live 테스트는 실제 서버, NAS, DL ngrok 서버가 켜져 있을 때만 실행합니다.
- 기본 테스트에서는 실제 외부 서버를 호출하지 않습니다.

## 인증 / 권한

인증 API:

```text
POST /api/v1/auth/login
POST /api/v1/auth/token
GET /api/v1/me
```

테스트 계정:

```text
CUSTOMER:
customer@test.com / demo1234!

OWNER:
owner@test.com / demo1234!
```

프론트 / 앱 로그인:

```text
POST /api/v1/auth/login
```

요청 예시:

```json
{
  "email": "owner@test.com",
  "password": "demo1234!"
}
```

Swagger Authorize:

```text
POST /api/v1/auth/token
```

Swagger Authorize 입력:

```text
username: owner@test.com
password: demo1234!
```

인증 헤더:

```text
Authorization: Bearer <access_token>
```

주의:

- CUSTOMER 화면은 CUSTOMER 토큰 사용
- OWNER 화면은 OWNER 토큰 사용
- CUSTOMER 토큰으로 OWNER API 호출 시 403 발생
- OWNER 토큰으로 CUSTOMER 전용 API 호출 시 권한 정책에 따라 실패 가능
- 인증 확인은 `GET /api/v1/me`로 확인
- `/api/v1/auth/login`은 JSON 로그인, `/api/v1/auth/token`은 Swagger Authorize / OAuth2 form login 용도입니다.

## 이메일 인증

이메일 인증 API:

```text
POST /api/v1/auth/email/send
POST /api/v1/auth/email/verify
GET /api/v1/auth/email/status
```

설명:

- `EMAIL_VERIFICATION_REQUIRED=false`이면 기존 회원가입 / 로그인 흐름을 유지합니다.
- `EMAIL_DEV_MODE=true`이면 개발 테스트가 가능합니다.
- 실제 SMTP 비밀번호는 `.env`에만 저장합니다.
- 실제 운영 모드에서는 인증번호가 응답에 노출되지 않도록 해야 합니다.

## 핵심 E2E 흐름

CUSTOMER 흐름:

```text
1. POST /api/v1/auth/login
2. GET /api/v1/me
3. GET /api/v1/products
4. GET /api/v1/products/{product_id}
5. GET /api/v1/products/{product_id}/slots
6. POST /api/v1/reservations
7. GET /api/v1/me/reservations
8. POST /api/v1/orders/from-reservation
9. POST /api/v1/payments/mock-approve
10. GET /api/v1/me/orders
11. GET /api/v1/me/orders/{order_id}
12. GET /api/v1/me/orders/{order_id}/shipment
13. POST /api/v1/returns
14. GET /api/v1/me/returns
```

OWNER 흐름:

```text
1. POST /api/v1/auth/login
2. GET /api/v1/me
3. GET /api/v1/owner/dashboard
4. GET /api/v1/owner/farms/me
5. GET /api/v1/owner/products
6. POST /api/v1/owner/products
7. POST /api/v1/owner/products/{product_id}/image
8. GET /api/v1/owner/procurements
9. PATCH /api/v1/owner/procurements/{procurement_id}/decision
10. POST /api/v1/owner/quality-inspections/analyze
11. POST /api/v1/owner/quality-inspections
12. POST /api/v1/owner/shipments
13. PATCH /api/v1/owner/shipments/{shipment_id}/status
14. GET /api/v1/owner/returns
15. PATCH /api/v1/owner/returns/{return_request_id}/decision
```

반품 / 환불 완료 상태:

```text
order_status = REFUNDED
payment_status = REFUNDED
return_status = REFUNDED
refund_status = COMPLETED
```

중복 반품 승인 요청은 500이 아니라 400을 반환해야 합니다.

## 이미지 / NAS 연동

NAS API는 `docs/upload_image_usage.md` 기준으로 연동됩니다.

상품 이미지 업로드:

```text
POST /api/v1/owner/products/{product_id}/image
```

설명:

- 상품 이미지는 고객 화면에 계속 보여야 하므로 NAS 저장 대상입니다.
- 성공 시 `products.image_url`이 업데이트됩니다.
- 프론트 / 앱은 응답의 `image_url`을 화면에 사용합니다.

신선도 검사 이미지 저장 전용:

```text
POST /api/v1/owner/quality-inspections/image
```

설명:

- 호출하면 NAS 저장이 발생합니다.
- analyze API와 다르게 저장 전용 API입니다.
- 저장된 `image_url`을 quality-inspections 최종 저장 API에 넣을 수 있습니다.

일반 이미지 CRUD:

```text
POST /api/v1/images/upload
GET /api/v1/images
GET /api/v1/images/{file_name}
PUT /api/v1/images/{file_name}
DELETE /api/v1/images/{file_name}
```

주의:

- OWNER 권한 필요
- CUSTOMER 토큰으로 호출하면 403
- 허용 확장자: jpg, jpeg, png, gif, webp
- `POST`, `PUT`, `DELETE`는 실제 NAS 파일에 영향을 줄 수 있음
- `saved_path`, `file_path` 같은 NAS 내부 경로는 프론트 응답에 노출하지 않음

## DL 신선도 검사

현재 구조:

```text
앱/웹/백엔드
→ 백엔드 FastAPI
→ 외부 DL FastAPI/ngrok endpoint
→ Kaggle Notebook 내부 PyTorch 모델 추론
→ JSON 응답 반환
```

중요:

- 백엔드는 torch / torchvision / model 파일을 직접 import하지 않습니다.
- DL 담당자가 Kaggle Notebook에서 FastAPI 서버를 실행하고 ngrok URL을 열면 백엔드가 호출합니다.
- 현재 DL 모델은 사과 전용입니다.
- smart_dl 기준 최신 모델 폴더는 `models/apple_balanced`입니다.
- 기본값 `DL_QUALITY_ENABLED=false`에서는 `mock-dl-v1` 결과를 반환합니다.
- `DL_QUALITY_ENABLED=true`이고 `DL_QUALITY_API_URL`이 설정되면 외부 DL API를 호출합니다.
- DL API 파일 필드명은 `image`입니다.
- ngrok URL은 매번 바뀔 수 있으므로 코드에 하드코딩하지 않습니다.

분석 API:

```text
POST /api/v1/owner/quality-inspections/analyze
```

역할:

- DL 신선도 검사 분석용 API
- 기본적으로 DB 저장 안 함
- 기본적으로 NAS 저장 안 함
- `persist_image=false`가 기본값
- `persist_image=true`이면 NAS 저장 후 NAS `file_url`을 `image_url`로 우선 사용
- analyze API는 `quality_inspections` 테이블에 바로 insert하지 않음

요청 예시:

```json
{
  "procurement_item_id": 1,
  "image_url": "https://example.com/sample.jpg",
  "persist_image": false
}
```

multipart 사용 시:

```text
procurement_item_id: 1
image: apple_test.jpg
persist_image: false
```

응답 주요 필드:

```text
image_persisted
model_grade
freshness_score
color_score
roundness_score
bruise_probability
model_decision
action_required
angle_label
angle_confidence
grade_confidence
view_confidence_threshold
grade_confidence_threshold
retake_reason
model_version
image_quality
```

프론트 / 앱 분기 기준:

```text
action_required = RETAKE
→ 재촬영 안내

action_required = OWNER_REVIEW
→ 점주 확인 화면 표시

model_decision = PASS
→ 통과 결과 표시

model_decision = HOLD 또는 REVIEW
→ 점주 확인 필요
```

최종 저장 API:

```text
POST /api/v1/owner/quality-inspections
```

저장 예시:

```json
{
  "procurement_item_id": 1,
  "image_url": "https://example.com/sample.jpg",
  "model_grade": "A",
  "freshness_score": 91.2,
  "color_score": 88.0,
  "roundness_score": 93.5,
  "bruise_probability": 0.06,
  "model_decision": "PASS",
  "owner_decision": "PASS",
  "owner_memo": "분석 결과 확인 후 점주가 최종 승인"
}
```

Swagger 테스트 기준 analyze 응답 예시:

```json
{
  "data": {
    "procurement_item_id": 1,
    "image_persisted": false,
    "fruit_type": "apple",
    "image_url": "https://example.com/sample.jpg",
    "model_grade": "A",
    "freshness_score": 91.2,
    "color_score": 88,
    "roundness_score": 93.5,
    "bruise_probability": 0.06,
    "model_decision": "PASS",
    "action_required": "OWNER_REVIEW",
    "angle_label": "top",
    "angle_confidence": 0.92,
    "grade_confidence": 0.74,
    "view_confidence_threshold": 0.6,
    "grade_confidence_threshold": 0.55,
    "retake_reason": null,
    "model_version": "mock-dl-v1",
    "image_quality": {}
  },
  "message": "quality analysis completed",
  "error": null
}
```

Swagger 테스트 기준 최종 저장 응답 예시:

```json
{
  "data": {
    "quality_inspection_id": 4,
    "procurement_item_id": 1,
    "procurement_id": 1,
    "procurement_no": "PRC-DEMO-001",
    "order_id": 1,
    "order_no": "ORD-DEMO-001",
    "farm_name": "Harvest Demo Farm",
    "product_id": 1,
    "product_name": "예약 사과 5kg",
    "owner_id": 1,
    "image_url": "https://example.com/sample.jpg",
    "model_grade": "A",
    "freshness_score": 91.2,
    "color_score": 88,
    "roundness_score": 93.5,
    "bruise_probability": 0.06,
    "model_decision": "PASS",
    "owner_confirmed_grade": null,
    "owner_decision": "PASS",
    "model_version": "mock-dl-v1"
  },
  "message": "success",
  "error": null
}
```

## 프론트/웹/앱 팀원 연동 가이드

### 서버 주소 안내

백엔드 서버는 실행하는 사람의 PC IP에 따라 주소가 달라집니다. baseUrl은 반드시 `/api/v1`까지 포함해야 합니다.

```text
Swagger:
http://<서버_PC_IP>:8000/docs

API Base URL:
http://<서버_PC_IP>:8000/api/v1
```

주의:

- `<서버_PC_IP>`는 서버를 실행하는 사람의 IPv4 주소
- 학원 / 집 / 와이파이에 따라 IP가 바뀔 수 있음
- `127.0.0.1`은 자기 PC 기준이라 팀원 PC / 휴대폰에서는 접속 불가

### 인증 방식

프론트 / 앱은 로그인 후 `access_token`을 저장합니다.

이후 인증이 필요한 API에는 아래 헤더를 붙입니다.

```text
Authorization: Bearer <access_token>
```

주의:

- CUSTOMER 화면은 CUSTOMER 토큰 사용
- OWNER 화면은 OWNER 토큰 사용
- OWNER API에 CUSTOMER 토큰으로 요청하면 403
- 프론트 / 앱 일반 로그인은 `/api/v1/auth/login` JSON body 사용
- Swagger Authorize는 `/api/v1/auth/token` 기준 사용 가능

### 공통 응답 파싱

모든 API 응답은 기본적으로 아래 구조를 따릅니다.

```json
{
  "data": {},
  "message": "success",
  "error": null
}
```

프론트 / 앱 파싱 기준:

- 실제 데이터는 `json["data"]`에서 꺼냅니다.
- 성공 / 실패 메시지는 `message`를 확인합니다.
- 에러 상세는 `error`를 확인합니다.

### 자주 나오는 HTTP 상태 코드

```text
200 / 201
정상 처리

400
비즈니스 규칙 위반
예: 이미 처리된 반품, 잘못된 요청

401
토큰 없음 또는 만료

403
권한 문제
예: CUSTOMER 토큰으로 OWNER API 호출

404
데이터 없음
예: 존재하지 않는 product_id, procurement_item_id

422
요청 필드명 오류 또는 필수값 누락

500
백엔드 수정 필요

502
외부 NAS 또는 DL API 응답 오류

504
외부 NAS 또는 DL API timeout
```

### 웹팀 CUSTOMER 연동 흐름

웹팀은 CUSTOMER 토큰 기준으로 아래 흐름을 우선 연동합니다.

```text
1. POST /api/v1/auth/login
2. GET /api/v1/me
3. GET /api/v1/products
4. GET /api/v1/products/{product_id}
5. GET /api/v1/products/{product_id}/slots
6. POST /api/v1/reservations
7. GET /api/v1/me/reservations
8. POST /api/v1/orders/from-reservation
9. POST /api/v1/payments/mock-approve
10. GET /api/v1/me/orders
11. GET /api/v1/me/orders/{order_id}
12. GET /api/v1/me/orders/{order_id}/shipment
13. POST /api/v1/returns
14. GET /api/v1/me/returns
```

설명:

- 웹팀은 CUSTOMER 토큰 기준으로 연동합니다.
- 주문 / 결제는 실제 PG가 아니라 mock 결제 API를 사용합니다.
- 반품 요청은 배송 완료 이후 테스트하는 것이 자연스럽습니다.

### 앱팀 OWNER 연동 흐름

앱팀은 OWNER 토큰 기준으로 아래 흐름을 우선 연동합니다.

```text
1. POST /api/v1/auth/login
2. GET /api/v1/me
3. GET /api/v1/owner/dashboard
4. GET /api/v1/owner/farms/me
5. GET /api/v1/owner/products
6. POST /api/v1/owner/products
7. POST /api/v1/owner/products/{product_id}/image
8. GET /api/v1/owner/procurements
9. PATCH /api/v1/owner/procurements/{procurement_id}/decision
10. POST /api/v1/owner/quality-inspections/analyze
11. POST /api/v1/owner/quality-inspections
12. POST /api/v1/owner/shipments
13. PATCH /api/v1/owner/shipments/{shipment_id}/status
14. GET /api/v1/owner/returns
15. PATCH /api/v1/owner/returns/{return_request_id}/decision
```

설명:

- 앱팀은 OWNER 토큰 기준으로 연동합니다.
- 발주 승인 후 품질검사 / 배송 등록 흐름으로 진행합니다.
- 신선도 검사 analyze는 분석 전용이고, 최종 저장은 별도 API로 진행합니다.

### 신선도 검사 연동 요약

분석 API:

```text
POST /api/v1/owner/quality-inspections/analyze
```

핵심:

- 분석 전용 API
- 기본적으로 DB 저장 안 함
- 기본적으로 NAS 저장 안 함
- `persist_image=false`가 기본값
- `DL_QUALITY_ENABLED=false`이면 `mock-dl-v1` 결과 반환
- 점주가 최종 확인한 결과는 `POST /api/v1/owner/quality-inspections`로 저장

### 이미지 / NAS 연동 요약

상품 이미지:

```text
POST /api/v1/owner/products/{product_id}/image
```

신선도 검사 이미지 저장 전용:

```text
POST /api/v1/owner/quality-inspections/image
```

일반 이미지 CRUD:

```text
POST /api/v1/images/upload
GET /api/v1/images
GET /api/v1/images/{file_name}
PUT /api/v1/images/{file_name}
DELETE /api/v1/images/{file_name}
```

주의:

- 이미지 업로드 / 수정 / 삭제는 실제 NAS에 영향을 줄 수 있습니다.
- `persist_image=true`도 NAS 저장을 발생시킬 수 있습니다.
- `saved_path`, `file_path` 같은 내부 경로는 프론트 응답에 노출하지 않습니다.

### 팀원이 자주 실수할 부분

```text
1. baseUrl에 /api/v1을 빼먹는 경우
2. 127.0.0.1을 팀원 PC/휴대폰에서 사용하는 경우
3. Authorization Bearer 토큰을 안 붙이는 경우
4. CUSTOMER 토큰으로 OWNER API를 호출하는 경우
5. Swagger의 필드명과 다른 이름으로 요청하는 경우
6. multipart 파일 필드명을 잘못 보내는 경우
7. quality analyze 결과를 저장된 데이터로 착각하는 경우
8. persist_image=true가 NAS 저장을 발생시킨다는 점을 모르는 경우
9. image_url에서 NAS 저장 URL과 DL 임시 URL을 구분하지 않는 경우
10. 422 에러를 백엔드 오류로 착각하는 경우
```

### 프론트 / 앱 연동 핵심 요약

```text
- Base URL은 http://<서버_PC_IP>:8000/api/v1
- 로그인 후 access_token을 저장하고 Authorization: Bearer <token> 헤더를 붙입니다.
- CUSTOMER 화면은 CUSTOMER 토큰, OWNER 화면은 OWNER 토큰을 사용합니다.
- 응답 데이터는 json["data"] 기준으로 파싱합니다.
- 신선도 검사 analyze는 분석 전용이며 기본적으로 DB/NAS에 저장하지 않습니다.
- 점주가 최종 확인한 뒤 POST /api/v1/owner/quality-inspections로 저장합니다.
- 상품 이미지는 NAS 저장 대상이며 POST /api/v1/owner/products/{product_id}/image를 사용합니다.
- Swagger가 실제 API 계약 기준이므로 README와 함께 확인합니다.
```

## Swagger 확인 체크리스트

인증:

```text
POST /api/v1/auth/login
POST /api/v1/auth/token
GET /api/v1/me
```

이메일:

```text
POST /api/v1/auth/email/send
POST /api/v1/auth/email/verify
GET /api/v1/auth/email/status
```

상품 / 예약 / 주문:

```text
GET /api/v1/products
GET /api/v1/products/{product_id}
GET /api/v1/products/{product_id}/slots
POST /api/v1/reservations
GET /api/v1/me/reservations
POST /api/v1/orders/from-reservation
GET /api/v1/me/orders
GET /api/v1/me/orders/{order_id}
POST /api/v1/payments/mock-approve
```

발주 / 품질검사 / 배송 / 반품:

```text
GET /api/v1/owner/procurements
PATCH /api/v1/owner/procurements/{procurement_id}/decision
POST /api/v1/owner/quality-inspections/analyze
POST /api/v1/owner/quality-inspections
POST /api/v1/owner/quality-inspections/image
POST /api/v1/owner/shipments
PATCH /api/v1/owner/shipments/{shipment_id}/status
GET /api/v1/owner/returns
PATCH /api/v1/owner/returns/{return_request_id}/decision
```

이미지:

```text
POST /api/v1/owner/products/{product_id}/image
POST /api/v1/images/upload
GET /api/v1/images
GET /api/v1/images/{file_name}
PUT /api/v1/images/{file_name}
DELETE /api/v1/images/{file_name}
```

Harvest Slot 백엔드는 과수농가 수확 예약·직배송 플랫폼을 위한 FastAPI + MySQL 기반 API 서버입니다.  
고객 웹은 상품 조회, 예약, 주문, 결제, 배송 조회, 반품을 사용하고, 점주 앱은 상품/수확 슬롯 관리, 발주 승인, 신선도 검사, 배송, 반품/환불 처리를 사용합니다.

현재 ML/DL 예측과 품질 판정, 결제는 실제 외부 연동이 아니라 Mock 기반입니다.

## 시스템 구성

```text
CUSTOMER Web
  -> FastAPI Backend (/api/v1)
  -> MySQL

OWNER App
  -> FastAPI Backend (/api/v1)
  -> MySQL

ML / DL / Payment
  -> 현재 Mock 응답 및 Stub 로직 사용
```

## 빠른 시작

### 1. 가상환경 생성

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
CORS_ALLOWED_ORIGINS=*
```

`CORS_ALLOWED_ORIGINS` 예시:

- 전체 허용: `*`
- 로컬 프론트 허용: `http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173`

### 4. 서버 실행

로컬 전용:

```bash
uvicorn backend.app.main:app --reload
```

다른 팀원이 내 PC 서버에 접속해야 할 때:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 주요 주소

- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health: `http://127.0.0.1:8000/api/v1/health`
- API Prefix: `/api/v1`

## 팀원 접속 방법

- 같은 PC에서 테스트할 때는 `127.0.0.1` 또는 `localhost`를 사용합니다.
- 다른 팀원이 내 PC 서버에 접속할 때는 `127.0.0.1`이 아니라 내 PC의 IP를 사용해야 합니다.
- 예: 내 PC IP가 `192.168.0.15`면 Swagger 주소는 `http://192.168.0.15:8000/docs` 입니다.
- 외부 접속 테스트는 반드시 `--host 0.0.0.0`로 실행합니다.

## 테스트 계정 및 인증

| 역할 | 이메일 | 비밀번호 |
|---|---|---|
| CUSTOMER | `customer@test.com` | `demo1234!` |
| OWNER | `owner@test.com` | `demo1234!` |

인증 규칙:

- 인증이 필요한 API는 `Authorization: Bearer <token>` 헤더가 필요합니다.
- CUSTOMER API는 CUSTOMER 토큰으로 호출해야 합니다.
- OWNER API는 OWNER 토큰으로 호출해야 합니다.
- 권한이 맞지 않으면 `403 forbidden`이 반환됩니다.

Swagger Authorize 사용 방법:

1. Swagger 상단 `Authorize` 클릭
2. `username`에 이메일 입력
3. `password`에 비밀번호 입력
4. Bearer Token 발급 후 인증 API 호출

참고:

- 앱/웹 로그인 API: `POST /api/v1/auth/login`
- Swagger OAuth2 Authorize API: `POST /api/v1/auth/token`

## 공통 응답 형식

대부분의 API는 아래 구조를 사용합니다.

```json
{
  "data": {},
  "message": "success",
  "error": null
}
```

예외:

- `POST /api/v1/auth/token`은 OAuth2 표준 응답인 `{ "access_token": "...", "token_type": "bearer" }` 형태입니다.

## 이번 보강 사항

이번 정리에서 기존 엔드포인트와 요청 필드명은 유지하면서 아래 항목을 보강했습니다.

- 목록/상세 응답에 화면 표시용 필드 추가
- Swagger Request Body 예시 추가
- `403 forbidden`, `422 validation failed`, `400 database integrity error` 등 에러 응답 정리
- CORS 허용 origin을 `.env` 기반으로 관리
- 시드 데이터 확대
- 프론트/앱 연동 테스트 케이스 추가
- 이메일 인증 API 및 SMTP/개발 모드 지원 추가

## 이메일 인증 API

이메일 인증 화면이 아직 프론트/앱에 확정되지 않았더라도, 백엔드 API는 미리 준비되어 있습니다.

핵심 동작:

- `EMAIL_VERIFICATION_REQUIRED=false`이면 기존 회원가입 흐름은 그대로 유지됩니다.
- `EMAIL_VERIFICATION_REQUIRED=true`이면 회원가입 전에 `SIGNUP` 이메일 인증이 완료되어야 합니다.
- `EMAIL_DEV_MODE=true`이면 실제 메일 발송 없이 응답 `data.dev_code`로 인증번호를 확인할 수 있습니다.
- 운영 모드에서는 `EMAIL_DEV_MODE=false`로 두고 `dev_code`를 절대 노출하지 않습니다.
- SMTP 설정은 `.env`에서 관리합니다.

추가된 API:

- `POST /api/v1/auth/email/send`
- `POST /api/v1/auth/email/verify`
- `GET /api/v1/auth/email/status`

프론트 적용 시 호출 순서:

1. `POST /api/v1/auth/email/send`
2. 사용자가 이메일에서 인증번호 확인
3. `POST /api/v1/auth/email/verify`
4. 회원가입 또는 로그인 진행

## 보강된 응답 필드

아래 API들은 기존 필드에 더해 화면 표시용 필드가 추가되었습니다.

### CUSTOMER API

| API | 추가/보강된 대표 필드 |
|---|---|
| `GET /api/v1/products` | `farm_name`, `farm_region`, `farm_image_url`, `open_slot_count`, `min_open_slot_price` |
| `GET /api/v1/products/{product_id}` | `farm`, `farm_name`, `farm_region`, `farm_image_url` |
| `GET /api/v1/products/{product_id}/slots` | `farm_name`, `product_name`, `image_url`, `package_unit_kg`, `available_kg` |
| `GET /api/v1/me/reservations` | `customer_name`, `order_id`, `order_no`, `order_status`, item별 `product_name`, `farm_name`, `image_url` |
| `GET /api/v1/me/orders` | `reservation_no`, `customer_name`, `payment_status`, `shipment_status`, `return_status`, `refund_status`, item별 `product_name`, `farm_name`, `image_url` |
| `GET /api/v1/me/orders/{order_id}` | `payments`, `procurement`, `shipment`, `return_request`, `refund`, `reservation_no`, `tracking_no`, `refund_status` |
| `GET /api/v1/me/returns` | `order_no`, `reservation_no`, `customer_name`, `order_status`, `shipment_status`, `total_amount`, `refund_status`, item별 `product_name`, `image_url` |

### OWNER API

| API | 추가/보강된 대표 필드 |
|---|---|
| `GET /api/v1/owner/dashboard` | `owner_id`, `owner_name` |
| `GET /api/v1/owner/products` | `farm_name`, `farm_region`, `farm_image_url`, `open_slot_count`, `min_open_slot_price` |
| `GET /api/v1/owner/harvest-slots` | `farm_name`, `product_name`, `image_url`, `package_unit_kg`, `available_kg` |
| `GET /api/v1/owner/orders` | `reservation_no`, `customer_name`, `shipment_status`, `return_status`, `refund_status`, item별 `product_name`, `farm_name` |
| `GET /api/v1/owner/procurements` | `order_no`, `reservation_no`, `customer_name`, `farm_name`, `order_status`, `shipment_status`, `return_status`, `total_amount`, item별 `product_name`, `image_url`, `approved_kg` |
| `GET /api/v1/owner/quality-inspections` | `procurement_no`, `order_no`, `farm_name`, `product_name` |
| `GET /api/v1/owner/returns` | `order_no`, `reservation_no`, `customer_name`, `order_status`, `shipment_status`, `refund_status`, `total_amount`, item별 `product_name`, `image_url` |

## Swagger에서 바로 복사 가능한 요청 예시

아래 API들은 Request Body 예시가 Swagger에 보이도록 정리되어 있습니다.

- `POST /api/v1/reservations`
- `POST /api/v1/orders/from-reservation`
- `POST /api/v1/payments/mock-approve`
- `PATCH /api/v1/owner/procurements/{procurement_id}/decision`
- `POST /api/v1/owner/quality-inspections`
- `POST /api/v1/owner/shipments`
- `PATCH /api/v1/owner/shipments/{shipment_id}/status`
- `POST /api/v1/returns`
- `PATCH /api/v1/owner/returns/{return_request_id}/decision`

## 사용자 웹팀 연동 API

| Method | Path | 화면/기능 |
|---|---|---|
| POST | `/api/v1/auth/login` | 로그인 화면 |
| GET | `/api/v1/me` | 로그인 후 내 정보 확인 |
| GET | `/api/v1/products` | 상품 목록 화면 |
| GET | `/api/v1/products/{product_id}` | 상품 상세 화면 |
| GET | `/api/v1/products/{product_id}/slots` | 상품 상세 내 예약 가능 슬롯 |
| POST | `/api/v1/reservations/preview` | 예약 전 금액/중량 미리보기 |
| POST | `/api/v1/reservations` | 예약하기 버튼 |
| GET | `/api/v1/me/reservations` | 내 예약 목록 |
| POST | `/api/v1/orders/from-reservation` | 예약을 주문으로 전환 |
| GET | `/api/v1/me/orders` | 주문 목록 |
| GET | `/api/v1/me/orders/{order_id}` | 주문 상세 |
| POST | `/api/v1/payments/mock-approve` | 결제 완료 Mock 처리 |
| GET | `/api/v1/me/orders/{order_id}/shipment` | 배송 조회 |
| POST | `/api/v1/returns` | 반품 요청 |
| GET | `/api/v1/me/returns` | 반품 내역 |

## 점주 앱팀 연동 API

| Method | Path | 화면/기능 |
|---|---|---|
| POST | `/api/v1/auth/login` | 로그인 화면 |
| GET | `/api/v1/me` | 로그인 후 내 정보 확인 |
| GET | `/api/v1/owner/dashboard` | 대시보드 |
| GET | `/api/v1/owner/farms/me` | 내 농가 조회 |
| PUT | `/api/v1/owner/farms/{farm_id}` | 농가 수정 |
| GET | `/api/v1/owner/products` | 상품 목록 |
| POST | `/api/v1/owner/products` | 상품 등록 |
| GET | `/api/v1/owner/ml/predictions` | 수확 예측 이력 |
| POST | `/api/v1/owner/ml/predictions` | 수확 예측 실행 |
| GET | `/api/v1/owner/harvest-slots` | 수확 슬롯 목록 |
| POST | `/api/v1/owner/harvest-slots` | 수확 슬롯 생성 |
| PUT | `/api/v1/owner/harvest-slots/{slot_id}` | 수확 슬롯 수정 |
| PATCH | `/api/v1/owner/harvest-slots/{slot_id}/status` | 슬롯 상태 변경 |
| GET | `/api/v1/owner/orders` | 주문 목록 |
| GET | `/api/v1/owner/procurements` | 발주 목록 |
| PATCH | `/api/v1/owner/procurements/{procurement_id}/decision` | 발주 승인/거절 |
| POST | `/api/v1/owner/quality-inspections` | 신선도 검사 등록 |
| GET | `/api/v1/owner/quality-inspections` | 신선도 검사 이력 |
| POST | `/api/v1/owner/shipments` | 배송 등록 |
| PATCH | `/api/v1/owner/shipments/{shipment_id}/status` | 배송 상태 변경 |
| GET | `/api/v1/owner/returns` | 반품 요청 목록 |
| PATCH | `/api/v1/owner/returns/{return_request_id}/decision` | 반품 승인/거절 및 환불 |

## 핵심 E2E 테스트 흐름

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

### 배송 등록

- `tracking_number`가 아니라 `tracking_no`
- `shipped_package_count`, `shipped_kg` 필수
- `POST /api/v1/owner/shipments`에는 `shipment_status`를 보내지 않음

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

- `return_reason`이 아니라 `reason_code`
- `requested_amount` 필수
- 상세 사유는 `return_detail`이 아니라 `reason_detail`

```json
{
  "order_id": 1,
  "reason_code": "QUALITY_ISSUE",
  "requested_amount": 78000,
  "reason_detail": "상품 품질 문제로 반품 요청합니다."
}
```

### 신선도 검사

- `image_url` 필수
- 서버가 `model_grade`, `freshness_score`, `color_score`, `roundness_score`, `bruise_probability`, `model_decision`을 Mock 값으로 채움

```json
{
  "procurement_item_id": 1,
  "image_url": "/mock/quality/apple_sample_001.jpg",
  "owner_confirmed_grade": "A",
  "owner_decision": "PASS"
}
```

### Mock 결제 승인

```json
{
  "order_id": 1,
  "idempotency_key": "payment-order-1-try-1"
}
```

## 상태값 정리

### reservation_status

- `RESERVED`
- `ORDERED`
- `EXPIRED`
- `CANCELED`

### order_status

- `PAYMENT_PENDING`
- `PAID`
- `PROCUREMENT_REQUESTED`
- `PROCUREMENT_APPROVED`
- `PROCUREMENT_PARTIAL_APPROVED`
- `PROCUREMENT_REJECTED`
- `QUALITY_CHECKING`
- `READY_TO_SHIP`
- `SHIPPED`
- `DELIVERED`
- `RETURN_REQUESTED`
- `REFUNDED`
- `CANCELED`

### procurement_status

- `REQUESTED`
- `APPROVED`
- `PARTIAL_APPROVED`
- `REJECTED`

주의:

- 실제 코드 값은 `PARTIAL_APPROVED`
- `PARTIALLY_APPROVED` 아님

### shipment_status

- `READY`
- `SHIPPED`
- `DELIVERED`

### return_status

- `REQUESTED`
- `APPROVED`
- `REJECTED`
- `REFUNDED`

### refund_status

- `REQUESTED`
- `COMPLETED`
- `FAILED`

### payment_status

- `REQUESTED`
- `APPROVED`
- `FAILED`
- `CANCELED`
- `REFUNDED`

## 프론트/앱 연동 시 주의사항

- CUSTOMER API는 CUSTOMER 토큰으로 호출
- OWNER API는 OWNER 토큰으로 호출
- 권한이 다르면 `403 forbidden`
- `422 validation failed`는 요청 Body 누락/타입 오류/필드명 오타 가능성이 큼
- `400`은 비즈니스 규칙 위반
  예: `shipment already exists for order`, `return request already exists`, `return request already decided`
- `404`는 대상 데이터 없음
- `500`은 백엔드 수정 대상

## 시드 데이터

`python scripts/seed_demo_data.py`

현재 시드에는 아래 연동용 데이터가 포함되도록 정리되어 있습니다.

- CUSTOMER 테스트 계정
- OWNER 테스트 계정
- 농장 2개
- 상품 5개 이상
- OPEN 상태 harvest slot 여러 개
- 발주 대기 주문
- 배송 완료 주문
- 환불 완료 주문

가능한 한 아래 기준으로 중복 누적을 줄이도록 구성했습니다.

- `email`
- `farm_name`
- `product_name`
- `reservation_no`
- `order_no`
- `procurement_no`
- `idempotency_key`
- `return_no`

## 테스트

전체 테스트:

```bash
pytest tests -q
```

Live API 테스트:

- `tests/test_live_e2e_api.py`는 `TestClient`가 아니라 실제 실행 중인 FastAPI 서버에 HTTP 요청을 보냅니다.
- 이 테스트를 실행하기 전에 `uvicorn` 서버가 먼저 켜져 있어야 합니다.
- 이 테스트는 실제 DB에 예약/주문/결제/배송/반품 데이터를 생성합니다.

터미널 1:

```bash
uvicorn backend.app.main:app --reload
```

터미널 2 PowerShell:

```powershell
$env:BASE_URL="http://127.0.0.1:8000/api/v1"
pytest -v tests/test_live_e2e_api.py
```

기본 `BASE_URL`은 아래 값입니다.

```text
http://127.0.0.1:8000/api/v1
```

현재 포함된 주요 테스트:

- health check
- customer login
- owner login
- reservation create/list
- order create
- mock payment approve
- owner procurement decision
- return duplicate decision returns 400
- owner API with customer token returns 403
- live server HTTP E2E flow

## 참고 문서 레포

- `smart_docs`: `https://github.com/AI-MegaStudy/smart_docs.git`
- 백엔드 작업 시 참고 문서 기준: `../smart_docs/00_harvest_slot_docs_v3_2`
- `smart_docs`는 참고용 문서 레포입니다.
- 실제 백엔드 코드 수정은 현재 레포에서만 진행합니다.

## 팀 협업 안내

- 프론트/앱 팀원은 먼저 Swagger에서 실제 응답을 확인한 뒤 화면에 연동합니다.
- 필요한 응답 필드가 부족하면 백엔드 담당자에게 요청합니다.
- 요청 Body가 헷갈리면 Swagger Schema를 가장 먼저 확인합니다.
- `.env` 파일은 공유하거나 GitHub에 올리지 않습니다.
- NAS MySQL을 같이 쓰는 경우 테스트 데이터 ID는 계속 증가할 수 있습니다.

## 팀원이 먼저 볼 위치

1. `http://127.0.0.1:8000/docs`
2. 이 README의 `보강된 응답 필드`
3. 이 README의 `Swagger에서 바로 복사 가능한 요청 예시`
4. 이 README의 `핵심 E2E 테스트 흐름`
5. 이 README의 `시드 데이터`
## Image Upload API

기존 API URL과 JSON 요청 필드는 유지하고, 이미지 업로드만 별도 API로 추가했습니다.

- `POST /api/v1/owner/products/{product_id}/image`
  - `multipart/form-data`
  - 필수 필드: `file`
  - 업로드 성공 시 `products.image_url`이 바로 갱신됩니다.
- `POST /api/v1/owner/quality-inspections/image`
  - `multipart/form-data`
  - 필수 필드: `file`
  - 업로드 성공 시 `image_url`만 반환합니다.

기존 신선도 검사 저장 API는 그대로 유지됩니다.

1. `POST /api/v1/owner/quality-inspections/image`
2. 응답의 `image_url` 확인
3. `POST /api/v1/owner/quality-inspections`의 `image_url`에 그대로 넣어 저장

예시 응답 필드:

```json
{
  "data": {
    "image_url": "https://.../images/quality-inspections/1/sample.jpg",
    "file_name": "sample.jpg",
    "subfolder": "quality-inspections/1"
  },
  "message": "success",
  "error": null
}
```

참고:

- NAS 업로드 동작은 `docs/upload_image_usage.md`를 참고합니다.
- 이 문서는 참고용이며 수정 대상이 아닙니다.

## Quality Analyze API

신선도 분석은 현재 `mock-dl-v1` 기준으로 동작합니다. 아직 실제 DL 모델 파일 import나 `torch` 의존성은 추가하지 않았고, 실제 외부 DL 연동 방식도 확정 전입니다.

- `POST /api/v1/owner/quality-inspections/analyze`
- 필수값: `procurement_item_id`
- 입력 방식: JSON 또는 `multipart/form-data`
- 기본 동작: `persist_image=false`
- `persist_image=false`이면 NAS 저장 없이 분석만 수행
- `persist_image=true`이면 업로드한 이미지 파일을 NAS에 저장한 뒤 `image_url`을 분석 결과에 포함
- `DL_QUALITY_ENABLED=false`이면 외부 DL API를 호출하지 않고 mock 분석 결과를 반환
- `DL_QUALITY_ENABLED=true` 이고 `DL_QUALITY_API_URL`이 설정되면 외부 DL API 호출 구조로 확장 가능
- 외부 DL API로 파일을 보낼 때 multipart field name은 반드시 `image`

JSON 예시:

```json
{
  "procurement_item_id": 1,
  "image_url": "https://cdn.example.com/quality/apple_001.jpg",
  "persist_image": false
}
```

`multipart/form-data` 예시:

- `procurement_item_id`: `1`
- `persist_image`: `true` 또는 `false`
- `image`: 업로드 파일

응답 예시:

```json
{
  "data": {
    "procurement_item_id": 1,
    "image_persisted": false,
    "image_url": "https://cdn.example.com/quality/apple_001.jpg",
    "action_required": "OWNER_REVIEW",
    "model_grade": "A",
    "freshness_score": 91.2,
    "color_score": 88.0,
    "roundness_score": 93.5,
    "bruise_probability": 0.06,
    "model_decision": "PASS",
    "model_version": "mock-dl-v1"
  },
  "message": "quality analysis completed",
  "error": null
}
```

## DL Integration

현재 DL 연동 방식은 백엔드가 PyTorch 모델을 직접 실행하는 방식이 아니라, 외부 DL FastAPI를 호출하는 방식입니다.

구조:

```text
OWNER App / Backend
  -> DL_QUALITY_API_URL
  -> Kaggle Notebook FastAPI
  -> PyTorch model inference
  -> JSON response
```

현재 모델 범위:

- 사과 전용
- `smart_dl` 기준 최신 모델 폴더: `models/apple_balanced`
- 모델 파일:
  - `apple_view_top_middle_side_balanced_resnet18_best.pt`
  - `apple_top_grade_resnet18_best.pt`
  - `apple_middle_grade_resnet18_best.pt`
  - `apple_side_grade_resnet18_best.pt`

현재 연동 방식:

- Kaggle Notebook에서 FastAPI 실행
- ngrok public URL 생성
- 백엔드가 `DL_QUALITY_API_URL`로 `multipart/form-data` 요청 전송
- 파일 필드명은 `image`

DL API endpoint 예:

```text
https://xxxx.ngrok-free.app/owner/quality-inspections
```

`.env` 설정 예:

```env
DL_QUALITY_ENABLED=true
DL_QUALITY_API_URL=https://xxxx.ngrok-free.app/owner/quality-inspections
DL_QUALITY_TIMEOUT_SECONDS=60
```

주의:

- `DL_QUALITY_ENABLED=false`가 기본값이며, 이때는 `mock-dl-v1` 분석 결과를 사용합니다.
- 백엔드는 `torch`, `torchvision`, 모델 파일을 import하지 않습니다.
- `DL_QUALITY_API_URL`은 전체 endpoint URL로 넣어야 합니다.
- 코드에서 `/owner/quality-inspections`를 다시 붙이지 않습니다.
- DL API가 `/tmp`, `/kaggle/working/uploads` 같은 임시 경로 `image_url`을 반환하더라도 백엔드 DB 저장용 이미지 URL로 쓰지 않습니다.
- Kaggle Notebook 실행 중이어야 합니다.
- FastAPI 서버 셀이 실행 중이어야 합니다.
- ngrok tunnel 셀이 실행 중이어야 합니다.
- Kaggle 세션이 종료되면 URL이 끊깁니다.
- ngrok 무료 URL은 매번 바뀔 수 있습니다.
- 실제 DL 연동 테스트는 live test로 분리합니다.

## Test Modes

기본 테스트:

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -v tests
```

- 기본 테스트는 `TestClient`와 mock/monkeypatch 기반으로 동작합니다.
- 실제 SMTP 발송, 실제 NAS 업로드, 실제 외부 DL 서버에 의존하지 않습니다.

Live 서버 E2E 테스트:

```powershell
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.app.main:app --reload
$env:RUN_LIVE_API_TESTS="true"
$env:BASE_URL="http://127.0.0.1:8000/api/v1"
pytest -v tests/test_live_e2e_api.py
```

Live 이미지 업로드 테스트:

```powershell
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.app.main:app --reload
$env:RUN_LIVE_IMAGE_TESTS="true"
$env:BASE_URL="http://127.0.0.1:8000/api/v1"
pytest -v tests/test_live_image_api.py
```

Live DL 테스트:

```powershell
$env:RUN_LIVE_DL_TESTS="true"
$env:DL_QUALITY_ENABLED="true"
$env:DL_QUALITY_API_URL="https://xxxx.ngrok-free.app/owner/quality-inspections"
pytest -v tests/test_live_dl_quality_api.py
```

주의:

- live 테스트는 실제 서버와 외부 NAS 업로드 API, 외부 DL API를 호출할 수 있습니다.
- live 테스트는 DB 데이터를 생성하거나 상품 이미지 URL을 갱신할 수 있습니다.

## Swagger Checkpoints

이미지 업로드 추가 후 아래 API를 Swagger에서 같이 확인합니다.

- `POST /api/v1/images/upload`
- `GET /api/v1/images`
- `GET /api/v1/images/{file_name}`
- `PUT /api/v1/images/{file_name}`
- `DELETE /api/v1/images/{file_name}`
- `POST /api/v1/owner/products/{product_id}/image`
- `POST /api/v1/owner/quality-inspections/analyze`
- `POST /api/v1/owner/quality-inspections/image`
- `POST /api/v1/owner/quality-inspections`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/email/send`
- `POST /api/v1/auth/email/verify`
- `GET /api/v1/products`
- `GET /api/v1/me/orders/{order_id}`
- `PATCH /api/v1/owner/returns/{return_request_id}/decision`

확인 기준:

- `multipart/form-data`에서 `file` 또는 `image` 필드가 보이는지
- `persist_image` 기본값이 `false`로 보이는지
- 기존 auth, products, reservations, orders, returns API가 그대로 남아 있는지
- 기존 Request Body example이 유지되는지

## Image CRUD Policy

이미지 처리 정책은 아래 기준으로 정리합니다.

- 상품 이미지는 NAS 저장 대상입니다.
- 일반 이미지 CRUD는 `/api/v1/images`를 사용합니다.
- `POST /api/v1/owner/quality-inspections/analyze`는 기본적으로 NAS에 저장하지 않습니다.
- `persist_image=true`일 때만 analyze API에서 NAS 저장이 발생합니다.
- `POST /api/v1/owner/quality-inspections/image`는 저장 전용 API입니다. 이 API를 호출하면 NAS 저장이 발생합니다.
- 기존 `POST /api/v1/owner/quality-inspections` JSON 저장 API는 그대로 유지되며, `image_url`을 직접 넣는 흐름도 계속 사용할 수 있습니다.

관련 환경변수:

- `IMAGE_UPLOAD_URL`
- `IMAGE_UPLOAD_TIMEOUT_SECONDS`
- `IMAGE_DEFAULT_PRODUCT_SUBFOLDER`
- `IMAGE_DEFAULT_QUALITY_SUBFOLDER`
- `IMAGE_ALLOWED_EXTENSIONS`
- `IMAGE_MAX_SIZE_MB`
- `DL_QUALITY_ENABLED`
- `DL_QUALITY_API_URL`
- `DL_QUALITY_TIMEOUT_SECONDS`

일반 이미지 CRUD API:

- `POST /api/v1/images/upload`
- `GET /api/v1/images`
- `GET /api/v1/images/{file_name}`
- `PUT /api/v1/images/{file_name}`
- `DELETE /api/v1/images/{file_name}`

일반 이미지 CRUD 사용 예시:

업로드:

```text
POST /api/v1/images/upload
multipart/form-data
file=<image file>
product_seq=1
subfolder=products/1
```

목록 조회:

```text
GET /api/v1/images?subfolder=products/1
```

단건 조회:

```text
GET /api/v1/images/product_1_apple.jpg?subfolder=products/1
```

수정:

```text
PUT /api/v1/images/product_1_apple.jpg
multipart/form-data
file=<replacement image>
subfolder=products/1
```

삭제:

```text
DELETE /api/v1/images/product_1_apple.jpg?subfolder=products/1
```

## Frontend Flow For Images

상품 이미지:

1. OWNER 로그인
2. `POST /api/v1/owner/products/{product_id}/image`
3. 응답의 `image_url`을 상품 화면에 사용

신선도 검사 분석만:

1. OWNER 로그인
2. `POST /api/v1/owner/quality-inspections/analyze`
3. `Authorization: Bearer <owner_access_token>`
4. `multipart/form-data`로 `procurement_item_id`, `image`, `persist_image=false` 전송
5. `action_required=RETAKE`이면 재촬영 안내
6. `action_required=OWNER_REVIEW`이면 점주 최종 확인 화면 표시
7. 점주 확인 후 `POST /api/v1/owner/quality-inspections`로 저장

신선도 검사 이미지까지 저장:

1. OWNER 로그인
2. `POST /api/v1/owner/quality-inspections/analyze`
3. `Authorization: Bearer <owner_access_token>`
4. `multipart/form-data`로 `procurement_item_id`, `image`, `persist_image=true` 전송
5. 응답의 `image_url`, `file_name`, `subfolder`, 분석 결과를 확인
6. 점주 확인 후 `POST /api/v1/owner/quality-inspections`로 저장

기존 저장 전용 흐름:

1. `POST /api/v1/owner/quality-inspections/image`
2. 응답 `image_url` 확인
3. `POST /api/v1/owner/quality-inspections`의 `image_url`에 그대로 사용

## Run Commands

로컬 Swagger 확인용:

```powershell
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.app.main:app --reload
```

팀원 접속용:

```powershell
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

팀원 접속 주소:

- Swagger: `http://<서버_PC_IP>:8000/docs`
- API Base URL: `http://<서버_PC_IP>:8000/api/v1`

네트워크 안내:

- `127.0.0.1`과 `localhost`는 현재 서버를 띄운 내 PC 기준입니다.
- 다른 팀원 PC나 휴대폰에서는 `127.0.0.1`로 접속할 수 없습니다.
- 반드시 서버 실행 PC의 IPv4 주소를 사용해야 합니다.
- Windows에서는 `ipconfig`를 실행해서 IPv4 주소를 확인할 수 있습니다.
- README에 적힌 `192.168.0.15` 같은 값은 예시일 뿐이고, 실제 팀 환경에서는 각자 PC의 현재 IPv4 주소를 사용하면 됩니다.

환불 완료 후 상태 정합성:

- `GET /api/v1/me/orders/{order_id}`에서 주문 상세를 조회하면 환불 완료 후 `order_status=REFUNDED`로 확인됩니다.
- 같은 응답에서 `payment_status=REFUNDED`, `return_request.return_status=REFUNDED`, `refund.refund_status=COMPLETED` 흐름을 함께 확인할 수 있습니다.
## Login API Notes

- 프론트/앱 로그인은 `POST /api/v1/auth/login`에 JSON body를 보내는 방식입니다.
- Swagger `Try it out`에서도 아래 JSON request body를 바로 입력할 수 있어야 합니다.

```json
{
  "email": "owner@test.com",
  "password": "demo1234!"
}
```

- Swagger 상단 `Authorize`는 OAuth2 흐름 기준으로 `POST /api/v1/auth/token`을 사용합니다.
- 일반 화면 로그인은 `/api/v1/auth/login`, Swagger Bearer 인증 발급은 `/api/v1/auth/token`으로 구분하면 됩니다.
