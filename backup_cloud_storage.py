"""
백업 클라우드 저장 매니저

백업 파일을 AWS S3 및 Google Cloud Storage에 자동으로 업로드합니다.
- AWS S3 지원
- Google Cloud Storage 지원
- 자동 업로드/다운로드
- 멀티파트 업로드 (큰 파일)
- 암호화 지원
- 메타데이터 관리
"""

import os
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from google.cloud import storage as gcs
    from google.cloud.exceptions import GoogleCloudError
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


class StorageProvider(Enum):
    """스토리지 제공자"""
    AWS_S3 = "aws_s3"
    GOOGLE_CLOUD = "google_cloud"
    LOCAL = "local"


class StorageStatus(Enum):
    """스토리지 상태"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"


@dataclass
class CloudBackupMetadata:
    """클라우드 백업 메타데이터"""
    backup_id: str
    provider: StorageProvider
    bucket_name: str
    object_key: str
    upload_timestamp: str
    size_bytes: int
    etag: Optional[str] = None
    version_id: Optional[str] = None
    storage_class: str = "STANDARD"
    encryption: Optional[str] = None
    checksum: Optional[str] = None
    download_url: Optional[str] = None
    expiration: Optional[str] = None

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'backup_id': self.backup_id,
            'provider': self.provider.value,
            'bucket_name': self.bucket_name,
            'object_key': self.object_key,
            'upload_timestamp': self.upload_timestamp,
            'size_bytes': self.size_bytes,
            'etag': self.etag,
            'version_id': self.version_id,
            'storage_class': self.storage_class,
            'encryption': self.encryption,
            'checksum': self.checksum,
            'download_url': self.download_url,
            'expiration': self.expiration
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CloudBackupMetadata':
        """딕셔너리에서 객체 생성"""
        return cls(
            backup_id=data['backup_id'],
            provider=StorageProvider(data['provider']),
            bucket_name=data['bucket_name'],
            object_key=data['object_key'],
            upload_timestamp=data['upload_timestamp'],
            size_bytes=data['size_bytes'],
            etag=data.get('etag'),
            version_id=data.get('version_id'),
            storage_class=data.get('storage_class', 'STANDARD'),
            encryption=data.get('encryption'),
            checksum=data.get('checksum'),
            download_url=data.get('download_url'),
            expiration=data.get('expiration')
        )


class S3StorageManager:
    """AWS S3 저장소 매니저"""

    def __init__(self, aws_access_key: str, aws_secret_key: str,
                 region: str = "us-east-1", endpoint_url: Optional[str] = None):
        """
        S3 매니저 초기화

        Args:
            aws_access_key: AWS 액세스 키
            aws_secret_key: AWS 시크릿 키
            region: AWS 리전
            endpoint_url: S3 호환 엔드포인트 URL (선택 사항)
        """
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 패키지가 필요합니다. pip install boto3")

        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.region = region
        self.endpoint_url = endpoint_url
        self.logger = logging.getLogger(__name__)

        # S3 클라이언트 초기화
        self._init_client()

    def _init_client(self):
        """S3 클라이언트 초기화"""
        try:
            config = {
                'aws_access_key_id': self.aws_access_key,
                'aws_secret_access_key': self.aws_secret_key,
                'region_name': self.region
            }

            if self.endpoint_url:
                config['endpoint_url'] = self.endpoint_url

            self.s3_client = boto3.client('s3', **config)
            self.logger.info(f"S3 클라이언트 초기화 완료 (리전: {self.region})")

        except Exception as e:
            self.logger.error(f"S3 클라이언트 초기화 실패: {e}")
            raise

    def upload_file(self, file_path: str, bucket_name: str, object_key: str,
                   storage_class: str = "STANDARD",
                   encryption: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> Optional[CloudBackupMetadata]:
        """
        파일 업로드

        Args:
            file_path: 업로드할 파일 경로
            bucket_name: S3 버킷 이름
            object_key: 객체 키 (파일 경로)
            storage_class: 저장소 클래스 (STANDARD, IA, GLACIER 등)
            encryption: 암호화 방식 (AES256, aws:kms)
            metadata: 사용자 메타데이터

        Returns:
            CloudBackupMetadata: 업로드된 파일 메타데이터
        """
        try:
            self.logger.info(f"S3 업로드 시작: {file_path} -> {bucket_name}/{object_key}")

            # 파일 존재 확인
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")

            file_size = os.path.getsize(file_path)

            # 업로드 파라미터
            extra_args = {
                'StorageClass': storage_class
            }

            if encryption:
                extra_args['ServerSideEncryption'] = encryption

            if metadata:
                extra_args['Metadata'] = metadata

            # 멀티파트 업로드 (파일이 100MB 이상인 경우)
            if file_size > 100 * 1024 * 1024:  # 100MB
                self.logger.info(f"멀티파트 업로드 사용 (파일 크기: {file_size:,} bytes)")
                self.s3_client.upload_file(
                    file_path, bucket_name, object_key,
                    ExtraArgs=extra_args,
                    Config=boto3.s3.transfer.TransferConfig(
                        multipart_threshold=100 * 1024 * 1024,
                        max_concurrency=10
                    )
                )
            else:
                self.s3_client.upload_file(
                    file_path, bucket_name, object_key,
                    ExtraArgs=extra_args
                )

            # 객체 정보 조회
            response = self.s3_client.head_object(
                Bucket=bucket_name,
                Key=object_key
            )

            # 체크섬 계산
            checksum = self._calculate_file_checksum(file_path)

            # 메타데이터 생성
            cloud_metadata = CloudBackupMetadata(
                backup_id=Path(object_key).stem,
                provider=StorageProvider.AWS_S3,
                bucket_name=bucket_name,
                object_key=object_key,
                upload_timestamp=datetime.now().isoformat(),
                size_bytes=file_size,
                etag=response.get('ETag', '').strip('"'),
                version_id=response.get('VersionId'),
                storage_class=response.get('StorageClass', storage_class),
                encryption=encryption,
                checksum=checksum
            )

            self.logger.info(f"S3 업로드 완료: {object_key} ({file_size:,} bytes)")

            return cloud_metadata

        except ClientError as e:
            self.logger.error(f"S3 업로드 실패: {e}")
            return None
        except Exception as e:
            self.logger.error(f"S3 업로드 중 오류: {e}")
            return None

    def download_file(self, bucket_name: str, object_key: str,
                    download_path: str) -> bool:
        """
        파일 다운로드

        Args:
            bucket_name: S3 버킷 이름
            object_key: 객체 키
            download_path: 다운로드 경로

        Returns:
            성공 여부
        """
        try:
            self.logger.info(f"S3 다운로드 시작: {bucket_name}/{object_key} -> {download_path}")

            # 디렉토리 생성
            os.makedirs(os.path.dirname(download_path), exist_ok=True)

            # 파일 다운로드
            self.s3_client.download_file(bucket_name, object_key, download_path)

            self.logger.info(f"S3 다운로드 완료: {download_path}")
            return True

        except ClientError as e:
            self.logger.error(f"S3 다운로드 실패: {e}")
            return False
        except Exception as e:
            self.logger.error(f"S3 다운로드 중 오류: {e}")
            return False

    def list_backups(self, bucket_name: str, prefix: str = "") -> List[Dict]:
        """
        백업 파일 목록 조회

        Args:
            bucket_name: S3 버킷 이름
            prefix: 검색 Prefix (예: "backups/")

        Returns:
            백업 파일 리스트
        """
        try:
            backups = []

            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        backups.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat(),
                            'etag': obj['ETag'].strip('"'),
                            'storage_class': obj.get('StorageClass', 'STANDARD')
                        })

            return backups

        except ClientError as e:
            self.logger.error(f"S3 목록 조회 실패: {e}")
            return []

    def delete_file(self, bucket_name: str, object_key: str) -> bool:
        """
        파일 삭제

        Args:
            bucket_name: S3 버킷 이름
            object_key: 객체 키

        Returns:
            성공 여부
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            self.logger.info(f"S3 파일 삭제 완료: {object_key}")
            return True

        except ClientError as e:
            self.logger.error(f"S3 파일 삭제 실패: {e}")
            return False

    def generate_presigned_url(self, bucket_name: str, object_key: str,
                              expiration: int = 3600) -> Optional[str]:
        """
        presigned URL 생성

        Args:
            bucket_name: S3 버킷 이름
            object_key: 객체 키
            expiration: 유효 시간 (초)

        Returns:
            presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return url

        except ClientError as e:
            self.logger.error(f"presigned URL 생성 실패: {e}")
            return None

    def _calculate_file_checksum(self, file_path: str) -> str:
        """파일 체크섬 계산"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


