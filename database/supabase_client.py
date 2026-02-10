import os
import logging
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv


# 환경 변수 로드
load_dotenv()


_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Supabase 클라이언트 싱글톤 반환

    Returns:
        Supabase Client 인스턴스

    Raises:
        ValueError: 환경 변수가 설정되지 않은 경우
    """
    global _supabase_client

    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Supabase 환경 변수가 설정되지 않았습니다. "
                ".env 파일에 SUPABASE_URL과 SUPABASE_KEY를 설정하세요."
            )

        _supabase_client = create_client(supabase_url, supabase_key)
        logging.info("Supabase 클라이언트 초기화 완료")

    return _supabase_client


def reset_supabase_client():
    """Supabase 클라이언트 재설정 (테스트용)"""
    global _supabase_client
    _supabase_client = None
