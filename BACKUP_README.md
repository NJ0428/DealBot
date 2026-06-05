# 데이터베이스 백업 및 복구 시스템

SQLite 데이터베이스를 위한 완전한 백업 및 복구 솔루션입니다.

## 주요 기능

### 📦 백업 기능
- **전체 백업 (Full Backup)**: 데이터베이스 전체를 백업
- **증분 백업 (Incremental Backup)**: WAL(Write-Ahead Log) 파일 기반 변경 사항만 백업
- **자동 압축**: gzip 알고리즘으로 백업 파일 압축
- **체크섬 검증**: SHA256 체크섘으로 백업 무결성 보장

### ⏰ 스케줄링
- **자동 백업 스케줄링**: 매일/매주/매시간 백업 설정
- **재시도 메커니즘**: 백업 실패 시 자동 재시도
- **다중 데이터베이스 지원**: 여러 데이터베이스에 대한 독립적 스케줄링

### 🔄 복구 기능
- **단일 백업 복구**: 특정 백업 파일로 복구
- **증분 백업 체인 복구**: 전체 백업 + 증분 백업 조합으로 복구
- **특정 시점 복구 (PITR)**: 원하는 시점으로 데이터베이스 복구
- **안전 백업**: 복구 전 자동으로 현재 상태 백업
- **복구 후 검증**: 데이터베이스 무결성 자동 검사

### 📊 관리 기능
- **백업 통계**: 저장 공간, 백업 개수, 압축률 등 통계 제공
- **자동 정리**: 오래된 백업 자동 삭제
- **복구 추천**: 최적의 복구 포인트 추천
- **백업 비교**: 두 백업 간 차이점 비교

## 설치

```bash
# 필요한 패키지 설치
pip install schedule

# 파일 위치 확인
# - database_backup_manager.py: 백업 매니저
# - backup_scheduler.py: 백업 스케줄러
# - database_restorer.py: 복구 매니저
# - backup_config.json: 설정 파일
```

## 빠른 시작

### 1. 기본 백업 및 복구

```python
from database_backup_manager import DatabaseBackupManager

# 백업 매니저 초기화
backup_manager = DatabaseBackupManager(
    backup_dir="backups",
    compress=True,
    max_backups=30
)

# 전체 백업 생성
metadata = backup_manager.create_full_backup(
    "my_database.db",
    description="일일 전체 백업",
    tags=["daily", "full"]
)

print(f"백업 완료: {metadata.backup_id}")
print(f"크기: {metadata.size_bytes:,} bytes")
print(f"압축 크기: {metadata.compressed_size:,} bytes")

# 백업 복구
success = backup_manager.restore_backup(
    metadata.backup_id,
    restore_path="restored.db",
    force=True
)
```

### 2. 자동 백업 스케줄링

```python
from database_backup_manager import DatabaseBackupManager
from backup_scheduler import BackupScheduler, ScheduleType

# 백업 매니저 및 스케줄러 초기화
backup_manager = DatabaseBackupManager(backup_dir="backups")
scheduler = BackupScheduler(backup_manager)

# 매일 새벽 2시 전체 백업
scheduler.add_schedule(
    schedule_type=ScheduleType.FULL,
    database_path="my_database.db",
    interval="daily",
    time="02:00",
    description="일일 전체 백업",
    tags=["daily", "full"]
)

# 매시간 증분 백업
scheduler.add_schedule(
    schedule_type=ScheduleType.INCREMENTAL,
    database_path="my_database.db",
    interval="hourly",
    description="시간별 증분 백업",
    tags=["hourly", "incremental"]
)

# 스케줄러 시작
scheduler.start()
```

### 3. 데이터베이스 복구