class GCSStorageManager:
    """Google Cloud Storage 매니저"""

    def __init__(self, credentials_path: Optional[str] = None,
                 project_id: Optional[str] = None):
        """
        GCS 매니저 초기화

        Args:
            credentials_path: 서비스 계정 키 파일 경로
            project_id: GCP 프로젝트 ID
        """
        if not GCS_AVAILABLE:
            raise ImportError("google-cloud-storage 패키지가 필요합니다. "
                            "pip install google-cloud-storage")

        self.credentials_path = credentials_path
        self.project_id = project_id
        self.logger = logging.getLogger(__name__)

        # GCS 클라이언트 초기화
        self._init_client()

    def _init_client(self):
        """GCS 클라이언트 초기화"""
        try:
            if self.credentials_path:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path

            self.client = gcs.Client(project=self.project_id)
            self.logger.info(f"GCS 클라이언트 초기화 완료 (프로젝트: {self.project_id})")

        except Exception as e:
            self.logger.error(f"GCS 클라이언트 초기화 실패: {e}")
            raise

    def upload_file(self, file_path: str, bucket_name: str, object_key: str,
                   storage_class: str = "STANDARD",
                   encryption: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> Optional[CloudBackupMetadata]:
        """
        파일 업로드

        Args:
            file_path: 업로드할 파일 경로
            bucket_name: GCS 버킷 이름
            object_key: 객체 키
            storage_class: 저장소 클래스
            encryption: 암호화 키
            metadata: 사용자 메타데이터

        Returns:
            CloudBackupMetadata
        """
        try:
            self.logger.info(f"GCS 업로드 시작: {file_path} -> {bucket_name}/{object_key}")

            # 버킷 가져오기
            bucket = self.client.bucket(bucket_name)

            # 블롭 생성
            blob = bucket.blob(object_key)

            # 저장소 클래스 설정
            blob.storage_class = storage_class

            # 메타데이터 설정
            if metadata:
                blob.metadata = metadata

            # 암호화 설정
            if encryption:
                blob.encryption_key = encryption

            # 파일 업로드
            blob.upload_from_filename(file_path)

            # 파일 정보
            file_size = os.path.getsize(file_path)
            checksum = self._calculate_file_checksum(file_path)

            # 메타데이터 생성
            cloud_metadata = CloudBackupMetadata(
                backup_id=Path(object_key).stem,
                provider=StorageProvider.GOOGLE_CLOUD,
                bucket_name=bucket_name,
                object_key=object_key,
                upload_timestamp=datetime.now().isoformat(),
                size_bytes=file_size,
                etag=blob.etag,
                storage_class=storage_class,
                encryption=encryption,
                checksum=checksum,
                download_url=blob.generate_signed_url(expiration=datetime.timedelta(hours=1))
            )

            self.logger.info(f"GCS 업로드 완료: {object_key} ({file_size:,} bytes)")

            return cloud_metadata

        except GoogleCloudError as e:
            self.logger.error(f"GCS 업로드 실패: {e}")
            return None
        except Exception as e:
            self.logger.error(f"GCS 업로드 중 오류: {e}")
            return None

    def download_file(self, bucket_name: str, object_key: str,
                    download_path: str) -> bool:
        """
        파일 다운로드

        Args:
            bucket_name: GCS 버킷 이름
            object_key: 객체 키
            download_path: 다운로드 경로

        Returns:
            성공 여부
        """
        try:
            self.logger.info(f"GCS 다운로드 시작: {bucket_name}/{object_key} -> {download_path}")

            # 버킷 및 블롭 가져오기
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_key)

            # 디렉토리 생성
            os.makedirs(os.path.dirname(download_path), exist_ok=True)

            # 파일 다운로드
            blob.download_to_filename(download_path)

            self.logger.info(f"GCS 다운로드 완료: {download_path}")
            return True

        except GoogleCloudError as e:
            self.logger.error(f"GCS 다운로드 실패: {e}")
            return False
        except Exception as e:
            self.logger.error(f"GCS 다운로드 중 오류: {e}")
            return False

    def list_backups(self, bucket_name: str, prefix: str = "") -> List[Dict]:
        """
        백업 파일 목록 조회

        Args:
            bucket_name: GCS 버킷 이름
            prefix: 검색 Prefix

        Returns:
            백업 파일 리스트
        """
        try:
            backups = []

            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)

            for blob in blobs:
                backups.append({
                    'key': blob.name,
                    'size': blob.size,
                    'last_modified': blob.updated.isoformat(),
                    'etag': blob.etag,
                    'storage_class': blob.storage_class
                })

            return backups

        except GoogleCloudError as e:
            self.logger.error(f"GCS 목록 조회 실패: {e}")
            return []

    def delete_file(self, bucket_name: str, object_key: str) -> bool:
        """
        파일 삭제

        Args:
            bucket_name: GCS 버킷 이름
            object_key: 객체 키

        Returns:
            성공 여부
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_key)
            blob.delete()

            self.logger.info(f"GCS 파일 삭제 완료: {object_key}")
            return True

        except GoogleCloudError as e:
            self.logger.error(f"GCS 파일 삭제 실패: {e}")
            return False

    def _calculate_file_checksum(self, file_path: str) -> str:
        """파일 체크섬 계산"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


