# Harvest Slot Backend

Harvest Slot Backend는 과수농가 직배송 예약 서비스용 FastAPI 백엔드다. 과수농가가 상품을 등록하고 ML 예측을 참고해 수확 슬롯을 확정한 뒤, 고객이 예약, 주문, Mock 결제, 발주, 신선도 검사, 배송, 반품, 환불까지 이어서 처리할 수 있도록 초기 실무 구조를 제공한다.

## 기술 스택

- Backend: FastAPI
- DB: MySQL
- ORM: SQLAlchemy
- Auth: JWT
- Test: pytest

실제 ML/DL 연동은 이번 범위에서 제외했고, 나중에 `requirements-ai.txt` 로 분리할 수 있도록 Mock/Stub 구조를 남겼다.

## 폴더 구조

```text
backend/
  app/
    core/
    models/
    repositories/
    routers/
    schemas/
    services/
docs/
scripts/
tests/
```

## 주요 업무 흐름

상품 등록
→ ML 예측
→ 수확 슬롯 확정
→ 예약 생성
→ 주문 생성
→ Mock 결제 승인
→ 발주 생성
→ 발주 승인
→ 신선도 검사
→ 배송 등록
→ 반품 요청
→ 환불 처리

## 19개 테이블

- accounts
- customer_profiles
- owner_profiles
- email_verifications
- farms
- products
- ml_predictions
- harvest_slots
- reservations
- reservation_items
- orders
- order_items
- payments
- procurements
- procurement_items
- quality_inspections
- shipments
- return_requests
- refunds

## 실행 방법

`.env.example` 를 복사해서 `.env` 를 만든다.

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

값은 실제 비밀번호 대신 로컬 개발용 값을 직접 입력한다.

Windows 실행:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

macOS/Linux 실행:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

## Swagger / Health Check

- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health Check: `http://127.0.0.1:8000/api/v1/health`
- DB Health Check: `http://127.0.0.1:8000/api/v1/health/db`

## 로컬 스키마/시드

- 테이블 생성: `python scripts/create_tables.py`
- 데모 데이터 생성: `python scripts/seed_demo_data.py`

`create_tables.py` 는 MVP 로컬 테스트용이다. 운영/정식 스키마 적용은 `harvest-slot-docs-local/assets/10_schema_mysql.sql` 을 우선한다.

## 인증 테스트용 토큰

- `Authorization: Bearer mock-customer-token`
- `Authorization: Bearer mock-owner-token`

## 현재 Mock/Stub인 부분

- 이메일 인증 발송
- ML 예측
- DL 신선도 판별
- Mock 결제

## 다음 단계

- 실제 DB 연결 테스트
- 실제 ML 모델 연결
- 실제 DL 모델 연결
- 사용자 웹/점주 앱 연동 테스트
