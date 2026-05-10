# ML 예측 API 명세서

## 1. API 목적

농가가 입력한 과거 수확량, 시장가, 기상 관련 수치를 바탕으로 예상 수확량과 예약 가능 권장 물량을 조회하는 API입니다.

## 2. 호출 권한

- `OWNER` 계정만 호출할 수 있습니다.
- OWNER 로그인 후 발급받은 `access_token`이 필요합니다.

## 3. 요청 URL

| 구분 | 값 |
| --- | --- |
| 로컬 Base URL | `http://127.0.0.1:8000` |
| Endpoint | `POST /api/v1/owner/ml/predictions` |
| 최종 호출 예 | `http://127.0.0.1:8000/api/v1/owner/ml/predictions` |

## 4. Header

| Header | 값 |
| --- | --- |
| `Authorization` | `Bearer {access_token}` |
| `Content-Type` | `application/json` |

## 5. Request Body

```json
{
  "farm_id": 1,
  "product_id": 1,
  "features": {
    "past_yield_kg": 3000,
    "market_price": 5000,
    "variety": "부사",
    "mar_avg_temp": 8.5,
    "aug_sunshine": 210.0,
    "oct_rainfall": 65.0,
    "aug_humidity": 72.0
  }
}
```

## 6. Request 필드 설명

### 최상위 필드

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `farm_id` | number | 예측 대상 농가 ID |
| `product_id` | number | 예측 대상 상품 ID |
| `features` | object | ML 예측 입력값 묶음 |

### features 필드

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `past_yield_kg` | number | 사용자의 과거 평년 수확량, kg |
| `market_price` | number | 현재 시장가 |
| `variety` | string | 품종명, 예: `부사`, `황옥` |
| `mar_avg_temp` | number | 3월 평균 기온, ℃ |
| `aug_sunshine` | number | 8월 합계 일조시간, hr |
| `oct_rainfall` | number | 10월 누적 강수량, mm |
| `aug_humidity` | number | 8월 평균 상대습도, % |

## 7. Validation 범위

| 필드 | 조건 |
| --- | --- |
| `past_yield_kg` | `0`보다 커야 함 |
| `market_price` | `0`보다 커야 함 |
| `mar_avg_temp` | `-5` 이상 `25` 이하 |
| `aug_sunshine` | `50` 이상 `400` 이하 |
| `oct_rainfall` | `0` 이상 `600` 이하 |
| `aug_humidity` | `30` 이상 `100` 이하 |

## 8. Response Body

```json
{
  "data": {
    "prediction_id": 1,
    "farm_id": 1,
    "product_id": 1,
    "unit_yield_kg_10a": 1509.53,
    "predicted_harvest_start": "2026-06-09",
    "predicted_harvest_end": "2026-06-23",
    "estimated_yield_kg": 3321.5,
    "suggested_reservable_min_kg": 1328.6,
    "suggested_reservable_max_kg": 2491.13,
    "recommended_price": 5500,
    "confidence": 0.78,
    "safety_factor": 0.75,
    "warning_message": "정상",
    "model_version": "rf-apple-harvest-v1"
  },
  "message": "success",
  "error": null
}
```

## 9. Response 필드 설명

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `prediction_id` | number | 예측 결과 ID |
| `farm_id` | number | 농가 ID |
| `product_id` | number | 상품 ID |
| `unit_yield_kg_10a` | number | 모델이 예측한 10a 기준 예상 수확량 |
| `estimated_yield_kg` | number | 과거 수확량과 품종 가중치를 반영한 예상 총 수확량 |
| `suggested_reservable_min_kg` | number | 최소 예약 가능 권장 물량 |
| `suggested_reservable_max_kg` | number | 최대 예약 가능 권장 물량 |
| `recommended_price` | number | 추천 판매가 |
| `predicted_harvest_start` | string | 예상 수확 시작일, `YYYY-MM-DD` |
| `predicted_harvest_end` | string | 예상 수확 종료일, `YYYY-MM-DD` |
| `confidence` | number | 예측 신뢰도 |
| `safety_factor` | number | 안전계수 |
| `warning_message` | string | 경고 또는 상태 메시지 |
| `model_version` | string | 사용된 모델 버전 |

## 10. 에러 응답 예시

### 10-1. Validation 실패 422

예: `aug_humidity = 120`

```json
{
  "data": {},
  "message": "validation failed",
  "error": [
    {
      "type": "less_than_equal",
      "loc": ["body", "features", "aug_humidity"],
      "msg": "Input should be less than or equal to 100",
      "input": 120,
      "ctx": {
        "le": 100.0
      }
    }
  ]
}
```

### 10-2. 인증 실패 401

토큰이 없거나 잘못된 경우

```json
{
  "data": {},
  "message": "authentication required",
  "error": "authentication required"
}
```

### 10-3. 권한 실패 403

CUSTOMER 토큰으로 호출한 경우

```json
{
  "data": {},
  "message": "forbidden",
  "error": "forbidden"
}
```

## 11. Swagger 테스트 방법

1. 서버 실행 후 `http://127.0.0.1:8000/docs` 접속
2. OWNER 계정으로 로그인해서 access token 확보
3. Swagger 우측 상단 `Authorize` 클릭
4. `Bearer {access_token}` 형식으로 토큰 입력
5. `POST /api/v1/owner/ml/predictions` 펼치기
6. 요청 예시 JSON 입력 후 `Execute` 클릭
7. `data` 내부 예측 결과 확인

## 12. 웹/앱 연동 시 주의사항

- `Authorization` 헤더의 `Bearer` 접두사를 빼먹지 않아야 합니다.
- `features` 객체 내부 필드는 모두 보내는 것을 권장합니다.
- 숫자 필드는 문자열로 보내지 말고 number 타입으로 보내는 것이 안전합니다.
- `predicted_harvest_start`, `predicted_harvest_end`는 날짜 문자열이므로 화면 표시 시 포맷팅이 필요할 수 있습니다.
- `estimated_yield_kg`, `suggested_reservable_min_kg`, `suggested_reservable_max_kg`는 소수점이 포함될 수 있습니다.
- `warning_message`는 사용자 안내 문구 영역에 그대로 노출할 수 있습니다.
- `message`, `error`를 함께 확인해서 실패 응답을 분기 처리하세요.

