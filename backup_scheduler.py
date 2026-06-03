"""
데이터베이스 백업 스케줄러

자동 백업 스케줄링 기능을 제공합니다.
- 주기적 전체 백업
- 주기적 증분 백업
- 백업 실패 시 재시도
- 백업 알림
"""

import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import json

from database_backup_manager import DatabaseBackupManager, BackupType


class ScheduleType(Enum):
    """스케줄 타입"""
    FULL = "full"              # 전체 백업
    INCREMENTAL = "incremental"  # 증분 백업


@dataclass
class BackupSchedule:
    """백업 스케줄 설정"""
    schedule_id: str
    schedule_type: ScheduleType
    database_path: str
    interval: str  # "daily", "hourly", "weekly", cron expression
    time: Optional[str] = None  # "09:00"
    enabled: bool = True
    max_retries: int = 3
    retry_interval_minutes: int = 5
    tags: List[str] = field(default_factory=list)
    description: str = ""
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    last_status: Optional[str] = None

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'schedule_id': self.schedule_id,
            'schedule_type': self.schedule_type.value,
            'database_path': self.database_path,
            'interval': self.interval,
            'time': self.time,
            'enabled': self.enabled,
            'max_retries': self.max_retries,
            'retry_interval_minutes': self.retry_interval_minutes,
            'tags': self.tags,
            'description': self.description,
            'last_run': self.last_run,
            'next_run': self.next_run,
            'last_status': self.last_status
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BackupSchedule':
        """딕셔너리에서 객체 생성"""
        return cls(
            schedule_id=data['schedule_id'],
            schedule_type=ScheduleType(data['schedule_type']),
            database_path=data['database_path'],
            interval=data['interval'],
            time=data.get('time'),
            enabled=data.get('enabled', True),
            max_retries=data.get('max_retries', 3),
            retry_interval_minutes=data.get('retry_interval_minutes', 5),
            tags=data.get('tags', []),
            description=data.get('description', ''),
            last_run=data.get('last_run'),
            next_run=data.get('next_run'),
            last_status=data.get('last_status')
        )


