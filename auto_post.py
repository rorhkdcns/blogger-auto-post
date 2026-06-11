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

# 📚 [핵심 변경 1] 뉴스 RSS 대신 장기적으로 트래픽이 쌓이는 정보성/에버그린 키워드 풀
# 📚 [확장된 정보성/에버그린 키워드 풀] - 총 140개 이상 완벽 세팅
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

# 🔄 [핵심 변경 2] 블로그에 최근 발행된 글 제목을 확인하여 중복되지 않는 키워드 추출
def get_unique_target_keyword(blogger, blog_id):
    print("📡 정보성 키워드 풀에서 중복 없는 오늘의 포스팅 주제 선정 시작...")
    
    recent_titles = []
    try:
        posts = blogger.posts().list(blogId=blog_id, maxResults=30).execute()
        for item in posts.get('items', []):
            clean_title = re.sub(r'\s+', '', item.get('title', ''))
            recent_titles.append(clean_title)
    except Exception as e:
        print(f"⚠️ 최근 글 제목 수집 실패 (중복 체크 건너뜀): {e}")

    shuffled_keywords = STOCK_INFO_KEYWORDS.copy()
    random.shuffle(shuffled_keywords)
    
    for keyword in shuffled_keywords:
        short_keyword = keyword.split(" ")[0] # 예: "주식" 등 첫 단어
        is_duplicated = False
        
        for r_title in recent_titles:
            if re.sub(r'\s+', '', short_keyword) in r_title:
                is_duplicated = True
                break
                
        if not is_duplicated:
            print(f"🎯 중복 검증 완료! 오늘의 타겟 키워드: {keyword}")
            return keyword
            
    chosen_keyword = random.choice(STOCK_INFO_KEYWORDS)
    print(f"⚠️ 모든 키워드가 최근 발행과 겹칩니다. 무작위 강제 선택: {chosen_keyword}")
    return chosen_keyword


def calculate_scheduled_time():
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst) 
    today = now.date()
    candidates = [
        datetime.datetime.combine(today, datetime.time(9, 0), tzinfo=kst),
        datetime.datetime.combine(today, datetime.time(13, 0), tzinfo=kst),
        datetime.datetime.combine(today, datetime.time(16, 0), tzinfo=kst),
        datetime.datetime.combine(today, datetime.time(20, 0), tzinfo=kst)
    ]
    scheduled_time = None
    for c in candidates:
        if c > now: 
            scheduled_time = c
            break
    if not scheduled_time:
        tomorrow = today + datetime.timedelta(days=1)
        scheduled_time = datetime.datetime.combine(tomorrow, datetime.time(9, 0), tzinfo=kst)
        
    iso_str = scheduled_time.strftime('%Y-%m-%dT%H:%M:%S+09:00')
    return iso_str

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
            <span style="display: block; font-size: 11px; color: #64748b; margin-top: 4px;">보유 종목 평단가 및 추매 시뮬레이션</span>
        </a>
        <a href="{URL_손절익절}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 14px; font-weight: 700; color: #0f766e;">💰 익절/손절 기준 계산기</span>
            <span style="display: block; font-size: 11px; color: #64748b; margin-top: 4px;">단타 실전 매매 맞춤형 목표가 설정</span>
        </a>
        <a href="{URL_복리}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 14px; font-weight: 700; color: #4338ca;">📈 연복리 자산 시뮬레이터</span>
            <span style="display: block; font-size: 11px; color: #64748b; margin-top: 4px;">장기 투자 및 복리 마법 데이터 예측</span>
        </a>
        <a href="{URL_환율}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 14px; font-weight: 700; color: #334155;">🎯 미국주식 실시간 환율 계산</span>
            <span style="display: block; font-size: 11px; color: #64748b; margin-top: 4px;">해외주식 양도세 및 환율 변동성 체크</span>
        </a>
    </div>