```python
from database_restorer import DatabaseRestorer
from database_backup_manager import DatabaseBackupManager

backup_manager = DatabaseBackupManager(backup_dir="backups")
restorer = DatabaseRestorer(backup_manager)

# 복구 가능한 포인트 조회
recovery_points = restorer.list_recovery_points("my_database.db")

for point in recovery_points:
    print(f"{point.backup_id} - {point.timestamp}")

# 복구 추천 받기
recommendations = restorer.get_recovery_recommendations("my_database.db")

for rec in recommendations[:3]:
    print(f"{rec['backup_id']} - 점수: {rec['score']}")
    print(f"  사유: {rec['recommendation_reason']}")

# 복구 실행
restorer.restore_to_point(
    backup_id="full_20240101_020000",
    create_safety_backup=True,
    verify_after_restore=True
)
```

## 설정

`backup_config.json` 파일에서 시스템 설정을 구성할 수 있습니다.

```json
{
  "general": {
    "backup_dir": "backups",
    "compress": true,
    "max_backups": 30,
    "enable_wal": true
  },
  "retention": {
    "daily_backups_keep_days": 7,
    "weekly_backups_keep_weeks": 4,
    "monthly_backups_keep_months": 12
  },
  "schedules": {
    "full_backup_daily": {
      "enabled": true,
      "type": "full",
      "interval": "daily",
      "time": "02:00"
    }
  }
}
```

## 사용 예제

### 기본 백업 예제

```bash
# 예제 실행
python database_backup_example.py

# 테스트 실행
python test_database_backup.py
```

### 프로그래밍 방식 사용

```python
import sqlite3
from database_backup_manager import DatabaseBackupManager
from backup_scheduler import BackupScheduler, ScheduleType
from database_restorer import DatabaseRestorer

# 1. 데이터베이스 생성
conn = sqlite3.connect("app.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
cursor.execute("INSERT INTO users (name) VALUES ('Alice')")
conn.commit()
conn.close()

# 2. 백업 시스템 초기화
backup_manager = DatabaseBackupManager(
    backup_dir="backups",
    compress=True,
    max_backups=30
)

# 3. 전체 백업
full_backup = backup_manager.create_full_backup(
    "app.db",
    description="초기 백업"
)

# 4. 데이터 수정
conn = sqlite3.connect("app.db")
cursor = conn.cursor()
cursor.execute("INSERT INTO users (name) VALUES ('Bob')")
conn.commit()
conn.close()

# 5. 증분 백업
inc_backup = backup_manager.create_incremental_backup(
    "app.db",
    description="Bob 추가"
)

# 6. 백업 목록 확인
backups = backup_manager.list_backups()
for backup in backups:
    print(f"{backup.backup_id}: {backup.description}")

# 7. 스케줄링 설정
scheduler = BackupScheduler(backup_manager)
scheduler.add_schedule(
    schedule_type=ScheduleType.FULL,
    database_path="app.db",
    interval="daily",
    time="02:00"
)
scheduler.start()

# 8. 복구
restorer = DatabaseRestorer(backup_manager)
recovery_points = restorer.list_recovery_points("app.db")

# 최신 백업으로 복구
if recovery_points:
    restorer.restore_to_point(
        recovery_points[0].backup_id,
        create_safety_backup=True
    )
```

## 백업 타입 비교

| 타입 | 장점 | 단점 | 사용 시나리오 |
|------|------|------|--------------|
| **전체 백업** | 완전한 복구 가능, 단순함 | 크기 큼, 시간 소요 | 일일/주간 백업 |
| **증분 백업** | 크기 작음, 빠름 | WAL 모드 필요, 체인 복구 필요 | 시간별 백업 |

## 복구 전략

### 1. 단일 백업 복구
가장 간단한 복구 방법입니다.

```python
restorer.restore_to_point(backup_id)
```

### 2. 체인 복구 (전체 + 증분)
최신 상태로 복구합니다.

```python
# 자동으로 가장 가까운 전체 백업 + 증분 백업들 적용
restorer.restore_to_point(incremental_backup_id)
```

### 3. 특정 시점 복구 (PITR)
원하는 시점으로 복구합니다.

```python
from datetime import datetime

target_time = datetime(2024, 1, 1, 12, 0, 0)
restorer.restore_to_time(target_time, "app.db")
```

## 백업 보존 정책

기본 보존 정책:
- **일일 백업**: 7일 보존
- **주간 백업**: 4주 보존
- **월간 백업**: 12개월 보존
- **최소 전체 백업**: 3개 항상 유지