class BackupCloudStorage:
    """백업 클라우드 저장소 매니저"""

    def __init__(self, config: Dict):
        """
        클라우드 저장소 매니저 초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

        # 스토리지 매니저 초기화
        self.s3_manager: Optional[S3StorageManager] = None
        self.gcs_manager: Optional[GCSStorageManager] = None

        # 메타데이터 파일
        self.metadata_file = Path(config.get('backup_dir', 'backups')) / 'cloud_metadata.json'
        self.cloud_metadata: Dict[str, CloudBackupMetadata] = {}

        # 메타데이터 로드
        self._load_metadata()

        # 초기화
        self._init_managers()

    def _init_managers(self):
        """스토리지 매니저 초기화"""
        # S3 초기화
        s3_config = self.config.get('aws_s3', {})
        if s3_config.get('enabled', False):
            try:
                self.s3_manager = S3StorageManager(
                    aws_access_key=s3_config['access_key'],
                    aws_secret_key=s3_config['secret_key'],
                    region=s3_config.get('region', 'us-east-1'),
                    endpoint_url=s3_config.get('endpoint_url')
                )
                self.logger.info("S3 매니저 초기화 완료")
            except Exception as e:
                self.logger.error(f"S3 매니저 초기화 실패: {e}")

        # GCS 초기화
        gcs_config = self.config.get('google_cloud', {})
        if gcs_config.get('enabled', False):
            try:
                self.gcs_manager = GCSStorageManager(
                    credentials_path=gcs_config.get('credentials_path'),
                    project_id=gcs_config.get('project_id')
                )
                self.logger.info("GCS 매니저 초기화 완료")
            except Exception as e:
                self.logger.error(f"GCS 매니저 초기화 실패: {e}")

    def _load_metadata(self):
        """클라우드 메타데이터 로드"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for backup_id, meta_data in data.items():
                        self.cloud_metadata[backup_id] = CloudBackupMetadata.from_dict(meta_data)
                self.logger.info(f"로드된 클라우드 백업 메타데이터: {len(self.cloud_metadata)}개")
            except Exception as e:
                self.logger.error(f"메타데이터 로드 실패: {e}")
                self.cloud_metadata = {}

    def _save_metadata(self):
        """클라우드 메타데이터 저장"""
        try:
            data = {
                backup_id: meta.to_dict()
                for backup_id, meta in self.cloud_metadata.items()
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"메타데이터 저장 실패: {e}")

    def upload_backup(self, backup_id: str, file_path: str,
                     providers: Optional[List[StorageProvider]] = None) -> Dict[StorageProvider, CloudBackupMetadata]:
        """
        백업 파일을 클라우드에 업로드

        Args:
            backup_id: 백업 ID
            file_path: 백업 파일 경로
            providers: 업로드할 제공자 목록 (None이면 모두)

        Returns:
            제공자별 업로드 결과
        """
        with self._lock:
            results = {}

            # 업로드할 제공자 결정
            if providers is None:
                providers = []
                if self.s3_manager:
                    providers.append(StorageProvider.AWS_S3)
                if self.gcs_manager:
                    providers.append(StorageProvider.GOOGLE_CLOUD)

            # 파일명에서 객체 키 생성
            filename = os.path.basename(file_path)
            object_key = f"backups/{filename}"

            # 각 제공자에 업로드
            for provider in providers:
                try:
                    if provider == StorageProvider.AWS_S3 and self.s3_manager:
                        s3_config = self.config.get('aws_s3', {})
                        metadata = self.s3_manager.upload_file(
                            file_path,
                            s3_config['bucket_name'],
                            object_key,
                            storage_class=s3_config.get('storage_class', 'STANDARD'),
                            encryption=s3_config.get('encryption'),
                            metadata={'backup_id': backup_id}
                        )
                        if metadata:
                            results[provider] = metadata
                            self.cloud_metadata[f"{backup_id}_{provider.value}"] = metadata

                    elif provider == StorageProvider.GOOGLE_CLOUD and self.gcs_manager:
                        gcs_config = self.config.get('google_cloud', {})
                        metadata = self.gcs_manager.upload_file(
                            file_path,
                            gcs_config['bucket_name'],
                            object_key,
                            storage_class=gcs_config.get('storage_class', 'STANDARD'),
                            encryption=gcs_config.get('encryption_key'),
                            metadata={'backup_id': backup_id}
                        )
                        if metadata:
                            results[provider] = metadata
                            self.cloud_metadata[f"{backup_id}_{provider.value}"] = metadata

                except Exception as e:
                    self.logger.error(f"{provider.value} 업로드 실패: {e}")

            # 메타데이터 저장
            if results:
                self._save_metadata()

            self.logger.info(f"클라우드 업로드 완료: {len(results)}개 제공자")

            return results

    def download_backup(self, backup_id: str, provider: StorageProvider,
                       download_path: str) -> bool:
        """
        클라우드에서 백업 다운로드

        Args:
            backup_id: 백업 ID
            provider: 스토리지 제공자
            download_path: 다운로드 경로

        Returns:
            성공 여부
        """
        with self._lock:
            try:
                # 메타데이터 조회
                metadata_key = f"{backup_id}_{provider.value}"
                if metadata_key not in self.cloud_metadata:
                    self.logger.error(f"클라우드 메타데이터를 찾을 수 없습니다: {metadata_key}")
                    return False

                metadata = self.cloud_metadata[metadata_key]

                # 제공자별 다운로드
                if provider == StorageProvider.AWS_S3 and self.s3_manager:
                    return self.s3_manager.download_file(
                        metadata.bucket_name,
                        metadata.object_key,
                        download_path
                    )
                elif provider == StorageProvider.GOOGLE_CLOUD and self.gcs_manager:
                    return self.gcs_manager.download_file(
                        metadata.bucket_name,
                        metadata.object_key,
                        download_path
                    )
                else:
                    self.logger.error(f"제공자가 초기화되지 않았습니다: {provider.value}")
                    return False

            except Exception as e:
                self.logger.error(f"클라우드 다운로드 실패: {e}")
                return False

    def list_cloud_backups(self, provider: Optional[StorageProvider] = None) -> List[CloudBackupMetadata]:
        """
        클라우드 백업 목록 조회

        Args:
            provider: 필터링할 제공자 (None이면 전체)

        Returns:
            백업 메타데이터 리스트
        """
        backups = list(self.cloud_metadata.values())

        if provider:
            backups = [b for b in backups if b.provider == provider]

        # 시간순 정렬
        backups.sort(key=lambda x: x.upload_timestamp, reverse=True)

        return backups

    def delete_cloud_backup(self, backup_id: str, provider: StorageProvider) -> bool:
        """
        클라우드 백업 삭제

        Args:
            backup_id: 백업 ID
            provider: 스토리지 제공자

        Returns:
            성공 여부
        """
        with self._lock:
            try:
                # 메타데이터 조회
                metadata_key = f"{backup_id}_{provider.value}"
                if metadata_key not in self.cloud_metadata:
                    self.logger.error(f"클라우드 메타데이터를 찾을 수 없습니다: {metadata_key}")
                    return False

                metadata = self.cloud_metadata[metadata_key]

                # 제공자별 삭제
                success = False

                if provider == StorageProvider.AWS_S3 and self.s3_manager:
                    success = self.s3_manager.delete_file(
                        metadata.bucket_name,
                        metadata.object_key
                    )
                elif provider == StorageProvider.GOOGLE_CLOUD and self.gcs_manager:
                    success = self.gcs_manager.delete_file(
                        metadata.bucket_name,
                        metadata.object_key
                    )

                # 메타데이터에서 제거
                if success:
                    del self.cloud_metadata[metadata_key]
                    self._save_metadata()

                return success

            except Exception as e:
                self.logger.error(f"클라우드 백업 삭제 실패: {e}")
                return False

    def get_storage_stats(self) -> Dict:
        """스토리지 통계 조회"""
        stats = {
            'total_cloud_backups': len(self.cloud_metadata),
            'by_provider': {
                'aws_s3': len([b for b in self.cloud_metadata.values()
                              if b.provider == StorageProvider.AWS_S3]),
                'google_cloud': len([b for b in self.cloud_metadata.values()
                                    if b.provider == StorageProvider.GOOGLE_CLOUD])
            },
            'total_size_bytes': sum(m.size_bytes for m in self.cloud_metadata.values()),
            'latest_backup': None,
            'oldest_backup': None
        }

        if self.cloud_metadata:
            timestamps = [m.upload_timestamp for m in self.cloud_metadata.values()]
            stats['latest_backup'] = max(timestamps)
            stats['oldest_backup'] = min(timestamps)

        return stats


def create_cloud_storage_config(aws_access_key: str = None,
                                aws_secret_key: str = None,
                                aws_bucket: str = None,
                                gcp_credentials: str = None,
                                gcp_bucket: str = None,
                                gcp_project: str = None,
                                backup_dir: str = "backups") -> Dict:
    """
    클라우드 저장소 설정 생성

    Returns:
        설정 딕셔너리
    """
    config = {
        'backup_dir': backup_dir,
        'aws_s3': {
            'enabled': False,
            'access_key': aws_access_key or '',
            'secret_key': aws_secret_key or '',
            'bucket_name': aws_bucket or '',
            'region': 'ap-northeast-2',  # Seoul
            'storage_class': 'STANDARD',
            'encryption': 'AES256'
        },
        'google_cloud': {
            'enabled': False,
            'credentials_path': gcp_credentials or '',
            'bucket_name': gcp_bucket or '',
            'project_id': gcp_project or '',
            'storage_class': 'STANDARD',
            'encryption_key': None
        }
    }

    # 활성화된 제공자 자동 감지
    if aws_access_key and aws_secret_key and aws_bucket:
        config['aws_s3']['enabled'] = True

    if gcp_credentials and gcp_bucket:
        config['google_cloud']['enabled'] = True

    return config