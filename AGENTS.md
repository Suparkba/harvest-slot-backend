# Harvest Slot Backend Working Guide

- 코드는 `./harvest-slot-backend` 안에서만 생성하고 수정한다.
- `./harvest-slot-docs-local` 문서는 읽기 전용으로만 참고한다.
- DB/ERD/API 기준은 Harvest Slot 문서를 우선하고, 문서에 없는 테이블·컬럼·API·상태값은 임의로 추가하지 않는다.
- 모든 API Base URL은 `/api/v1` 이고 응답은 `data/message/error` 공통 구조를 따른다.
- 트랜잭션 로직은 Service 계층에 둔다.
- Repository 계층은 DB 접근만 담당한다.
- 실제 비밀번호, JWT Secret, API Key, 이메일 비밀번호는 코드와 문서에 적지 않는다.
- `.env` 는 Git에 올리지 않고 `.env.example` 만 유지한다.
- 이미지 저장소 전략은 이번 범위에서 새로 설계하지 않는다.
- ML/DL, 이메일, 결제는 실제 연동 대신 Mock/Stub 구조로 유지한다.
- 구현 후 `docs/API_SPEC_BACKEND.md`, `docs/DB_MODEL_REVIEW.md` 를 같이 갱신한다.
- `git add`, `git commit`, `git push` 는 하지 않는다.
