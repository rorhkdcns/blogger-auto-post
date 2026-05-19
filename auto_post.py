import os
import sys
import subprocess
import time

# [1단계] 깃허브 액션 환경 내부에서 필요한 라이브러리를 '완벽하게' 설치 완료할 때까지 강제 대기합니다.
required_modules = [
    "feedparser", 
    "google-auth-oauthlib", 
    "google-auth-httplib2", 
    "google-api-python-client", 
    "google-genai"  # 최신 표준 패키지
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

# [2단계] 설치가 완벽히 끝난 것을 확인한 후 라이브러리들을 안전하게 불러옵니다.
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
# ⚙️ [설정 완료] 구글 블로그 및 애드센스 고유 정보
# =====================================================================
BLOG_ID = "347204372769511011"  
GOOGLE_ADSENSE_CLIENT = "ca-pub-4292478378917157"
GOOGLE_ADSENSE_SLOT = "5317754949"

# 🔍 구글 알리미 주식 투자 RSS 피드 주소
GOOGLE_ALERT_RSS_URL = "https://www.google.co.kr/alerts/feeds/13793017153619247481/11360882853986229297"

# =====================================================================
# 📡 [RSS 리더] 구글 알리미에서 주식 뉴스 데이터 추출 함수
# =====================================================================
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

# =====================================================================
# 🕒 [시간 설정] 하루 3번 예약 발행 시간 계산기 (9시, 13시, 18시)
# =====================================================================
def calculate_scheduled_time():
    now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9) # KST 변환
    today = now.date()
    
    candidates = [
        datetime.datetime.combine(today, datetime.time(9, 0)),
        datetime.datetime.combine(today, datetime.time(13, 0)),
        datetime.datetime.combine(today, datetime.time(18, 0))
    ]
    
    scheduled_time = None
    for c in candidates:
        if c > now:
            scheduled_time = c
            break
            
    if not scheduled_time:
        tomorrow = today + datetime.timedelta(days=1)
        scheduled_time = datetime.datetime.combine(tomorrow, datetime.time(9, 0))
        
    return scheduled_time.isoformat() + "+09:00"

# =====================================================================
# 💰 [광고 & 마케팅] 구글 애드센스 및 주식 블로그용 CTA
# =====================================================================
ADSENSE_CODE = """
<div class="adsense-container" style="text-align:center; margin: 25px 0;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={CLIENT}" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="{CLIENT}" data-ad-slot="{SLOT}" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
""".replace("{CLIENT}", GOOGLE_ADSENSE_CLIENT).replace("{SLOT}", GOOGLE_ADSENSE_SLOT)

CTA_CODE = """
<div class="cta-box" style="border: 2px solid #3b82f6; padding: 20px; border-radius: 10px; background-color: #f8fafc; margin-top: 40px;">
    <p style="font-size: 15px; color: #1e293b; font-weight: bold; margin-bottom: 8px;">💡 투자 참고 유의사항</p>
    <p style="font-size: 13px; color: #64748b; line-height: 1.6; margin: 0;">
        본 콘텐츠는 구글 알리미 주식 투자 관련 뉴스를 기반으로 AI가 요약·편집한 정보성 글이며, 특정 종목에 대한 추천이나 투자 권유가 아닙니다. 모든 투자의 책임은 투자자 본인에게 있으므로 신중하게 결정하시기 바랍니다. <b>성공적인 투자를 응원합니다.</b>
    </p>
</div>
"""

