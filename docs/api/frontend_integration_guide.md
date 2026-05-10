# 프론트 연동 가이드

Flutter Web / Flutter App 담당자가 ML 예측 API를 붙일 때 참고하는 문서입니다.

## 1. 기본 호출 순서

1. OWNER 로그인
2. 로그인 응답에서 `access_token` 저장
3. API 호출 시 `Authorization: Bearer {access_token}` 헤더 추가
4. `POST /api/v1/owner/ml/predictions` 호출
5. 응답값을 화면에 표시

## 2. 추천 화면 표시 필드

- `estimated_yield_kg`
- `suggested_reservable_min_kg`
- `suggested_reservable_max_kg`
- `recommended_price`
- `predicted_harvest_start`
- `predicted_harvest_end`
- `warning_message`

## 3. 요청 예시

```http
POST /api/v1/owner/ml/predictions
Authorization: Bearer {access_token}
Content-Type: application/json
```

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

## 4. 응답 사용 예시

성공 시 `data` 내부 값을 화면에 사용하면 됩니다.

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

## 5. Dart DTO 참고 예시

참고용 구조입니다. 실제 프로젝트 스타일에 맞게 수정해서 사용하세요.

```dart
class MlPredictionFeatures {
  final double pastYieldKg;
  final double marketPrice;
  final String variety;
  final double marAvgTemp;
  final double augSunshine;
  final double octRainfall;
  final double augHumidity;

  MlPredictionFeatures({
    required this.pastYieldKg,
    required this.marketPrice,
    required this.variety,
    required this.marAvgTemp,
    required this.augSunshine,
    required this.octRainfall,
    required this.augHumidity,
  });

  Map<String, dynamic> toJson() => {
        'past_yield_kg': pastYieldKg,
        'market_price': marketPrice,
        'variety': variety,
        'mar_avg_temp': marAvgTemp,
        'aug_sunshine': augSunshine,
        'oct_rainfall': octRainfall,
        'aug_humidity': augHumidity,
      };
}

class MlPredictionRequest {
  final int farmId;
  final int productId;
  final MlPredictionFeatures features;

  MlPredictionRequest({
    required this.farmId,
    required this.productId,
    required this.features,
  });

  Map<String, dynamic> toJson() => {
        'farm_id': farmId,
        'product_id': productId,
        'features': features.toJson(),
      };
}

class MlPredictionData {
  final int predictionId;
  final int farmId;
  final int productId;
  final double? unitYieldKg10a;
  final String predictedHarvestStart;
  final String predictedHarvestEnd;
  final double estimatedYieldKg;
  final double suggestedReservableMinKg;
  final double suggestedReservableMaxKg;
  final int recommendedPrice;
  final double confidence;
  final double safetyFactor;
  final String warningMessage;
  final String modelVersion;

  MlPredictionData({
    required this.predictionId,
    required this.farmId,
    required this.productId,
    required this.unitYieldKg10a,
    required this.predictedHarvestStart,
    required this.predictedHarvestEnd,
    required this.estimatedYieldKg,
    required this.suggestedReservableMinKg,
    required this.suggestedReservableMaxKg,
    required this.recommendedPrice,
    required this.confidence,
    required this.safetyFactor,
    required this.warningMessage,
    required this.modelVersion,
  });
}
```

## 6. 프론트 처리 팁

- 요청 전 `farm_id`, `product_id`가 현재 선택된 농가/상품과 일치하는지 확인하세요.
- 입력 폼 단계에서 validation 범위를 미리 막아주면 422 응답을 줄일 수 있습니다.
- `recommended_price`는 정수 가격으로 바로 표시할 수 있습니다.
- `warning_message`가 비어 있지 않으면 강조 문구로 노출하는 것을 권장합니다.
- 토큰 만료나 누락 시 401이 내려오므로 로그인 화면 또는 토큰 재발급 흐름으로 연결하세요.
- CUSTOMER 계정으로 호출하면 403이 내려오므로 OWNER 전용 화면에서만 호출하세요.

