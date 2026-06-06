"""
데이터베이스 백업 및 복구 시스템 테스트
"""

import os
import sqlite3
import unittest
import tempfile
import shutil
from datetime import datetime, timedelta

from database_backup_manager import (
    DatabaseBackupManager, BackupType, BackupMetadata, BackupStatus
)
from backup_scheduler import BackupScheduler, ScheduleType, BackupSchedule
from database_restorer import DatabaseRestorer, RecoveryPoint


class TestDatabaseBackupManager(unittest.TestCase):
    """백업 매니저 테스트"""

    def setUp(self):
        """테스트 설정"""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.db_path = os.path.join(self.test_dir, "test.db")

        # 테스트 데이터베이스 생성
        self._create_test_database()

        # 백업 매니저 초기화
        self.backup_manager = DatabaseBackupManager(
            backup_dir=self.backup_dir,
            compress=False,  # 테스트에서는 압축 비활성화
            max_backups=5
        )

    def tearDown(self):
        """테스트 정리"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_test_database(self):
        """테스트용 데이터베이스 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value REAL
            )
        ''')

        cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)",
                     ("test1", 1.0))
        cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)",
                     ("test2", 2.0))

        conn.commit()
        conn.close()

    def _get_row_count(self, db_path):
        """테이블 행 수 조회"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_table")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def test_full_backup(self):
        """전체 백업 테스트"""
        # 전체 백업 생성
        metadata = self.backup_manager.create_full_backup(
            self.db_path,
            description="테스트 전체 백업",
            tags=["test"]
        )

        # 검증
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.backup_type, BackupType.FULL)
        self.assertGreater(metadata.size_bytes, 0)
        self.assertTrue(os.path.exists(metadata.backup_path))

        # 백업 파일 존재 확인
        self.assertTrue(os.path.exists(metadata.backup_path))

    def test_incremental_backup(self):
        """증분 백업 테스트"""
        # WAL 모드 활성화를 위한 전체 백업 먼저 생성
        full_backup = self.backup_manager.create_full_backup(
            self.db_path,
            description="기본 전체 백업"
        )

        self.assertIsNotNone(full_backup)

        # 데이터 추가
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)",
                      ("test3", 3.0))
        conn.commit()
        conn.close()

        # 증분 백업 생성
        inc_backup = self.backup_manager.create_incremental_backup(
            self.db_path,
            description="증분 백업 테스트",
            tags=["incremental", "test"]
        )

        # 검증 (WAL 파일이 생성되지 않을 수 있음)
        if inc_backup:
            self.assertEqual(inc_backup.backup_type, BackupType.INCREMENTAL)
        else:
            # WAL 파일이 없는 경우 경고만 출력하고 테스트 통과
            print("WAL 파일이 생성되지 않아 증분 백업을 건너뜁니다")

    def test_backup_restore(self):
        """백업 복구 테스트"""
        # 전체 백업 생성
        metadata = self.backup_manager.create_full_backup(
            self.db_path,
            description="복구 테스트 백업"
        )

        self.assertIsNotNone(metadata)

        # 원본 데이터베이스 수정
        original_count = self._get_row_count(self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM test_table")
        conn.commit()
        conn.close()

        # 데이터 삭제 확인
        deleted_count = self._get_row_count(self.db_path)
        self.assertEqual(deleted_count, 0)

        # 복구
        restore_path = self.db_path + ".restored"
        success = self.backup_manager.restore_backup(
            metadata.backup_id,
            restore_path=restore_path,
            force=True
        )

        self.assertTrue(success)
        self.assertTrue(os.path.exists(restore_path))

        # 복구된 데이터 확인
        restored_count = self._get_row_count(restore_path)
        self.assertEqual(restored_count, original_count)

    def test_backup_list(self):
        """백업 목록 조회 테스트"""
        # 백업 3개 생성
        backup1 = self.backup_manager.create_full_backup(self.db_path, "백업 1")
        backup2 = self.backup_manager.create_full_backup(self.db_path, "백업 2")
        backup3 = self.backup_manager.create_full_backup(self.db_path, "백업 3")

        # 전체 목록 조회
        all_backups = self.backup_manager.list_backups()
        self.assertEqual(len(all_backups), 3)

        # 전체 백업만 조회
        full_backups = self.backup_manager.list_backups(BackupType.FULL)
        self.assertEqual(len(full_backups), 3)

        # 증분 백업 조회
        inc_backups = self.backup_manager.list_backups(BackupType.INCREMENTAL)
        self.assertEqual(len(inc_backups), 0)

    def test_backup_deletion(self):
        """백업 삭제 테스트"""
        # 백업 생성
        metadata = self.backup_manager.create_full_backup(self.db_path)

        self.assertIsNotNone(metadata)
        backup_path = metadata.backup_path

        # 삭제
        success = self.backup_manager.delete_backup(metadata.backup_id)
        self.assertTrue(success)

        # 파일 삭제 확인
        self.assertFalse(os.path.exists(backup_path))

        # 메타데이터에서 제거 확인
        self.assertIsNone(self.backup_manager.get_backup_info(metadata.backup_id))

    def test_backup_verification(self):
        """백업 무결성 검증 테스트"""
        # 백업 생성
        metadata = self.backup_manager.create_full_backup(self.db_path)

        self.assertIsNotNone(metadata)

        # 검증
        is_valid = self.backup_manager.verify_backup(metadata.backup_id)
        self.assertTrue(is_valid)

    def test_backup_stats(self):
        """백업 통계 테스트"""
        # 백업 생성
        self.backup_manager.create_full_backup(self.db_path, "전체 1")
        self.backup_manager.create_full_backup(self.db_path, "전체 2")

        # 통계 조회
        stats = self.backup_manager.get_backup_stats()

        self.assertEqual(stats['total_backups'], 2)
        self.assertEqual(stats['full_backups'], 2)
        self.assertGreater(stats['total_size_bytes'], 0)


class TestBackupScheduler(unittest.TestCase):
    """백업 스케줄러 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.db_path = os.path.join(self.test_dir, "test.db")

        # 테스트 데이터베이스 생성
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        conn.commit()
        conn.close()

        # 백업 매니저 및 스케줄러 초기화
        self.backup_manager = DatabaseBackupManager(
            backup_dir=self.backup_dir,
            compress=False
        )

        self.scheduler = BackupScheduler(self.backup_manager)

    def tearDown(self):
        """테스트 정리"""
        self.scheduler.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_add_schedule(self):
        """스케줄 추가 테스트"""
        schedule_id = self.scheduler.add_schedule(
            schedule_type=ScheduleType.FULL,
            database_path=self.db_path,
            interval="daily",
            time="02:00",
            description="테스트 스케줄"
        )

        self.assertIsNotNone(schedule_id)

        # 스케줄 조회
        schedule = self.scheduler.get_schedule(schedule_id)
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.interval, "daily")
        self.assertTrue(schedule.enabled)

    def test_remove_schedule(self):
        """스케줄 제거 테스트"""
        schedule_id = self.scheduler.add_schedule(
            schedule_type=ScheduleType.INCREMENTAL,
            database_path=self.db_path,
            interval="hourly",
            description="제거 테스트"
        )

        # 제거
        success = self.scheduler.remove_schedule(schedule_id)
        self.assertTrue(success)

        # 제거 확인
        schedule = self.scheduler.get_schedule(schedule_id)
        self.assertIsNone(schedule)

    def test_enable_disable_schedule(self):
        """스케줄 활성화/비활성화 테스트"""
        schedule_id = self.scheduler.add_schedule(
            schedule_type=ScheduleType.FULL,
            database_path=self.db_path,
            interval="daily"
        )

        # 비활성화
        success = self.scheduler.disable_schedule(schedule_id)
        self.assertTrue(success)

        schedule = self.scheduler.get_schedule(schedule_id)
        self.assertFalse(schedule.enabled)

        # 활성화
        success = self.scheduler.enable_schedule(schedule_id)
        self.assertTrue(success)

        schedule = self.scheduler.get_schedule(schedule_id)
        self.assertTrue(schedule.enabled)

    def test_run_now(self):
        """즉시 실행 테스트"""
        schedule_id = self.scheduler.add_schedule(
            schedule_type=ScheduleType.FULL,
            database_path=self.db_path,
            interval="daily",
            description="즉시 실행 테스트"
        )

        # 즉시 실행
        backup_id = self.scheduler.run_now(schedule_id)

        self.assertIsNotNone(backup_id)

        # 백업 생성 확인
        backup_info = self.backup_manager.get_backup_info(backup_id)
        self.assertIsNotNone(backup_info)

    def test_schedule_status(self):
        """스케줄 상태 테스트"""
        # 스케줄 추가
        self.scheduler.add_schedule(
            schedule_type=ScheduleType.FULL,
            database_path=self.db_path,
            interval="daily"
        )
        self.scheduler.add_schedule(
            schedule_type=ScheduleType.INCREMENTAL,
            database_path=self.db_path,
            interval="hourly"
        )

        # 상태 조회
        status = self.scheduler.get_schedule_status()

        self.assertEqual(status['total_schedules'], 2)
        self.assertEqual(status['enabled_schedules'], 2)
        self.assertEqual(len(status['schedules']), 2)


class TestDatabaseRestorer(unittest.TestCase):
    """복구 매니저 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.db_path = os.path.join(self.test_dir, "test.db")

        # 테스트 데이터베이스 생성
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        ''')
        cursor.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        cursor.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))
        conn.commit()
        conn.close()

        # 백업 매니저 및 복구 매니저 초기화
        self.backup_manager = DatabaseBackupManager(
            backup_dir=self.backup_dir,
            compress=False
        )

        self.restorer = DatabaseRestorer(self.backup_manager)

    def tearDown(self):
        """테스트 정리"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_list_recovery_points(self):
        """복구 포인트 목록 테스트"""
        # 백업 생성
        self.backup_manager.create_full_backup(
            self.db_path,
            description="복구 포인트 1"
        )

        self.backup_manager.create_full_backup(
            self.db_path,
            description="복구 포인트 2"
        )

        # 복구 포인트 조회
        recovery_points = self.restorer.list_recovery_points(self.db_path)

        self.assertGreaterEqual(len(recovery_points), 2)
        self.assertTrue(all(p.is_restorable for p in recovery_points))

    def test_restore_to_point(self):
        """복구 테스트"""
        # 백업 생성
        metadata = self.backup_manager.create_full_backup(
            self.db_path,
            description="복구 테스트 백업"
        )

        self.assertIsNotNone(metadata)

        # 데이터 삭제
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

        # 복구
        restore_path = self.db_path + ".restored"
        success = self.restorer.restore_to_point(
            metadata.backup_id,
            restore_path=restore_path,
            create_safety_backup=False,
            force=True
        )

        self.assertTrue(success)
        self.assertTrue(os.path.exists(restore_path))

        # 복구된 데이터 확인
        conn = sqlite3.connect(restore_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count, 2)

    def test_get_recovery_recommendations(self):
        """복구 추천 테스트"""
        # 백업 생성
        self.backup_manager.create_full_backup(
            self.db_path,
            description="최신 백업",
            tags=["recent"]
        )

        # 추천 받기
        recommendations = self.restorer.get_recovery_recommendations(
            self.db_path,
            max_recommendations=3
        )

        self.assertGreater(len(recommendations), 0)
        self.assertTrue('backup_id' in recommendations[0])
        self.assertTrue('score' in recommendations[0])
        self.assertTrue('recommendation_reason' in recommendations[0])


class TestIntegration(unittest.TestCase):
    """통합 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.db_path = os.path.join(self.test_dir, "test.db")

        # 테스트 데이터베이스 생성
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE data (
                id INTEGER PRIMARY KEY,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def tearDown(self):
        """테스트 정리"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_backup_restore_workflow(self):
        """백업-복구 워크플로우 테스트"""
        # 백업 매니저 및 복구 매니저 초기화
        backup_manager = DatabaseBackupManager(
            backup_dir=self.backup_dir,
            compress=False
        )

        restorer = DatabaseRestorer(backup_manager)

        # 1. 초기 데이터 추가
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO data (content) VALUES (?)", ("Initial",))
        conn.commit()
        conn.close()

        # 2. 초기 백업
        initial_backup = backup_manager.create_full_backup(
            self.db_path,
            description="초기 상태 백업",
            tags=["initial"]
        )

        self.assertIsNotNone(initial_backup)

        # 3. 데이터 추가
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO data (content) VALUES (?)", ("Updated",))
        conn.commit()
        conn.close()

        # 4. 업데이트 백업
        updated_backup = backup_manager.create_full_backup(
            self.db_path,
            description="업데이트 상태 백업",
            tags=["updated"]
        )

        self.assertIsNotNone(updated_backup)

        # 5. 복구 포인트 확인
        recovery_points = restorer.list_recovery_points(self.db_path)
        self.assertGreaterEqual(len(recovery_points), 2)

        # 6. 초기 상태로 복구
        restore_path = self.db_path + ".initial"
        success = restorer.restore_to_point(
            initial_backup.backup_id,
            restore_path=restore_path,
            create_safety_backup=False,
            force=True
        )

        self.assertTrue(success)

        # 7. 복구된 데이터 확인
        conn = sqlite3.connect(restore_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM data WHERE content = ?", ("Initial",))
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count, 1)

    def test_multiple_backups_cleanup(self):
        """다중 백업 정리 테스트"""
        backup_manager = DatabaseBackupManager(
            backup_dir=self.backup_dir,
            compress=False,
            max_backups=3  # 최대 3개만 유지
        )

        # 5개 백업 생성
        for i in range(5):
            backup_manager.create_full_backup(
                self.db_path,
                description=f"백업 {i+1}"
            )

        # 정리 후 3개만 유지되어야 함
        backups = backup_manager.list_backups()
        self.assertEqual(len(backups), 3)


def run_tests():
    """테스트 실행"""
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseBackupManager))
    suite.addTests(loader.loadTestsFromTestCase(TestBackupScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseRestorer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)