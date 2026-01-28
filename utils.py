# utils.py
import re
from datetime import datetime, timedelta

def clean_author_name(name):
    """기자 이름에서 불필요한 직함 등을 제거 - 1어절만 남김"""
    if not name: return "미상"
    
    # 기본 정리
    name = str(name).replace('#', '').replace('전문기자', '').replace('기자', '').strip()
    
    # 직함 목록
    titles = ['편집인', '전문', '편집', '기자']
    
    # 1단계: 공백으로 분리하여 단어별로 처리
    words = name.split()
    
    # 2어절 이상이면 첫 번째 단어만 남김 (1어절만 유지)
    if len(words) > 1:
        # 첫 번째 단어가 직함이면 두 번째 단어 사용, 아니면 첫 번째 단어 사용
        if words[0] in titles and len(words) > 1:
            name = words[1]
        else:
            name = words[0]
    elif len(words) == 1:
        name = words[0]
    else:
        name = name
    
    # 2단계: 공백 없이 붙어있는 직함 제거 (정규표현식 사용)
    for title in titles:
        # "이름직함" 패턴 제거
        name = re.sub(rf'{re.escape(title)}', '', name)
        # "이름 직함" 패턴 제거 (공백 포함)
        name = re.sub(rf'\s*{re.escape(title)}\s*', '', name)
    
    # 3단계: 정리 (여러 공백을 하나로, 앞뒤 공백 제거)
    name = ' '.join(name.split()).strip()
    
    return name if name else "미상"

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