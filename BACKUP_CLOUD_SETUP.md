# 백업 시스템 클라우드 설정 가이드

데이터베이스 백업 시스템의 클라우드 저장 및 알림 기능 설정 방법입니다.

## 📦 필요한 패키지 설치

```bash
# AWS S3 지원
pip install boto3

# Google Cloud Storage 지원
pip install google-cloud-storage

# 이메일 및 웹훅 지원 (이미 설치되어 있음)
pip install requests

# 전체 설치
pip install boto3 google-cloud-storage requests schedule
```

## ☁️ 클라우드 설정

### AWS S3 설정

#### 1. IAM 사용자 생성

1. AWS Management Console 접속
2. IAM → Users → "Create user"
3. 사용자명: `database-backup-user`
4. 권한: "AmazonS3FullAccess" 또는 직접 정책 생성

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-backup-bucket",
        "arn:aws:s3:::your-backup-bucket/*"
      ]
    }
  ]
}
```

#### 2. S3 버킷 생성

1. S3 → "Create bucket"
2. 버킷명: `your-backup-bucket`
3. 리전: `Asia Pacific (Seoul) ap-northeast-2`
4. 액세스: 차단 또는 공개 (선택 사항)

#### 3. 액세스 키 생성

1. IAM → 사용자 선택 → "Security credentials"
2. "Create access key"
3. 액세스 키와 시크릿 키 저장

#### 4. 설정 파일 수정

```json
{
  "aws_s3": {
    "enabled": true,
    "access_key": "AKIAXXXXXXXXXXXXXXXXX",
    "secret_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "bucket_name": "your-backup-bucket",
    "region": "ap-northeast-2",
    "storage_class": "STANDARD",
    "encryption": "AES256"
  }
}
```

### Google Cloud Storage 설정

#### 1. 서비스 계정 생성

1. Google Cloud Console 접속
2. IAM & Admin → Service Accounts → "Create Service Account"
3. 이름: `database-backup-sa`

#### 2. 권한 부여

1. 생성된 서비스 계정 선택
2. "Keys" 탭 → "Add key" → "Create new key"
3. 키 타입: "JSON"
4. JSON 키 파일 다운로드

#### 3. GCS 버킷 생성

```bash
# 또는 Console에서 생성
gsutil mb -p your-project-id gs://your-backup-bucket
```

#### 4. 설정 파일 수정

```json
{
  "google_cloud": {
    "enabled": true,
    "credentials_path": "/path/to/credentials.json",
    "bucket_name": "your-backup-bucket",
    "project_id": "your-project-id",
    "storage_class": "STANDARD"
  }
}
```

## 🔔 알림 설정

### 이메일 알림 (Gmail)

#### 1. Gmail 애플리케이션 비밀번호 생성

1. Google Account → Security
2. 2-Step Verification 활성화
3. App passwords → "Generate"
4. 앱 선택: "Mail"
5. 기기 선택: "Windows Computer"
6. 비밀번호 복사 (16자리)

#### 2. 설정 파일 수정

```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "abcd efgh ijkl mnop",
    "from_email": "your-email@gmail.com",
    "use_tls": true
  },
  "default_recipients": ["admin@example.com", "dba@example.com"]
}
```

### 이메일 알림 (다른 SMTP)

```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.office365.com",
    "smtp_port": 587,
    "username": "your-email@company.com",
    "password": "your-password",
    "from_email": "backup@company.com",
    "use_tls": true
  }
}
```

### Slack 알림

#### 1. Slack 앱 생성

1. Slack App Directory → "Create New App"
2. 앱 이름: `Database Backup Bot`
3. 워크스페이스 선택

#### 2. Incoming Webhooks 활성화

1. "Incoming Webhooks" → "On"
2. "Add New Webhook to Workspace"
3. 채널 선택: `#backups`
4. Webhook URL 복사

#### 3. 설정 파일 수정

```json
{
  "slack": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/T00/B00/XXXX",
    "channel": "#backups",
    "username": "Backup Bot",
    "icon_emoji": ":floppy_disk:"
  }
}
```

### 웹훅 알림

#### 1. 웹훅 엔드포인트 생성

```python
# Flask 예제
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook/backup', methods=['POST'])
def backup_webhook():
    data = request.json
    print(f"백업 알림: {data}")
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(port=5000)
```

#### 2. 설정 파일 수정

```json
{
  "webhook": {
    "enabled": true,
    "url": "https://your-domain.com/webhook/backup",
    "headers": {
      "Authorization": "Bearer your-token"
    }
  }
}
```

## 🚀 완전 설정 예시

