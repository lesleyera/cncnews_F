# utils.py
import re
from datetime import datetime, timedelta

def clean_author_name(name):
    """기자 이름에서 불필요한 직함 등을 제거"""
    if not name: return "미상"
    # 직함 제거: 전문기자, 기자 등
    name = name.replace('#', '').replace('전문기자', '').replace('기자', '').strip()
    
    # 공백 없이 붙어있는 직함 제거 (예: "김성민편집인" -> "김성민")
    name = name.replace('편집인', '').replace('전문', '').replace('편집', '').strip()
    
    # 2어절 직함 제거: 편집인, 전문 등
    words = name.split()
    if len(words) >= 2:
        # 첫 번째 단어가 직함인 경우 제거 (편집인, 전문 등)
        if words[0] in ['편집인', '전문', '기자', '편집']:
            name = ' '.join(words[1:])
        # 마지막 단어가 직함인 경우 제거
        elif words[-1] in ['편집인', '전문', '기자', '편집']:
            name = ' '.join(words[:-1])
    
    return ' '.join(name.split())

def get_sunday_to_saturday_ranges(count=12):
    """최근 주차(일~토) 계산"""
    ranges = {}
    today = datetime.now()
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    for i in range(count):
        start_date = last_sunday - timedelta(weeks=i)
        end_date = start_date + timedelta(days=6)
        label = f"{start_date.isocalendar()[1]}주차"
        ranges[label] = f"{start_date.strftime('%Y.%m.%d')} ~ {end_date.strftime('%Y.%m.%d')}"
    return ranges

# 전역에서 사용할 주차 정보
WEEK_MAP = get_sunday_to_saturday_ranges()