</div>
"""

# 🧠 [핵심 변경 3] 뉴스가 아닌 '정보성 가이드 지식'을 생산하도록 프롬프트 전면 수정
def generate_blog_content(target_keyword):
    api_key_direct = os.environ.get("API_KEY")
    client = genai.Client(
        api_key=api_key_direct,
        http_options=types.HttpOptions(api_version="v1")
    )
    
prompt = (
        "네가 10년 차 전업 투자자이자 전문 금융 칼럼니스트라고 가정하고, "
        f"제시된 핵심 키워드인 [{target_keyword}]에 대해 독자에게 깊이 있는 지식과 통찰을 제공하는 '정보성 가이드 글'을 작성해줘.\n\n"
        "[필수 작성 지침]\n"
        "1. [제목 법칙]: 검색 엔진(SEO)에 최적화된 신뢰성 높은 정보성 제목을 구성하라. "
        "자극적인 낚시성 문구 대신, 유저들이 실제로 검색할 법한 핵심 키워드와 구체적인 해결책을 조합하라.\n\n"
        "2. [극강의 모바일 가독성 법칙 - 매우 중요]:\n"
        "   - AI 특유의 만연체(길게 늘어쓰는 텍스트 벽)를 절대 금지한다. 모든 문장은 핵심만 짧고 간결하게 끊어 써라.\n"
        "   - 스마트폰 화면에서 답답해 보이지 않도록, 하나의 문단은 절대 2~3문장을 넘기지 말고 과감하게 줄바꿈하라.\n"
        "   - 정보나 특징, 장단점을 나열할 때는 줄글로 풀지 말고, 반드시 글머리기호(-, 1. 2. 3. 등)를 사용하여 직관적으로 요약하라.\n"
        "   - 핵심 개념을 비교하거나 정리할 때는 표(Table)를 쓰지 말고, [개념 이름], [핵심 특징], [주의점] 등을 **볼드체 블록** 형태로 줄바꿈하여 한눈에 들어오게 정리하라.\n\n"
        "3. [강조 및 시선 유도 법칙]:\n"
        "   - 독자가 스크롤만 빠르게 훑어봐도 내용을 파악할 수 있도록, 문단 내 가장 중요한 핵심 문장에는 마크다운 **볼드체**를 적용하라.\n"
        "   - 전체 글을 통틀어 가장 핵심적인 수치나 데이터 딱 2~3개에만 구글 표준 <b><font color=\"#e11d48\">중요데이터</font></b> 양식을 적용하라.\n\n"
        "4. [에버그린 스토리텔링 흐름]:\n"
        "   - 실시간 뉴스 요약이나 일시적 시황은 배제하고, 수년 뒤에 읽어도 가치 있는 투자 철학과 원리를 설명하라.\n"
        "   - 유저가 불안감을 느끼는 지점에 공감하고 객관적인 가이드라인을 제시하되, 노골적인 계산기 사용 광고 문구는 피하라.\n"
        "   - 절대 금지어: 본문 어디에도 '파소나', 'PASONA', '카피라이팅', 'AI', '인공지능', '자동화', '프로그램', '단계별 전략'은 쓰지 마라.\n\n"
        "5. [파트 구성]: 본문은 구조적 완성도를 위해 3개의 파트로 명확히 나누고, 직관적인 소제목을 부여하라.\n"
        "   - 1단계 (개념과 원인): 이 주제가 왜 중요하며 흔히 저지르는 실수는 무엇인지 짧게 분석.\n"
        "   - 2단계 (실전 위협과 분석): 리스크가 평단가에 미치는 위협. (이 부분에 글머리기호나 볼드체 블록을 적극 활용하여 가독성을 높일 것)\n"
        "   - 3단계 (대응 가이드): 투자자가 취해야 할 객관적인 실천 방향 제안.\n\n"
        "6. [시각화]: 영문 이미지 검색 키워드를 IMAGE_PROMPT에 직관적인 2-3단어 명사로 추천하라.\n\n"
        "7. [태그 추출]: 본문 내용과 밀접하며 실제 검색 유입 의도가 반영된 구체적인 주식 키워드를 3개만 추출해라. (쉼표 구분)\n\n"
        "8. [초보자 맞춤 눈높이 법칙]: 독자는 주식에 대해 잘 모르는 왕초보라고 가정하라. "
        "전문 용어(예: 펀더멘털, 뇌동매매, 지지선 등)를 사용할 때는 반드시 일상생활의 친숙한 비유(예: 건물의 뼈대, 바닥 확인 등)를 활용하거나, "
        "문맥 속에 중학생도 이해할 수 있는 아주 쉬운 뜻풀이를 자연스럽게 녹여내라.\n\n"
        "[출력 포맷 고정]\n"
        "[TITLE]: 신뢰감 있는 정보성 제목\n"
        "[TAGS]: 주식투자, 재테크, 국내증시\n"
        "[IMAGE_PROMPT]: finance growth chart\n"
        "[SUB_TITLE_1]: 소제목1\n"
        "[BODY_1]: 내용1 (짧은 문장, 볼드체, 초보자 눈높이 쉬운 설명 활용)\n"
        "[SUB_TITLE_2]: 소제목2\n"
        "[BODY_2]: 내용2 (표 대신 볼드체 블록과 리스트 활용, 가독성 극대화)\n"
        "[SUB_TITLE_3]: 소제목3\n"
        "[BODY_3]: 내용3 (객관적 실천 방향)"
    )
    
    target_models = ['gemini-2.5-flash', 'gemini-2.5-pro']
    for target_model in target_models:
        for attempt in range(3):
            try:
                print(f"🤖 Gemini API 호출 중... (모델: {target_model}, 시도: {attempt+1}/3)")
                response = client.models.generate_content(model=target_model, contents=prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"⚠️ 지연 발생: {e}")
                if attempt < 2: time.sleep(10)
                    
    raise RuntimeError("🚨 데이터 생성 실패")

def check_already_posted(blogger, blog_id):
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst)
    today_str = now.strftime('%Y-%m-%d')
    
    try:
        posts = blogger.posts().list(blogId=blog_id, maxResults=10).execute()
        today_post_count = 0
        
        for item in posts.get('items', []):
            pub_str = item.get('published', '')
            
            # 1. 오늘 날짜에 쓰여진 글 개수 카운트
            if pub_str.startswith(today_str):
                today_post_count += 1
                
                # 2. 가장 최근 글이 '2시간 이내'에 올라왔는지 확인 (동시간대 중복 차단)
                try:
                    pub_time = datetime.datetime.fromisoformat(pub_str).astimezone(kst)
                    time_diff_hours = (now - pub_time).total_seconds() / 3600
                    
                    if time_diff_hours < 2.0:
                        print(f"⏳ 최근 2시간 이내에 이미 글이 발행되었습니다. 중복 실행을 차단합니다.")
                        return True # 발행 중단
                except ValueError:
                    pass
        
        # 3. 오늘 하루 목표치인 4개를 다 채웠는지 확인
        if today_post_count >= 4:
            print("🛑 오늘 하루 4개 포스팅을 모두 완료했습니다.")
            return True # 발행 중단
            
    except Exception as e:
        print(f"⚠️ 중복 체크 오류: {e}")
        
    return False # 문제 없으므로 발행 진행!

def main():
    b64_token = os.environ.get("TOKEN_PICKLE_BASE64")
    if not b64_token:
        print("❌ 에러: TOKEN_PICKLE_BASE64가 없습니다.")
        return
        
    creds = pickle.loads(base64.b64decode(b64_token))
    blogger = build('blogger', 'v3', credentials=creds)
    
    if check_already_posted(blogger, BLOG_ID):
        print(f"⏩ 오늘({datetime.datetime.now().date()}) 이미 포스팅이 확인되었습니다. 중복 방지를 위해 작업을 종료합니다.")
        return
    
    # [핵심 변경 4] 뉴스 RSS 수집 함수 대신, 키워드 추출 함수 실행 (blogger 권한 전달)
    target_keyword = get_unique_target_keyword(blogger, BLOG_ID)
    ai_raw = generate_blog_content(target_keyword)
    
    def re_extract_line(tag, text, default=""):
        pattern = r'\[?' + re.escape(tag) + r'\]?\s*:\s*(.*)'
        for line in text.split('\n'):
            if tag in line:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        return default

    title = re_extract_line('TITLE', ai_raw, "오늘의 주식 투자 지식 요약")
    title = re.sub(r'<[^>]*>', '', title).replace('`', '').replace('**', '').replace('__', '').strip()
    
    tags_raw = re_extract_line('TAGS', ai_raw, "주식투자, 재테크, 국내증시")
    sub1 = re_extract_line('SUB_TITLE_1', ai_raw, "📈 핵심 개념 이해")
    sub2 = re_extract_line('SUB_TITLE_2', ai_raw, "📊 주요 분석 및 실전 위협 체크")
    sub3 = re_extract_line('SUB_TITLE_3', ai_raw, "💡 향후 대응 및 실천 가이드")
    
    def extract_block(text, start_tag, end_tag=None):
        try:
            start_idx = text.find(start_tag)
            if start_idx == -1: return ""
            start_idx += len(start_tag)
            if end_tag:
                end_idx = text.find(end_tag)
                return text[start_idx:end_idx].strip() if end_idx != -1 else text[start_idx:].strip()
            return text[start_idx:].strip()
        except:
            return ""

    def clean_html_garbage(text):
        text = text.replace('`', '').replace('**', '').replace('__', '')
        text = text.replace('<span>', '').replace('</span>', '')
        text = re.sub(r'<\s*span[^>]*>', '', text) 
        text = re.sub(r'\[.*?\]\s*:\s*', '', text)
        return text.strip()

    body1 = extract_block(ai_raw, '[BODY_1]:', '[SUB_TITLE_2]')
    body2 = extract_block(ai_raw, '[BODY_2]:', '[SUB_TITLE_3]')
    body3 = extract_block(ai_raw, '[BODY_3]:')

    body1 = clean_html_garbage(body1)
    body2 = clean_html_garbage(body2)
    body3 = clean_html_garbage(body3)
    sub1 = clean_html_garbage(sub1)
    sub2 = clean_html_garbage(sub2)
    sub3 = clean_html_garbage(sub3)

    if not body2.strip() and not body3.strip():
        print("⚠️ [경고] Gemini가 포맷을 이탈하여 전체 글을 통째로 출력했습니다. 강제 파싱을 시작합니다.")
        paragraphs = [p.strip() for p in body1.split('\n') if p.strip()]
        total_p = len(paragraphs)
        
        if total_p >= 3:
            size = total_p // 3
            body1 = "\n\n".join(paragraphs[:size])
            body2 = "\n\n".join(paragraphs[size:size*2])
            body3 = "\n\n".join(paragraphs[size*2:])
        else:
            body2 = "정확한 개념 이해를 바탕으로 자산 방어 전략 수립이 시급한 시점입니다."
            body3 = "객관적인 데이터를 기반으로 리스크를 관리하고 안정적인 수익을 누리세요."

    ai_tags = [t.strip() for t in tags_raw.replace('`','').replace('**','').split(',') if t.strip()]
    fixed_tags = ['주식투자', '재테크', '국내증시']
    tags = list(set(ai_tags + fixed_tags))

    sample_count = min(3, len(github_images_pool))
    chosen_images = random.sample(github_images_pool, sample_count)
    
    base_url_clean = GITHUB_IMAGE_BASE_URL.strip()
    img_url1 = f"{base_url_clean}{chosen_images[0].strip()}" if sample_count >= 1 else "https://placehold.co/800x450/1e3a8a/ffffff/png?text=STOCK+IMAGE+1"
    img_url2 = f"{base_url_clean}{chosen_images[1].strip()}" if sample_count >= 2 else "https://placehold.co/800x450/0d9488/ffffff/png?text=STOCK+IMAGE+2"
    img_url3 = f"{base_url_clean}{chosen_images[2].strip()}" if sample_count >= 3 else "https://placehold.co/800x450/4f46e5/ffffff/png?text=STOCK+IMAGE+3"
    
    print(f"🎲 [실시간 이미지 매칭 확정]: {chosen_images}")
    
    # 💡 가독성 극대화를 위한 문단(Paragraph) 포매팅 함수
    def format_paragraphs(text):
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        return "".join([f'<p style="margin-bottom: 22px; word-break: keep-all; line-height: 1.8;">{p}</p>' for p in paragraphs])

    b1_html = format_paragraphs(body1)
    b2_html = format_paragraphs(body2)
    b3_html = format_paragraphs(body3)

    final_html = (
        f'<div style="text-align:center; margin-bottom:25px;"><img src="{img_url1}" alt="Market Update Part 1" style="max-width:100%; height:auto; border-radius:8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);"/></div>'
        f'{ADSENSE_CODE}'  
        f'<h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 25px; margin-bottom: 20px;">{sub1}</h3>'
        f'<div class="post-p1" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b1_html}</div>'
        f'{CALCULATOR_BOARD_CODE}'  
        f'<div style="text-align:center; margin-bottom:25px; margin-top:35px;"><img src="{img_url2}" alt="Market Update Part 2" style="max-width:100%; height:auto; border-radius:8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);"/></div>'
        f'<h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 15px; margin-bottom: 20px;">{sub2}</h3>'
        f'<div class="post-p2" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b2_html}</div>'
        f'<div style="text-align:center; margin-bottom:25px; margin-top:35px;"><img src="{img_url3}" alt="Market Update Part 3" style="max-width:100%; height:auto; border-radius:8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);"/></div>'
        f'<h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 15px; margin-bottom: 20px;">{sub3}</h3>'
        f'<div class="post-p3" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b3_html}</div>'
        f'{ADSENSE_CODE}{CTA_CODE}'  
    )

    scheduled_publish_time = calculate_scheduled_time()

    post_data = {
        'title': title,
        'content': final_html,
        'labels': tags,
        'published': scheduled_publish_time
    }
    
    print(f"📡 [디버그] 예약 발행 시간 (KST): {scheduled_publish_time}")
    print("📝 무결성 클린 레이아웃 기반 블로그 업로드 API 요청 전송 중...")
    
    try:
        posts_service = blogger.posts()
        request = posts_service.insert(blogId=BLOG_ID, body=post_data, isDraft=False)
        created_post = request.execute()
        print(f"✅ [배치 완료] 구글 블로거에 글과 {sample_count}장의 깃허브 원본 이미지가 무결성 상태로 발행 성공했습니다!")
    except Exception as api_err:
        print(f"❌ [네트워크/API 에러 발생] 원인: {api_err}")

if __name__ == "__main__":
    main()
