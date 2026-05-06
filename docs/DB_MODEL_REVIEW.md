# DB_MODEL_REVIEW

## 19개 모델 생성 체크

- [x] `accounts`
- [x] `customer_profiles`
- [x] `owner_profiles`
- [x] `email_verifications`
- [x] `farms`
- [x] `products`
- [x] `ml_predictions`
- [x] `harvest_slots`
- [x] `reservations`
- [x] `reservation_items`
- [x] `orders`
- [x] `order_items`
- [x] `payments`
- [x] `procurements`
- [x] `procurement_items`
- [x] `quality_inspections`
- [x] `shipments`
- [x] `return_requests`
- [x] `refunds`

## SQL 기준 반영 결과

- 테이블명, 컬럼명, PK/FK/UNIQUE, nullable 기준은 `10_schema_mysql.sql` 을 따라 모델링했다.
- 1:1, 1:N 관계는 `10_관계_카디널리티_전체.md` 기준으로 SQLAlchemy relationship 을 구성했다.
- `harvest_slots.prediction_id` 는 nullable 로 유지했다.
- `orders.reservation_id`, `procurements.order_id`, `shipments.order_id`, `return_requests.order_id`, `refunds.return_request_id`, `refunds.payment_id` 는 UNIQUE 관계로 반영했다.

## 문서와 구현 간 메모

- `OrderStatus.QUALITY_CHECKING`, `OrderStatus.READY_TO_SHIP` 는 업무흐름 문서와 작업 요청에 등장하지만, SQL DDL의 `orders.order_status` CHECK 목록에는 없다.
- 따라서 상수는 `backend/app/core/status.py` 에 남겼지만, 실제 DB 모델 제약 기준은 SQL 우선 원칙에 따라 `orders` 테이블 컬럼 자체에는 별도 enum 제약 확장을 하지 않았다.
- `products.product_status`, `order_items.order_item_status`, `quality_inspections.model_grade`, `email_verifications.purpose` 는 SQL DDL 값 체계를 그대로 유지했다.

## TODO

- MySQL 실 DB에 `assets/10_schema_mysql.sql` 을 적용한 뒤 `create_all` 결과와 차이가 없는지 재검증
- 문서에 없는 추가 상태 전이가 필요한지 API/업무흐름 재확인
- 발표/연동 전 `quality_inspections` 와 `return_requests` 의 실제 입력 필드 확정 여부 점검
