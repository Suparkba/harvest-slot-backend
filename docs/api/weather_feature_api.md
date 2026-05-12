# 날씨 피처 API

## API 목적

이 API는 웹/앱이 날씨 피처값을 직접 계산하지 않아도 백엔드가 기상청 ASOS 데이터를 기준으로 ML용 날씨 피처를 생성할 수 있게 해줍니다.

## API 경로

- Method: `GET`
- Path: `/api/v1/weather/features`

## 쿼리 파라미터

| 필드 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| `stn_id` | string | 아니오 | 관측소 번호, 기본값 `136` |
| `target_year` | integer | 예 | 예측 대상 연도 |

## 기본 관측소

- 안동 ASOS 지점번호 `136`

## 데이터 출처

- 기상청 ASOS 일자료 API

## 생성 피처

- `mar_avg_temp`: 3월 평균기온, `avgTa` 단순 평균
- `aug_sunshine`: 8월 합계 일조시간, `sumSsHr` 단순 합계
- `oct_rainfall`: 10월 누적 강수량, `sumRn` 단순 합계
- `aug_humidity`: 8월 평균습도, `avgRhm` 단순 평균

## fallback 정책

- 대상 월 데이터가 없으면 전년도 데이터를 사용합니다.
- 최대 3년 전까지 fallback을 시도합니다.
- 각 피처는 독립적으로 fallback 됩니다.
- `feature_source_years`로 피처별 실제 사용 연도를 확인할 수 있습니다.

## 2025 정상 응답 예시

```http
GET /api/v1/weather/features?stn_id=136&target_year=2025
```

```json
{
  "data": {
    "target_year": 2025,
    "stn_id": "136",
    "mar_avg_temp": 7.42,
    "aug_sunshine": 238.8,
    "oct_rainfall": 161.6,
    "aug_humidity": 75.58,
    "source": "KMA_ASOS_DAILY_API",
    "fallback_used": false,
    "fallback_year": null,
    "fallback_reason": null,
    "feature_source_years": {
      "mar_avg_temp": 2025,
      "aug_sunshine": 2025,
      "oct_rainfall": 2025,
      "aug_humidity": 2025
    }
  },
  "message": "success",
  "error": null
}
```

## 2026 fallback 응답 예시

```http
GET /api/v1/weather/features?stn_id=136&target_year=2026
```

```json
{
  "data": {
    "target_year": 2026,
    "stn_id": "136",
    "mar_avg_temp": 7.42,
    "aug_sunshine": 238.8,
    "oct_rainfall": 161.6,
    "aug_humidity": 75.58,
    "source": "KMA_ASOS_DAILY_API",
    "fallback_used": true,
    "fallback_year": 2025,
    "fallback_reason": "future_month_or_missing_data",
    "feature_source_years": {
      "mar_avg_temp": 2026,
      "aug_sunshine": 2025,
      "oct_rainfall": 2025,
      "aug_humidity": 2025
    }
  },
  "message": "success",
  "error": null
}
```

## 앱/웹 사용 방법

- 앱/웹은 기상청 API를 직접 호출하지 않고 이 백엔드 API를 호출합니다.
- 앱/웹은 KMA API Key를 알 필요가 없습니다.

## 주의사항

- `KMA_ASOS_SERVICE_KEY`는 `.env`에만 저장해야 합니다.
- `.env`와 실제 API Key는 GitHub에 올리면 안 됩니다.