## 무결성 검사

백업 파일과 복구된 데이터베이스의 무결성을 자동으로 검사합니다.

### 백업 파일 검증
```python
is_valid = backup_manager.verify_backup(backup_id)
```

### 복구된 데이터베이스 검증
- PRAGMA integrity_check
- PRAGMA foreign_key_check
- PRAGMA quick_check
- 테이블 구조 확인

## 모니터링 및 알림

### 백업 상태 확인
```python
stats = backup_manager.get_backup_stats()
print(f"전체 백업: {stats['full_backups']}")
print(f"증분 백업: {stats['incremental_backups']}")
print(f"총 크기: {stats['total_compressed_size_bytes']:,} bytes")
```

### 스케줄 상태 확인
```python
status = scheduler.get_schedule_status()
print(f"활성화된 스케줄: {status['enabled_schedules']}")
for schedule in status['schedules']:
    print(f"{schedule['schedule_id']}: {schedule['last_status']}")
```

## 성능 팁

1. **압축 사용**: 디스크 공간 60-80% 절약
2. **증분 백업**: 백업 시간 90% 단축
3. **적절한 보존 정책**: 디스크 사용량 최적화
4. **비수기 스케줄링**: 새벽 시간대 백업 권장

## 보안 고려사항

1. **백업 파일 권한**: 적절한 파일 권한 설정
2. **암호화**: 민감한 데이터는 암호화된 백업 고려
3. **격리된 저장**: 백업을 원본과 분리된 위치에 저장
4. **접근 제어**: 백업 디렉토리 접근 제한

## 문제 해결

### WAL 파일이 없는 경우
```
경고: WAL 파일이 존재하지 않습니다. WAL 모드가 활성화되어 있지 않거나 변경 사항이 없습니다.
```

**해결**: WAL 모드가 자동으로 활성화됩니다. 데이터를 변경한 후 다시 시도하세요.

### 복구 실패
```
오류: 복구된 데이터베이스 무결성 검사 실패
```

**해결**:
1. 안전 백업 ID로 롤백
2. 다른 백업 파일로 시도
3. 백업 파일 검증 실행

### 디스크 공간 부족
**해결**:
1. `max_backups` 설정 감소
2. 압축 활성화
3. 오래된 백업 수동 삭제

## 테스트

```bash
# 전체 테스트 실행
python test_database_backup.py

# 특정 테스트 클래스 실행
python -m unittest test_database_backup.TestDatabaseBackupManager

# 상세 테스트 결과
python -m unittest test_database_backup -v
```

## API 레퍼런스

### DatabaseBackupManager
- `create_full_backup(db_path, description, tags)`: 전체 백업 생성
- `create_incremental_backup(db_path, description, tags)`: 증분 백업 생성
- `restore_backup(backup_id, restore_path, force)`: 백업 복구
- `list_backups(backup_type)`: 백업 목록 조회
- `verify_backup(backup_id)`: 백업 검증
- `delete_backup(backup_id)`: 백업 삭제

### BackupScheduler
- `add_schedule(...)`: 스케줄 추가
- `remove_schedule(schedule_id)`: 스케줄 제거
- `start()`: 스케줄러 시작
- `stop()`: 스케줄러 정지
- `run_now(schedule_id)`: 즉시 실행

### DatabaseRestorer
- `list_recovery_points(database_path)`: 복구 포인트 조회
- `restore_to_point(backup_id, ...)`: 특정 포인트로 복구
- `restore_to_time(target_time, ...)`: 특정 시점으로 복구
- `get_recovery_recommendations(database_path)`: 복구 추천

## 라이선스

이 백업 시스템은 데이터 보호를 위해 설계되었습니다. 상업적/비상업적 사용이 가능합니다.

## 지원 및 기여

문제 보고나 기능 요청은 프로젝트 이슈 트래커를 이용해주세요.

---

**⚠️ 중요**: 백업 시스템을 프로덕션에 사용하기 전에 반드시 테스트 환경에서 충분히 검증하세요.