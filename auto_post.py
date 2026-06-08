import os
import sys
import subprocess
import time
import re
import random

# [1단계] 라이브러리 자동 설치 및 검증
required_modules = [
    "feedparser", 
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

import pickle
import base64
import datetime
import urllib.parse
import html
import feedparser  
from googleapiclient.discovery import build
from google import genai 
from google.genai import types  

# =====================================================================
# ⚙️ 고유 설정 정보 (8개 RSS 주소 완벽 반영 및 무결성 검증)
# =====================================================================
BLOG_ID = "347204372769511011"  
GOOGLE_ADSENSE_CLIENT = "ca-pub-4292478378917157"
GOOGLE_ADSENSE_SLOT = "5317754949"

# 🔗 구글 알리미 복수 RSS 피드 주소 리스트 (총 8개 완벽 통합)
GOOGLE_ALERT_RSS_URLS = [
    "https://www.google.co.kr/alerts/feeds/13793017153619247481/11360882853986229297",  # 기존 피드
    "https://www.google.co.kr/alerts/feeds/13793017153619247481/6920293583916476350",     # 추가 피드 1
    "https://www.google.co.kr/alerts/feeds/13793017153619247481/14642687874364656262",    # 추가 피드 2
    "https://www.google.co.kr/alerts/feeds/13793017153619247481/15677364953719324839",    # 추가 피드 3
    "https://www.google.co.kr/alerts/feeds/13793017153619247481/6920293583916476340",     # 추가 피드 4
    "https://www.google.co.kr/alerts/feeds/13793017153619247481/15677364953719326324",    # 추가 피드 5
    "https://www.google.co.kr/alerts/feeds/13793017153619247481/6920293583916477680",     # 추가 피드 6
    "https://www.google.co.kr/alerts/feeds/13793017153619247481/6920293583916478309"      # 추가 피드 7
]

GITHUB_USER_ID = "rorhkdcns"  
GITHUB_REPO_NAME = "blogger-auto-post"  

# 💡 주소 뒤에 유령 공백이 붙지 않도록 완전히 한 줄로 하드코딩 처리
GITHUB_IMAGE_BASE_URL = "https://raw.githubusercontent.com/rorhkdcns/blogger-auto-post/main/blog_images/stock/"

# 🔗 원본 png 확장자와 순번을 100% 보존하고 내부에 숨어있던 유령 공백을 전수 도려낸 클린 리스트
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

def fetch_google_alerts_news():
    print("📡 등록된 8개의 구글 알리미 주식 RSS 피드 수집 시작...")
    news_content = ""
    news_count = 1
    
    # 8개 피드를 순회하며 데이터 취합
    for url in GOOGLE_ALERT_RSS_URLS:
        try:
            feed = feedparser.parse(url)
            
            # 피드 개수가 많으므로 피드당 가장 최신 뉴스 1개씩만 압축 수집하여 데이터 무결성 유지
            for entry in feed.entries[:1]:
                title = html.escape(entry.title).replace('<b>', '').replace('</b>', '')
                summary = html.escape(entry.summary).replace('<b>', '').replace('</b>', '')
                news_content += f"\n[시장 정보 {news_count}]\n제목: {title}\n요약: {summary}\n"
                news_count += 1
        except Exception as e:
            print(f"⚠️ RSS 피드 수집 실패 (건너뛰기) -> {url}: {e}")
            
    if not news_content.strip():
        news_content = "현재 국내외 주식 시장 시황 및 주요 거시 경제 지표 변동성 확대 현상 발생."
        
    print(f"✅ 총 {news_count-1}개의 교차 시장 뉴스 데이터를 성공적으로 병합했습니다.")
    return news_content

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

def generate_blog_content(news_data):
    api_key_direct = os.environ.get("API_KEY")
    client = genai.Client(
        api_key=api_key_direct,
        http_options=types.HttpOptions(api_version="v1")
    )
    
    prompt = (
        "아래 제공된 주식 투자 뉴스 데이터를 기반으로, 독자에게 깊이 있는 통찰을 제공하는 전문 시황 분석 글을 작성해줘.\n\n"
        f"[뉴스 데이터]\n{news_data}\n\n"
        "[필수 작성 지침]\n"
        "1. [제목 법칙]: 검색 엔진(SEO)에 최적화된 정보성 제목을 구성하라. 자극적인 낚시성 문구 대신, 구체적인 수치와 시장의 핵심 화두를 조합하여 신뢰감을 주어야 한다. (예: 환율 1510원 돌파와 국내 증시 영향, 투자자가 주목할 3가지 변수)\n\n"
        "2. [독창적 스토리텔링 및 설득 흐름]:\n"
        "   - 뉴스 데이터를 단순 요약하거나 나열하는 방식을 절대 금지한다. 수집된 뉴스가 개인 투자자의 자산에 미칠 실질적인 영향과 거시경제적 인과관계를 논리적으로 분석하라.\n"
        "   - 문맥의 흐름 속에서 투자자가 스스로 리스크를 점검할 수 있도록 자연스럽게 유도하라. 주식 계산기나 툴을 강제로 쓰라는 식의 노골적인 광고 문구는 절대 배제하라.\n"
        "   - 절대 금지어: 본문 그 어디에도 '파소나', 'PASONA', '카피라이팅', 'AI', '인공지능', '자동화', '프로그램', '단계별 전략'이라는 단어를 영문/국문 불문하고 절대 사용하지 마라.\n\n"
        "3. [자연스러운 가독성 법칙]: 사람이 직접 쓴 블로그처럼 자연스럽고 친근하면서도 전문적인 어조(예: ~입니다, ~시점입니다)를 유지하라. 문장은 모바일 가독성을 위해 2~3문장 단위로 흐름을 나누되, 기계적인 끊어 읽기 느낌이 나지 않도록 연결성을 확보하라. 본문에 대괄호([])나 불필요한 이모지, 특수기호는 완전히 배제하라.\n\n"
        "4. [강조 법칙]: 글 전체에서 가장 핵심이 되는 지표나 수치(예: 환율 변동 폭, 투자 유치 금액 등) 딱 2~3개에만 구글 표준 <b><font color=\"#e11d48\">중요데이터</font></b> 양식을 적용하라. 문장 전체나 단순 키워드마다 무분별하게 강조를 남발하면 스팸으로 분류되므로 극도로 절제하여 사용하라.\n\n"
        "5. [파트 구성]: 본문은 구조적 완성도를 위해 3개의 파트로 명확히 나누고, 정보의 가치가 높은 소제목을 부여하라.\n"
        "   - 1단계: 현재 시장의 변동성과 수집된 뉴스 데이터가 가진 이면의 의미를 거시적으로 분석하라.\n"
        "   - 2단계: 고환율/고금리 등 리스크 요인이 개인 투자자의 심리와 포트폴리오에 미치는 실질적 위협을 서술하라.\n"
        "   - 3단계: 리스크를 방어하기 위해 투자자가 취해야 할 객관적인 자산 배분 방향과 마음가짐을 제안하라.\n\n"
        "6. [시각화]: 영문 이미지 검색 키워드를 IMAGE_PROMPT에 직관적인 2-3단어 명사로 추천하라.\n\n"
        "7. [태그 추출]: 본문 내용과 밀접하며 검색 의도가 반영된 구체적인 주식 키워드를 3개만 추출해라. (쉼표 구분)\n\n"
        "[출력 포맷 고정]\n"
        "[TITLE]: 신뢰감 있는 정보성 제목\n"
        "[TAGS]: 주식투자, 재테크, 국내증시\n"
        "[IMAGE_PROMPT]: finance growth chart\n"
        "[SUB_TITLE_1]: 소제목1\n"
        "[BODY_1]: 내용1 (강조 양식은 문맥상 꼭 필요한 수치에만 딱 1번 적용)\n"
        "[SUB_TITLE_2]: 소제목2\n"
        "[BODY_2]: 내용2 (강조 양식은 문맥상 꼭 필요한 수치에만 딱 1번 적용)\n"
        "[SUB_TITLE_3]: 소제목3\n"
        "[BODY_3]: 내용3 (강조 양식은 문맥상 꼭 필요한 수치에만 딱 1번 적용)"
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

# 👇 이 함수 부분만 교체해 주세요!
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
    
    # 👇 [추가된 부분 2] 실행 시 오늘 이미 글이 발행되었는지 확인 후 중단
    if check_already_posted(blogger, BLOG_ID):
        print(f"⏩ 오늘({datetime.datetime.now().date()}) 이미 포스팅이 확인되었습니다. 중복 방지를 위해 작업을 종료합니다.")
        return
    
    google_alerts_stock_news = fetch_google_alerts_news()
    ai_raw = generate_blog_content(google_alerts_stock_news)
    
    def re_extract_line(tag, text, default=""):
        pattern = r'\[?' + re.escape(tag) + r'\]?\s*:\s*(.*)'
        for line in text.split('\n'):
            if tag in line:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        return default

    title = re_extract_line('TITLE', ai_raw, "오늘의 주식 투자 시황 핵심 분석 요약")
    title = re.sub(r'<[^>]*>', '', title).replace('`', '').replace('**', '').replace('__', '').strip()
    
    tags_raw = re_extract_line('TAGS', ai_raw, "주식투자, 재테크, 국내증시")
    sub1 = re_extract_line('SUB_TITLE_1', ai_raw, "📈 오늘 시장 핵심 경제 시황")
    sub2 = re_extract_line('SUB_TITLE_2', ai_raw, "📊 주요 분석 및 핵심 지표 체크")
    sub3 = re_extract_line('SUB_TITLE_3', ai_raw, "💡 향후 투자 전략 및 대응")
    
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
            body2 = "시장 변동성에 따른 자산 방어 전략 수립이 시급한 시점입니다."
            body3 = "정확한 데이터를 기반으로 리스크를 관리하고 안정적인 수익을 누리세요."

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
    
    b1_html = body1.replace('\n', '<br>')
    b2_html = body2.replace('\n', '<br>')
    b3_html = body3.replace('\n', '<br>')

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
