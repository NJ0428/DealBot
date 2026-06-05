"""
데이터베이스 백업 및 복구 시스템 사용 예제

백업 매니저, 스케줄러, 복구 기능의 사용 방법을 보여줍니다.
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta

from database_backup_manager import DatabaseBackupManager, BackupType
from backup_scheduler import BackupScheduler, ScheduleType, create_default_schedules
from database_restorer import DatabaseRestorer


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


def modify_database(db_path: str):
    """데이터베이스 수정 (증분 백업 테스트용)"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 새 데이터 추가
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)",
                  ("Charlie", "charlie@example.com"))
    cursor.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
                  ("Mouse", 29.99, "Wireless mouse"))

    conn.commit()
    conn.close()

    print(f"데이터베이스 수정 완료: {db_path}")


def example_basic_backup():
    """기본 백업 예제"""
    print("\n" + "="*50)
    print("예제 1: 기본 백업 및 복구")
    print("="*50)

    # 샘플 데이터베이스 생성
    db_path = "sample.db"
    create_sample_database(db_path)

    # 백업 매니저 초기화
    backup_manager = DatabaseBackupManager(
        backup_dir="example_backups",
        compress=True,
        max_backups=10
    )

    # 전체 백업 생성
    print("\n전체 백업 생성 중...")
    full_backup = backup_manager.create_full_backup(
        db_path,
        description="초기 전체 백업",
        tags=["initial", "full"]
    )

    if full_backup:
        print(f"전체 백업 완료: {full_backup.backup_id}")
        print(f"  크기: {full_backup.size_bytes:,} bytes")
        print(f"  압축 크기: {full_backup.compressed_size:,} bytes")
        print(f"  압축률: {(1 - full_backup.compressed_size / full_backup.size_bytes) * 100:.1f}%")

    # 데이터베이스 수정
    print("\n데이터베이스 수정 중...")
    modify_database(db_path)

    # 증분 백업 생성
    print("\n증분 백업 생성 중...")
    incremental_backup = backup_manager.create_incremental_backup(
        db_path,
        description="수정 사항 증분 백업",
        tags=["incremental"]
    )

    if incremental_backup:
        print(f"증분 백업 완료: {incremental_backup.backup_id}")

    # 백업 목록 조회
    print("\n백업 목록:")
    backups = backup_manager.list_backups()
    for backup in backups:
        print(f"  - {backup.backup_id} ({backup.backup_type.value}) - {backup.timestamp}")

    # 백업 통계
    stats = backup_manager.get_backup_stats()
    print(f"\n백업 통계:")
    print(f"  전체 백업: {stats['full_backups']}개")
    print(f"  증분 백업: {stats['incremental_backups']}개")
    print(f"  총 크기: {stats['total_size_bytes']:,} bytes")
    print(f"  압축 크기: {stats['total_compressed_size_bytes']:,} bytes")
    print(f"  압축률: {stats['compression_ratio']}")

    # 백업 무결성 검증
    if full_backup:
        print(f"\n백업 무결성 검증: {full_backup.backup_id}")
        is_valid = backup_manager.verify_backup(full_backup.backup_id)
        print(f"  검증 결과: {'통과' if is_valid else '실패'}")


def example_scheduled_backup():
    """스케줄 백업 예제"""
    print("\n" + "="*50)
    print("예제 2: 스케줄 백업")
    print("="*50)

    # 샘플 데이터베이스
    db_path = "sample.db"

    # 백업 매니저 및 스케줄러 초기화
    backup_manager = DatabaseBackupManager(
        backup_dir="example_backups",
        compress=True
    )

    scheduler = BackupScheduler(backup_manager)

    # 기본 스케줄 생성
    print("\n기본 백업 스케줄 생성...")
    create_default_schedules(scheduler, db_path)

    # 사용자 정의 스케줄 추가
    print("\n사용자 정의 스케줄 추가...")
    scheduler.add_schedule(
        schedule_type=ScheduleType.FULL,
        database_path=db_path,
        interval="daily",
        time="01:00",
        description="심야 전체 백업",
        tags=["nightly", "full"]
    )

    # 스케줄 목록 조회
    schedules = scheduler.list_schedules()
    print(f"\n등록된 스케줄: {len(schedules)}개")
    for sched in schedules:
        print(f"  - {sched.schedule_id}")
        print(f"    타입: {sched.schedule_type.value}")
        print(f"    주기: {sched.interval} {sched.time or ''}")
        print(f"    활성화: {sched.enabled}")

    # 스케줄 상태
    status = scheduler.get_schedule_status()
    print(f"\n스케줄러 상태:")
    print(f"  실행 중: {status['running']}")
    print(f"  활성화된 스케줄: {status['enabled_schedules']}개")
    print(f"  비활성화된 스케줄: {status['disabled_schedules']}개")

    # 스케줄러 시작
    print("\n스케줄러 시작...")
    scheduler.start()

    # 즉시 실행 테스트
    print("\n스케줄 즉시 실행 테스트...")
    if schedules:
        backup_id = scheduler.run_now(schedules[0].schedule_id)
        if backup_id:
            print(f"  백업 완료: {backup_id}")
        else:
            print("  백업 실패")

    # 스케줄러 정지
    print("\n스케줄러 정지...")
    scheduler.stop()


