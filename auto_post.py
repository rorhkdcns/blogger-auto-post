import os
import sys
import subprocess
import time
import re
import random
import pickle
import base64
import datetime
import urllib.parse
import html

# [1단계] 라이브러리 자동 설치 및 검증
required_modules = [
    "google-auth-oauthlib", 
    "google-auth-httplib2", 
    "google-api-python-client", 
    "google-genai"  
]

print("🔄 깃허브 액션 서버 환경 내 라이브러리 자동 설치 시작...")
for module in required_modules:
    try:
        if module == "google-genai":
            import google.genai
        else:
            __import__(module.replace('-', '_'))
    except ImportError:
        print(f"📦 {module} 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", module])
        time.sleep(1)

print("✅ 모든 라이브러리 설치 및 인식 완료! 본 코드를 시작합니다.")
print("-" * 60)

from googleapiclient.discovery import build
from google import genai 
from google.genai import types  

# =====================================================================
# ⚙️ 고유 설정 정보
# =====================================================================
BLOG_ID = "347204372769511011"  
GOOGLE_ADSENSE_CLIENT = "ca-pub-4292478378917157"
GOOGLE_ADSENSE_SLOT = "5317754949"

STOCK_INFO_KEYWORDS = [
    "주식초보", "주린이 첫걸음", "주식투자 시작하기", "주식 계좌 개설 방법", "증권사 추천", 
    "주식 거래 시간", "시간외 단일가 매매", "주식 용어 정리", "예수금 뜻", "미수금 위험성", 
    "증거금 100%", "신용융자", "D+2 예수금", "주식 매수 매도", "호가창 보는 법", 
    "지정가 주문", "시장가 주문", "조건부 지정가", "최유리 지정가", "LOC 주문", 
    "VWAP 매매", "주식 수수료 비교", "유관기관 제비용", "세금 거래세", "양도소득세 기준", 
    "배당소득세율", "종합소득세 주식", "금융투자소득세 금투세", "ISA 계좌 장점", "비과세 만능통장", 
    "연금저축펀드 주식", "주식 차트 보는 법", "봉차트 양봉 음봉", "이동평균선 정배열", "이평선 역배열", 
    "골든크로스 매수", "데드크로스 매도", "거래량의 비밀", "지지선과 저항선", "추세선 그리기", 
    "MACD 보조지표", "RSI 과매수 과매도", "스토캐스틱 활용", "볼린저밴드 매매법", "일목균형표 기초", 
    "재무제표 보는 법", "시가총액 순위", "매출액 영업이익", "당기순이익 뜻", "EPS 주당순이익", 
    "PER 주가수익비율", "PBR 주가순자산비율", "ROE 자기자본이익률", "EV/EBITDA", "부채비율 적정선", 
    "유동비율이란", "배당 성향", "배당수익률 높은 주식", "고배당주 추천", "배당금 지급일 확인", 
    "배당락일 매수", "분기배당 주식", "월배당 ETF", "미국주식 시작하기", "소수점 투자", 
    "환전 수수료 우대", "환율 주가 관계", "미국 증시 개장시간", "서학개미 인기주식", "양도세 절세 팁", 
    "W-8BEN 작성", "애프터마켓 거래", "프리마켓 시간", "S&P500 지수", "나스닥 100", 
    "다우존스 지수", "러셀2000", "ETF 투자 방법", "레버리지 ETF 위험성", "인버스 ETF 곱버스", 
    "ETN 차이점", "자산배분 전략", "올웨더 포트폴리오", "바벨 전략", "분할매수 분할매도", 
    "적립식 투자 장점", "물타기 불타기", "손절매 기준", "익절 타이밍", "가치투자 대가", 
    "워런 버핏 명언", "피터 린치 성장주", "모멘텀 투자", "퀀트 투자 기초", "주식 리포트 읽는 법", 
    "공시 확인 방법", "DART 전자공시", "유상증자 주가 호재 악재", "무상증자 권리락", "전환사채 CB", 
    "신주인수권부사채 BW", "주식분할 액면분할", "액면병합 효과", "자사주 매입 소각", "내부자 거래 지분", 
    "대주주 매도", "공매도 숏커버링", "숏스퀴즈 뜻", "신규상장 IPO", "따따블 기준", 
    "공모주 청약 방법", "균등배정 비례배정", "의무보유확약 기관", "주총 참석 방법", "전자투표 권리 행사", 
    "테마주 매매 리스크", "정치테마주 현실", "세력주 작전주 구별", "뇌동매매 고치기", "포모(FOMO) 증후군", 
    "주식 일지 작성", "투자 원칙 세우기", "거시경제 지표", "금리와 주가 관계", "인플레이션 수혜주", 
    "스태그플레이션 자산", "Fed 연준 금리인하", "FOMC 일정", "CPI 소비자물가지수", "고용지표 발표", 
    "환율 상승 수혜주", "유가 상승 관련주", "경기방어주 종류", "경기민감주 사이클", "주도주 찾는 법", 
    "대형주 중소형주 차이", "우선주 보통주 차이", "괴리율이란", "주식 리스크 관리", "복리 효과 계산", 
    "주식 책 추천", "주식 유튜브 채널 추천", "가상계좌 모의투자"
]

