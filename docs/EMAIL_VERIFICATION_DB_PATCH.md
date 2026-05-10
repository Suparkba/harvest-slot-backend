# Email Verification DB Patch

`email_verifications` 테이블은 운영 DB에서 `create_all`만으로 컬럼 구조가 바뀌지 않습니다.
아래 SQL을 적용하기 전에 먼저 현재 컬럼 상태를 확인하세요.

```sql
SHOW COLUMNS FROM email_verifications;
```

`ADD COLUMN` 구문은 이미 컬럼이 있으면 실패할 수 있습니다.
운영 반영 전 컬럼 존재 여부를 확인한 뒤 필요한 구문만 선택해서 실행하세요.

## Patch SQL

```sql
ALTER TABLE email_verifications
ADD COLUMN attempt_count INT NOT NULL DEFAULT 0 AFTER verified_at;

ALTER TABLE email_verifications
ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

ALTER TABLE email_verifications
MODIFY COLUMN account_id INT NULL;

ALTER TABLE email_verifications
MODIFY COLUMN verification_code VARCHAR(255) NOT NULL;
```

## Signup Test Flow

Swagger 또는 `curl`로 아래 순서대로 확인할 수 있습니다.

### 1. Send verification email

`POST /api/v1/auth/email/send`

```json
{
  "email": "test@example.com",
  "purpose": "SIGNUP"
}
```

### 2. Verify code

`POST /api/v1/auth/email/verify`

```json
{
  "email": "test@example.com",
  "code": "123456",
  "purpose": "SIGNUP"
}
```

### 3. Owner signup

`POST /api/v1/auth/owners/signup`

```json
{
  "email": "test@example.com",
  "password": "pass1234!",
  "name": "\ub18d\uac00\ub300\ud45c",
  "phone": "010-2222-3333"
}
```

### 4. Customer signup

`POST /api/v1/auth/customers/signup`

```json
{
  "email": "test@example.com",
  "password": "pass1234!",
  "name": "\uace0\uac1d\ud14c\uc2a4\ud2b8",
  "phone": "010-1111-2222"
}
```

회원가입이 성공하면 `accounts.email_verified = true` 상태가 유지되어야 합니다.
