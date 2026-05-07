#!/usr/bin/env python3
"""
API 키 인증 시스템
API 키 생성, 검증, 관리 기능 제공
"""

import hashlib
import secrets
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import threading

# 로깅 설정
logger = logging.getLogger(__name__)

class APIKey:
    """API 키 클래스"""

    def __init__(self, key_id: str, key_secret: str, name: str,
                 created_at: str, expires_at: Optional[str] = None,
                 is_active: bool = True, rate_limit: int = 1000,
                 usage_count: int = 0, last_used: Optional[str] = None,
                 permissions: List[str] = None):
        self.key_id = key_id
        self.key_secret = key_secret
        self.name = name
        self.created_at = created_at
        self.expires_at = expires_at
        self.is_active = is_active
        self.rate_limit = rate_limit
        self.usage_count = usage_count
        self.last_used = last_used
        self.permissions = permissions or ['read', 'write']

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'key_id': self.key_id,
            'key_secret': self.key_secret,
            'name': self.name,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'is_active': self.is_active,
            'rate_limit': self.rate_limit,
            'usage_count': self.usage_count,
            'last_used': self.last_used,
            'permissions': self.permissions
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'APIKey':
        """딕셔너리에서 인스턴스 생성"""
        return cls(
            key_id=data['key_id'],
            key_secret=data['key_secret'],
            name=data['name'],
            created_at=data['created_at'],
            expires_at=data.get('expires_at'),
            is_active=data.get('is_active', True),
            rate_limit=data.get('rate_limit', 1000),
            usage_count=data.get('usage_count', 0),
            last_used=data.get('last_used'),
            permissions=data.get('permissions', ['read', 'write'])
        )

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if not self.expires_at:
            return False
        try:
            expires_at = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expires_at
        except:
            return False

    def is_rate_limited(self) -> bool:
        """Rate limit 초과 여부 확인"""
        return self.usage_count >= self.rate_limit

    def increment_usage(self):
        """사용 횟수 증가"""
        self.usage_count += 1
        self.last_used = datetime.now().isoformat()

