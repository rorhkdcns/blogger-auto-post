import os
import sys
import subprocess
import time
import re

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
# ⚙️ 고유 설정 정보
# =====================================================================
BLOG_ID = "347204372769511011"  
GOOGLE_ADSENSE_CLIENT = "ca-pub-4292478378917157"
GOOGLE_ADSENSE_SLOT = "5317754949"
GOOGLE_ALERT_RSS_URL = "https://www.google.co.kr/alerts/feeds/13793017153619247481/11360882853986229297"

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
        datetime.datetime.combine(today, datetime.time(18, 0), tzinfo=kst)
    ]
    scheduled_time = None
    for c in candidates:
        if c > now: 
            scheduled_time = c
            break
    if not scheduled_time:
        tomorrow = today + datetime.timedelta(days=1)
        scheduled_time = datetime.datetime.combine(tomorrow, datetime.time(9, 0), tzinfo=kst)
    return scheduled_time.isoformat()

ADSENSE_CODE = """
<div class="adsense-container" style="text-align:center; margin: 30px 0;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={CLIENT}" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="{CLIENT}" data-ad-slot="{SLOT}" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
""".replace("{CLIENT}", GOOGLE_ADSENSE_CLIENT).replace("{SLOT}", GOOGLE_ADSENSE_SLOT)

CTA_CODE = """
<div class="cta-box" style="border: 2px solid #3b82f6; padding: 20px; border-radius: 10px; background-color: #f8fafc; margin-top: 40px;">
    <p style="font-size: 15px; color: #1e293b; font-weight: bold; margin-bottom: 8px;">💡 투자 참고 유의사항</p>
    <p style="font-size: 13px; color: #64748b; line-height: 1.6; margin: 0;">
        본 콘텐츠는 구글 알리미 주식 투자 관련 뉴스를 기반으로 금융 분석 시스템과 시장 데이터를 활용해 요약·편집한 정보성 글이며, 특정 종목에 대한 추천이나 투자 권유가 아닙니다. 모든 투자의 책임은 투자자 본인에게 있으므로 신중하게 결정하시기 바랍니다. <b>성공적인 투자를 응원합니다.</b>
    </p>
</div>
"""

