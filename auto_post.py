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

# ⏰ [여기가 바뀐 부분입니다!] 9시, 13시, 16시, 20시로 예약 시간 변경 완료
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
    
    # ⚡ [제목 후킹 업그레이드] 실전 조회수 폭발을 위한 강력한 제목 생성 지침 주입
    prompt = (
        "아래 주식 투자 뉴스 데이터를 기반으로 블로그 포스팅용 전문 시황 분석 글을 작성해줘.\n\n"
        f"[뉴스 데이터]\n{news_data}\n\n"
        "[필수 작성 지침 - 제목 및 본문 고도화]\n"
        "1. [★가장 중요 - 제목 법칙★]: 글 제목은 반드시 다음 2가지 법칙을 조합하여 자극적이고 검색량이 많은 형태로 작성해라.\n"
        "   - 법칙 A (실전 SEO 키워드): 사람들이 매일 검색창에 검색하는 단어 (예: 삼성전자, 코스피 시황, 외국인 매도, 미국 증시, 주식 투자 전략 등 뉴스에 해당되는 실제 고유명사 필수 포함)\n"
        "   - 법칙 B (숫자 및 손실공포 후킹): 인간의 심리를 자극하는 강렬한 마케팅 문구 (예: ~폭탄 충격, 안 보면 폭망, 딱 3 가지만 체크, 이대로 괜찮을까? 등)\n"
        "   - 제목 예시: '외국인 매도 폭탄 충격! 삼성전자 4만 원대 붕괴 위기 속 살아남을 투자 전략' 또는 '코스피 함정 탈출법! 2030 대출 연체율 급증 속 무조건 체크할 자산 배분법'\n"
        "2. 마케팅 카피라이팅 기법인 PASONA 법칙을 적용하여 자연스럽게 풀어써줘. 단, 파소나, AI, 인공지능 단어는 절대 언급 금지.\n"
        "3. 모바일 화면 최적화를 위해 한 문장이 끝날 때마다 줄바꿈을 하고, 2-3문장마다 공백 라인을 두어라. 본문에 특수 기호나 대괄호를 섞지 마라.\n"
        "4. 본문 내용 중 가장 핵심이 되는 주식 용어, 주요 종목명, 시장 방향성 키워드를 선정하여 반드시 구글 블로그 표준 태그 양식인 <b><font color=\"#e11d48\">중요키워드</font></b> 양식으로 감싸라. 단락당 2~3개 정도가 적당하다. 스팬(span)이나 스타일 태그는 절대 사용 금지.\n"
        "5. 본문은 반드시 3개의 파트로 나누고 소제목을 추출해줘.\n"
        "6. 영문 이미지 검색 키워드를 IMAGE_PROMPT에 딱 2-3단어 명사로 짧게 추천해줘.\n"
        "7. 검색용 주식 태그를 3-5개 추출해줘. (쉼표 구분)\n\n"
        "[출력 포맷 고정]\n"
        "[TITLE]: 2대 법칙을 적용하여 자극적으로 낚는 실전 주식 제목\n"
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
    tags_raw = re_extract_line('TAGS', ai_raw, "주식투자, 재테크, 국내증시")
    img_prompt = re_extract_line('IMAGE_PROMPT', ai_raw, "STOCK MARKET").upper()
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

    body1 = extract_block(ai_raw, '[BODY_1]:', '[SUB_TITLE_2]')
    body2 = extract_block(ai_raw, '[BODY_2]:', '[SUB_TITLE_3]')
    body3 = extract_block(ai_raw, '[BODY_3]:')

    if not body1:
        body1 = ai_raw
    
    def clean_html_garbage(text):
        text = text.replace('`', '').replace('**', '').replace('__', '')
        text = text.replace('<span>', '').replace('</span>', '')
        text = re.sub(r'<\s*span[^>]*>', '', text) 
        text = re.sub(r'\[.*?\]\s*:\s*', '', text)
        return text.strip()

    body1 = clean_html_garbage(body1)
    body2 = clean_html_garbage(body2)
    body3 = clean_html_garbage(body3)
    sub1 = clean_html_garbage(sub1)
    sub2 = clean_html_garbage(sub2)
    sub3 = clean_html_garbage(sub3)

    tags = [t.strip() for t in tags_raw.replace('`','').replace('**','').split(',') if t.strip()]
    if not tags:
        tags = ['주식투자', '재테크', '국내증시']

    keyword = img_prompt if img_prompt else 'STOCK MARKET'
    encoded_text = urllib.parse.quote(f"FINANCE ANALYSIS: {keyword}")
    
    thumbnail_url = f"https://placehold.co/800x450/1e3a8a/ffffff/png?text={encoded_text}&font=playfair"
    inline_image_url = f"https://placehold.co/800x450/0f172a/38bdf8/png?text=FINANCE+INVESTMENT+RETAIL&font=roboto"
    
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

    post_data = {
        'title': title,
        'content': final_html,
        'labels': tags,
        'published': scheduled_publish_time
    }
    
    print(f"📡 [디버그] 전송 준비 완료 - 블로그 ID: {BLOG_ID}")
    print(f"📡 [디버그] 후킹 완성된 제목: {title}")
    print(f"📡 [디버그] 설정된 예약 발행 시간 (KST): {scheduled_publish_time}")
    print("📝 무결성 클린 레이아웃 기반 블로그 업로드 API 요청 전송 중...")
    
    try:
        posts_service = blogger.posts()
        request = posts_service.insert(blogId=BLOG_ID, body=post_data, isDraft=False)
        print("📡 [디버그] 구글 API 엔드포인트 커넥션 성공. 데이터 패킷 동기화 실행...")
        
        created_post = request.execute()
        
        print(f"✅ [안정화 본딩 성공] 구글 블로거에 글이 완벽하게 등록되었습니다!")
        print(f"🔗 최종 연동된 포스트 제목: {created_post.get('title')}")
    except Exception as api_err:
        print(f"❌ [네트워크/API 에러 발생]: 구글 서버가 전송을 거부했거나 오류를 반환했습니다. 원인: {api_err}")

if __name__ == "__main__":
    main()