GITHUB_USER_ID = "rorhkdcns"  
GITHUB_REPO_NAME = "blogger-auto-post"  
GITHUB_IMAGE_BASE_URL = "https://raw.githubusercontent.com/rorhkdcns/blogger-auto-post/main/blog_images/stock/"

github_images_pool = [
    "1.jpg", "2.png", "3.jpg", "4.jpg", "5.jpg", "6.jpg", "7.jpg", "8.jpg", "9.jpg", "10.jpg",
    "11.jpg", "12.jpg", "13.jpg", "14.png", "15.jpg", "16.jpg", "17.jpg", "18.jpg", "19.jpg", "20.jpg",
    "21.jpg", "22.jpg", "23.jpg", "24.jpg", "25.jpg", "26.png", "27.jpg", "28.jpg", "29.jpg", "30.jpg",
    "31.jpg", "32.jpg", "33.jpg", "34.jpg", "35.jpg", "36.jpg", "37.jpg", "38.png", "39.jpg", "40.jpg",
    "41.jpg", "42.jpg", "43.jpg", "44.jpg", "45.jpg", "46.jpg", "47.jpg", "48.jpg", "49.jpg", "50.png",
    "51.jpg", "52.jpg", "53.jpg", "54.jpg", "55.jpg", "56.jpg", "57.jpg", "58.jpg", "59.jpg", "60.jpg",
    "61.jpg", "62.png", "63.jpg", "64.jpg", "65.jpg", "66.jpg", "67.jpg", "68.png", "69.jpg", "70.png",
    "71.jpg", "72.png"
]

URL_물타기 = "https://invest.gwangchoon.com/2026/05/1_0144690541.html"
URL_손절익절 = "https://invest.gwangchoon.com/2026/05/blog-post_281.html"
URL_복리 = "https://invest.gwangchoon.com/2026/05/10-1.html"
URL_환율 = "https://invest.gwangchoon.com/2026/05/blog-post_989.html"

# 보조 함수: 상단으로 이동
def re_extract_line(tag, text, default=""):
    pattern = r'\[?' + re.escape(tag) + r'\]?\s*:\s*(.*)'
    for line in text.split('\n'):
        if tag in line:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return default

def get_unique_target_keyword(blogger, blog_id):
    recent_titles = []
    try:
        posts = blogger.posts().list(blogId=blog_id, maxResults=30).execute()
        for item in posts.get('items', []):
            clean_title = re.sub(r'\s+', '', item.get('title', ''))
            recent_titles.append(clean_title)
    except:
        pass
    shuffled_keywords = STOCK_INFO_KEYWORDS.copy()
    random.shuffle(shuffled_keywords)
    for keyword in shuffled_keywords:
        short_keyword = keyword.split(" ")[0]
        if not any(re.sub(r'\s+', '', short_keyword) in r_title for r_title in recent_titles):
            return keyword
    return random.choice(STOCK_INFO_KEYWORDS)

