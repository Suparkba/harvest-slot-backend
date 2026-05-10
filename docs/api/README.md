# API 문서 안내

Harvest Slot 백엔드의 프론트 연동용 API 문서 모음입니다.
웹/앱 담당자는 아래 3개 파일을 우선 확인하면 됩니다.

## 먼저 볼 파일

1. `docs/api/ml_prediction_api.md`
2. `docs/api/examples/ml_prediction_request.json`
3. `docs/api/frontend_integration_guide.md`

## 문서 목록

| 파일 | 설명 |
| --- | --- |
| `docs/api/ml_prediction_api.md` | ML 예측 API 명세서 |
| `docs/api/frontend_integration_guide.md` | Flutter Web / Flutter App 연동 가이드 |
| `docs/api/examples/ml_prediction_request.json` | 요청 바디 예시 |
| `docs/api/examples/ml_prediction_response.json` | 성공 응답 예시 |
| `docs/api/examples/ml_prediction_validation_error.json` | 422 validation 실패 예시 |
| `docs/api/examples/ml_prediction_auth_error.json` | 401/403 인증 또는 권한 실패 예시 |

## 권장 확인 순서

1. `ml_prediction_api.md`에서 요청/응답 구조 확인
2. `ml_prediction_request.json`, `ml_prediction_response.json`으로 실제 payload 형태 확인
3. `frontend_integration_guide.md`에서 로그인 후 호출 순서와 화면 표시 항목 확인

