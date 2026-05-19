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

# =====================================================================
# 💰 [광고 & 마케팅] 구글 애드센스 및 주식 블로그용 CTA (AI 단어 제거)
# =====================================================================
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

# =====================================================================
# 🧠 [AI 프롬프트] 소제목 분할형 고급 블로그 프롬프트
# =====================================================================
def generate_blog_content(news_data):
    api_key_direct = os.environ.get("API_KEY")
    if not api_key_direct:
        print("⚠️ 경고: GEMINI_API_KEY 환경 변수가 비어있습니다.")
        
    client = genai.Client(
        api_key=api_key_direct,
        http_options=types.HttpOptions(api_version="v1")
    )
    
    prompt = f"""
    아래 주식 투자 뉴스 데이터를 기반으로 블로그 포스팅용 전문 시황 분석 글을 작성해줘.
    
    [뉴스 데이터]
    {news_data}
    
    [필수 작성 지침]
    1. 마케팅 카피라이팅 기법인 PASONA 법칙을 적용하여 독자가 공감하고 몰입할 수 있도록 자연스럽게 풀어써줘. ('파소나', 'AI', '인공지능' 단어는 절대 본문에 언급 금지)
    2. 본문은 반드시 3개의 명확한 문단으로 나누고, 각 문단 시작 전에는 해당 파트의 핵심 내용을 관통하는 '소제목'을 양식에 맞춰 작성해줘.
    3. 글 전체의 분위기와 매칭되는 영문 이미지 검색 키워드를 [IMAGE_PROMPT]에 딱 2~3단어의 명사 형태로만 짧게 추천해줘 (예: stock chart, economy trend).
    4. 이 글에 어울리는 검색용 주식 태그(라벨)를 3~5개 추출해줘. (쉼표로 구분, 예: 주식투자, 국내증시, 시황분석)
    5. 이 글의 핵심 내용을 130자 내외의 완성된 문장으로 요약한 '검색 설명(Search Description)'을 [DESCRIPTION] 뒤에 정확히 작성해줘. (누락 절대 금지)
    
    [출력 포맷 고정 - 형식을 절대 깨뜨리지 마세요]
    [TITLE]: 여기에 매력적이고 직관적인 주식 제목 작성
    [TAGS]: 주식투자, 국내증시, 시황분석
    [DESCRIPTION]: 여기에 본문 핵심 요약 1문장 작성 (130자 내외)
    [IMAGE_PROMPT]: stock market index
    [SUB_TITLE_1]: 첫 번째 소제목 작성 (예: 📉 변동성 확대되는 시장, 현재 상황은?)
    [BODY_1]: 첫 번째 단락 내용 (시장 문제 제기 및 투자자 공감대 형성)
    [SUB_TITLE_2]: 두 번째 소제목 작성 (예: 📊 주요 뉴스 분석과 핵심 지표 체크)
    [BODY_2]: 두 번째 단락 내용 (제공된 뉴스 데이터를 바탕으로 한 구체적인 분석)
    [SUB_TITLE_3]: 세 번째 소제목 작성 (예: 💡 향후 투자 전략 및 주목해야 할 포인트)
    [BODY_3]: 세 번째 단락 내용 (결론 및 앞으로의 대응 방안, 투자 아이디어 제안)
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text

# =====================================================================
# 🛠️ [메인 엔진] 문단 파싱 및 애드센스/이미지 교차 배치 조립
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
    
    # 딕셔너리 초기화
    parsed = {
        'title': '', 'tags': ['주식투자', '재테크'], 'desc': '', 
        'sub1': '', 'body1': '', 'sub2': '', 'body2': '', 'sub3': '', 'body3': ''
    }
    
    # AI 출력을 라인별로 정밀 분석하여 매칭
    for line in ai_raw.split('\n'):
        line_str = line.strip()
        if line_str.startswith('[TITLE]:'): parsed['title'] = line_str.replace('[TITLE]:', '').strip()
        elif line_str.startswith('[TAGS]:'): parsed['tags'] = [t.strip() for t in line_str.replace('[TAGS]:', '').split(',')]
        elif line_str.startswith('[DESCRIPTION]:'): parsed['desc'] = line_str.replace('[DESCRIPTION]:', '').strip()
        elif line_str.startswith('[SUB_TITLE_1]:'): parsed['sub1'] = line_str.replace('[SUB_TITLE_1]:', '').strip()
        elif line_str.startswith('[SUB_TITLE_2]:'): parsed['sub2'] = line_str.replace('[SUB_TITLE_2]:', '').strip()
        elif line_str.startswith('[SUB_TITLE_3]:'): parsed['sub3'] = line_str.replace('[SUB_TITLE_3]:', '').strip()
        
    # BODY 부분 블록 추출 정교화
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

    parsed['body1'] = extract_block(ai_raw, '[BODY_1]:', '[SUB_TITLE_2]')
    parsed['body2'] = extract_block(ai_raw, '[BODY_2]:', '[SUB_TITLE_3]')
    parsed['body3'] = extract_block(ai_raw, '[BODY_3]:')

    # 만약 정밀 파싱 실패 시 예외 처리 코드
    if not parsed['body1']:
        parsed['body1'] = ai_raw
        parsed['sub1'] = "📈 오늘 시장 핵심 경제 시황"

    # 고품질 이미지 에셋 (Unsplash 이미지 연동)
    thumbnail_url = "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&auto=format&fit=crop"
    inline_image_url = "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&auto=format&fit=crop"
    
    # 엔터값을 HTML 줄바꿈 태그로 치환
    b1_html = parsed['body1'].replace('\n', '<br>')
    b2_html = parsed['body2'].replace('\n', '<br>')
    b3_html = parsed['body3'].replace('\n', '<br>')

    # 🧱 [블로그 본문 HTML 구조 고도화 레이아웃 조립]
    final_html = f"""
    <!-- 1. 상단 타이틀 섬네일 -->
    <div style="text-align:center; margin-bottom:30px;">
        <img src="{thumbnail_url}" alt="Market Stock Analysis" style="max-width:100%; height:auto; border-radius:8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);"/>
    </div>
    
    <!-- 2. 단락 1 -->
    <h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 30px; margin-bottom: 15px;">{parsed['sub1']}</h3>
    <div class="post-p1" style="font-size:16px; line-height:1.8; color:#334155; margin-bottom: 25px;">
        {b1_html}
    </div>
    
    <!-- 3. 중간 애드센스 광고 배치 1 -->
    {ADSENSE_CODE}
    
    <!-- 4. 단락 2 -->
    <h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 30px; margin-bottom: 15px;">{parsed['sub2']}</h3>
    <div class="post-p2" style="font-size:16px; line-height:1.8; color:#334155; margin-bottom: 25px;">
        {b2_html}
    </div>
    
    <!-- 5. 중간 흐름 환기용 본문 이미지 배치 -->
    <div style="text-align:center; margin: 30px 0;">
        <img src="{inline_image_url}" alt="Financial Investment Trend" style="max-width:100%; height:auto; border-radius:6px;"/>
    </div>
    
    <!-- 6. 단락 3 -->
    <h3 style="font-size: 20px; color: #1e3a8a; border-left: 5px solid #3b82f6; padding-left: 10px; margin-top: 30px; margin-bottom: 15px;">{parsed['sub3']}</h3>
    <div class="post-p3" style="font-size:16px; line-height:1.8; color:#334155; margin-bottom: 25px;">
        {b3_html}
    </div>
    
    <!-- 7. 하단 애드센스 광고 배치 2 -->
    {ADSENSE_CODE}
    
    <!-- 8. 최종 면책 조항 안내 박스 (AI 단어 전면 제거) -->
    {CTA_CODE}
    """

    scheduled_publish_time = calculate_scheduled_time()
    
    # 포스팅 최종 업로드 데이터 매핑
    data = {
        'title': parsed['title'] if parsed['title'] else '오늘의 주식 투자 시황 핵심 분석 요약',
        'content': final_html,
        'labels': parsed['tags'],
        'published': scheduled_publish_time,
        'searchDescription': parsed['desc'] if parsed['desc'] else '국내외 증시 시황 및 주식 시장 핵심 변동성 지표를 분석하여 향후 대응 전략과 합리적인 투자 아이디어를 공유합니다.'
    }
    
    posts = blogger.posts()
    request = posts.insert(blogId=BLOG_ID, body=data, isDraft=False)
    result = request.execute()
    
    print(f"✅ 주식 블로그 포스팅 최종 예약 발행 프로세스 성공!")
    print(f"⏰ 발행 시간 (KST): {scheduled_publish_time}")
    print(f"🔍 등록된 검색 설명: {data['searchDescription']}")

if __name__ == "__main__":
    main()
