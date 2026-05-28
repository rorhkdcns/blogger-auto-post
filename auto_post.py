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
# ⚙️ 고유 설정 정보 (유저님 세팅 완벽 반영 및 무결성 검증)
# =====================================================================
BLOG_ID = "347204372769511011"  
GOOGLE_ADSENSE_CLIENT = "ca-pub-4292478378917157"
GOOGLE_ADSENSE_SLOT = "5317754949"
GOOGLE_ALERT_RSS_URL = "https://www.google.co.kr/alerts/feeds/13793017153619247481/11360882853986229297"

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
    print("📡 구글 알리미 주식 RSS 피드 수집 중...")
    feed = feedparser.parse(GOOGLE_ALERT_RSS_URL)
    news_content = ""
    for i, entry in enumerate(feed.entries[:5]):
        title = html.escape(entry.title).replace('<b>', '').replace('</b>', '')
        summary = html.escape(entry.summary).replace('<b>', '').replace('</b>', '')
        news_content += f"\n[뉴스 {i+1}]\n제목: {title}\n요약: {summary}\n"
    if not news_content.strip():
        news_content = "현재 국내외 주식 시장 시황 및 주요 거시 경제 지표 변동성 확대 현상 발생."
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
<div class="cta-box" style="border: 2px dashed #2563eb; padding: 22px; border-radius: 12px; background-color: #f0fdf4; margin-top: 40px; text-align: center;">
    <p style="font-size: 17px; color: #166534; font-weight: bold; margin-bottom: 10px; display: inline-block; background: #dcfce7; padding: 4px 12px; border-radius: 20px;">📊 손실 없는 완벽한 리스크 관리 법칙</p>
    <p style="font-size: 14px; color: #1e293b; line-height: 1.7; margin: 0 0 15px 0; font-weight: 500;">
        방금 확인하신 시장 변동성에 무작위로 대처하면 자산이 순식간에 손실 구간으로 진입할 수 있습니다.<br>
        지금 바로 본문에 배치된 <b>[실시간 주식 계산기 모음판]</b>으로 이동하여 본인의 정확한 <b>물타기 평단가</b>와 <b>손절/익절 가이드라인</b>을 수치로 직접 검증한 뒤 안전하게 매매를 진행하세요!
    </p>
    <a href="#calc-board-top" style="display: inline-block; background: #16a34a; color: white; font-weight: bold; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-size: 15px; box-shadow: 0 4px 6px -1px rgba(22, 163, 74, 0.2);">⚡ 실시간 계산기로 내 평단가 진단하기</a>
