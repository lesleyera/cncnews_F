# auth.py
import json
import os
from google.oauth2 import service_account 
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from functools import lru_cache

@lru_cache(maxsize=1)
def get_ga4_client():
    """GA4 클라이언트 생성 (캐싱 적용)"""
    try:
        # 로컬 환경: JSON 파일에서 읽기
        json_path = "ga-key.json"
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                key_dict = json.load(f)
            creds = service_account.Credentials.from_service_account_info(key_dict)
            return BetaAnalyticsDataClient(credentials=creds)
        
        # 환경 변수에서 읽기 (선택사항)
        ga4_creds_env = os.getenv("GA4_CREDENTIALS_JSON")
        if ga4_creds_env:
            key_dict = json.loads(ga4_creds_env)
            creds = service_account.Credentials.from_service_account_info(key_dict)
            return BetaAnalyticsDataClient(credentials=creds)
        
        # Streamlit 의존을 제거했기 때문에 여기서는 예외만 던지지 않고 None 반환
        return None
    except Exception as e:
        return None