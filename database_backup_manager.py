"""
데이터베이스 백업 매니저

SQLite 데이터베이스의 백업 및 복구 기능을 제공합니다.
- 전체 백업 (Full Backup)
- 증분 백업 (Incremental Backup) - WAL 파일 기반
- 백업 파일 관리
- 압축 저장 지원
- 백업 메타데이터 관리
"""

import os
import sqlite3
import shutil
import gzip
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading


class BackupType(Enum):
    """백업 타입"""
    FULL = "full"          # 전체 백업
    INCREMENTAL = "incremental"  # 증분 백업 (WAL 기반)


class BackupStatus(Enum):
    """백업 상태"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"


@dataclass
class BackupMetadata:
    """백업 메타데이터"""
    backup_id: str
    backup_type: BackupType
    timestamp: str
    database_path: str
    backup_path: str
    size_bytes: int
    compressed_size: Optional[int] = None
    checksum: Optional[str] = None
    wal_checkpoint: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'backup_id': self.backup_id,
            'backup_type': self.backup_type.value,
            'timestamp': self.timestamp,
            'database_path': self.database_path,
            'backup_path': self.backup_path,
            'size_bytes': self.size_bytes,
            'compressed_size': self.compressed_size,
            'checksum': self.checksum,
            'wal_checkpoint': self.wal_checkpoint,
            'description': self.description,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BackupMetadata':
        """딕셔너리에서 객체 생성"""
        return cls(
            backup_id=data['backup_id'],
            backup_type=BackupType(data['backup_type']),
            timestamp=data['timestamp'],
            database_path=data['database_path'],
            backup_path=data['backup_path'],
            size_bytes=data['size_bytes'],
            compressed_size=data.get('compressed_size'),
            checksum=data.get('checksum'),
            wal_checkpoint=data.get('wal_checkpoint'),
            description=data.get('description', ''),
            tags=data.get('tags', [])
        )


class DatabaseBackupManager:
    """데이터베이스 백업 관리자"""

    def __init__(self, backup_dir: str = "backups", compress: bool = True,
                 max_backups: int = 30, enable_wal: bool = True):
        """
        백업 매니저 초기화

        Args:
            backup_dir: 백업 파일 저장 디렉토리
            compress: 압축 사용 여부
            max_backups: 최대 백업 파일 개수
            enable_wal: WAL 모드 사용 여부 (증분 백업을 위해 필요)
        """
        self.backup_dir = Path(backup_dir)
        self.compress = compress
        self.max_backups = max_backups
        self.enable_wal = enable_wal
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

        # 백업 디렉토리 생성
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 메타데이터 로드
        self.metadata: Dict[str, BackupMetadata] = {}
        self._load_metadata()

    def _load_metadata(self):
        """백업 메타데이터 로드"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for backup_id, meta_data in data.items():
                        self.metadata[backup_id] = BackupMetadata.from_dict(meta_data)
                self.logger.info(f"로드된 백업 메타데이터: {len(self.metadata)}개")
            except Exception as e:
                self.logger.error(f"메타데이터 로드 실패: {e}")
                self.metadata = {}

    def _save_metadata(self):
        """백업 메타데이터 저장"""
        try:
            data = {
                backup_id: meta.to_dict()
                for backup_id, meta in self.metadata.items()
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"메타데이터 저장 실패: {e}")

    def _generate_backup_id(self, backup_type: BackupType) -> str:
        """백업 ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # 마이크로초 추가
        return f"{backup_type.value}_{timestamp}"

    def _calculate_checksum(self, file_path: str) -> str:
        """파일 체크섬 계산 (SHA256)"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _compress_file(self, source_path: str, output_path: str) -> int:
        """파일 압축 (gzip)"""
        with open(source_path, 'rb') as src_file:
            with gzip.open(output_path, 'wb') as dst_file:
                shutil.copyfileobj(src_file, dst_file)

        compressed_size = os.path.getsize(output_path)
        self.logger.info(f"압축 완료: {source_path} -> {output_path} "
                        f"({os.path.getsize(source_path)} -> {compressed_size} bytes)")
        return compressed_size

    def _decompress_file(self, source_path: str, output_path: str):
        """파일 압축 해제"""
        with gzip.open(source_path, 'rb') as src_file:
            with open(output_path, 'wb') as dst_file:
                shutil.copyfileobj(src_file, dst_file)
        self.logger.info(f"압축 해제 완료: {source_path} -> {output_path}")

    def _enable_wal_mode(self, db_path: str) -> Tuple[bool, str]:
        """
        데이터베이스 WAL 모드 활성화

        Returns:
            (성공 여부, WAL 체크포인트)
        """
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.commit()

            # WAL 체크포인트 수행 (트랜잭션 번호 기록)
            checkpoint_result = conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
            conn.close()

            wal_checkpoint = f"{checkpoint_result[0]}_{checkpoint_result[1]}_{checkpoint_result[2]}"
            self.logger.info(f"WAL 모드 활성화 완료. 체크포인트: {wal_checkpoint}")
            return True, wal_checkpoint
        except Exception as e:
            self.logger.error(f"WAL 모드 활성화 실패: {e}")
            return False, ""

    def _perform_wal_checkpoint(self, db_path: str) -> str:
        """WAL 체크포인트 수행"""
        try:
            conn = sqlite3.connect(db_path)
            checkpoint_result = conn.execute("PRAGMA wal_checkpoint(FULL)").fetchone()
            conn.close()

            wal_checkpoint = f"{checkpoint_result[0]}_{checkpoint_result[1]}_{checkpoint_result[2]}"
            return wal_checkpoint
        except Exception as e:
            self.logger.error(f"WAL 체크포인트 실패: {e}")
            return ""

    def create_full_backup(self, db_path: str, description: str = "",
                          tags: List[str] = None) -> Optional[BackupMetadata]:
        """
        전체 백업 생성

        Args:
            db_path: 데이터베이스 파일 경로
            description: 백업 설명
            tags: 백업 태그

        Returns:
            BackupMetadata: 백업 메타데이터 (실패시 None)
        """
        with self._lock:
            db_path = os.path.abspath(db_path)

            if not os.path.exists(db_path):
                self.logger.error(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
                return None

            try:
                self.logger.info(f"전체 백업 시작: {db_path}")

                # WAL 모드 확인 및 활성화
                wal_checkpoint = ""
                if self.enable_wal:
                    success, wal_checkpoint = self._enable_wal_mode(db_path)
                    if not success:
                        self.logger.warning("WAL 모드 활성화 실패, 일반 백업 진행")

                # 백업 ID 생성
                backup_id = self._generate_backup_id(BackupType.FULL)

                # 백업 파일 경로 결정
                backup_filename = f"{backup_id}.db"
                if self.compress:
                    backup_filename += ".gz"
                backup_path = self.backup_dir / backup_filename

                # 데이터베이스 파일 백업
                # 안전한 백업을 위해 데이터베이스가 닫혀 있는지 확인
                # (또는 WAL 모드 사용 중인 경우)

                # 임시 파일에 백업 후 최종 위치로 이동
                temp_backup_path = str(backup_path) + ".temp"

                try:
                    # 파일 복사 (SQLite는 단순 파일 복사로도 백업 가능)
                    shutil.copy2(db_path, temp_backup_path)
                except Exception as e:
                    self.logger.error(f"파일 복사 실패: {e}")
                    raise e

                # 압축
                final_backup_path = str(backup_path)
                original_size = os.path.getsize(temp_backup_path)
                compressed_size = None

                if self.compress:
                    self._compress_file(temp_backup_path, final_backup_path)
                    # Windows에서 파일 핸들링 문제 해결
                    import gc
                    gc.collect()
                    try:
                        os.remove(temp_backup_path)
                    except PermissionError:
                        # 잠시 대기 후 재시도
                        import time
                        time.sleep(0.1)
                        gc.collect()
                        if os.path.exists(temp_backup_path):
                            os.remove(temp_backup_path)
                    compressed_size = os.path.getsize(final_backup_path)
                else:
                    # Windows에서 os.rename은 기존 파일이 있으면 실패
                    # shutil.move를 사용하거나 기존 파일 삭제 후 이동
                    if os.path.exists(final_backup_path):
                        os.remove(final_backup_path)
                    shutil.move(temp_backup_path, final_backup_path)

                # 체크섬 계산
                checksum = self._calculate_checksum(final_backup_path)

                # 메타데이터 생성
                metadata = BackupMetadata(
                    backup_id=backup_id,
                    backup_type=BackupType.FULL,
                    timestamp=datetime.now().isoformat(),
                    database_path=db_path,
                    backup_path=str(backup_path),
                    size_bytes=original_size,
                    compressed_size=compressed_size,
                    checksum=checksum,
                    wal_checkpoint=wal_checkpoint,
                    description=description,
                    tags=tags or []
                )

                # 메타데이터 저장
                self.metadata[backup_id] = metadata
                self._save_metadata()

                # 오래된 백업 정리
                self._cleanup_old_backups()

                self.logger.info(f"전체 백업 완료: {backup_id} "
                               f"(원본: {original_size:,} bytes, "
                               f"압축: {compressed_size:,} bytes)" if compressed_size else
                               f"전체 백업 완료: {backup_id} "
                               f"(원본: {original_size:,} bytes)")

                return metadata

            except Exception as e:
                self.logger.error(f"전체 백업 실패: {e}")

                # 임시 파일 정리 (Windows 호환)
                temp_path = str(backup_path) + ".temp"
                if os.path.exists(temp_path):
                    try:
                        import gc
                        gc.collect()
                        os.remove(temp_path)
                    except PermissionError:
                        try:
                            import time
                            time.sleep(0.1)
                            gc.collect()
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                        except:
                            pass  # 최종 실패 시 무시

                return None

    def create_incremental_backup(self, db_path: str, description: str = "",
                                 tags: List[str] = None) -> Optional[BackupMetadata]:
        """
        증분 백업 생성 (WAL 파일 기반)

        Args:
            db_path: 데이터베이스 파일 경로
            description: 백업 설명
            tags: 백업 태그

        Returns:
            BackupMetadata: 백업 메타데이터 (실패시 None)
        """
        with self._lock:
            db_path = os.path.abspath(db_path)

            if not os.path.exists(db_path):
                self.logger.error(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
                return None

            try:
                self.logger.info(f"증분 백업 시작: {db_path}")

                # WAL 파일 경로 확인
                wal_path = db_path + "-wal"

                if not os.path.exists(wal_path):
                    self.logger.warning("WAL 파일이 존재하지 않습니다. "
                                       "WAL 모드가 활성화되어 있지 않거나 "
                                       "변경 사항이 없습니다.")

                    # WAL 모드 활성화 시도
                    success, wal_checkpoint = self._enable_wal_mode(db_path)
                    if not success:
                        self.logger.error("증분 백업을 위해 WAL 모드가 필요합니다")
                        return None

                    # WAL 파일이 생성될 때까지 잠시 대기
                    import time
                    time.sleep(1)

                # WAL 체크포인트 수행
                wal_checkpoint = self._perform_wal_checkpoint(db_path)

                # 백업 ID 생성
                backup_id = self._generate_backup_id(BackupType.INCREMENTAL)

                # 백업 파일 경로
                wal_backup_filename = f"{backup_id}_wal"
                if self.compress:
                    wal_backup_filename += ".gz"
                wal_backup_path = self.backup_dir / wal_backup_filename

                # WAL 파일 백업
                original_size = os.path.getsize(wal_path)
                compressed_size = None

                if self.compress:
                    compressed_size = self._compress_file(wal_path, str(wal_backup_path))
                else:
                    shutil.copy2(wal_path, wal_backup_path)

                # 체크섬 계산
                checksum = self._calculate_checksum(str(wal_backup_path))

                # 메타데이터 생성
                metadata = BackupMetadata(
                    backup_id=backup_id,
                    backup_type=BackupType.INCREMENTAL,
                    timestamp=datetime.now().isoformat(),
                    database_path=db_path,
                    backup_path=str(wal_backup_path),
                    size_bytes=original_size,
                    compressed_size=compressed_size,
                    checksum=checksum,
                    wal_checkpoint=wal_checkpoint,
                    description=description,
                    tags=tags or []
                )

                # 메타데이터 저장
                self.metadata[backup_id] = metadata
                self._save_metadata()

                # 오래된 백업 정리
                self._cleanup_old_backups()

                self.logger.info(f"증분 백업 완료: {backup_id} "
                               f"(WAL: {original_size:,} bytes, "
                               f"압축: {compressed_size:,} bytes)" if compressed_size else
                               f"증분 백업 완료: {backup_id} "
                               f"(WAL: {original_size:,} bytes)")

                return metadata

            except Exception as e:
                self.logger.error(f"증분 백업 실패: {e}")
                return None

    def restore_backup(self, backup_id: str, restore_path: Optional[str] = None,
                      force: bool = False) -> bool:
        """
        백업 복구

        Args:
            backup_id: 복구할 백업 ID
            restore_path: 복구 경로 (None이면 원본 위치에 복구)
            force: 기존 파일 덮어쓰기

        Returns:
            성공 여부
        """
        with self._lock:
            if backup_id not in self.metadata:
                self.logger.error(f"백업을 찾을 수 없습니다: {backup_id}")
                return False

            metadata = self.metadata[backup_id]
            backup_path = metadata.backup_path

            if not os.path.exists(backup_path):
                self.logger.error(f"백업 파일이 존재하지 않습니다: {backup_path}")
                return False

            try:
                # 복구 경로 결정
                target_path = restore_path or metadata.database_path

                # 기존 파일 확인
                if os.path.exists(target_path) and not force:
                    self.logger.error(f"복구 대상 파일이 이미 존재합니다: {target_path}")
                    return False

                self.logger.info(f"백업 복구 시작: {backup_id} -> {target_path}")

                # 백업 파일 복사
                if backup_path.endswith('.gz'):
                    # 압축 해제
                    temp_path = target_path + ".temp"
                    self._decompress_file(backup_path, temp_path)

                    # 체크섬 검증
                    original_checksum = metadata.checksum
                    current_checksum = self._calculate_checksum(backup_path)

                    if original_checksum != current_checksum:
                        self.logger.error("백업 파일 체크섬 불일치! 파일이 손상되었을 수 있습니다.")
                        os.remove(temp_path)
                        return False

                    os.rename(temp_path, target_path)
                else:
                    shutil.copy2(backup_path, target_path)

                self.logger.info(f"백업 복구 완료: {backup_id}")
                return True

            except Exception as e:
                self.logger.error(f"백업 복구 실패: {e}")
                return False

    def restore_incremental_chain(self, start_backup_id: str,
                                 restore_path: Optional[str] = None,
                                 force: bool = False) -> bool:
        """
        증분 백업 체인 복구
        (가장 최근 전체 백업 + 이후 증분 백업들 적용)

        Args:
            start_backup_id: 시작점이 될 전체 백업 ID
            restore_path: 복구 경로
            force: 기존 파일 덮어쓰기

        Returns:
            성공 여부
        """
        with self._lock:
            if start_backup_id not in self.metadata:
                self.logger.error(f"시작 백업을 찾을 수 없습니다: {start_backup_id}")
                return False

            start_metadata = self.metadata[start_backup_id]

            if start_metadata.backup_type != BackupType.FULL:
                self.logger.error("시작 백업은 전체 백업이어야 합니다")
                return False

            try:
                self.logger.info(f"증분 백업 체인 복구 시작: {start_backup_id}")

                # 1. 전체 백업 복구
                if not self.restore_backup(start_backup_id, restore_path, force):
                    return False

                target_path = restore_path or start_metadata.database_path

                # 2. 이후 증분 백업 찾기
                start_timestamp = datetime.fromisoformat(start_metadata.timestamp)
                incremental_backups = [
                    meta for meta in self.metadata.values()
                    if (meta.backup_type == BackupType.INCREMENTAL and
                        datetime.fromisoformat(meta.timestamp) > start_timestamp and
                        meta.database_path == start_metadata.database_path)
                ]

                # 시간순 정렬
                incremental_backups.sort(key=lambda x: x.timestamp)

                # 3. 증분 백업 순차 적용 (SQLite는 자동으로 WAL을 적용함)
                for inc_meta in incremental_backups:
                    self.logger.info(f"증분 백업 적용: {inc_meta.backup_id}")

                    # WAL 파일 복원
                    wal_backup_path = inc_meta.backup_path
                    wal_restore_path = target_path + "-wal"

                    if not os.path.exists(wal_backup_path):
                        self.logger.warning(f"WAL 백업 파일이 존재하지 않음: {wal_backup_path}")
                        continue

                    if wal_backup_path.endswith('.gz'):
                        self._decompress_file(wal_backup_path, wal_restore_path)
                    else:
                        shutil.copy2(wal_backup_path, wal_restore_path)

                self.logger.info("증분 백업 체인 복구 완료")
                return True

            except Exception as e:
                self.logger.error(f"증분 백업 체인 복구 실패: {e}")
                return False

    def _cleanup_old_backups(self):
        """오래된 백업 정리"""
        if len(self.metadata) <= self.max_backups:
            return

        # 타임스탬프순 정렬
        sorted_backups = sorted(
            self.metadata.items(),
            key=lambda x: x[1].timestamp
        )

        # 삭제할 백업 선택 (전체 백업은 우선 보존)
        to_delete = []
        full_backup_count = 0

        for backup_id, metadata in reversed(sorted_backups):
            if metadata.backup_type == BackupType.FULL:
                full_backup_count += 1
                # 최소 3개의 전체 백업은 유지
                if full_backup_count <= 3:
                    continue

            to_delete.append(backup_id)

            if len(self.metadata) - len(to_delete) <= self.max_backups:
                break

        # 백업 삭제
        for backup_id in to_delete:
            self.delete_backup(backup_id)

    def delete_backup(self, backup_id: str) -> bool:
        """
        백업 삭제

        Args:
            backup_id: 삭제할 백업 ID

        Returns:
            성공 여부
        """
        with self._lock:
            if backup_id not in self.metadata:
                return False

            metadata = self.metadata[backup_id]

            try:
                # 백업 파일 삭제
                if os.path.exists(metadata.backup_path):
                    os.remove(metadata.backup_path)
                    self.logger.info(f"백업 파일 삭제: {metadata.backup_path}")

                # 메타데이터에서 제거
                del self.metadata[backup_id]
                self._save_metadata()

                return True

            except Exception as e:
                self.logger.error(f"백업 삭제 실패: {e}")
                return False

    def list_backups(self, backup_type: Optional[BackupType] = None) -> List[BackupMetadata]:
        """
        백업 목록 조회

        Args:
            backup_type: 필터링할 백업 타입 (None이면 전체)

        Returns:
            백업 메타데이터 리스트 (시간순 정렬)
        """
        backups = list(self.metadata.values())

        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]

        # 시간순 정렬 (최신순)
        backups.sort(key=lambda x: x.timestamp, reverse=True)

        return backups

    def get_backup_info(self, backup_id: str) -> Optional[BackupMetadata]:
        """백업 정보 조회"""
        return self.metadata.get(backup_id)

    def get_backup_stats(self) -> Dict:
        """백업 통계 정보"""
        total_backups = len(self.metadata)
        full_backups = sum(1 for m in self.metadata.values()
                          if m.backup_type == BackupType.FULL)
        incremental_backups = total_backups - full_backups

        total_size = sum(m.size_bytes for m in self.metadata.values())
        total_compressed_size = sum(m.compressed_size or m.size_bytes
                                    for m in self.metadata.values())

        return {
            'total_backups': total_backups,
            'full_backups': full_backups,
            'incremental_backups': incremental_backups,
            'total_size_bytes': total_size,
            'total_compressed_size_bytes': total_compressed_size,
            'compression_ratio': f"{(1 - total_compressed_size / total_size) * 100:.1f}%"
                                 if total_size > 0 else "0%",
            'backup_dir': str(self.backup_dir),
            'oldest_backup': min((m.timestamp for m in self.metadata.values()), default=None),
            'newest_backup': max((m.timestamp for m in self.metadata.values()), default=None)
        }

    def verify_backup(self, backup_id: str) -> bool:
        """
        백업 무결성 검증

        Args:
            backup_id: 검증할 백업 ID

        Returns:
            무결성 여부
        """
        if backup_id not in self.metadata:
            return False

        metadata = self.metadata[backup_id]
        backup_path = metadata.backup_path

        if not os.path.exists(backup_path):
            self.logger.error(f"백업 파일이 존재하지 않습니다: {backup_path}")
            return False

        try:
            # 체크섬 검증
            current_checksum = self._calculate_checksum(backup_path)

            if metadata.checksum != current_checksum:
                self.logger.error(f"체크섬 불일치: 기록={metadata.checksum}, 현재={current_checksum}")
                return False

            # SQLite 데이터베이스 무결성 검사 (전체 백업의 경우)
            if metadata.backup_type == BackupType.FULL:
                temp_db = backup_path + ".verify"

                try:
                    # 압축 해제 후 검증
                    if backup_path.endswith('.gz'):
                        self._decompress_file(backup_path, temp_db)
                    else:
                        temp_db = backup_path

                    # SQLite 무결성 검사
                    conn = sqlite3.connect(temp_db)
                    result = conn.execute("PRAGMA integrity_check").fetchall()
                    conn.close()

                    if result[0][0] != "ok":
                        self.logger.error(f"데이터베이스 무결성 검사 실패: {result}")
                        return False

                finally:
                    # 임시 파일 정리
                    if backup_path.endswith('.gz'):
                        if os.path.exists(temp_db):
                            os.remove(temp_db)

            self.logger.info(f"백업 무결성 검증 완료: {backup_id}")
            return True

        except Exception as e:
            self.logger.error(f"백업 검증 실패: {e}")
            return False