```json
{
  "backup_dir": "backups",
  "compression": {
    "enabled": true
  },
  "retention": {
    "max_backups": 30,
    "daily_backups_keep_days": 7,
    "weekly_backups_keep_weeks": 4
  },
  "cloud_storage": {
    "enabled": true,
    "auto_upload": true,
    "providers": ["aws_s3", "google_cloud"]
  },
  "notifications": {
    "enabled": true,
    "on_backup_success": true,
    "on_backup_failed": true,
    "on_restore_success": true,
    "on_restore_failed": true,
    "weekly_report": true
  },
  "aws_s3": {
    "enabled": true,
    "access_key": "AKIAXXXXXXXXXXXXXXXXX",
    "secret_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "bucket_name": "my-backup-bucket",
    "region": "ap-northeast-2",
    "storage_class": "STANDARD",
    "encryption": "AES256"
  },
  "google_cloud": {
    "enabled": true,
    "credentials_path": "/path/to/gcs-credentials.json",
    "bucket_name": "my-backup-bucket",
    "project_id": "my-project-id",
    "storage_class": "STANDARD"
  },
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "backup@example.com",
    "password": "app-specific-password",
    "from_email": "backup@example.com",
    "use_tls": true
  },
  "slack": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/T00/B00/XXXX",
    "channel": "#backups",
    "username": "Backup Bot",
    "icon_emoji": ":floppy_disk:"
  },
  "webhook": {
    "enabled": true,
    "url": "https://api.example.com/backup/webhook"
  },
  "default_recipients": ["admin@example.com", "dba@example.com"]
}
```

## 💻 프로그래밍 방식 설정

```python
from backup_integration_manager import create_integration_config, BackupIntegrationManager
from database_backup_manager import BackupType

# 설정 생성
config = create_integration_config(
    backup_dir="backups",
    enable_compression=True,
    max_backups=30,
    enable_cloud=True,
    auto_upload=True,
    enable_notifications=True,
    notify_backup_success=True,
    notify_backup_failed=True,
    # AWS S3
    aws_enabled=True,
    aws_access_key="AKIAXXXXXXXXXXXXXXXXX",
    aws_secret_key="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    aws_bucket="my-backup-bucket",
    aws_region="ap-northeast-2",
    # Google Cloud
    gcs_enabled=True,
    gcs_credentials="path/to/credentials.json",
    gcs_bucket="my-backup-bucket",
    gcs_project="my-project-id",
    # 이메일
    email_enabled=True,
    email_smtp="smtp.gmail.com",
    email_port=587,
    email_user="backup@gmail.com",
    email_password="app-password",
    email_from="backup@gmail.com",
    # Slack
    slack_enabled=True,
    slack_webhook="https://hooks.slack.com/services/T00/B00/XXXX",
    slack_channel="#backups",
    # 수신자
    recipients=["admin@example.com", "dba@example.com"]
)

# 통합 매니저 초기화
manager = BackupIntegrationManager()

# 백업 생성 (자동으로 클라우드 업로드 및 알림)
backup_id = manager.create_backup(
    "my_database.db",
    backup_type=BackupType.FULL,
    description="자동 백업"
)

print(f"백업 완료: {backup_id}")
```

## 🔒 보안 고려사항

### 1. 자격 증명 보호

```bash
# 환경 변수 사용 권장
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export GCS_CREDENTIALS="/path/to/credentials.json"

# 또는 .env 파일 사용
echo 'AWS_ACCESS_KEY_ID=your-access-key' >> .env
echo 'AWS_SECRET_ACCESS_KEY=your-secret-key' >> .env
```

### 2. 버킷 정책

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedObjectUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::your-bucket/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    }
  ]
}
```

### 3. 버전 관리 활성화

```bash
# S3 버킷 버전 관리
aws s3api put-bucket-versioning \
  --bucket your-bucket \
  --versioning-configuration Status=Enabled
```

## 📊 모니터링 및 비용 최적화

### 1. 수명 주기 정책

```bash
# S3 수명 주기 정책
aws s3api put-bucket-lifecycle-configuration \
  --bucket your-bucket \
  --lifecycle-configuration file://lifecycle.json
```

```json
{
  "Rules": [
    {
      "Id": "DeleteOldBackups",
      "Status": "Enabled",
      "Prefix": "backups/",
      "Expiration": {
        "Days": 90
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 60,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

### 2. 비용 추적

```python
# 통계 조회
stats = manager.get_system_stats()

print(f"총 저장 공간: {stats['cloud_storage']['total_size_bytes'] / 1024 / 1024:.2f} MB")
print(f"월 예상 비용: ${stats['cloud_storage']['total_size_bytes'] / 1024 / 1024 / 1024 * 0.023:.2f}")
```

## 🧪 테스트

```python
# 설정 테스트
from backup_integration_manager import BackupIntegrationManager

manager = BackupIntegrationManager()

# 시스템 상태 확인
stats = manager.get_system_stats()

# 테스트 백업
backup_id = manager.create_backup(
    "test.db",
    backup_type=BackupType.FULL,
    description="테스트 백업"
)

# 테스트 복구
manager.restore_backup(backup_id, "restored_test.db")
```

## 📝 문제 해결

### 자주 발생하는 문제

1. **AWS 자격 증명 오류**
   - IAM 권한 확인
   - 액세스 키 재생성

2. **이메일 발송 실패**
   - 애플리케이션 비밀번호 확인
   - 방화벽 확인

3. **Slack 웹훅 실패**
   - 웹훅 URL 확인
   - 채널 권한 확인

---

이제 백업 시스템의 클라우드 기능을 완전히 활용할 수 있습니다! 🎉