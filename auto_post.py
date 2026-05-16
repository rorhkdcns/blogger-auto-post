import os
import pickle
import feedparser
import json
import base64
from google import genai
from google.genai import types
from googleapiclient.discovery import build

# 깃허브 금고(Secrets)에서 환경변수 안전하게 가져오기
API_KEY = os.environ.get('API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')
TOKEN_BASE64 = os.environ.get('TOKEN_PICKLE_BASE64')

# 수집할 구글 알리미 RSS 주소
RSS_URL = "https://www.google.co.kr/alerts/feeds/13793017153619247481/11360882853986229297"

# 실제 애드센스 광고 코드
ADSENSE_CODE = """
<div style="text-align:center; margin:20px 0;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4292478378917157" crossorigin="anonymous"></script>
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-4292478378917157"
         data-ad-slot="5317754949"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
"""

# 하단 인사이트 마무리 영역
CTA_SECTION = """
<div style="background:#f9f9f9; padding:25px; border-radius:10px; margin-top:30px; border:1px solid #eee; text-align:center;">
    <h3 style="color:#333; margin:0 0 10px 0;">💡 오늘의 투자 인사이트</h3>
    <p style="color:#666; line-height:1.6;">본문의 내용에 대해 궁금한 점이나 여러분의 소중한 의견이 있다면 <b>아래 댓글</b>로 자유롭게 남겨주세요!</p>
</div>
"""

# --- [안전한 토큰 복구 구간] ---
if not TOKEN_BASE64:
    raise ValueError("❌ GITHUB_SECRET에 TOKEN_PICKLE_BASE64 값이 누락되었습니다.")

# 혹시 모를 글자 공백 및 줄바꿈 기호 제거
TOKEN_BASE64 = TOKEN_BASE64.strip().replace("\n", "").replace("\r", "")

# 패딩 부족 시 (=) 기호 자동 보정 치트키 코드
missing_padding = len(TOKEN_BASE64) % 4
if missing_padding:
    TOKEN_BASE64 += '=' * (4 - missing_padding)

# 최종 복구 실행
token_data = base64.b64decode(TOKEN_BASE64)
creds = pickle.loads(token_data)
# ----------------------------------

# 최신 규격 Gemini 클라이언트 초기화
client = genai.Client(api_key=API_KEY)

def generate_seo_content(news_title, news_summary):
    prompt = f"""
    당신은 주식 전문 칼럼니스트입니다. 아래 뉴스를 바탕으로 블로그 글을 작성하되, 반드시 JSON 형식으로 응답하세요.
    제목: {news_title} / 요약: {news_summary}
    [JSON 형식]
    {{
        "blog_title": "제목",
        "blog_content": "HTML 본문 ([AD_SLOT] 포함)",
        "search_description": "요약 문구",
        "labels": ["주식투자", "경제이슈"]
    }}
    """
    try:
        response = client.models.generate_content(
         model="gemini-1.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ Gemini 생성 오류: {e}")
        return None

def run_auto_post():
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries: 
            print("새 소식 없음")
            return
        entry = feed.entries[0]

        print("🤖 깨끗한 깃허브 클라우드에서 수익형 글 생성 중...")
        seo_data = generate_seo_content(entry.title, entry.summary)
        if not seo_data: return

        final_html = seo_data['blog_content'].replace("[AD_SLOT]", ADSENSE_CODE) + CTA_SECTION

        service = build('blogger', 'v3', credentials=creds)
        
        body = {
            'title': seo_data['blog_title'],
            'content': final_html,
            'labels': seo_data['labels'],
            'customMetaData': seo_data['search_description']
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body).execute()
        print(f"✅ 깃허브 자동 포스팅 성공: {seo_data['blog_title']}")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    run_auto_post()
