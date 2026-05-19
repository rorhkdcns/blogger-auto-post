import os
import sys
import subprocess
import time

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
    2. [가독성 절대 조건]: 한 문장이 끝날 때마다 줄바꿈(엔터)을 하고, 2~3문장마다 공백 라인(더블 엔터)을 주어라.
    3. [시각적 강조 조건]: 핵심 주식 용어, 주요 종목명, 시장 방향성 키워드를 반드시 `<b><span style="color: #e11d48;">중요키워드</span></b>` 양식으로 감싸라. 단락당 2~3개 정도가 적당하다.
    4. 본문은 반드시 3개의 파트로 나누고 소제목을 추출해줘.
    5. 영문 이미지 검색 키워드를 [IMAGE_PROMPT]에 딱 2~3단어 명사로 짧게 추천해줘.
    6. 검색용 주식 태그를 3~5개 추출해줘. (쉼표 구분)
    7. 이 글의 핵심 내용을 130자 내외의 완성된 문장으로 요약한 '검색 설명'을 [DESCRIPTION] 뒤에 정확히 작성해줘.
    
    [출력 포맷 고정]
    [TITLE]: 제목
    [TAGS]: 태그1, 태그2
    [DESCRIPTION]: 검색 설명 내용
    [IMAGE_PROMPT]: stock market
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
    
    parsed = {
        'title': '', 'tags': ['주식투자', '재테크'], 'desc': '', 'img_prompt': 'STOCK MARKET',
        'sub1': '', 'body1': '', 'sub2': '', 'body2': '', 'sub3': '', 'body3': ''
    }
    
    for line in ai_raw.split('\n'):
        clean_line = line.strip().replace('**', '') 
        if '[TITLE]:' in clean_line: parsed['title'] = clean_line.split('[TITLE]:')[-1].strip()
        elif '[TAGS]:' in clean_line: parsed['tags'] = [t.strip() for t in clean_line.split('[TAGS]:')[-1].split(',')]
        elif '[DESCRIPTION]:' in clean_line: parsed['desc'] = clean_line.split('[DESCRIPTION]:')[-1].strip()
        elif '[IMAGE_PROMPT]:' in clean_line: parsed['img_prompt'] = clean_line.split('[IMAGE_PROMPT]:')[-1].strip().upper()
        elif '[SUB_TITLE_1]:' in clean_line: parsed['sub1'] = clean_line.split('[SUB_TITLE_1]:')[-1].strip()
        elif '[SUB_TITLE_2]:' in clean_line: parsed['sub2'] = clean_line.split('[SUB_TITLE_2]:')[-1].strip()
        elif '[SUB_TITLE_3]:' in clean_line: parsed['sub3'] = clean_line.split('[SUB_TITLE_3]:')[-1].strip()
        
    def extract_block(text, start_tag, end_tag=None):
        try:
            start_idx = text.find(start_tag)
            if start_idx == -1: return ""
            start_idx += len(start_tag)
            if end_tag:
                end_idx = text.find(end_tag)
                return text[start_idx:end_idx].strip() if end_idx != -1 else text[start_idx:].strip()
            return text[start_idx:].strip()
        except: return ""

    parsed['body1'] = extract_block(ai_raw, '[BODY_1]:', '[SUB_TITLE_2]')
    parsed['body2'] = extract_block(ai_raw, '[BODY_2]:', '[SUB_TITLE_3]')
    parsed['body3'] = extract_block(ai_raw, '[BODY_3]:')

    if not parsed['body1']:
        parsed['body1'] = ai_raw
        parsed['sub1'] = "📈 오늘 시장 핵심 경제 시황"

    keyword = parsed.get('img_prompt', 'STOCK MARKET')
    encoded_text = urllib.parse.quote(f"FINANCE ANALYSIS: {keyword}")
    dynamic_tags = f"TREND: {', '.join(parsed['tags'][:3])}".upper()
    encoded_tags_text = urllib.parse.quote(dynamic_tags)
    
    thumbnail_url = f"https://placehold.co/800x450/1e3a8a/ffffff/png?text={encoded_text}&font=playfair"
    inline_image_url = f"https://placehold.co/800x450/0f172a/38bdf8/png?text={encoded_tags_text}&font=roboto"
    
    b1_html = parsed['body1'].replace('\n', '<br>')
    b2_html = parsed['body2'].replace('\n', '<br>')
    b3_html = parsed['body3'].replace('\n', '<br>')

    final_html = f"""
    <div style="text-align:center; margin-bottom:30px;">
        <img src="{thumbnail_url}" alt="{keyword} Report" style="max-width:100%; height:auto; border-radius:8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);"/>
    </div>
    <h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 35px; margin-bottom: 20px;">{parsed['sub1']}</h3>
    <div class="post-p1" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b1_html}</div>
    {ADSENSE_CODE}
    <h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 35px; margin-bottom: 20px;">{parsed['sub2']}</h3>
    <div class="post-p2" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b2_html}</div>
    <div style="text-align:center; margin: 35px 0;"><img src="{inline_image_url}" alt="Market Index Trend" style="max-width:100%; height:auto; border-radius:6px;"/></div>
    <h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 35px; margin-bottom: 20px;">{parsed['sub3']}</h3>
    <div class="post-p3" style="font-size:16px; line-height:1.9; color:#334155; margin-bottom: 25px; letter-spacing: -0.3px;">{b3_html}</div>
    {ADSENSE_CODE}
    {CTA_CODE}
    """

    scheduled_publish_time = calculate_scheduled_time()
    fallback_desc = parsed['body1'][:130].strip() if parsed['body1'] else '국내외 증시 시황 및 주식 시장 핵심 변동성 지표 분석.'
    final_desc = parsed['desc'] if parsed['desc'] else fallback_desc

    # [1단계] 우선 본문과 제목, 태그만 넣고 뼈대 글을 생성합니다. (구글 API 버그 우회)
    initial_data = {
        'title': parsed['title'] if parsed['title'] else '오늘의 주식 투자 시황 핵심 분석 요약',
        'content': final_html,
        'labels': parsed['tags'],
        'published': scheduled_publish_time
    }
    
    posts_service = blogger.posts()
    print("📝 1단계: 기본 포스팅 뼈대 생성 중...")
    created_post = posts_service.insert(blogId=BLOG_ID, body=initial_data, isDraft=False).execute()
    post_id = created_post.get('id')
    
    # 🌟 [2단계: 핵심 패치] 방금 생성된 글 ID에 'PATCH' 메소드로 검색 설명을 강제 주입합니다!
    print(f"🔧 2단계: 구글 API 버그 우회 - 포스트 ID({post_id})에 검색 설명 강제 주입 패치 개시...")
    patch_data = {
        'customMetaData': final_desc
    }
    
    # patch 호출 시 반드시 원래 글 구조를 유지하도록 추가 처리를 진행합니다.
    updated_post = posts_service.patch(blogId=BLOG_ID, postId=post_id, body=patch_data).execute()
    
    print(f"✅ [최종 성공] 구글 버그 우회 주입 성공!")
    print(f"⏰ 발행 시간 (KST): {scheduled_publish_time}")
    print(f"🔍 강제 주입된 검색 설명: {updated_post.get('customMetaData')}")

if __name__ == "__main__":
    main()