def calculate_scheduled_time():
    kst = datetime.timezone(datetime.timedelta(hours=9))
    # 현재 시간보다 5분 미래로 강제 설정하여 API가 '과거'라고 판단하지 않게 함
    now = datetime.datetime.now(kst) + datetime.timedelta(minutes=5) 
    today = now.date()
    
    # 9시, 11시, 13시, 15시, 17시, 19시, 21시 중 가장 가까운 미래 찾기
    candidates = [datetime.datetime.combine(today, datetime.time(h, random.randint(1, 15)), tzinfo=kst) for h in [9, 11, 13, 15, 17, 19, 21]]
    
    # 지금보다 최소 5분 뒤의 시간 중 가장 빠른 시간 선택
    scheduled_time = next((c for c in candidates if c > now), None)
    
    if not scheduled_time:
        # 오늘 다 지났으면 내일 9시로 예약
        scheduled_time = datetime.datetime.combine(today + datetime.timedelta(days=1), datetime.time(9, random.randint(1, 15)), tzinfo=kst)
        
    return scheduled_time.strftime('%Y-%m-%dT%H:%M:%S+09:00')

ADSENSE_CODE = """
<div class="adsense-container" style="text-align:center; margin: 30px 0;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={CLIENT}" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="{CLIENT}" data-ad-slot="{SLOT}" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
""".replace("{CLIENT}", GOOGLE_ADSENSE_CLIENT).replace("{SLOT}", GOOGLE_ADSENSE_SLOT)

CTA_CODE = """
<div class="cta-box" style="border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; background-color: #f8fafc; margin-top: 40px; text-align: center;">
    <p style="font-size: 15px; color: #334155; font-weight: 700; margin-bottom: 8px; display: inline-block; background: #e2e8f0; padding: 4px 12px; border-radius: 6px;">💡 투자자 가이드 안내</p>
    <p style="font-size: 14px; color: #475569; line-height: 1.7; margin: 0 0 15px 0; font-weight: 500;">
        시장 변동성이 커질수록 감정에 치우친 매매보다 객관적인 수치 확인이 중요합니다.<br>
        본문에 배치된 <b>[실시간 주식 계산기 모음판]</b>으로 이동하셔서 본인의 포트폴리오 평단가와 리스크 가이드라인을 간편하게 점검해 보시기 바랍니다.
    </p>
    <a href="#calc-board-top" style="display: inline-block; background: #334155; color: white; font-weight: bold; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; transition: background 0.2s;">⚡ 실시간 계산기로 이동하기</a>
</div>
"""

CALCULATOR_BOARD_CODE = f"""
<div id="calc-board-top" class="calc-board-container" style="margin: 35px 0; padding: 20px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
    <p style="margin: 0 0 15px 0; font-size: 16px; font-weight: 700; color: #1e293b; text-align: left; border-left: 4px solid #475569; padding-left: 8px;">📊 실시간 투자 리스크 관리 툴 바로가기</p>
    <div class="calc-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
        <a href="{URL_물타기}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 14px; font-weight: 700; color: #1e40af;">📉 주식 물타기 계산기</span>
        </a>
        <a href="{URL_손절익절}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 14px; font-weight: 700; color: #0f766e;">💰 익절/손절 기준 계산기</span>
        </a>
        <a href="{URL_복리}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 14px; font-weight: 700; color: #4338ca;">📈 연복리 자산 시뮬레이터</span>
        </a>
        <a href="{URL_환율}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 14px; font-weight: 700; color: #334155;">🎯 미국주식 실시간 환율 계산</span>
        </a>
    </div>
</div>
"""