</div>
"""

# 🎯 [무결성 새 창 열기 교정 완료] 4가지 <a> 태그 내부에 target="_blank"를 정확하게 심었습니다.
CALCULATOR_BOARD_CODE = f"""
<div id="calc-board-top" class="calc-board-container" style="margin: 40px 0; padding: 20px 10px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <p style="margin: 0 0 20px 0; font-size: 20px; font-weight: 900; color: #0f172a; text-align: center; letter-spacing: -0.5px;">⚡ 리스크 관리를 위한 실시간 주식 계산기 모음</p>
    <div class="calc-grid" style="display: flex; flex-direction: column; gap: 12px;">
        <a href="{URL_물타기}" target="_blank" style="display: block; background: #2563eb; border-radius: 12px; padding: 22px 10px; text-align: center; text-decoration: none; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2); box-sizing: border-box;">
            <span style="display: block; font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; line-height: 1.2;">[📉 주식 물타기 계산기 실행하기]</span>
            <span style="display: block; font-size: 15px; color: #bfdbfe; margin-top: 6px; font-weight: 700;">보유 종목 평단가 낮추기 및 추가 매수 시뮬레이션</span>
        </a>
        <a href="{URL_손절익절}" target="_blank" style="display: block; background: #0d9488; border-radius: 12px; padding: 22px 10px; text-align: center; text-decoration: none; box-shadow: 0 4px 6px -1px rgba(13, 148, 136, 0.2); box-sizing: border-box;">
            <span style="display: block; font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; line-height: 1.2;">[💰 익절 / 손절가 기준 계산기]</span>
            <span style="display: block; font-size: 15px; color: #ccfbf1; margin-top: 6px; font-weight: 700;">단타 실전 매매 맞춤형 목표가 및 유상 설정</span>
        </a>
        <a href="{URL_복리}" target="_blank" style="display: block; background: #4f46e5; border-radius: 12px; padding: 22px 10px; text-align: center; text-decoration: none; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2); box-sizing: border-box;">
            <span style="display: block; font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; line-height: 1.2;">[📈 연복리 자산 성장 시뮬레이터]</span>
            <span style="display: block; font-size: 15px; color: #e0e7ff; margin-top: 6px; font-weight: 700;">장기 투자 및 복리 마법 기반 미래 자산 예측</span>
        </a>
        <a href="{URL_환율}" target="_blank" style="display: block; background: #334155; border-radius: 12px; padding: 22px 10px; text-align: center; text-decoration: none; box-shadow: 0 4px 6px -1px rgba(51, 65, 85, 0.2); box-sizing: border-box;">
            <span style="display: block; font-size: 25px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; line-height: 1.2;">[🎯 미국주식 실시간 환율 계산기]</span>
            <span style="display: block; font-size: 15px; color: #cbd5e1; margin-top: 6px; font-weight: 700;">해외주식 양도소득세 및 환율 변동성 체크</span>
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
        "아래 주식 투자 뉴스 데이터를 기반으로 블로그 포스팅용 전문 시황 분석 글을 작성해줘.\n\n"
        f"[뉴스 데이터]\n{news_data}\n\n"
        "[필수 작성 지침]\n"
"1. [제목 법칙]: 실전 SEO 키워드와 구체적인 수치를 조합하여 정보성 가치가 드러나는 강력한 제목을 구성하라. (예: 삼성전자 7만 원대 대응 전략, 지금 당장 계산해봐야 할 3가지)\n\n"
"2. [설득 흐름]: 독자의 문제를 인식시키고 위기감을 조성한 뒤, 논리적인 해결책으로 유도하라.\n"
"   - 문제 제기: 시장의 변화나 데이터로 독자의 공감을 유도하라.\n"
"   - 위기 증폭: 상황을 방치했을 때의 잠재적 손실을 수치로 제시하라.\n"
"   - 해결책 제시: 위기를 극복할 수 있는 구체적인 투자 방향을 제시하라.\n"
"   - 행동 유도: 블로그 내 계산기 툴을 활용하여 독자가 스스로 수치를 확인하도록 강력하게 권장하라.\n"
"   - 절대 금지: 본문 그 어디에도 '파소나', 'PASONA', '카피라이팅', 'AI', '인공지능', '자동화'라는 영문/국문 단어를 절대로 쓰지 마라.\n\n"
"3. [가독성 법칙]: 모바일 화면 최적화를 위해 짧은 문장 위주로 작성하고, 2-3문장마다 문단을 나누어라. 본문에 대괄호나 불필요한 특수기호를 절대 사용하지 마라.\n\n"
"4. [강조 법칙]: 시장의 핵심 용어 및 투자 판단의 근거가 되는 지표는 반드시 구글 표준 <b><font color=\"#e11d48\">중요키워드</font></b> 양식으로만 강조하라. 문장 전체가 아닌 핵심 데이터에만 적용하라.\n\n"
"5. [파트 구성]: 본문은 무조건 3개의 파트로 나누고 정보성 소제목을 확실히 부여하라.\n"
"   - 1단계: 시장 현황, 뉴스 데이터, 수치적 변화를 객관적으로 분석하라.\n"
"   - 2단계: 위 사실이 개인 투자자의 자산에 미치는 영향과 위험을 서술하라.\n"
"   - 3단계: 준비된 계산기 툴을 활용하여 대응 수치를 직접 계산해 보도록 강력히 유도하라.\n\n"
"6. [시각화]: 영문 이미지 검색 키워드를 IMAGE_PROMPT에 직관적인 2-3단어 명사로 추천하라.\n\n"
"7. [태그 추출]: 검색 의도가 반영된 구체적인 주식 키워드를 3-5개 추출해라. (쉼표 구분)\n\n"
        "[출력 포맷 고정]\n"
        "[TITLE]: 실전 주식 자극적 제목\n"
        "[TAGS]: 주식투자, 재테크, 국내증시\n"
        "[IMAGE_PROMPT]: stock market index\n"
        "[SUB_TITLE_1]: 소제목1\n"
        "[BODY_1]: 내용1 (반드시 <b><font color=\"#e11d48\">강조용어</font></b> 적극 활용)\n"
        "[SUB_TITLE_2]: 소제목2\n"
        "[BODY_2]: 내용2 (반드시 <b><font color=\"#e11d48\">강조용어</font></b> 적극 활용)\n"
        "[SUB_TITLE_3]: 소제목3\n"
        "[BODY_3]: 내용3 (반드시 <b><font color=\"#e11d48\">강조용어</font></b> 적극 활용)"
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