class APIKeyManager:
    """API 키 관리자"""

    def __init__(self, storage_path: str = 'api_keys.json'):
        self.storage_path = Path(storage_path)
        self.api_keys: Dict[str, APIKey] = {}
        self.lock = threading.Lock()
        self._load_keys()

    def _load_keys(self):
        """API 키 로드"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key_id, key_data in data.items():
                        self.api_keys[key_id] = APIKey.from_dict(key_data)
                logger.info(f"API 키 로드 완료: {len(self.api_keys)}개")
        except Exception as e:
            logger.error(f"API 키 로드 실패: {e}")
            self.api_keys = {}

    def _save_keys(self):
        """API 키 저장"""
        try:
            data = {key_id: key.to_dict() for key_id, key in self.api_keys.items()}
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("API 키 저장 완료")
        except Exception as e:
            logger.error(f"API 키 저장 실패: {e}")

    def generate_key_id(self) -> str:
        """고유 키 ID 생성"""
        return f"dk_{secrets.token_hex(16)}"

    def generate_key_secret(self) -> str:
        """키 시크릿 생성"""
        return f"sk_{secrets.token_urlsafe(32)}"

    def create_api_key(self, name: str, rate_limit: int = 1000,
                      expires_in_days: Optional[int] = None,
                      permissions: List[str] = None) -> APIKey:
        """API 키 생성"""
        with self.lock:
            key_id = self.generate_key_id()
            key_secret = self.generate_key_secret()
            created_at = datetime.now().isoformat()

            # 만료일 설정
            expires_at = None
            if expires_in_days:
                expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()

            api_key = APIKey(
                key_id=key_id,
                key_secret=key_secret,
                name=name,
                created_at=created_at,
                expires_at=expires_at,
                rate_limit=rate_limit,
                permissions=permissions or ['read', 'write']
            )

            self.api_keys[key_id] = api_key
            self._save_keys()

            logger.info(f"API 키 생성: {key_id} ({name})")
            return api_key

    def verify_api_key(self, key_id: str, key_secret: str) -> Optional[APIKey]:
        """API 키 검증"""
        with self.lock:
            api_key = self.api_keys.get(key_id)

            if not api_key:
                logger.warning(f"API 키를 찾을 수 없음: {key_id}")
                return None

            if not api_key.is_active:
                logger.warning(f"비활성화된 API 키: {key_id}")
                return None

            if api_key.key_secret != key_secret:
                logger.warning(f"잘못된 API 키 시크릿: {key_id}")
                return None

            if api_key.is_expired():
                logger.warning(f"만료된 API 키: {key_id}")
                return None

            # 사용 횟수 증가
            api_key.increment_usage()
            self._save_keys()

            logger.info(f"API 키 검증 성공: {key_id}")
            return api_key

    def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """API 키 조회"""
        return self.api_keys.get(key_id)

    def list_api_keys(self) -> List[Dict]:
        """모든 API 키 목록"""
        with self.lock:
            keys = []
            for api_key in self.api_keys.values():
                key_info = api_key.to_dict()
                # 시크릿 키는 노출하지 않음
                key_info['key_secret'] = '****' + key_info['key_secret'][-4:]
                keys.append(key_info)
            return keys

    def deactivate_api_key(self, key_id: str) -> bool:
        """API 키 비활성화"""
        with self.lock:
            api_key = self.api_keys.get(key_id)
            if api_key:
                api_key.is_active = False
                self._save_keys()
                logger.info(f"API 키 비활성화: {key_id}")
                return True
            return False

    def activate_api_key(self, key_id: str) -> bool:
        """API 키 활성화"""
        with self.lock:
            api_key = self.api_keys.get(key_id)
            if api_key:
                api_key.is_active = True
                self._save_keys()
                logger.info(f"API 키 활성화: {key_id}")
                return True
            return False

    def delete_api_key(self, key_id: str) -> bool:
        """API 키 삭제"""
        with self.lock:
            if key_id in self.api_keys:
                del self.api_keys[key_id]
                self._save_keys()
                logger.info(f"API 키 삭제: {key_id}")
                return True
            return False

    def update_rate_limit(self, key_id: str, rate_limit: int) -> bool:
        """Rate limit 업데이트"""
        with self.lock:
            api_key = self.api_keys.get(key_id)
            if api_key:
                api_key.rate_limit = rate_limit
                self._save_keys()
                logger.info(f"Rate limit 업데이트: {key_id} -> {rate_limit}")
                return True
            return False

    def reset_usage_count(self, key_id: str) -> bool:
        """사용 횟수 초기화"""
        with self.lock:
            api_key = self.api_keys.get(key_id)
            if api_key:
                api_key.usage_count = 0
                self._save_keys()
                logger.info(f"사용 횟수 초기화: {key_id}")
                return True
            return False

    def get_usage_stats(self, key_id: str) -> Optional[Dict]:
        """사용 통계 조회"""
        api_key = self.api_keys.get(key_id)
        if not api_key:
            return None

        return {
            'key_id': api_key.key_id,
            'name': api_key.name,
            'usage_count': api_key.usage_count,
            'rate_limit': api_key.rate_limit,
            'usage_percentage': (api_key.usage_count / api_key.rate_limit * 100) if api_key.rate_limit > 0 else 0,
            'last_used': api_key.last_used,
            'created_at': api_key.created_at,
            'expires_at': api_key.expires_at,
            'is_active': api_key.is_active
        }

class APIKeyAuthMiddleware:
    """API 키 인증 미들웨어"""

    def __init__(self, api_key_manager: APIKeyManager):
        self.api_key_manager = api_key_manager

    def authenticate(self, key_id: str, key_secret: str) -> Optional[APIKey]:
        """API 인증"""
        return self.api_key_manager.verify_api_key(key_id, key_secret)

    def check_permission(self, api_key: APIKey, required_permission: str) -> bool:
        """권한 확인"""
        return required_permission in api_key.permissions

# 전역 API 키 관리자 인스턴스
_api_key_manager_instance = None

def get_api_key_manager() -> APIKeyManager:
    """전역 API 키 관리자 인스턴스 반환"""
    global _api_key_manager_instance
    if _api_key_manager_instance is None:
        _api_key_manager_instance = APIKeyManager()
    return _api_key_manager_instance

def create_default_api_key() -> Optional[APIKey]:
    """기본 API 키 생성"""
    manager = get_api_key_manager()

    # 기본 키가 없으면 생성
    if not manager.list_api_keys():
        default_key = manager.create_api_key(
            name="Default Admin Key",
            rate_limit=10000,
            expires_in_days=365,
            permissions=['read', 'write', 'admin']
        )
        logger.info("기본 API 키 생성 완료")
        return default_key

    return None