def generate_blog_content(target_keyword):
    api_key_direct = os.environ.get("API_KEY")
    client = genai.Client(api_key=api_key_direct, http_options=types.HttpOptions(api_version="v1"))
    prompt = (
        "너는 10년 차 전업 투자자이자 전문 금융 칼럼니스트야. "
        f"[{target_keyword}]를 검색한 사용자의 의도를 완벽히 해결하는 '실전 가이드'를 작성해줘.\n\n"
        
        "[필수 작성 지침]\n"
        "1. [제목 법칙]: 핵심 키워드와 함께 유저가 '내 궁금증이 바로 해결되겠구나'라고 느낄 수 있는 구체적인 가치를 담아라.\n\n"
        
        "2. [이미지 배치 법칙 - 매우 중요]:\n"
        "   - [SUB_TITLE_1], [SUB_TITLE_2], [SUB_TITLE_3] 바로 위에는 반드시 '[IMAGE]'라는 문구를 넣어라.\n"
        "   - 글 중간에 시각적 환기점이 있어야 이탈률이 낮아지므로, 소제목 직전마다 반드시 이미지 공간을 확보할 것.\n\n"
        
        "3. [극강의 모바일 가독성 - 절대 준수]:\n"
        "   - 문장 길이를 극도로 짧게 유지하라. 1문장은 20자 내외로 끊어라.\n"
        "   - 문단은 절대 2문장을 넘기지 마라. (엔터키를 과감하게 활용할 것)\n"
        "   - '또한', '반면에', '결론적으로' 등 불필요한 접속사를 80% 이상 삭제하라.\n"
        "   - 정보 나열은 반드시 리스트(-, 1. 2.)를 사용하고, 비교 분석은 표(Table)로 반드시 구현하라.\n\n"
        
        "4. [스크롤 방지 장치]:\n"
        "   - [BODY_1] 첫 문장에 사용자의 고민에 대한 즉각적인 공감과 해답을 제시하라.\n"
        "   - 핵심 문장과 중요 수치는 반드시 **볼드체**와 <b><font color=\"#e11d48\">중요데이터</font></b> 양식을 적용해 시선을 뺏어라.\n\n"
        
        "5. [금지어]: '파소나', 'PASONA', '카피라이팅', 'AI', '인공지능', '자동화', '프로그램', '단계별 전략' 절대 금지.\n\n"
        
        "6. [구조 설계]:\n"
        "   - [BODY_1]: 독자의 고민 공감 + 바로 확인 가능한 핵심 결론 (두괄식).\n"
        "   - [BODY_2]: [초보자의 실수] vs [현명한 대응]을 2열 표로 대조하여 가독성 극대화.\n"
        "   - [BODY_3]: 지금 당장 실천할 수 있는 객관적인 3가지 액션 가이드.\n\n"
        
        "7. [시각화 및 태그]: IMAGE_PROMPT는 직관적인 명사 2-3개. 태그는 실제 검색량이 많은 구체적 키워드 3개.\n\n"
        
        "8. [초보자 눈높이]: 전문 용어 사용 시 반드시 괄호를 열고 5자 이내의 쉬운 비유를 덧붙일 것.\n\n"
        
        "9. [글로벌 독자 대응]: 블로그 최상단에 'Global Summary'를 영어로 3문장 작성하고, 소제목 'Global Market Impact' 추가.\n\n"
        
        "[출력 포맷 고정]\n"
        "[TITLE]: (제목)\n"
        "[GLOBAL_SUMMARY]: (영문 요약)\n"
        "[TAGS]: (키워드 3개)\n"
        "[IMAGE_PROMPT]: (이미지 키워드)\n"
        "[IMAGE]\n[SUB_TITLE_1]: (핵심 답변형 소제목)\n"
        "[BODY_1]: (핵심 결론 우선 배치)\n"
        "[IMAGE]\n[SUB_TITLE_2]: (비교 분석형 소제목)\n"
        "[BODY_2]: (표 삽입 필수)\n"
        "[IMAGE]\n[SUB_TITLE_3]: (액션 플랜형 소제목)\n"
        "[BODY_3]: (실천 가이드)\n\n"
        
        "[자기 검증 루프]:\n"
        "1. 위 지침을 100% 준수했는지 스스로 체크하라.\n"
        "2. 소제목 바로 위에 [IMAGE] 태그가 모두 포함되었는지 확인하라.\n"
        "3. 모든 수정이 완료되면 [최종 결과물] 태그와 함께 출력하라."
    )
    # 이하 동일
    
    for model in ['gemini-2.5-flash', 'gemini-2.5-pro']:
        for attempt in range(3):
            try:
                print(f"🤖 Gemini API 호출 중... (모델: {model}, 시도: {attempt+1}/3)")
                response = client.models.generate_content(model=model, contents=prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"⚠️ 지연 발생: {e}")
                if attempt < 2: time.sleep(10)
    raise RuntimeError("🚨 데이터 생성 실패")

def check_already_posted(blogger, blog_id):
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst)
    try:
        posts = blogger.posts().list(blogId=blog_id, maxResults=10).execute()
        count = sum(1 for item in posts.get('items', []) if item.get('published', '').startswith(now.strftime('%Y-%m-%d')))
        if count >= 4: return True
    except: pass
    return False




