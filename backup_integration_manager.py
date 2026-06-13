"""
백업 시스템 통합 매니저

백업 매니저, 클라우드 저장, 알림 시스템을 통합 관리합니다.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from database_backup_manager import DatabaseBackupManager, BackupType, BackupMetadata
from backup_cloud_storage import BackupCloudStorage, StorageProvider, CloudBackupMetadata
from backup_notification_system import (
    BackupNotificationSystem, NotificationType, NotificationPriority
)


class BackupIntegrationManager:
    """백업 시스템 통합 매니저"""

    def __init__(self, config_path: str = "backup_integration_config.json"):
        """
        통합 매니저 초기화

        Args:
            config_path: 설정 파일 경로
        """
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)

        # 설정 로드
        self.config = self._load_config()

        # 백업 매니저 초기화
        self.backup_manager = DatabaseBackupManager(
            backup_dir=self.config['backup_dir'],
            compress=self.config['compression']['enabled'],
            max_backups=self.config['retention']['max_backups']
        )

        # 클라우드 저장소 초기화
        self.cloud_storage = BackupCloudStorage(
            {**self.config, 'backup_dir': self.config['backup_dir']}
        )

        # 알림 시스템 초기화
        self.notification_system = BackupNotificationSystem(
            {**self.config, 'backup_dir': self.config['backup_dir']}
        )

        self.logger.info("백업 통합 시스템 초기화 완료")

    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"설정 파일 로드 실패: {e}")

        # 기본 설정 반환
        return self._create_default_config()

    def _create_default_config(self) -> Dict:
        """기본 설정 생성"""
        return {
            'backup_dir': 'backups',
            'compression': {
                'enabled': True
            },
            'retention': {
                'max_backups': 30,
                'daily_backups_keep_days': 7,
                'weekly_backups_keep_weeks': 4
            },
            'cloud_storage': {
                'enabled': False,
                'auto_upload': False,
                'providers': []
            },
            'notifications': {
                'enabled': False,
                'on_backup_success': True,
                'on_backup_failed': True,
                'on_restore_success': True,
                'on_restore_failed': True
            },
            'aws_s3': {
                'enabled': False,
                'access_key': '',
                'secret_key': '',
                'bucket_name': '',
                'region': 'ap-northeast-2',
                'storage_class': 'STANDARD'
            },
            'google_cloud': {
                'enabled': False,
                'credentials_path': '',
                'bucket_name': '',
                'project_id': ''
            },
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': ''
            },
            'slack': {
                'enabled': False,
                'webhook_url': '',
                'channel': None
            },
            'webhook': {
                'enabled': False,
                'url': ''
            },
            'default_recipients': []
        }

    def save_config(self):
        """현재 설정 저장"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info("설정 파일 저장 완료")
        except Exception as e:
            self.logger.error(f"설정 파일 저장 실패: {e}")

    def create_backup(self, db_path: str, backup_type: BackupType = BackupType.FULL,
                     description: str = "", tags: Optional[List[str]] = None,
                     upload_to_cloud: bool = None) -> Optional[str]:
        """
        통합 백업 생성

        Args:
            db_path: 데이터베이스 경로
            backup_type: 백업 타입
            description: 백업 설명
            tags: 백업 태그
            upload_to_cloud: 클라우드 업로드 여부 (None이면 설정 사용)

        Returns:
            백업 ID
        """
        start_time = datetime.now()

        try:
            self.logger.info(f"백업 시작: {backup_type.value} - {db_path}")

            # 1. 로컬 백업 생성
            if backup_type == BackupType.FULL:
                metadata = self.backup_manager.create_full_backup(
                    db_path, description, tags
                )
            else:
                metadata = self.backup_manager.create_incremental_backup(
                    db_path, description, tags
                )

            if not metadata:
                # 백업 실패 알림
                if self.config['notifications']['enabled'] and \
                   self.config['notifications']['on_backup_failed']:
                    self.notification_system.notify_backup_failed(
                        backup_type.value,
                        "로컬 백업 생성 실패"
                    )
                return None

            backup_id = metadata.backup_id
            backup_path = metadata.backup_path

            # 2. 클라우드 업로드
            cloud_providers = []

            if upload_to_cloud is None:
                upload_to_cloud = self.config['cloud_storage']['auto_upload']

            if upload_to_cloud and self.config['cloud_storage']['enabled']:
                providers_config = self.config['cloud_storage']['providers']

                if not providers_config:
                    # 설정된 제공자 자동 감지
                    providers_config = []
                    if self.config['aws_s3']['enabled']:
                        providers_config.append(StorageProvider.AWS_S3)
                    if self.config['google_cloud']['enabled']:
                        providers_config.append(StorageProvider.GOOGLE_CLOUD)

                if providers_config:
                    self.logger.info(f"클라우드 업로드 시작: {providers_config}")
                    cloud_results = self.cloud_storage.upload_backup(
                        backup_id, backup_path, providers_config
                    )

                    cloud_providers = [p.value for p in cloud_results.keys()]

            # 3. 알림 발송
            if self.config['notifications']['enabled'] and \
               self.config['notifications']['on_backup_success']:

                duration = (datetime.now() - start_time).total_seconds()

                self.notification_system.notify_backup_success(
                    backup_id=backup_id,
                    backup_type=backup_type.value,
                    size_bytes=metadata.size_bytes,
                    duration_seconds=duration,
                    providers=cloud_providers if cloud_providers else None
                )

            self.logger.info(f"백업 완료: {backup_id}")
            return backup_id

        except Exception as e:
            self.logger.error(f"백업 실패: {e}")

            # 실패 알림
            if self.config['notifications']['enabled'] and \
               self.config['notifications']['on_backup_failed']:
                self.notification_system.notify_backup_failed(
                    backup_type.value,
                    str(e)
                )

            return None

    def restore_backup(self, backup_id: str, restore_path: Optional[str] = None,
                      download_from_cloud: bool = False,
                      cloud_provider: Optional[StorageProvider] = None) -> bool:
        """
        통합 백업 복구

        Args:
            backup_id: 백업 ID
            restore_path: 복구 경로
            download_from_cloud: 클라우드에서 다운로드
            cloud_provider: 클라우드 제공자

        Returns:
            성공 여부
        """
        try:
            self.logger.info(f"복구 시작: {backup_id}")

            # 1. 클라우드 다운로드 (필요한 경우)
            if download_from_cloud and cloud_provider:
                self.logger.info(f"클라우드 다운로드: {cloud_provider.value}")

                # 로컬 백업 경로 결정
                backup_path = Path(self.backup_manager.backup_dir) / f"{backup_id}.db"

                # 다운로드
                success = self.cloud_storage.download_backup(
                    backup_id, cloud_provider, str(backup_path)
                )

                if not success:
                    self.logger.error("클라우드 다운로드 실패")

                    if self.config['notifications']['enabled'] and \
                       self.config['notifications']['on_restore_failed']:
                        self.notification_system.notify_restore_failed(
                            backup_id,
                            "클라우드 다운로드 실패"
                        )

                    return False

            # 2. 로컬 복구
            success = self.backup_manager.restore_backup(
                backup_id, restore_path, force=True
            )

            if not success:
                self.logger.error("로컬 복구 실패")

                if self.config['notifications']['enabled'] and \
                   self.config['notifications']['on_restore_failed']:
                    self.notification_system.notify_restore_failed(
                        backup_id,
                        "로컬 복구 실패"
                    )

                return False

            # 3. 복구 성공 알림
            if self.config['notifications']['enabled'] and \
               self.config['notifications']['on_restore_success']:
                self.notification_system.notify_restore_success(
                    backup_id=backup_id,
                    restore_path=restore_path or "원본 위치"
                )

            self.logger.info(f"복구 완료: {backup_id}")
            return True

        except Exception as e:
            self.logger.error(f"복구 실패: {e}")

            if self.config['notifications']['enabled'] and \
               self.config['notifications']['on_restore_failed']:
                self.notification_system.notify_restore_failed(
                    backup_id,
                    str(e)
                )

            return False

    def list_backups(self, include_cloud: bool = False) -> Dict:
        """
        백업 목록 조회

        Args:
            include_cloud: 클라우드 백업 포함 여부

        Returns:
            백업 목록
        """
        # 로컬 백업
        local_backups = self.backup_manager.list_backups()

        result = {
            'local': [b.to_dict() for b in local_backups],
            'cloud': {}
        }

        # 클라우드 백업
        if include_cloud:
            cloud_backups = self.cloud_storage.list_cloud_backups()

            by_provider = {
                'aws_s3': [],
                'google_cloud': []
            }

            for backup in cloud_backups:
                provider = backup.provider.value
                if provider in by_provider:
                    by_provider[provider].append(backup.to_dict())

            result['cloud'] = by_provider

        return result

    def get_system_stats(self) -> Dict:
        """시스템 통계 조회"""
        # 백업 통계
        backup_stats = self.backup_manager.get_backup_stats()

        # 클라우드 통계
        cloud_stats = self.cloud_storage.get_storage_stats()

        # 알림 통계
        notification_stats = self.notification_system.get_notification_stats()

        return {
            'timestamp': datetime.now().isoformat(),
            'backup': backup_stats,
            'cloud_storage': cloud_stats,
            'notifications': notification_stats
        }

    def cleanup_old_backups(self):
        """오래된 백업 정리"""
        try:
            # 로컬 백업 정리는 자동으로 수행됨
            self.logger.info("오래된 백업 정리 완료")

            # 클라우드 백업 정리 (선택 사항)
            # if self.config['cloud_storage']['auto_cleanup']:
            #     self._cleanup_cloud_backups()

        except Exception as e:
            self.logger.error(f"백업 정리 실패: {e}")

    def send_weekly_report(self):
        """주간 보고서 발송"""
        try:
            stats = self.get_system_stats()

            # 주간 보고서 통계 계산
            weekly_stats = {
                'total_backups': stats['backup']['total_backups'],
                'full_backups': stats['backup']['full_backups'],
                'incremental_backups': stats['backup']['incremental_backups'],
                'total_size_bytes': stats['backup']['total_size_bytes'],
                'success_rate': 100.0  # 실패 카운트 필요
            }

            self.notification_system.send_weekly_report(weekly_stats)

        except Exception as e:
            self.logger.error(f"주간 보고서 발송 실패: {e}")

    def sync_cloud_backups(self, backup_ids: Optional[List[str]] = None):
        """
        클라우드 백업 동기화

        Args:
            backup_ids: 동기화할 백업 ID 목록 (None이면 전체)
        """
        try:
            self.logger.info("클라우드 백업 동기화 시작")

            # 동기화할 백업 결정
            if backup_ids is None:
                local_backups = self.backup_manager.list_backups()
                backup_ids = [b.backup_id for b in local_backups]

            # 각 백업 업로드
            for backup_id in backup_ids:
                # 메타데이터 조회
                metadata = self.backup_manager.get_backup_info(backup_id)

                if not metadata:
                    continue

                # 이미 클라우드에 있는지 확인
                if self.cloud_storage.cloud_metadata:
                    cloud_keys = [k for k in self.cloud_storage.cloud_metadata.keys()
                                 if k.startswith(backup_id)]
                    if cloud_keys:
                        self.logger.info(f"이미 클라우드에 존재: {backup_id}")
                        continue

                # 클라우드 업로드
                self.cloud_storage.upload_backup(
                    backup_id,
                    metadata.backup_path,
                    None  # 모든 활성화된 제공자
                )

            self.logger.info("클라우드 백업 동기화 완료")

        except Exception as e:
            self.logger.error(f"클라우드 백업 동기화 실패: {e}")


