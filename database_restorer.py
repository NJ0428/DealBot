"""
데이터베이스 복구 관리자

데이터베이스 복구 기능을 제공합니다.
- 백업 파일 선택 및 복구
- 증분 백업 체인 복구
- 특정 시점으로 복구 (Point-in-Time Recovery)
- 복구 전 백업 (Safety Backup)
- 복구 유효성 검사
"""

import os
import sqlite3
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import threading

from database_backup_manager import DatabaseBackupManager, BackupType, BackupMetadata


class RecoveryPointType(Enum):
    """복구 포인트 타입"""
    FULL = "full"              # 전체 백업
    INCREMENTAL = "incremental"  # 증분 백업
    CUSTOM = "custom"          # 사용자 지정 시점


@dataclass
class RecoveryPoint:
    """복구 포인트"""
    backup_id: str
    timestamp: str
    backup_type: BackupType
    description: str
    size_bytes: int
    is_restorable: bool = True

    def __str__(self):
        return f"{self.backup_id} ({self.timestamp}) - {self.description}"


class DatabaseRestorer:
    """데이터베이스 복구 관리자"""

    def __init__(self, backup_manager: DatabaseBackupManager):
        """
        복구 매니저 초기화

        Args:
            backup_manager: 백업 매니저 인스턴스
        """
        self.backup_manager = backup_manager
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

        # 복구 히스토리
        self.recovery_history: List[Dict] = []
        self._load_recovery_history()

    def _load_recovery_history(self):
        """복구 히스토리 로드"""
        history_file = self.backup_manager.backup_dir / "recovery_history.json"

        if history_file.exists():
            try:
                import json
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.recovery_history = json.load(f)
            except Exception as e:
                self.logger.error(f"복구 히스토리 로드 실패: {e}")

    def _save_recovery_history(self):
        """복구 히스토리 저장"""
        history_file = self.backup_manager.backup_dir / "recovery_history"

        try:
            import json
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.recovery_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"복구 히스토리 저장 실패: {e}")

    def list_recovery_points(self, database_path: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[RecoveryPoint]:
        """
        복구 가능한 포인트 목록 조회

        Args:
            database_path: 필터링할 데이터베이스 경로
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            복구 포인트 리스트
        """
        backups = self.backup_manager.list_backups()

        recovery_points = []

        for backup in backups:
            # 데이터베이스 경로 필터링
            if database_path and backup.database_path != database_path:
                continue

            # 날짜 필터링
            backup_time = datetime.fromisoformat(backup.timestamp)

            if start_date and backup_time < start_date:
                continue

            if end_date and backup_time > end_date:
                continue

            # 복구 가능성 확인
            is_restorable = True

            # 증분 백업은 이전 전체 백업이 있어야 복구 가능
            if backup.backup_type == BackupType.INCREMENTAL:
                # 이전 전체 백업 찾기
                has_base_backup = any(
                    b.backup_type == BackupType.FULL and
                    datetime.fromisoformat(b.timestamp) < backup_time and
                    b.database_path == backup.database_path
                    for b in backups
                )

                if not has_base_backup:
                    is_restorable = False

            recovery_points.append(RecoveryPoint(
                backup_id=backup.backup_id,
                timestamp=backup.timestamp,
                backup_type=backup.backup_type,
                description=backup.description or f"{backup.backup_type.value} backup",
                size_bytes=backup.size_bytes,
                is_restorable=is_restorable
            ))

        # 시간순 정렬 (최신순)
        recovery_points.sort(key=lambda x: x.timestamp, reverse=True)

        return recovery_points

    def restore_to_point(self, backup_id: str, restore_path: Optional[str] = None,
                        create_safety_backup: bool = True,
                        force: bool = False,
                        verify_after_restore: bool = True) -> bool:
        """
        특정 복구 포인트로 복구

        Args:
            backup_id: 복구할 백업 ID
            restore_path: 복구 경로 (None이면 원본 위치)
            create_safety_backup: 복구 전 안전 백업 생성
            force: 기존 파일 덮어쓰기
            verify_after_restore: 복구 후 무결성 검사

        Returns:
            성공 여부
        """
        with self._lock:
            try:
                self.logger.info(f"복구 시작: {backup_id}")

                # 백업 메타데이터 조회
                metadata = self.backup_manager.get_backup_info(backup_id)

                if not metadata:
                    self.logger.error(f"백업을 찾을 수 없습니다: {backup_id}")
                    return False

                target_path = restore_path or metadata.database_path

                # 복구 전 안전 백업
                safety_backup_id = None
                if create_safety_backup and os.path.exists(target_path):
                    self.logger.info("복구 전 안전 백업 생성 중...")

                    if metadata.backup_type == BackupType.FULL:
                        safety_meta = self.backup_manager.create_full_backup(
                            target_path,
                            description=f"복구 전 안전 백업 (복구 대상: {backup_id})",
                            tags=["safety", "pre-recovery"]
                        )
                    else:
                        safety_meta = self.backup_manager.create_incremental_backup(
                            target_path,
                            description=f"복구 전 안전 백업 (복구 대상: {backup_id})",
                            tags=["safety", "pre-recovery"]
                        )

                    if safety_meta:
                        safety_backup_id = safety_meta.backup_id
                        self.logger.info(f"안전 백업 완료: {safety_backup_id}")
                    else:
                        self.logger.warning("안전 백업 생성 실패, 복구 계속 진행")

                # 복구 실행
                success = False

                if metadata.backup_type == BackupType.FULL:
                    # 전체 백업 복구
                    success = self.backup_manager.restore_backup(
                        backup_id, restore_path, force
                    )
                else:
                    # 증분 백업 복구 (체인 복구)
                    # 가장 최근 전체 백업 찾기
                    backup_time = datetime.fromisoformat(metadata.timestamp)
                    full_backups = [
                        b for b in self.backup_manager.list_backups(BackupType.FULL)
                        if (datetime.fromisoformat(b.timestamp) < backup_time and
                            b.database_path == metadata.database_path)
                    ]

                    if not full_backups:
                        self.logger.error("증분 백업을 위한 기본 전체 백업을 찾을 수 없습니다")
                        return False

                    # 가장 최근 전체 백업 선택
                    base_full_backup = max(full_backups, key=lambda x: x.timestamp)

                    self.logger.info(f"기본 전체 백업: {base_full_backup.backup_id}")

                    # 체인 복구
                    success = self.backup_manager.restore_incremental_chain(
                        base_full_backup.backup_id, restore_path, force
                    )

                if not success:
                    self.logger.error("복구 실패")
                    return False

                # 복구 후 검증
                if verify_after_restore and success:
                    self.logger.info("복구 후 무결성 검사 중...")

                    if not self._verify_restored_database(target_path):
                        self.logger.error("복구된 데이터베이스 무결성 검사 실패")

                        # 안전 백업으로 복원 시도
                        if safety_backup_id:
                            self.logger.info("안전 백업으로 복원 시도 중...")
                            self.backup_manager.restore_backup(
                                safety_backup_id, target_path, force=True
                            )

                        return False

                    self.logger.info("복구된 데이터베이스 무결성 검사 완료")

                # 복구 히스토리 기록
                self.recovery_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'backup_id': backup_id,
                    'restore_path': target_path,
                    'safety_backup_id': safety_backup_id,
                    'success': True
                })
                self._save_recovery_history()

                self.logger.info(f"복구 완료: {backup_id} -> {target_path}")

                # 안전 백업 ID 반환
                if safety_backup_id:
                    self.logger.info(f"안전 백업 ID: {safety_backup_id}")

                return True

            except Exception as e:
                self.logger.error(f"복구 중 오류 발생: {e}")
                return False

    def restore_to_time(self, target_time: datetime, database_path: str,
                       restore_path: Optional[str] = None,
                       create_safety_backup: bool = True) -> bool:
        """
        특정 시점으로 복구 (Point-in-Time Recovery)

        Args:
            target_time: 복구할 시점
            database_path: 데이터베이스 경로
            restore_path: 복구 경로
            create_safety_backup: 복구 전 안전 백업 생성

        Returns:
            성공 여부
        """
        self.logger.info(f"시점 복구 시작: {target_time}")

        # 타겟 시점 이전의 백업 찾기
        backups = self.backup_manager.list_backups()

        candidates = [
            b for b in backups
            if (datetime.fromisoformat(b.timestamp) <= target_time and
                b.database_path == database_path)
        ]

        if not candidates:
            self.logger.error(f"시점 {target_time} 이전의 백업을 찾을 수 없습니다")
            return False

        # 가장 가까운 전체 백업 찾기
        full_backups = [
            b for b in candidates
            if b.backup_type == BackupType.FULL
        ]

        if not full_backups:
            self.logger.error("복구 가능한 전체 백업을 찾을 수 없습니다")
            return False

        # 가장 최근 전체 백업 선택
        base_backup = max(full_backups, key=lambda x: x.timestamp)

        self.logger.info(f"기본 전체 백업: {base_backup.backup_id} ({base_backup.timestamp})")

        # 체인 복구 수행
        success = self.restore_to_point(
            base_backup.backup_id,
            restore_path,
            create_safety_backup,
            verify_after_restore=True
        )

        if not success:
            return False

        # 증분 백업 순차 적용 (타겟 시점까지)
        target_path = restore_path or database_path

        incremental_backups = [
            b for b in candidates
            if (b.backup_type == BackupType.INCREMENTAL and
                datetime.fromisoformat(b.timestamp) > datetime.fromisoformat(base_backup.timestamp))
        ]

        # 시간순 정렬
        incremental_backups.sort(key=lambda x: x.timestamp)

        # 타겟 시점까지의 증분 백업만 적용
        applied_count = 0
        for inc_backup in incremental_backups:
            if datetime.fromisoformat(inc_backup.timestamp) <= target_time:
                self.logger.info(f"증분 백업 적용: {inc_backup.backup_id}")

                # WAL 파일 복원
                wal_backup_path = inc_backup.backup_path
                wal_restore_path = target_path + "-wal"

                try:
                    if wal_backup_path.endswith('.gz'):
                        self.backup_manager._decompress_file(wal_backup_path, wal_restore_path)
                    else:
                        shutil.copy2(wal_backup_path, wal_restore_path)

                    applied_count += 1

                except Exception as e:
                    self.logger.error(f"WAL 파일 적용 실패: {e}")
            else:
                break  # 타겟 시점 초과

        self.logger.info(f"시점 복구 완료. 적용된 증분 백업: {applied_count}개")

        return True

    def _verify_restored_database(self, db_path: str) -> bool:
        """
        복구된 데이터베이스 무결성 검사

        Args:
            db_path: 데이터베이스 경로

        Returns:
            무결성 여부
        """
        try:
            if not os.path.exists(db_path):
                self.logger.error(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
                return False

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 1. 무결성 검사
            self.logger.info("데이터베이스 무결성 검사 중...")
            result = cursor.execute("PRAGMA integrity_check").fetchall()

            if result[0][0] != "ok":
                self.logger.error(f"무결성 검사 실패: {result}")
                conn.close()
                return False

            # 2. 외래키 검사
            self.logger.info("외래키 검사 중...")
            result = cursor.execute("PRAGMA foreign_key_check").fetchall()

            if result:
                self.logger.error(f"외래키 검사 실패: {result}")
                conn.close()
                return False

            # 3. 빠른 검사 (quick_test)
            self.logger.info("빠른 검사 중...")
            cursor.execute("PRAGMA quick_check")
            result = cursor.fetchall()

            if result[0][0] != "ok":
                self.logger.error(f"빠른 검사 실패: {result}")
                conn.close()
                return False

            # 4. 테이블 목록 확인
            self.logger.info("테이블 확인 중...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            self.logger.info(f"발견된 테이블: {len(tables)}개")

            # 5. 기본 통계
            cursor.execute("SELECT COUNT(*) FROM sqlite_master")
            object_count = cursor.fetchone()[0]
            self.logger.info(f"데이터베이스 객체 수: {object_count}")

            conn.close()

            self.logger.info("복구된 데이터베이스 검증 완료")
            return True

        except Exception as e:
            self.logger.error(f"데이터베이스 검증 중 오류: {e}")
            return False

    def compare_backups(self, backup_id1: str, backup_id2: str) -> Dict:
        """
        두 백업 비교

        Args:
            backup_id1: 첫 번째 백업 ID
            backup_id2: 두 번째 백업 ID

        Returns:
            비교 결과
        """
        metadata1 = self.backup_manager.get_backup_info(backup_id1)
        metadata2 = self.backup_manager.get_backup_info(backup_id2)

        if not metadata1 or not metadata2:
            return {'error': '백업을 찾을 수 없습니다'}

        time1 = datetime.fromisoformat(metadata1.timestamp)
        time2 = datetime.fromisoformat(metadata2.timestamp)
        time_diff = abs((time2 - time1).total_seconds())

        return {
            'backup_id1': backup_id1,
            'backup_id2': backup_id2,
            'time_diff_seconds': time_diff,
            'time_diff_readable': str(timedelta(seconds=int(time_diff))),
            'size_diff_bytes': metadata2.size_bytes - metadata1.size_bytes,
            'size_diff_percentage': ((metadata2.size_bytes - metadata1.size_bytes) /
                                    metadata1.size_bytes * 100) if metadata1.size_bytes > 0 else 0,
            'type1': metadata1.backup_type.value,
            'type2': metadata2.backup_type.value,
            'description1': metadata1.description,
            'description2': metadata2.description
        }

    def get_recovery_recommendations(self, database_path: str,
                                    max_recommendations: int = 5) -> List[Dict]:
        """
        복구 추천 목록 제공

        Args:
            database_path: 데이터베이스 경로
            max_recommendations: 최대 추천 수

        Returns:
            추천 복구 포인트 리스트
        """
        recovery_points = self.list_recovery_points(database_path)

        # 우선순위 계산
        scored_points = []

        for point in recovery_points:
            if not point.is_restorable:
                continue

            score = 0

            # 전체 백업 우선
            if point.backup_type == BackupType.FULL:
                score += 100

            # 최근 백업 우선
            age_hours = (datetime.now() - datetime.fromisoformat(point.timestamp)).total_seconds() / 3600
            if age_hours < 24:
                score += 50
            elif age_hours < 168:  # 1주일 이내
                score += 30

            # 크기 고려 (너무 작으면 불완전할 수 있음)
            if point.size_bytes > 1024 * 1024:  # 1MB 이상
                score += 20

            scored_points.append({
                'point': point,
                'score': score,
                'age_hours': age_hours
            })

        # 점수순 정렬
        scored_points.sort(key=lambda x: x['score'], reverse=True)

        # 추천 목록 생성
        recommendations = []

        for item in scored_points[:max_recommendations]:
            point = item['point']

            recommendations.append({
                'backup_id': point.backup_id,
                'timestamp': point.timestamp,
                'type': point.backup_type.value,
                'description': point.description,
                'score': item['score'],
                'age_hours': item['age_hours'],
                'size_mb': point.size_bytes / (1024 * 1024),
                'recommendation_reason': self._get_recommendation_reason(point, item['score'], item['age_hours'])
            })

        return recommendations

    def _get_recommendation_reason(self, point: RecoveryPoint, score: int, age_hours: float) -> str:
        """추천 사유 생성"""
        reasons = []

        if point.backup_type == BackupType.FULL:
            reasons.append("전체 백업으로 안전한 복구 가능")

        if age_hours < 24:
            reasons.append("최신 백업으로 데이터 손실 최소화")
        elif age_hours < 168:
            reasons.append("최근 1주 이내의 백업")

        if point.size_bytes > 1024 * 1024:
            reasons.append("완전한 백업 파일")

        if not reasons:
            reasons.append("일반 복구 포인트")

        return ", ".join(reasons)

    def rollback_to_safety_backup(self, safety_backup_id: str,
                                 target_path: Optional[str] = None,
                                 force: bool = False) -> bool:
        """
        안전 백업으로 롤백

        Args:
            safety_backup_id: 안전 백업 ID
            target_path: 롤백 경로
            force: 기존 파일 덮어쓰기

        Returns:
            성공 여부
        """
        self.logger.info(f"안전 백업으로 롤백: {safety_backup_id}")

        safety_backup = self.backup_manager.get_backup_info(safety_backup_id)

        if not safety_backup:
            self.logger.error(f"안전 백업을 찾을 수 없습니다: {safety_backup_id}")
            return False

        if "safety" not in safety_backup.tags and "pre-recovery" not in safety_backup.tags:
            self.logger.warning("안전 백업 태그가 없습니다")

        return self.backup_manager.restore_backup(
            safety_backup_id,
            target_path,
            force
        )

    def export_backup(self, backup_id: str, export_path: str) -> bool:
        """
        백업 파일 내보내기

        Args:
            backup_id: 내보낼 백업 ID
            export_path: 내보내기 경로

        Returns:
            성공 여부
        """
        try:
            metadata = self.backup_manager.get_backup_info(backup_id)

            if not metadata:
                self.logger.error(f"백업을 찾을 수 없습니다: {backup_id}")
                return False

            backup_path = metadata.backup_path

            if not os.path.exists(backup_path):
                self.logger.error(f"백업 파일이 존재하지 않습니다: {backup_path}")
                return False

            shutil.copy2(backup_path, export_path)

            self.logger.info(f"백업 내보내기 완료: {backup_id} -> {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"백업 내보내기 실패: {e}")
            return False

    def import_backup(self, import_path: str, description: str = "",
                     tags: List[str] = None) -> Optional[str]:
        """
        백업 파일 가져오기

        Args:
            import_path: 가져올 파일 경로
            description: 백업 설명
            tags: 백업 태그

        Returns:
            생성된 백업 ID
        """
        try:
            if not os.path.exists(import_path):
                self.logger.error(f"파일이 존재하지 않습니다: {import_path}")
                return None

            # 백업 ID 생성
            backup_type = BackupType.FULL if ".db" in import_path else BackupType.INCREMENTAL
            backup_id = self.backup_manager._generate_backup_id(backup_type)

            # 대상 경로 결정
            backup_filename = f"{backup_id}.db"
            if import_path.endswith('.gz'):
                backup_filename += ".gz"

            backup_path = self.backup_manager.backup_dir / backup_filename

            # 파일 복사
            shutil.copy2(import_path, backup_path)

            # 메타데이터 생성
            file_size = os.path.getsize(import_path)
            compressed_size = os.path.getsize(backup_path) if import_path.endswith('.gz') else None

            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=backup_type,
                timestamp=datetime.now().isoformat(),
                database_path="<imported>",
                backup_path=str(backup_path),
                size_bytes=file_size,
                compressed_size=compressed_size,
                checksum=self.backup_manager._calculate_checksum(str(backup_path)),
                description=description,
                tags=tags or []
            )

            # 메타데이터 저장
            self.backup_manager.metadata[backup_id] = metadata
            self.backup_manager._save_metadata()

            self.logger.info(f"백업 가져오기 완료: {import_path} -> {backup_id}")

            return backup_id

        except Exception as e:
            self.logger.error(f"백업 가져오기 실패: {e}")
            return None