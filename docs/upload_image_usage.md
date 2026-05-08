# upload_image.php 사용법

`upload_image.php`는 NAS의 `/share/Web/images` 아래에서 이미지 파일을 CRUD 처리하는 PHP API입니다.

기본 URL:

```text
https://cheng80.myqnapcloud.com/upload_image.php
```

## 공통 규칙

- 응답 형식은 JSON입니다.
- 이미지 확장자는 `jpg`, `jpeg`, `png`, `gif`, `webp`만 허용합니다.
- `subfolder`는 선택값입니다.
- `subfolder`를 생략하면 `/share/Web/images` 바로 아래에 저장됩니다.
- `subfolder=products/2026`처럼 지정하면 `/share/Web/images/products/2026` 아래에 저장됩니다.
- `subfolder` 허용 문자는 영문, 숫자, `_`, `-`, `/`입니다.
- `../` 같은 상위 경로 이동은 허용하지 않습니다.

## 지원 action

| action | 의미 | 메서드 |
|---|---|---|
| `upload` | 이미지 업로드/Create | `POST` |
| `create` | `upload` 별칭 | `POST` |
| `list` | 이미지 목록 조회/Read | `GET` 또는 `POST` |
| `get` | 이미지 단건 조회/Read | `GET` 또는 `POST` |
| `read` | `file_name`이 있으면 `get`, 없으면 `list` | `GET` 또는 `POST` |
| `update` | 기존 이미지 교체/Update | `POST` |
| `delete` | 이미지 삭제/Delete | `DELETE` 또는 `POST` |

`action`을 생략하면 기존 호환성을 위해 `upload`로 처리됩니다.

## 1. 업로드/Create

이미지를 업로드합니다.

요청:

```bash
curl -X POST https://cheng80.myqnapcloud.com/upload_image.php \
  -F "action=upload" \
  -F "product_seq=1" \
  -F "subfolder=products/2026" \
  -F "file=@test.jpg"
```

`action`은 생략할 수 있습니다.

```bash
curl -X POST https://cheng80.myqnapcloud.com/upload_image.php \
  -F "product_seq=1" \
  -F "subfolder=products/2026" \
  -F "file=@test.jpg"
```

저장 파일명:

```text
product_{product_seq}_{원본파일명}.{확장자}
```

예를 들어 `product_seq=1`, 원본 파일명이 `test.jpg`이면:

```text
product_1_test.jpg
```

성공 응답 예:

```json
{
  "result": "OK",
  "action": "upload",
  "file_url": "https://cheng80.myqnapcloud.com/images/products/2026/product_1_test.jpg",
  "file_name": "product_1_test.jpg",
  "file_type": "image",
  "subfolder": "products/2026",
  "saved_path": "/share/Web/images/products/2026/product_1_test.jpg",
  "file_path": "/share/Web/images/products/2026/product_1_test.jpg"
}
```

## 2. 목록 조회/Read

특정 폴더의 이미지 목록을 조회합니다.

요청:

```bash
curl "https://cheng80.myqnapcloud.com/upload_image.php?action=list&subfolder=products/2026"
```

`subfolder` 없이 조회:

```bash
curl "https://cheng80.myqnapcloud.com/upload_image.php?action=list"
```

성공 응답 예:

```json
{
  "result": "OK",
  "action": "list",
  "subfolder": "products/2026",
  "count": 1,
  "files": [
    {
      "file_name": "product_1_test.jpg",
      "file_type": "image",
      "subfolder": "products/2026",
      "file_url": "https://cheng80.myqnapcloud.com/images/products/2026/product_1_test.jpg",
      "file_size": 12345,
      "modified_at": "2026-05-08T10:30:00+09:00"
    }
  ]
}
```

## 3. 단건 조회/Read

파일 하나의 정보를 조회합니다.

요청:

```bash
curl "https://cheng80.myqnapcloud.com/upload_image.php?action=get&subfolder=products/2026&file_name=product_1_test.jpg"
```

성공 응답 예:

```json
{
  "result": "OK",
  "action": "get",
  "file_name": "product_1_test.jpg",
  "file_type": "image",
  "subfolder": "products/2026",
  "file_url": "https://cheng80.myqnapcloud.com/images/products/2026/product_1_test.jpg",
  "file_size": 12345,
  "modified_at": "2026-05-08T10:30:00+09:00",
  "saved_path": "/share/Web/images/products/2026/product_1_test.jpg",
  "file_path": "/share/Web/images/products/2026/product_1_test.jpg"
}
```

## 4. 수정/Update

기존 파일명을 유지하고 파일 내용만 교체합니다.

주의:

- `file_name`은 기존에 저장된 파일명입니다.
- 새로 업로드하는 파일의 확장자는 기존 `file_name`의 확장자와 같아야 합니다.

요청:

```bash
curl -X POST https://cheng80.myqnapcloud.com/upload_image.php \
  -F "action=update" \
  -F "subfolder=products/2026" \
  -F "file_name=product_1_test.jpg" \
  -F "file=@new_test.jpg"
```

성공 응답 예:

```json
{
  "result": "OK",
  "action": "update",
  "file_url": "https://cheng80.myqnapcloud.com/images/products/2026/product_1_test.jpg",
  "file_name": "product_1_test.jpg",
  "file_type": "image",
  "subfolder": "products/2026",
  "saved_path": "/share/Web/images/products/2026/product_1_test.jpg",
  "file_path": "/share/Web/images/products/2026/product_1_test.jpg"
}
```

## 5. 삭제/Delete

이미지를 삭제합니다.

`DELETE` 요청:

```bash
curl -X DELETE "https://cheng80.myqnapcloud.com/upload_image.php?action=delete&subfolder=products/2026&file_name=product_1_test.jpg"
```

`POST` 요청:

```bash
curl -X POST https://cheng80.myqnapcloud.com/upload_image.php \
  -F "action=delete" \
  -F "subfolder=products/2026" \
  -F "file_name=product_1_test.jpg"
```

성공 응답 예:

```json
{
  "result": "OK",
  "action": "delete",
  "file_name": "product_1_test.jpg",
  "subfolder": "products/2026"
}
```

## 오류 응답

오류가 발생하면 HTTP 400과 함께 JSON이 반환됩니다.

예:

```json
{
  "result": "Error",
  "errorMsg": "파일을 찾을 수 없습니다."
}
```

## 배포 후 문법 확인

NAS에 PHP CLI가 있으면 배포 후 아래 명령으로 문법을 확인할 수 있습니다.

```bash
php -l /share/Web/upload_image.php
```
