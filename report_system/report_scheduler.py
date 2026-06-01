"""
리포트 스케줄링 시스템

정기 리포트 자동 생성을 위한 스케줄링 기능을 제공합니다.
"""

import os
import logging
import signal
import sys
from typing import Dict, Any, Optional, Callable
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import pytz

from .config import ReportConfig
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class ReportScheduler:
    """리포트 스케줄링 클래스"""

    def __init__(self, config: ReportConfig = None, generator: ReportGenerator = None):
        """
        리포트 스케줄러 초기화

        Args:
            config: 리포트 설정
            generator: 리포트 생성기 (None인 경우 자동 생성)
        """
        self.config = config or ReportConfig()
        self.generator = generator or ReportGenerator(self.config)

        # 스케줄러 설정
        self.scheduler = BackgroundScheduler(timezone=self.config.general.timezone)
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        # 작업 상태 추적
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.is_running = False

        # 시그널 핸들러 등록
        self._setup_signal_handlers()

        logger.info("리포트 스케줄러 초기화 완료")

    def _setup_signal_handlers(self):
        """시그널 핸들러 설정"""
        def signal_handler(signum, frame):
            logger.info(f"시그널 수신: {signum}, 스케줄러 종료 중...")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _job_listener(self, event):
        """작업 이벤트 리스너"""
        if event.exception:
            job_id = event.job_id
            logger.error(f"작업 실패: {job_id} - {event.exception}")
            self._update_job_status(job_id, 'failed', str(event.exception))
        else:
            job_id = event.job_id
            logger.info(f"작업 완료: {job_id}")
            self._update_job_status(job_id, 'completed')

    def _update_job_status(self, job_id: str, status: str, error: str = None):
        """작업 상태 업데이트"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = status
            self.jobs[job_id]['last_run'] = datetime.now().isoformat()
            if error:
                self.jobs[job_id]['last_error'] = error
                self.jobs[job_id]['error_count'] = self.jobs[job_id].get('error_count', 0) + 1

    def schedule_daily_report(self, report_time: str = "09:00", job_id: str = None) -> bool:
        """
        일일 리포트 스케줄링

        Args:
            report_time: 리포트 생성 시간 (HH:MM 형식)
            job_id: 작업 ID (None인 경우 자동 생성)

        Returns:
            스케줄링 성공 여부
        """
        try:
            # 시간 파싱
            hour, minute = map(int, report_time.split(':'))

            # 작업 ID 생성
            if job_id is None:
                job_id = f"daily_report_{report_time.replace(':', '')}"

            # 리포트 타입 확인
            if not self.config.is_report_type_enabled('daily'):
                logger.warning("일일 리포트가 비활성화되어 있습니다.")
                return False

            # 스케줄 등록
            self.scheduler.add_job(
                self._execute_daily_report,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=self.config.general.timezone),
                id=job_id,
                name=f"일일 리포트 ({report_time})",
                replace_existing=True
            )

            # 작업 정보 저장
            self.jobs[job_id] = {
                'type': 'daily',
                'time': report_time,
                'enabled': True,
                'status': 'scheduled',
                'created_at': datetime.now().isoformat(),
                'error_count': 0
            }

            logger.info(f"일일 리포트 스케줄링 완료: {report_time}")
            return True

        except Exception as e:
            logger.error(f"일일 리포트 스케줄링 실패: {e}")
            return False

    def schedule_weekly_report(self, day: str = "monday", report_time: str = "09:00", job_id: str = None) -> bool:
        """
        주간 리포트 스케줄링

        Args:
            day: 요일 (monday, tuesday, wednesday, thursday, friday, saturday, sunday)
            report_time: 리포트 생성 시간 (HH:MM 형식)
            job_id: 작업 ID (None인 경우 자동 생성)

        Returns:
            스케줄링 성공 여부
        """
        try:
            # 요일 매핑
            day_map = {
                'monday': 0,
                'tuesday': 1,
                'wednesday': 2,
                'thursday': 3,
                'friday': 4,
                'saturday': 5,
                'sunday': 6
            }

            day_of_week = day_map.get(day.lower())
            if day_of_week is None:
                raise ValueError(f"잘못된 요일: {day}")

            # 시간 파싱
            hour, minute = map(int, report_time.split(':'))

            # 작업 ID 생성
            if job_id is None:
                job_id = f"weekly_report_{day}_{report_time.replace(':', '')}"

            # 리포트 타입 확인
            if not self.config.is_report_type_enabled('weekly'):
                logger.warning("주간 리포트가 비활성화되어 있습니다.")
                return False

            # 스케줄 등록
            self.scheduler.add_job(
                self._execute_weekly_report,
                trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute,
                                   timezone=self.config.general.timezone),
                id=job_id,
                name=f"주간 리포트 ({day} {report_time})",
                replace_existing=True
            )

            # 작업 정보 저장
            self.jobs[job_id] = {
                'type': 'weekly',
                'day': day,
                'time': report_time,
                'enabled': True,
                'status': 'scheduled',
                'created_at': datetime.now().isoformat(),
                'error_count': 0
            }

            logger.info(f"주간 리포트 스케줄링 완료: {day} {report_time}")
            return True

        except Exception as e:
            logger.error(f"주간 리포트 스케줄링 실패: {e}")
            return False

    def schedule_monthly_report(self, day: int = 1, report_time: str = "09:00", job_id: str = None) -> bool:
        """
        월간 리포트 스케줄링

        Args:
            day: 날짜 (1-31)
            report_time: 리포트 생성 시간 (HH:MM 형식)
            job_id: 작업 ID (None인 경우 자동 생성)

        Returns:
            스케줄링 성공 여부
        """
        try:
            if not 1 <= day <= 31:
                raise ValueError(f"잘못된 날짜: {day} (1-31 사이여야 함)")

            # 시간 파싱
            hour, minute = map(int, report_time.split(':'))

            # 작업 ID 생성
            if job_id is None:
                job_id = f"monthly_report_{day}_{report_time.replace(':', '')}"

            # 리포트 타입 확인
            if not self.config.is_report_type_enabled('monthly'):
                logger.warning("월간 리포트가 비활성화되어 있습니다.")
                return False

            # 스케줄 등록
            self.scheduler.add_job(
                self._execute_monthly_report,
                trigger=CronTrigger(day=day, hour=hour, minute=minute,
                                   timezone=self.config.general.timezone),
                id=job_id,
                name=f"월간 리포트 (매월 {day}일 {report_time})",
                replace_existing=True
            )

            # 작업 정보 저장
            self.jobs[job_id] = {
                'type': 'monthly',
                'day': day,
                'time': report_time,
                'enabled': True,
                'status': 'scheduled',
                'created_at': datetime.now().isoformat(),
                'error_count': 0
            }

            logger.info(f"월간 리포트 스케줄링 완료: 매월 {day}일 {report_time}")
            return True

        except Exception as e:
            logger.error(f"월간 리포트 스케줄링 실패: {e}")
            return False

    def schedule_custom_report(self, callback: Callable, interval_minutes: int = 60,
                               job_id: str = None, job_name: str = None) -> bool:
        """
        사용자 정의 리포트 스케줄링

        Args:
            callback: 실행할 콜백 함수
            interval_minutes: 실행 간격 (분)
            job_id: 작업 ID (None인 경우 자동 생성)
            job_name: 작업 이름

        Returns:
            스케줄링 성공 여부
        """
        try:
            if job_id is None:
                job_id = f"custom_report_{datetime.now().timestamp()}"

            if job_name is None:
                job_name = f"사용자 정의 리포트 ({interval_minutes}분 간격)"

            # 스케줄 등록
            self.scheduler.add_job(
                callback,
                trigger=IntervalTrigger(minutes=interval_minutes,
                                       timezone=self.config.general.timezone),
                id=job_id,
                name=job_name,
                replace_existing=True
            )

            # 작업 정보 저장
            self.jobs[job_id] = {
                'type': 'custom',
                'interval_minutes': interval_minutes,
                'enabled': True,
                'status': 'scheduled',
                'created_at': datetime.now().isoformat(),
                'error_count': 0
            }

            logger.info(f"사용자 정의 리포트 스케줄링 완료: {interval_minutes}분 간격")
            return True

        except Exception as e:
            logger.error(f"사용자 정의 리포트 스케줄링 실패: {e}")
            return False

    def setup_default_schedules(self) -> bool:
        """
        기본 스케줄 설정

        Returns:
            설정 성공 여부
        """
        try:
            logger.info("기본 스케줄 설정 시작")

            # 설정 파일에서 스케줄 정보 읽기
            for report_type, report_config in self.config.report_types.items():
                if not report_config.enabled:
                    logger.info(f"{report_type} 리포트는 비활성화되어 있습니다.")
                    continue

                schedule_str = report_config.schedule

                # 스케줄 파싱 및 설정
                if report_type == 'daily':
                    # "09:00" 형식
                    if ':' in schedule_str:
                        self.schedule_daily_report(schedule_str)

                elif report_type == 'weekly':
                    # "monday 09:00" 형식
                    parts = schedule_str.split()
                    if len(parts) == 2:
                        day, time = parts
                        self.schedule_weekly_report(day, time)

                elif report_type == 'monthly':
                    # "1st 09:00" 형식
                    parts = schedule_str.split()
                    if len(parts) == 2:
                        day_str, time = parts
                        day = int(day_str.replace('st', '').replace('nd', '').replace('rd', '').replace('th', ''))
                        self.schedule_monthly_report(day, time)

            logger.info("기본 스케줄 설정 완료")
            return True

        except Exception as e:
            logger.error(f"기본 스케줄 설정 실패: {e}")
            return False

    def start(self) -> bool:
        """
        스케줄러 시작

        Returns:
            시작 성공 여부
        """
        try:
            if self.is_running:
                logger.warning("스케줄러가 이미 실행 중입니다.")
                return False

            logger.info("스케줄러 시작")
            self.scheduler.start()
            self.is_running = True

            # 등록된 작업 정보 출력
            jobs = self.scheduler.get_jobs()
            logger.info(f"등록된 작업 수: {len(jobs)}")
            for job in jobs:
                logger.info(f"  - {job.name} (다음 실행: {job.next_run_time})")

            return True

        except Exception as e:
            logger.error(f"스케줄러 시작 실패: {e}")
            return False

    def stop(self) -> bool:
        """
        스케줄러 중지

        Returns:
            중지 성공 여부
        """
        try:
            if not self.is_running:
                logger.warning("스케줄러가 실행 중이 아닙니다.")
                return False

            logger.info("스케줄러 중지")
            self.scheduler.shutdown(wait=False)
            self.is_running = False

            return True

        except Exception as e:
            logger.error(f"스케줄러 중지 실패: {e}")
            return False

    def shutdown(self) -> bool:
        """
        스케줄러 안전 종료

        Returns:
            종료 성공 여부
        """
        try:
            logger.info("스케줄러 안전 종료 시작")

            if self.is_running:
                # 실행 중인 작업 완료 대기
                self.scheduler.shutdown(wait=True)
                self.is_running = False

            logger.info("스케줄러 안전 종료 완료")
            return True

        except Exception as e:
            logger.error(f"스케줄러 안전 종료 실패: {e}")
            return False

    def remove_job(self, job_id: str) -> bool:
        """
        작업 제거

        Args:
            job_id: 작업 ID

        Returns:
            제거 성공 여부
        """
        try:
            self.scheduler.remove_job(job_id)

            if job_id in self.jobs:
                del self.jobs[job_id]

            logger.info(f"작업 제거 완료: {job_id}")
            return True

        except Exception as e:
            logger.error(f"작업 제거 실패: {job_id} - {e}")
            return False

    def pause_job(self, job_id: str) -> bool:
        """
        작업 일시 중지

        Args:
            job_id: 작업 ID

        Returns:
            중지 성공 여부
        """
        try:
            self.scheduler.pause_job(job_id)

            if job_id in self.jobs:
                self.jobs[job_id]['enabled'] = False
                self.jobs[job_id]['status'] = 'paused'

            logger.info(f"작업 일시 중지: {job_id}")
            return True

        except Exception as e:
            logger.error(f"작업 일시 중지 실패: {job_id} - {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """
        작업 재개

        Args:
            job_id: 작업 ID

        Returns:
            재개 성공 여부
        """
        try:
            self.scheduler.resume_job(job_id)

            if job_id in self.jobs:
                self.jobs[job_id]['enabled'] = True
                self.jobs[job_id]['status'] = 'scheduled'

            logger.info(f"작업 재개: {job_id}")
            return True

        except Exception as e:
            logger.error(f"작업 재개 실패: {job_id} - {e}")
            return False

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        작업 상태 조회

        Args:
            job_id: 작업 ID

        Returns:
            작업 상태 정보
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }

                # 추가 정보 병합
                if job_id in self.jobs:
                    job_info.update(self.jobs[job_id])

                return job_info

            return None

        except Exception as e:
            logger.error(f"작업 상태 조회 실패: {job_id} - {e}")
            return None

    def get_all_jobs(self) -> list:
        """
        모든 작업 정보 조회

        Returns:
            작업 정보 목록
        """
        jobs_info = []

        for job in self.scheduler.get_jobs():
            job_info = {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }

            # 추가 정보 병합
            if job.id in self.jobs:
                job_info.update(self.jobs[job.id])

            jobs_info.append(job_info)

        return jobs_info

    def modify_job_time(self, job_id: str, new_time: str) -> bool:
        """
        작업 시간 수정

        Args:
            job_id: 작업 ID
            new_time: 새로운 시간 (HH:MM 형식)

        Returns:
            수정 성공 여부
        """
        try:
            # 기존 작업 정보 조회
            job_info = self.get_job_status(job_id)
            if not job_info:
                logger.error(f"작업을 찾을 수 없습니다: {job_id}")
                return False

            # 작업 제거 및 재등록
            self.remove_job(job_id)

            # 작업 타입에 따라 재등록
            if job_info['type'] == 'daily':
                self.schedule_daily_report(new_time, job_id)
            elif job_info['type'] == 'weekly':
                day = job_info.get('day', 'monday')
                self.schedule_weekly_report(day, new_time, job_id)
            elif job_info['type'] == 'monthly':
                day = job_info.get('day', 1)
                self.schedule_monthly_report(day, new_time, job_id)

            logger.info(f"작업 시간 수정 완료: {job_id} -> {new_time}")
            return True

        except Exception as e:
            logger.error(f"작업 시간 수정 실패: {job_id} - {e}")
            return False

    def _execute_daily_report(self):
        """일일 리포트 실행"""
        logger.info("일일 리포트 실행 시작")
        try:
            result = self.generator.generate_daily_report()
            if result.get('success'):
                logger.info(f"일일 리포트 실행 완료: {result.get('output_path')}")

                # 이메일 알림 전송
                if self.config.email_notification.enabled:
                    self._send_email_notification(result)
            else:
                logger.error(f"일일 리포트 실행 실패: {result.get('error')}")

                # 오류 알림 전송
                if self.config.email_notification.enabled:
                    self._send_error_notification(result.get('error'), '일일')
        except Exception as e:
            logger.error(f"일일 리포트 실행 중 예외 발생: {e}")

            # 오류 알림 전송
            if self.config.email_notification.enabled:
                self._send_error_notification(str(e), '일일')
            raise

    def _execute_weekly_report(self):
        """주간 리포트 실행"""
        logger.info("주간 리포트 실행 시작")
        try:
            result = self.generator.generate_weekly_report()
            if result.get('success'):
                logger.info(f"주간 리포트 실행 완료: {result.get('output_path')}")

                # 이메일 알림 전송
                if self.config.email_notification.enabled:
                    self._send_email_notification(result)
            else:
                logger.error(f"주간 리포트 실행 실패: {result.get('error')}")

                # 오류 알림 전송
                if self.config.email_notification.enabled:
                    self._send_error_notification(result.get('error'), '주간')
        except Exception as e:
            logger.error(f"주간 리포트 실행 중 예외 발생: {e}")

            # 오류 알림 전송
            if self.config.email_notification.enabled:
                self._send_error_notification(str(e), '주간')
            raise

    def _execute_monthly_report(self):
        """월간 리포트 실행"""
        logger.info("월간 리포트 실행 시작")
        try:
            result = self.generator.generate_monthly_report()
            if result.get('success'):
                logger.info(f"월간 리포트 실행 완료: {result.get('output_path')}")

                # 이메일 알림 전송
                if self.config.email_notification.enabled:
                    self._send_email_notification(result)
            else:
                logger.error(f"월간 리포트 실행 실패: {result.get('error')}")

                # 오류 알림 전송
                if self.config.email_notification.enabled:
                    self._send_error_notification(result.get('error'), '월간')
        except Exception as e:
            logger.error(f"월간 리포트 실행 중 예외 발생: {e}")

            # 오류 알림 전송
            if self.config.email_notification.enabled:
                self._send_error_notification(str(e), '월간')
            raise

    def _send_email_notification(self, report_result: dict):
        """이메일 알림 전송"""
        try:
            from .report_notifier import ReportNotifier

            notifier = ReportNotifier(self.config.email_notification)
            success = notifier.send_report_notification(report_result)

            if success:
                logger.info("이메일 알림 전송 완료")
            else:
                logger.warning("이메일 알림 전송 실패")

        except Exception as e:
            logger.error(f"이메일 알림 전송 중 예외 발생: {e}")

    def _send_error_notification(self, error_message: str, report_type: str):
        """오류 알림 전송"""
        try:
            from .report_notifier import ReportNotifier

            notifier = ReportNotifier(self.config.email_notification)
            success = notifier.send_error_notification(error_message, report_type)

            if success:
                logger.info(f"{report_type} 리포트 오류 알림 전송 완료")
            else:
                logger.warning(f"{report_type} 리포트 오류 알림 전송 실패")

        except Exception as e:
            logger.error(f"오류 알림 전송 중 예외 발생: {e}")


def create_report_scheduler(config_path: str = None) -> ReportScheduler:
    """
    리포트 스케줄러 팩토리 함수

    Args:
        config_path: 설정 파일 경로 (None인 경우 기본 설정 사용)

    Returns:
        리포트 스케줄러 인스턴스
    """
    if config_path and os.path.exists(config_path):
        config = ReportConfig.from_json(config_path)
    else:
        config = ReportConfig()

    generator = ReportGenerator(config)
    scheduler = ReportScheduler(config, generator)

    # 기본 스케줄 설정
    scheduler.setup_default_schedules()

    return scheduler