def example_recovery():
    """복구 예제"""
    print("\n" + "="*50)
    print("예제 3: 데이터베이스 복구")
    print("="*50)

    db_path = "sample.db"

    # 백업 매니저 및 복구 매니저 초기화
    backup_manager = DatabaseBackupManager(
        backup_dir="example_backups",
        compress=True
    )

    restorer = DatabaseRestorer(backup_manager)

    # 복구 가능한 포인트 조회
    print("\n복구 가능한 포인트:")
    recovery_points = restorer.list_recovery_points(db_path)

    for i, point in enumerate(recovery_points[:5], 1):
        status = "복구 가능" if point.is_restorable else "복구 불가"
        print(f"  {i}. {point.backup_id}")
        print(f"     시간: {point.timestamp}")
        print(f"     타입: {point.backup_type.value}")
        print(f"     상태: {status}")

    # 복구 추천
    print("\n복구 추천:")
    recommendations = restorer.get_recovery_recommendations(db_path, max_recommendations=3)

    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec['backup_id']}")
        print(f"     시간: {rec['timestamp']}")
        print(f"     점수: {rec['score']}")
        print(f"     사유: {rec['recommendation_reason']}")

    # 복구 테스트 (샘플 데이터베이스 백업 생성)
    print("\n복구 테스트...")

    # 테스트용 백업 생성
    if recovery_points:
        backup_id = recovery_points[0].backup_id

        # 복구 (안전 백업 생성)
        restore_path = "restored_sample.db"

        success = restorer.restore_to_point(
            backup_id,
            restore_path=restore_path,
            create_safety_backup=True,
            verify_after_restore=True
        )

        if success:
            print(f"복구 성공: {backup_id} -> {restore_path}")

            # 복구된 데이터베이스 확인
            if os.path.exists(restore_path):
                conn = sqlite3.connect(restore_path)
                cursor = conn.cursor()

                # 사용자 수 확인
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]

                print(f"복구된 사용자 수: {user_count}")

                conn.close()
        else:
            print("복구 실패")


def example_backup_comparison():
    """백업 비교 예제"""
    print("\n" + "="*50)
    print("예제 4: 백업 비교")
    print("="*50)

    backup_manager = DatabaseBackupManager(
        backup_dir="example_backups"
    )

    restorer = DatabaseRestorer(backup_manager)

    # 백업 목록
    backups = backup_manager.list_backups()

    if len(backups) >= 2:
        # 첫 번째와 마지막 백업 비교
        backup1 = backups[-1]
        backup2 = backups[0]

        print(f"\n백업 비교: {backup1.backup_id} vs {backup2.backup_id}")

        comparison = restorer.compare_backups(backup1.backup_id, backup2.backup_id)

        print(f"  시간 차이: {comparison['time_diff_readable']}")
        print(f"  크기 차이: {comparison['size_diff_bytes']:,} bytes ({comparison['size_diff_percentage']:.1f}%)")
        print(f"  타입: {comparison['type1']} vs {comparison['type2']}")


def example_cleanup():
    """정리 예제"""
    print("\n" + "="*50)
    print("예제 5: 백업 정리")
    print("="*50)

    backup_manager = DatabaseBackupManager(
        backup_dir="example_backups",
        max_backups=3  # 최대 3개만 유지
    )

    # 현재 백업 수
    current_count = len(backup_manager.list_backups())
    print(f"현재 백업 수: {current_count}개")

    # 새 백업 생성 (자동 정리 트리거)
    db_path = "sample.db"
    if os.path.exists(db_path):
        print("\n새 백업 생성 (자동 정리 트리거)...")
        backup_manager.create_full_backup(
            db_path,
            description="정리 테스트 백업"
        )

        # 정리 후 백업 수
        new_count = len(backup_manager.list_backups())
        print(f"정리 후 백업 수: {new_count}개")


def setup_logging():
    """로깅 설정"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 로그 디렉토리 생성
    os.makedirs('backups', exist_ok=True)

    # 파일 핸들러
    file_handler = logging.FileHandler(
        'backups/backup.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)

    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)


def main():
    """메인 함수"""
    print("데이터베이스 백업 및 복구 시스템 예제")

    # 로깅 설정
    setup_logging()

    try:
        # 예제 실행
        example_basic_backup()
        example_scheduled_backup()
        example_recovery()
        example_backup_comparison()
        example_cleanup()

        print("\n" + "="*50)
        print("모든 예제 실행 완료!")
        print("="*50)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()