# =====================================================================
# 🧠 [AI 프롬프트] 최신 google-genai 규격 맞춤형 주식 프롬프트 함수
# =====================================================================
def generate_blog_content(news_data):
    api_key_direct = os.environ.get("API_KEY")
    
    if not api_key_direct:
        print("⚠️ 경고: GEMINI_API_KEY 환경 변수가 비어있습니다. API_KEY 확인이 필요합니다.")
        
    # 유료 결제망 정식 통로 고정
    client = genai.Client(
        api_key=api_key_direct,
        http_options=types.HttpOptions(api_version="v1")
    )
    
    prompt = f"""
    아래 주식 투자 뉴스 데이터를 기반으로 블로그 포스팅용 글을 작성해줘.
    
    [뉴스 데이터]
    {news_data}
    
    [필수 작성 지침]
    1. 글의 구조는 철저히 마케팅 카피라이팅 기법인 PASONA 법칙(투자자들의 가려운 곳/불안 요소 자극 -> 공감 -> 시장 뉴스 분석을 통한 해결책 제시 -> 향후 투자 아이디어 제안)을 따르되, 본문에 '파소나'나 'PASONA'라는 단어는 절대 직접 언급하지 말고 아주 자연스러운 시황 분석 글처럼 풀어써줘.
    2. 형식은 가독성이 좋은 깔끔한 블로그 스타일로 작성해줘.
    3. 글 전체 분위기(예: 주식 차체, 불마켓, 재테크 등)와 어울리는 영문 이미지 검색 키워드를 [IMAGE_PROMPT]에 딱 2~3단어로만 짧게 추천해줘 (예: stock chart, trading desk).
    4. 이 글에 어울리는 검색용 주식 태그(라벨)를 3~5개 추출해줘. (쉼표로 구분, 예: 주식투자, 국내증시, 에코프로)
    5. 이 글의 핵심 시황을 150자 이내로 요약한 '검색 설명(Search Description)'을 작성해줘.
    
    [출력 포맷 고정]
    반드시 아래 형식을 정확히 지켜서 출력해줘:
    
    ---
    [TITLE]: 여기에 어울리는 매력적인 주식 제목 작성
    [TAGS]: 주식투자, 국내증시, 시황분석
    [DESCRIPTION]: 여기에 검색 설명 문장 작성
    [IMAGE_PROMPT]: stock market chart
    [BODY]:
    여기에 PASONA 구조를 적용한 주식 분석 본문 내용 작성
    ---
    """
    
    # ⚡ [수정 반영 완료] 기존 만료 대상이었던 'gemini-2.0-flash-001'을 무버전형 최신 표준 모델명인 'gemini-2.0-flash'로 변경했습니다.
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
    )
    return response.text

# =====================================================================
# 🛠️ [메인 엔진] 파싱 및 블로그 최종 발행
# =====================================================================
def main():
    b64_token = os.environ.get("TOKEN_PICKLE_BASE64")
    if not b64_token:
        print("❌ 에러: 깃허브 Secrets에 TOKEN_PICKLE_BASE64가 없습니다.")
        return
        
    creds = pickle.loads(base64.b64decode(b64_token))
    blogger = build('blogger', 'v3', credentials=creds)
    
    google_alerts_stock_news = fetch_google_alerts_news()
    ai_raw = generate_blog_content(google_alerts_stock_news)
    
    parsed = {'title': '', 'tags': ['주식투자', '재테크'], 'desc': '', 'img_prompt': 'stock market', 'body': ''}
    
    for line in ai_raw.split('\n'):
        if line.startswith('[TITLE]:'): parsed['title'] = line.replace('[TITLE]:', '').strip()
        elif line.startswith('[TAGS]:'): parsed['tags'] = [t.strip() for t in line.replace('[TAGS]:', '').split(',')]
        elif line.startswith('[DESCRIPTION]:'): parsed['desc'] = line.replace('[DESCRIPTION]:', '').strip()
        elif line.startswith('[IMAGE_PROMPT]:'): parsed['img_prompt'] = line.replace('[IMAGE_PROMPT]:', '').strip()
        
    if '[BODY]:' in ai_raw:
        body_start = ai_raw.find('[BODY]:') + 7
        parsed['body'] = ai_raw[body_start:].strip()
    else:
        parsed['body'] = ai_raw

    keyword = parsed.get('img_prompt', 'stock market')
    
    thumbnail_url = f"https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&auto=format&fit=crop"
    inline_image_url = f"https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&auto=format&fit=crop"
    
    formatted_body = parsed['body'].replace('\n', '<br>')
    
    html_top = f"""
    <div style="text-align:center; margin-bottom:20px;">
        <img src="{thumbnail_url}" alt="Stock Market Analysis" style="max-width:100%; height:auto; border-radius:8px;"/>
    </div>
    """
    
    html_mid = f"""
    <div class="post-body" style="font-size:16px; line-height:1.8; color:#1e293b;">
        {formatted_body}
    </div>
    <div style="text-align:center; margin:30px 0;">
        <img src="{inline_image_url}" alt="Stock Graph" style="max-width:100%; height:auto; border-radius:6px;"/>
    </div>
    """
    
    final_html = html_top + ADSENSE_CODE + html_mid + ADSENSE_CODE + CTA_CODE

    scheduled_publish_time = calculate_scheduled_time()
    
    data = {
        'title': parsed.get('title') if parsed.get('title') else '오늘의 주식 투자 시황 핵심 요약',
        'content': final_html,
        'labels': parsed.get('tags'),
        'published': scheduled_publish_time,
        'searchDescription': parsed.get('desc')
    }
    
    posts = blogger.posts()
    request = posts.insert(blogId=BLOG_ID, body=data, isDraft=False)
    result = request.execute()
    
    print(f"✅ 주식 블로그 알리미 기반 예약 발행 프로세스 성공 완료!")
    print(f"⏰ 예약 등록 타임 (KST): {scheduled_publish_time}")
    print(f"🔍 동기화된 검색 설명: {parsed.get('desc', '')}")

if __name__ == "__main__":
    main()
