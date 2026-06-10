"""
백업 시스템 통합 예제

클라우드 저장 및 알림 기능이 포함된 통합 백업 시스템의 사용 예제입니다.
"""

import os
import sqlite3
import logging
from datetime import datetime

from backup_integration_manager import BackupIntegrationManager, create_integration_config
from database_backup_manager import BackupType


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_sample_database(db_path: str):
    """샘플 데이터베이스 생성"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    ''')

    # 샘플 데이터 추가
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)",
                  ("Alice", "alice@example.com"))
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)",
                  ("Bob", "bob@example.com"))
    cursor.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
                  ("Laptop", 999.99, "High-performance laptop"))

    conn.commit()
    conn.close()

    print(f"샘플 데이터베이스 생성 완료: {db_path}")


def example_basic_integration():
    """기본 통합 예제"""
    print("\n" + "="*50)
    print("예제 1: 기본 통합 백업")
    print("="*50)

    # 샘플 데이터베이스 생성
    db_path = "integration_sample.db"
    create_sample_database(db_path)

    # 통합 매니저 초기화
    config = create_integration_config(
        backup_dir="integration_backups",
        enable_compression=True,
        max_backups=10
    )

    manager = BackupIntegrationManager()

    # 전체 백업
    print("\n전체 백업 생성 중...")
    backup_id = manager.create_backup(
        db_path,
        backup_type=BackupType.FULL,
        description="통합 테스트 전체 백업",
        tags=["integration", "test"]
    )

    if backup_id:
        print(f"백업 완료: {backup_id}")

        # 백업 목록 조회
        backups = manager.list_backups()
        print(f"총 백업 수: {len(backups['local'])}개")

        # 시스템 통계
        stats = manager.get_system_stats()
        print(f"시스템 통계:")
        print(f"  전체 백업: {stats['backup']['full_backups']}개")
        print(f"  총 크기: {stats['backup']['total_size_bytes']:,} bytes")


def example_cloud_backup():
    """클라우드 백업 예제"""
    print("\n" + "="*50)
    print("예제 2: 클라우드 백업 (데모)")
    print("="*50)

    # 클라우드 설정이 없는 경우 데모만 실행
    print("\n⚠️ 실제 클라우드 설정이 필요합니다.")

    # 설정 예시
    config = create_integration_config(
        backup_dir="integration_backups",
        enable_cloud=True,
        auto_upload=True,
        # AWS S3 설정 (실제 값으로 변경 필요)
        aws_enabled=False,  # 활성화하려면 True로 설정
        aws_access_key="YOUR_AWS_ACCESS_KEY",
        aws_secret_key="YOUR_AWS_SECRET_KEY",
        aws_bucket="your-backup-bucket",
        aws_region="ap-northeast-2",
        # Google Cloud 설정 (실제 값으로 변경 필요)
        gcs_enabled=False,  # 활성화하려면 True로 설정
        gcs_credentials="path/to/credentials.json",
        gcs_bucket="your-backup-bucket",
        gcs_project="your-project-id"
    )

    print("\n설정 예시:")
    print(f"  클라우드 활성화: {config['cloud_storage']['enabled']}")
    print(f"  자동 업로드: {config['cloud_storage']['auto_upload']}")
    print(f"  AWS S3 활성화: {config['aws_s3']['enabled']}")
    print(f"  GCS 활성화: {config['google_cloud']['enabled']}")


def example_notification_system():
    """알림 시스템 예제"""
    print("\n" + "="*50)
    print("예제 3: 알림 시스템 (데모)")
    print("="*50)

    print("\n⚠️ 실제 알림 설정이 필요합니다.")

    # 설정 예시
    config = create_integration_config(
        backup_dir="integration_backups",
        enable_notifications=True,
        # 이메일 설정
        email_enabled=False,  # 활성화하려면 True로 설정
        email_smtp="smtp.gmail.com",
        email_port=587,
        email_user="your-email@gmail.com",
        email_password="your-app-password",
        email_from="backup@yourdomain.com",
        # Slack 설정
        slack_enabled=False,  # 활성화하려면 True로 설정
        slack_webhook="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        slack_channel="#backups",
        # 웹훅 설정
        webhook_enabled=False,  # 활성화하려면 True로 설정
        webhook_url="https://your-domain.com/webhook",
        recipients=["admin@example.com", "dba@example.com"]
    )

    print("\n설정 예시:")
    print(f"  알림 활성화: {config['notifications']['enabled']}")
    print(f"  백업 성공 알림: {config['notifications']['on_backup_success']}")
    print(f"  백업 실패 알림: {config['notifications']['on_backup_failed']}")
    print(f"  이메일 활성화: {config['email']['enabled']}")
    print(f"  Slack 활성화: {config['slack']['enabled']}")
    print(f"  웹훅 활성화: {config['webhook']['enabled']}")
    print(f"  기본 수신자: {config['default_recipients']}")


def example_cloud_only_backup():
    """클라우드 전용 백업 예제"""
    print("\n" + "="*50)
    print("예제 4: 클라우드 전용 백업 워크플로우")
    print("="*50)

    # 설정
    config = create_integration_config(
        backup_dir="integration_backups",
        enable_cloud=True,
        auto_upload=True,
        # 최소한의 클라우드 설정
        aws_enabled=True,
        aws_access_key="demo_key",
        aws_secret_key="demo_secret",
        aws_bucket="demo-bucket"
    )

    # 통합 매니저 초기화
    manager = BackupIntegrationManager()

    # 샘플 데이터베이스
    db_path = "integration_sample.db"

    if not os.path.exists(db_path):
        create_sample_database(db_path)

    # 백업 생성 (자동 클라우드 업로드)
    print("\n백업 생성 및 클라우드 업로드...")

    backup_id = manager.create_backup(
        db_path,
        backup_type=BackupType.FULL,
        description="클라우드 전용 백업",
        upload_to_cloud=True
    )

    if backup_id:
        print(f"백업 완료: {backup_id}")

        # 클라우드 백업 목록
        backups = manager.list_backups(include_cloud=True)
        print(f"클라우드 백업:")
        for provider, backups_list in backups['cloud'].items():
            print(f"  {provider}: {len(backups_list)}개")


def example_restore_workflow():
    """복구 워크플로우 예제"""
    print("\n" + "="*50)
    print("예제 5: 통합 복구 워크플로우")
    print("="*50)

    # 통합 매니저 초기화
    manager = BackupIntegrationManager()

    # 백업 목록 조회
    backups = manager.list_backups()

    if not backups['local']:
        print("복구 가능한 백업이 없습니다.")
        return

    # 가장 최신 백업 선택
    latest_backup = backups['local'][0]
    backup_id = latest_backup['backup_id']

    print(f"\n복구할 백업: {backup_id}")
    print(f"  타입: {latest_backup['backup_type']}")
    print(f"  시간: {latest_backup['timestamp']}")

    # 복구
    restore_path = "restored_integration.db"

    print(f"\n복구 시작...")
    success = manager.restore_backup(
        backup_id,
        restore_path=restore_path
    )

    if success:
        print(f"복구 완료: {restore_path}")

        # 복구된 데이터베이스 확인
        if os.path.exists(restore_path):
            conn = sqlite3.connect(restore_path)
            cursor = conn.cursor()

            # 사용자 수 확인
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            print(f"복구된 사용자 수: {user_count}")

            conn.close()


def example_system_monitoring():
    """시스템 모니터링 예제"""
    print("\n" + "="*50)
    print("예제 6: 시스템 모니터링")
    print("="*50)

    # 통합 매니저 초기화
    manager = BackupIntegrationManager()

    # 시스템 통계
    stats = manager.get_system_stats()

    print("\n백업 시스템 통계:")
    print(f"  타임스탬프: {stats['timestamp']}")
    print(f"\n  백업:")
    print(f"    전체 백업: {stats['backup']['full_backups']}개")
    print(f"    증분 백업: {stats['backup']['incremental_backups']}개")
    print(f"    총 백업: {stats['backup']['total_backups']}개")
    print(f"    총 크기: {stats['backup']['total_size_bytes']:,} bytes")
    print(f"    압축률: {stats['backup']['compression_ratio']}")

    print(f"\n  클라우드 저장:")
    print(f"    총 클라우드 백업: {stats['cloud_storage']['total_cloud_backups']}개")
    print(f"    AWS S3: {stats['cloud_storage']['by_provider']['aws_s3']}개")
    print(f"    Google Cloud: {stats['cloud_storage']['by_provider']['google_cloud']}개")
    print(f"    총 크기: {stats['cloud_storage']['total_size_bytes']:,} bytes")

    print(f"\n  알림:")
    print(f"    총 알림: {stats['notifications']['total_notifications']}개")
    print(f"    타입별: {stats['notifications']['by_type']}")
    print(f"    상태별: {stats['notifications']['by_status']}")


def example_cloud_sync():
    """클라우드 동기화 예제"""
    print("\n" + "="*50)
    print("예제 7: 클라우드 백업 동기화")
    print("="*50)

    # 통합 매니저 초기화
    manager = BackupIntegrationManager()

    # 백업 목록 조회
    backups = manager.list_backups()
    local_backup_ids = [b['backup_id'] for b in backups['local']]

    print(f"\n로컬 백업: {len(local_backup_ids)}개")

    # 클라우드 동기화
    print("\n클라우드 동기화 시작...")
    manager.sync_cloud_backups(local_backup_ids)

    # 동기화 후 확인
    synced_backups = manager.list_backups(include_cloud=True)
    print(f"\n동기화 후:")
    for provider, backups_list in synced_backups['cloud'].items():
        print(f"  {provider}: {len(backups_list)}개")


def main():
    """메인 함수"""
    print("백업 시스템 통합 예제")
    print("클라우드 저장 및 알림 기능이 포함된 통합 시스템")

    try:
        # 예제 실행
        example_basic_integration()
        example_cloud_backup()
        example_notification_system()
        example_cloud_only_backup()
        example_restore_workflow()
        example_system_monitoring()
        example_cloud_sync()

        print("\n" + "="*50)
        print("모든 예제 실행 완료!")
        print("="*50)

        # 실제 사용을 위한 설정 가이드
        print("\n📝 실제 사용을 위한 설정 가이드:")
        print("\n1. AWS S3 설정:")
        print("   - IAM 사용자 생성 및 S3 권한 부여")
        print("   - 버킷 생성")
        print("   - 액세스 키 및 시크릿 키 획득")
        print("\n2. Google Cloud Storage 설정:")
        print("   - 서비스 계정 생성")
        print("   - JSON 키 파일 다운로드")
        print("   - 버킷 생성")
        print("\n3. 이메일 알림 설정:")
        print("   - SMTP 서버 정보")
        print("   - 애플리케이션 비밀번호 (Gmail의 경우)")
        print("\n4. Slack 알림 설정:")
        print("   - Slack 앱 생성")
        print("   - Incoming Webhook URL 획득")
        print("\n5. 설정 파일 생성:")
        print("   - backup_integration_config.json")
        print("   - 또는 create_integration_config() 함수 사용")

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()