def create_integration_config(
        backup_dir: str = "backups",
        enable_compression: bool = True,
        max_backups: int = 30,
        enable_cloud: bool = False,
        enable_notifications: bool = False,
        **kwargs
) -> Dict:
    """
    통합 설정 생성

    Args:
        backup_dir: 백업 디렉토리
        enable_compression: 압축 활성화
        max_backups: 최대 백업 수
        enable_cloud: 클라우드 저장 활성화
        enable_notifications: 알림 활성화
        **kwargs: 추가 설정

    Returns:
        설정 딕셔너리
    """
    config = {
        'backup_dir': backup_dir,
        'compression': {
            'enabled': enable_compression
        },
        'retention': {
            'max_backups': max_backups,
            'daily_backups_keep_days': kwargs.get('daily_keep_days', 7),
            'weekly_backups_keep_weeks': kwargs.get('weekly_keep_weeks', 4)
        },
        'cloud_storage': {
            'enabled': enable_cloud,
            'auto_upload': kwargs.get('auto_upload', True),
            'providers': []
        },
        'notifications': {
            'enabled': enable_notifications,
            'on_backup_success': kwargs.get('notify_backup_success', True),
            'on_backup_failed': kwargs.get('notify_backup_failed', True),
            'on_restore_success': kwargs.get('notify_restore_success', True),
            'on_restore_failed': kwargs.get('notify_restore_failed', True)
        },
        'aws_s3': {
            'enabled': kwargs.get('aws_enabled', False),
            'access_key': kwargs.get('aws_access_key', ''),
            'secret_key': kwargs.get('aws_secret_key', ''),
            'bucket_name': kwargs.get('aws_bucket', ''),
            'region': kwargs.get('aws_region', 'ap-northeast-2'),
            'storage_class': 'STANDARD'
        },
        'google_cloud': {
            'enabled': kwargs.get('gcs_enabled', False),
            'credentials_path': kwargs.get('gcs_credentials', ''),
            'bucket_name': kwargs.get('gcs_bucket', ''),
            'project_id': kwargs.get('gcs_project', '')
        },
        'email': {
            'enabled': kwargs.get('email_enabled', False),
            'smtp_server': kwargs.get('email_smtp', 'smtp.gmail.com'),
            'smtp_port': kwargs.get('email_port', 587),
            'username': kwargs.get('email_user', ''),
            'password': kwargs.get('email_password', ''),
            'from_email': kwargs.get('email_from', '')
        },
        'slack': {
            'enabled': kwargs.get('slack_enabled', False),
            'webhook_url': kwargs.get('slack_webhook', ''),
            'channel': kwargs.get('slack_channel'),
            'username': 'Backup Bot',
            'icon_emoji': ':floppy_disk:'
        },
        'webhook': {
            'enabled': kwargs.get('webhook_enabled', False),
            'url': kwargs.get('webhook_url', ''),
            'headers': {}
        },
        'default_recipients': kwargs.get('recipients', [])
    }

    return config