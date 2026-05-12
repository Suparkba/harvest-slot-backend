# 프론트엔드 연동 가이드

## 연동 방식

### 1. 날씨 피처를 먼저 조회하는 방식

```http
GET /api/v1/weather/features?stn_id=136&target_year=2026
```

날씨 피처를 먼저 화면에 보여주거나 확인이 필요한 경우 이 방식을 사용합니다.

### 2. 기존 ML 예측 API 호출 방식

```http
POST /api/v1/owner/ml/predictions
```

이 방식에서는 클라이언트가 `features` 안에 날씨 피처값을 직접 넣어야 합니다.

### 3. 자동 날씨 ML 예측 API 호출 방식

```http
POST /api/v1/owner/ml/predictions/auto-weather
```

이 방식에서는 클라이언트가 `target_year`와 선택적 `stn_id`만 보내면, 백엔드가 날씨 피처를 자동 생성합니다.

## 웹/앱 담당자가 알아야 할 내용

- 웹/앱은 기상청 API Key를 알 필요가 없습니다.
- 기상청 API 호출은 백엔드 책임입니다.
- OWNER 전용 API는 `Authorization` 헤더가 필요합니다.
- 현재 코드 기준으로 `GET /api/v1/weather/features`는 인증이 필요하지 않습니다.
- 기본 `stn_id`는 안동 `136`입니다.