def main():
    b64_token = os.environ.get("TOKEN_PICKLE_BASE64")
    if not b64_token:
        print("❌ 에러: TOKEN_PICKLE_BASE64가 없습니다.")
        return
        
    creds = pickle.loads(base64.b64decode(b64_token))
    blogger = build('blogger', 'v3', credentials=creds)
    
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

    # 🛡️ Gemini의 전체 통합 출력에 대응하는 무결성 강제 3분할 로직
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

    # 🔗 [라벨 누적 부활 방어 시스템 가동]
    ai_tags = [t.strip() for t in tags_raw.replace('`','').replace('**','').split(',') if t.strip()]
    fixed_tags = ['주식투자', '재테크', '국내증시']
    
    # 두 리스트를 결합한 후 set으로 중복을 제거하여 항상 고정 라벨이 포함되도록 조치
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

# 🏗️ 중간 계산기 보드와 하단 CTA 박스의 레이아웃 배치 완전 영구 고정 (상단 광고 최적화 버전)
    final_html = (
        f'<div style="text-align:center; margin-bottom:25px;"><img src="{img_url1}" alt="Market Update Part 1" style="max-width:100%; height:auto; border-radius:8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);"/></div>'
        f'{ADSENSE_CODE}'  # 🚀 [최상단 정석 배치] 첫 이미지 바로 아래, 글 시작하기 전에 고단가 광고 노출!
        f'<h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 25px; margin-bottom: 20px;">{sub1}</h3>'
        f'<div class="post-p1" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b1_html}</div>'
        f'{CALCULATOR_BOARD_CODE}'  # 중간 광고를 위로 올렸으므로 여기서는 깔끔하게 계산기 보드로 유저 집중
        f'<div style="text-align:center; margin-bottom:25px; margin-top:35px;"><img src="{img_url2}" alt="Market Update Part 2" style="max-width:100%; height:auto; border-radius:8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);"/></div>'
        f'<h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 15px; margin-bottom: 20px;">{sub2}</h3>'
        f'<div class="post-p2" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b2_html}</div>'
        f'<div style="text-align:center; margin-bottom:25px; margin-top:35px;"><img src="{img_url3}" alt="Market Update Part 3" style="max-width:100%; height:auto; border-radius:8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);"/></div>'
        f'<h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 15px; margin-bottom: 20px;">{sub3}</h3>'
        f'<div class="post-p3" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b3_html}</div>'
        f'{ADSENSE_CODE}{CTA_CODE}'  # [하단 배치] 마지막 글이 끝나고 광고 노출 후 하단 행동유도(CTA)로 연결
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