class BackupScheduler:
    """백업 스케줄러"""

    def __init__(self, backup_manager: DatabaseBackupManager,
                 on_backup_complete: Optional[Callable] = None,
                 on_backup_failed: Optional[Callable] = None):
        """
        백업 스케줄러 초기화

        Args:
            backup_manager: 백업 매니저 인스턴스
            on_backup_complete: 백업 완료 시 콜백 (backup_metadata)
            on_backup_failed: 백업 실패 시 콜백 (error_message)
        """
        self.backup_manager = backup_manager
        self.on_backup_complete = on_backup_complete
        self.on_backup_failed = on_backup_failed

        self.schedules: Dict[str, BackupSchedule] = {}
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # 스케줄 설정 파일
        self.config_file = self.backup_manager.backup_dir / "backup_schedules.json"

        # 설정 로드
        self._load_schedules()

    def _load_schedules(self):
        """스케줄 설정 로드"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for schedule_id, schedule_data in data.items():
                        self.schedules[schedule_id] = BackupSchedule.from_dict(schedule_data)
                self.logger.info(f"로드된 백업 스케줄: {len(self.schedules)}개")
            except Exception as e:
                self.logger.error(f"스케줄 설정 로드 실패: {e}")
                self.schedules = {}

    def _save_schedules(self):
        """스케줄 설정 저장"""
        try:
            data = {
                schedule_id: schedule.to_dict()
                for schedule_id, schedule in self.schedules.items()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"스케줄 설정 저장 실패: {e}")

    def add_schedule(self, schedule_type: ScheduleType, database_path: str,
                    interval: str, time: Optional[str] = None,
                    description: str = "", tags: List[str] = None,
                    schedule_id: Optional[str] = None) -> str:
        """
        백업 스케줄 추가

        Args:
            schedule_type: 백업 타입 (전체/증분)
            database_path: 데이터베이스 경로
            interval: 실행 주기 ("daily", "hourly", "weekly")
            time: 실행 시간 ("09:00")
            description: 설명
            tags: 태그
            schedule_id: 스케줄 ID (None이면 자동 생성)

        Returns:
            schedule_id: 생성된 스케줄 ID
        """
        with self._lock:
            if schedule_id is None:
                schedule_id = f"{schedule_type.value}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            schedule = BackupSchedule(
                schedule_id=schedule_id,
                schedule_type=schedule_type,
                database_path=database_path,
                interval=interval,
                time=time,
                description=description,
                tags=tags or []
            )

            self.schedules[schedule_id] = schedule
            self._save_schedules()

            # 스케줄러가 실행 중이면 등록
            if self._running:
                self._register_schedule(schedule)

            self.logger.info(f"백업 스케줄 추가됨: {schedule_id} ({schedule_type.value})")
            return schedule_id

    def remove_schedule(self, schedule_id: str) -> bool:
        """
        백업 스케줄 제거

        Args:
            schedule_id: 제거할 스케줄 ID

        Returns:
            성공 여부
        """
        with self._lock:
            if schedule_id not in self.schedules:
                return False

            del self.schedules[schedule_id]
            self._save_schedules()

            # 스케줄러에서 제거
            schedule.clear(schedule_id)

            self.logger.info(f"백업 스케줄 제거됨: {schedule_id}")
            return True

    def enable_schedule(self, schedule_id: str) -> bool:
        """스케줄 활성화"""
        with self._lock:
            if schedule_id not in self.schedules:
                return False

            self.schedules[schedule_id].enabled = True
            self._save_schedules()

            if self._running:
                self._register_schedule(self.schedules[schedule_id])

            return True

    def disable_schedule(self, schedule_id: str) -> bool:
        """스케줄 비활성화"""
        with self._lock:
            if schedule_id not in self.schedules:
                return False

            self.schedules[schedule_id].enabled = False
            self._save_schedules()

            # 스케줄러에서 제거
            schedule.clear(schedule_id)

            return True

    def _register_schedule(self, schedule: BackupSchedule):
        """스케줄 등록"""
        job_id = schedule.schedule_id

        # 기존 스케줄 제거
        schedule.clear(job_id)

        if not schedule.enabled:
            return

        # 실행 시간 결정
        run_time = schedule.time or "02:00"  # 기본 새벽 2시

        # 주기별 스케줄 등록
        if schedule.interval == "daily":
            schedule.every().day.at(run_time).do(self._execute_backup, schedule).tag(job_id)
        elif schedule.interval == "hourly":
            schedule.every().hour.do(self._execute_backup, schedule).tag(job_id)
        elif schedule.interval == "weekly":
            schedule.every().week.at(run_time).do(self._execute_backup, schedule).tag(job_id)
        else:
            # 간격 기반 (예: "every 2 hours")
            try:
                parts = schedule.interval.split()
                if len(parts) >= 2 and parts[0].isdigit():
                    interval_value = int(parts[0])
                    interval_unit = parts[1]

                    if interval_unit.startswith("hour"):
                        schedule.every(interval_value).hours.do(self._execute_backup, schedule).tag(job_id)
                    elif interval_unit.startswith("day"):
                        schedule.every(interval_value).days.at(run_time).do(self._execute_backup, schedule).tag(job_id)
                    elif interval_unit.startswith("week"):
                        schedule.every(interval_value).weeks.at(run_time).do(self._execute_backup, schedule).tag(job_id)
                    else:
                        self.logger.warning(f"지원하지 않는 간격: {schedule.interval}")
            except Exception as e:
                self.logger.error(f"스케줄 등록 실패: {e}")

    def _execute_backup(self, schedule: BackupSchedule) -> Optional[str]:
        """
        백업 실행

        Args:
            schedule: 백업 스케줄

        Returns:
            backup_id: 생성된 백업 ID (실패시 None)
        """
        # 마지막 실행 시간 기록
        schedule.last_run = datetime.now().isoformat()

        # 다음 실행 시간 계산 (선택 사항)
        # schedule 라이브러리의 기능을 사용하여 계산
        try:
            next_run_job = schedule.next_run(schedule_id=schedule.schedule_id)
            if next_run_job:
                schedule.next_run = next_run_job.isoformat()
        except:
            schedule.next_run = None

        self.logger.info(f"스케줄된 백업 실행 시작: {schedule.schedule_id}")

        # 백업 실행
        retry_count = 0
        backup_id = None

        while retry_count <= schedule.max_retries:
            try:
                # 백업 타입별 실행
                if schedule.schedule_type == ScheduleType.FULL:
                    metadata = self.backup_manager.create_full_backup(
                        schedule.database_path,
                        description=schedule.description,
                        tags=schedule.tags
                    )
                else:  # INCREMENTAL
                    metadata = self.backup_manager.create_incremental_backup(
                        schedule.database_path,
                        description=schedule.description,
                        tags=schedule.tags
                    )

                if metadata:
                    backup_id = metadata.backup_id
                    schedule.last_status = "SUCCESS"
                    self.logger.info(f"스케줄된 백업 완료: {backup_id}")

                    # 완료 콜백
                    if self.on_backup_complete:
                        self.on_backup_complete(metadata)

                    break
                else:
                    retry_count += 1
                    if retry_count <= schedule.max_retries:
                        self.logger.warning(f"백업 실패, 재시도 ({retry_count}/{schedule.max_retries})")
                        time.sleep(schedule.retry_interval_minutes * 60)

            except Exception as e:
                retry_count += 1
                self.logger.error(f"백업 실행 중 오류: {e}")

                if retry_count <= schedule.max_retries:
                    time.sleep(schedule.retry_interval_minutes * 60)

        # 실패 시 기록
        if backup_id is None:
            schedule.last_status = "FAILED"
            error_msg = f"백업 실패: {schedule.schedule_id} (재시도 {retry_count}회 후 실패)"
            self.logger.error(error_msg)

            # 실패 콜백
            if self.on_backup_failed:
                self.on_backup_failed(error_msg)

        # 상태 저장
        self._save_schedules()

        return backup_id

    def start(self):
        """스케줄러 시작"""
        with self._lock:
            if self._running:
                self.logger.warning("스케줄러가 이미 실행 중입니다")
                return

            self._running = True

            # 활성화된 스케줄 등록
            for schedule in self.schedules.values():
                if schedule.enabled:
                    self._register_schedule(schedule)

            # 스케줄러 스레드 시작
            self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self._thread.start()

            self.logger.info("백업 스케줄러 시작")

    def _run_scheduler(self):
        """스케줄러 실행 루프"""
        while self._running:
            try:
                schedule.run_pending()
                time.sleep(1)  # 1초 대기
            except Exception as e:
                self.logger.error(f"스케줄러 실행 중 오류: {e}")
                time.sleep(5)

    def stop(self):
        """스케줄러 정지"""
        with self._lock:
            if not self._running:
                return

            self._running = False
            schedule.clear()

            if self._thread:
                self._thread.join(timeout=5)
                self._thread = None

            self.logger.info("백업 스케줄러 정지")

    def is_running(self) -> bool:
        """실행 중 여부 확인"""
        return self._running

    def run_now(self, schedule_id: str) -> Optional[str]:
        """
        스케줄 즉시 실행

        Args:
            schedule_id: 실행할 스케줄 ID

        Returns:
            backup_id: 생성된 백업 ID
        """
        with self._lock:
            if schedule_id not in self.schedules:
                self.logger.error(f"스케줄을 찾을 수 없습니다: {schedule_id}")
                return None

            schedule = self.schedules[schedule_id]
            return self._execute_backup(schedule)

    def list_schedules(self) -> List[BackupSchedule]:
        """스케줄 목록 조회"""
        return list(self.schedules.values())

    def get_schedule(self, schedule_id: str) -> Optional[BackupSchedule]:
        """스케줄 조회"""
        return self.schedules.get(schedule_id)

    def get_schedule_status(self) -> Dict:
        """스케줄러 상태 조회"""
        return {
            'running': self._running,
            'total_schedules': len(self.schedules),
            'enabled_schedules': sum(1 for s in self.schedules.values() if s.enabled),
            'disabled_schedules': sum(1 for s in self.schedules.values() if not s.enabled),
            'schedules': [
                {
                    'schedule_id': s.schedule_id,
                    'type': s.schedule_type.value,
                    'interval': s.interval,
                    'enabled': s.enabled,
                    'last_run': s.last_run,
                    'next_run': s.next_run,
                    'last_status': s.last_status
                }
                for s in self.schedules.values()
            ]
        }


def create_default_schedules(scheduler: BackupScheduler, database_path: str):
    """
    기본 백업 스케줄 생성

    Args:
        scheduler: 백업 스케줄러 인스턴스
        database_path: 데이터베이스 경로
    """
    # 매일 새벽 2시 전체 백업
    scheduler.add_schedule(
        schedule_type=ScheduleType.FULL,
        database_path=database_path,
        interval="daily",
        time="02:00",
        description="일일 전체 백업",
        tags=["daily", "full"]
    )

    # 매시간 증분 백업
    scheduler.add_schedule(
        schedule_type=ScheduleType.INCREMENTAL,
        database_path=database_path,
        interval="hourly",
        description="시간별 증분 백업",
        tags=["hourly", "incremental"]
    )

    # 매주 일요일 새벽 3시 전체 백업 (주간 백업)
    scheduler.add_schedule(
        schedule_type=ScheduleType.FULL,
        database_path=database_path,
        interval="weekly",
        time="03:00",
        description="주간 전체 백업",
        tags=["weekly", "full"]
    )