def generate_blog_content(news_data):
    api_key_direct = os.environ.get("API_KEY")
    client = genai.Client(
        api_key=api_key_direct,
        http_options=types.HttpOptions(api_version="v1")
    )
    
    prompt = f"""
    아래 주식 투자 뉴스 데이터를 기반으로 블로그 포스팅용 전문 시황 분석 글을 작성해줘.
    
    [뉴스 데이터]
    {news_data}
    
    [필수 작성 지침]
    1. 마케팅 카피라이팅 기법인 PASONA 법칙을 적용하여 자연스럽게 풀어써줘. ('파소나', 'AI', '인공지능' 단어 본문 언급 절대 금지)
    2. [가독성 절대 조건]: 한 문장이 끝날 때마다 줄바꿈(엔터)을 하고, 2~3문장마다 공백 라인(더블 엔터)을 주어라. 본문에 백틱(`) 기호나 불필요한 따옴표 문장 부호를 섞지 마라.
    3. [시각적 강조 조건]: 핵심 주식 용어, 주요 종목명, 시장 방향성 키워드를 반드시 `<b><span style="color: #e11d48;">중요키워드</span></b>` 양식으로 감싸라. 단락당 2~3개 정도가 적당하다. 중요 키워드 앞뒤에 백틱이나 불필요한 기호를 붙이지 마라.
    4. 본문은 반드시 3개의 파트로 나누고 소제목을 추출해줘.
    5. 영문 이미지 검색 키워드를 [IMAGE_PROMPT]에 딱 2~3단어 명사로 짧게 추천해줘.
    6. 검색용 주식 태그를 3~5개 추출해줘. (쉼표 구분)
    7. 이 글의 핵심 내용을 130자 내외의 완성된 문장으로 요약한 '검색 설명'을 [DESCRIPTION] 뒤에 정확히 작성해줘.
    
    [출력 포맷 고정 - 형식 절대 파괴 금지]
    [TITLE]: 제목 내용
    [TAGS]: 태그1, 태그2, 태그3
    [DESCRIPTION]: 검색 설명 내용
    [IMAGE_PROMPT]: stock market index
    [SUB_TITLE_1]: 소제목1
    [BODY_1]: 내용1
    [SUB_TITLE_2]: 소제목2
    [BODY_2]: 내용2
    [SUB_TITLE_3]: 소제목3
    [BODY_3]: 내용3
    """
    
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
    
    # 🌟 [오류 진압 1단계] 정규식을 통한 무적의 패턴 매칭 파싱 시스템 도입
    def re_extract(pattern, text, default=""):
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return default

    title = re_extract(r'\[TITLE\]\s*:\s*(.*?)(?=\n\[|$)', ai_raw, "오늘의 주식 투자 시황 핵심 분석 요약")
    tags_raw = re_extract(r'\[TAGS\]\s*:\s*(.*?)(?=\n\[|$)', ai_raw, "주식투자, 국내증시, 시황분석")
    desc = re_extract(r'\[DESCRIPTION\]\s*:\s*(.*?)(?=\n\[|$)', ai_raw, "")
    img_prompt = re_extract(r'\[IMAGE_PROMPT\]\s*:\s*(.*?)(?=\n\[|$)', ai_raw, "STOCK MARKET").upper()
    
    sub1 = re_extract(r'\[SUB_TITLE_1\]\s*:\s*(.*?)(?=\n\[|$)', ai_raw, "📈 오늘 시장 핵심 경제 시황")
    body1 = re_extract(r'\[BODY_1\]\s*:\s*(.*?)(?=\n\[|$)', ai_raw, "")
    
    sub2 = re_extract(r'\[SUB_TITLE_2\]\s*:\s*(.*?)(?=\n\[|$)', ai_raw, "📊 주요 분석 및 핵심 지표 체크")
    body2 = re_extract(r'\[BODY_2\]\s*:\s*(.*?)(?=\n\[|$)', ai_raw, "")
    
    sub3 = re_extract(r'\[SUB_TITLE_3\]\s*:\s*(.*?)(?=\n\[|$)', ai_raw, "💡 향후 투자 전략 및 대응")
    body3 = re_extract(r'\[BODY_3\]\s*(.*?)$', ai_raw, "")

    # 백업 방어선 작동
    if not body1:
        body1 = ai_raw
    
    # 태그 배열 안전 세팅
    tags = [t.strip() for t in tags_raw.split(',') if t.strip()]
    if not tags:
        tags = ['주식투자', '재테크', '시황분석']

    # 🌟 [오류 진압 2단계] 본문에 난입한 불필요한 백틱(`) 및 따옴표 기호 강제 세척 제거
    def clean_symbols(text):
        text = text.replace('`', '')
        # 잘못 파싱되어 본문에 잔류한 프롬프트 잔여물 강제 제거
        text = re.sub(r'\[.*?\]\s*:\s*', '', text)
        return text.strip()

    body1 = clean_symbols(body1)
    body2 = clean_symbols(body2)
    body3 = clean_symbols(body3)
    sub1 = clean_symbols(sub1)
    sub2 = clean_symbols(sub2)
    sub3 = clean_symbols(sub3)

    # 이미지 인코딩 및 처리
    keyword = img_prompt if img_prompt else 'STOCK MARKET'
    encoded_text = urllib.parse.quote(f"FINANCE ANALYSIS: {keyword}")
    
    # 상위 3개 태그 추출 및 빈값 방지 처리
    valid_tags = [t for t in tags if t]
    if len(valid_tags) < 3:
        valid_tags += ['INVEST', 'STOCK', 'MARKET']
    dynamic_tags = f"TREND: {', '.join(valid_tags[:3])}".upper()
    encoded_tags_text = urllib.parse.quote(dynamic_tags)
    
    thumbnail_url = f"https://placehold.co/800x450/1e3a8a/ffffff/png?text={encoded_text}&font=playfair"
    inline_image_url = f"https://placehold.co/800x450/0f172a/38bdf8/png?text={encoded_tags_text}&font=roboto"
    
    b1_html = body1.replace('\n', '<br>')
    b2_html = body2.replace('\n', '<br>')
    b3_html = body3.replace('\n', '<br>')

    final_html = f"""
    <div style="text-align:center; margin-bottom:30px;">
        <img src="{thumbnail_url}" alt="{keyword} Report" style="max-width:100%; height:auto; border-radius:8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);"/>
    </div>
    <h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 35px; margin-bottom: 20px;">{sub1}</h3>
    <div class="post-p1" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b1_html}</div>
    {ADSENSE_CODE}
    <h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 35px; margin-bottom: 20px;">{sub2}</h3>
    <div class="post-p2" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b2_html}</div>
    <div style="text-align:center; margin: 35px 0;"><img src="{inline_image_url}" alt="Market Index Trend" style="max-width:100%; height:auto; border-radius:6px;"/></div>
    <h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 35px; margin-bottom: 20px;">{sub3}</h3>
    <div class="post-p3" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b3_html}</div>
    {ADSENSE_CODE}
    {CTA_CODE}
    """

    scheduled_publish_time = calculate_scheduled_time()
    fallback_desc = body1[:130].strip() if body1 else '국내외 증시 시황 및 주식 시장 핵심 변동성 지표 분석.'
    final_desc = desc if desc else fallback_desc
    final_desc = clean_symbols(final_desc)

    initial_data = {
        'title': title,
        'content': final_html,
        'labels': tags,
        'published': scheduled_publish_time
    }
    
    posts_service = blogger.posts()
    print("📝 1단계: 청정화된 본문 데이터로 기본 뼈대 포스팅 생성 중...")
    created_post = posts_service.insert(blogId=BLOG_ID, body=initial_data, isDraft=False).execute()
    post_id = created_post.get('id')
    
    # 🌟 [3단계] 뼈대 빌드가 성공적으로 끝난 뒤 고유 ID 권한을 쥐고 검색 설명을 강제 집행 패치
    print(f"🔧 2단계: 생성 완료된 글 ID({post_id})에 동기식으로 검색 설명 강제 주입 중...")
    patch_data = {
        'customMetaData': final_desc
    }
    
    updated_post = posts_service.patch(blogId=BLOG_ID, postId=post_id, body=patch_data).execute()
    
    print(f"✅ [버그 박멸 완료] 완벽한 레이아웃으로 포스팅 예약 성공!")
    print(f"⏰ 발행 예정 시간 (KST): {scheduled_publish_time}")
    print(f"🔍 주입된 정제 검색 설명: {updated_post.get('customMetaData')}")

if __name__ == "__main__":
    main()