def main():
    kst = datetime.timezone(datetime.timedelta(hours=9))
    b64_token = os.environ.get("TOKEN_PICKLE_BASE64")
    if not b64_token: return
    blogger = build('blogger', 'v3', credentials=pickle.loads(base64.b64decode(b64_token)))
    
    if check_already_posted(blogger, BLOG_ID): return
    
    try:
        posts = blogger.posts().list(blogId=BLOG_ID, maxResults=1).execute()
        if posts.get('items'):
            last_pub_time = datetime.datetime.fromisoformat(posts['items'][0].get('published', '').replace('Z', '+00:00')).astimezone(kst)
            if (datetime.datetime.now(kst) - last_pub_time).total_seconds() < 3600: return 
    except: pass
    
    target_keyword = get_unique_target_keyword(blogger, BLOG_ID)
    ai_raw = generate_blog_content(target_keyword)
    
    # [핵심 수정] 태그 이름과 상관없이 내용을 안전하게 뽑아내는 함수
    def extract_flexible(text, start_tag):
        # 태그를 대괄호 포함해서 찾고, 다음 태그가 나오기 전까지의 내용을 전부 가져옵니다.
        pattern = rf"{re.escape(start_tag)}[:\s]*(.*?)(?=\[SUB_TITLE|\[BODY_1|\[BODY_2|\[BODY_3|\[GLOBAL_SUMMARY|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    # [데이터 추출]
    title = re.sub(r'<[^>]*>', '', re_extract_line('TITLE', ai_raw, "투자 정보")).strip()
    tags = list(set([t.strip() for t in re_extract_line('TAGS', ai_raw, "주식투자").split(',')]))
    
    sub1, sub2, sub3 = re_extract_line('SUB_TITLE_1', ai_raw), re_extract_line('SUB_TITLE_2', ai_raw), re_extract_line('SUB_TITLE_3', ai_raw)
    body1 = extract_flexible(ai_raw, '[BODY_1]')
    body2 = extract_flexible(ai_raw, '[BODY_2]')
    body3 = extract_flexible(ai_raw, '[BODY_3]')
    
    # [이미지 및 HTML 처리]
    def get_image_tag():
        return f'<div style="text-align:center; margin:20px 0;"><img src="{GITHUB_IMAGE_BASE_URL}{random.choice(github_images_pool)}" style="max-width:100%; border-radius:8px;"/></div>'

    def replace_image_tags(text):
        return text.replace('[IMAGE]', get_image_tag())
    
    global_summary = re_extract_line('GLOBAL_SUMMARY', ai_raw, "")
    gs_html = format_paragraphs(global_summary) if global_summary else ""
    summary_box = f'<div style="background:#f8fafc; border:1px solid #e2e8f0; padding:15px; margin-bottom:20px;">{gs_html}</div>' if gs_html else ""
    
    final_html = get_image_tag() + summary_box + ADSENSE_CODE + \
                 f'<h3 style="border-left:5px solid #3b82f6; padding-left:10px;">{sub1}</h3>{format_paragraphs(replace_image_tags(body1))}' + \
                 CALCULATOR_BOARD_CODE + \
                 f'<h3 style="border-left:5px solid #3b82f6; padding-left:10px;">{sub2}</h3>{format_paragraphs(replace_image_tags(body2))}' + \
                 f'<h3 style="border-left:5px solid #3b82f6; padding-left:10px;">{sub3}</h3>{format_paragraphs(replace_image_tags(body3))}' + ADSENSE_CODE + CTA_CODE

    # [마지막으로 본문에 남아있을지 모르는 태그 찌꺼기 제거]
    final_html = re.sub(r'\[SUB_TITLE_\d+\]:.*', '', final_html)
    final_html = re.sub(r'\[BODY_\d+\]:', '', final_html)

    try:
        blogger.posts().insert(blogId=BLOG_ID, body={'title': title, 'content': final_html, 'labels': tags, 'published': calculate_scheduled_time()}, isDraft=False).execute()
        print("✅ 발행 완료")
    except Exception as e:
        print(f"❌ 에러: {e}")

        
if __name__ == "__main__":
    main()
