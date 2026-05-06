# CODEX_GUIDE

- 문서 기준을 벗어나서 테이블, 컬럼, API를 임의로 만들지 않는다.
- API 추가 시 `docs/API_SPEC_BACKEND.md` 를 같이 수정한다.
- DB 모델 수정 시 `docs/DB_MODEL_REVIEW.md` 를 같이 수정한다.
- 실제 비밀번호, API Key, 토큰은 절대 작성하지 않는다.
- 한 번에 너무 많은 기능을 완성하려고 하지 않는다.
- 트랜잭션 로직은 Service 계층에 둔다.
- Repository는 DB 접근만 담당한다.
- Swagger에서 먼저 테스트한 뒤 앱과 연동한다.
