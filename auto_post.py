import os
import pickle
import feedparser
import json
import base64
from google import genai
from google.genai import types
from googleapiclient.discovery import build

# 환경 변수로부터 안전하게 값 로드
API_KEY = os.environ.get('API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')
TOKEN_BASE64 = os.environ.get('TOKEN_PICKLE_BASE64')
RSS_URL = "https://www.google.co.kr/alerts/feeds/13793017153619247481/11360882853986229297"

# 구글 애드센스 HTML 구조화
ADSENSE_CODE = '''<div style="text-align:center; margin:20px 0;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4292478378917157" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-4292478378917157" data-ad-slot="5317754949" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>'''

CTA_SECTION = '''<div style="background:#f9f9f9; padding:25px; border-radius:10px; margin-top:30px; border:1px solid #eee; text-align:center;">
    <h3 style="color:#333; margin:0 0 10px 0;">💡 오늘의 투자 인사이트</h3>
    <p style="color:#666; line-height:1.6;">본문의 내용에 대해 궁금한 점이나 여러분의 소중한 의견이 있다면 <b>아래 댓글</b>로 자유롭게 남겨주세요!</p>
</div>'''

# Base64로 암호화되어 보관 중인 Blogger 인증 토큰을 바이너리로 복원 및 로드
# 줄바꿈 및 공백 에러 방지 처리 추가
TOKEN_BASE64 = TOKEN_BASE64.strip().replace("\n", "").replace("\r", "")
missing_padding = len(TOKEN_BASE64) % 4
if missing_padding:
    TOKEN_BASE64 += '=' * (4 - missing_padding)

creds = pickle.loads(base64.b64decode(TOKEN_BASE64))
client = genai.Client(api_key=API_KEY)

def generate_seo_content(news_title, news_summary):
    prompt = f"""
    당신은 주식 전문 최고의 칼럼니스트입니다. 아래 제공된 뉴스의 제목과 요약을 바탕으로 블로그 글을 새로 작성해 주세요.
    원문을 그대로 복사하지 말고 당신의 언어로 완전히 재구성해야 합니다.
    
    [입력 데이터]
    - 제목: {news_title}
    - 요약: {news_summary}
    
    [요구사항]
    - blog_content 작성 시, 본문 중간에 구글 애드센스가 삽입될 위치를 지정하기 위해 반드시 문자열 '[AD_SLOT]'을 포함해 주세요.
    - 본문 내용은 가독성을 위해 <p>, <h3>, <ul> 등의 HTML 태그를 적절히 섞어 구조화해 주세요.
    """
    
    try:
        # 모델 엔드포인트 경로 수정 및 JSON 데이터 파싱 에러 방지를 위한 스키마 강제 정의
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt, 
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "blog_title": {"type": "STRING"},
                        "blog_content": {"type": "STRING"},
                        "search_description": {"type": "STRING"},
                        "labels": {"type": "ARRAY", "items": {"type": "STRING"}}
                    },
                    "required": ["blog_title", "blog_content", "search_description", "labels"]
                },
                temperature=0.7
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ Gemini AI 연동 에러: {e}")
        return None

def run_auto_post():
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            print("📅 새로운 알리미 뉴스가 없습니다.")
            return
            
        entry = feed.entries[0]
        print(f"📰 타겟 뉴스 수집 성공: {entry.title}")
        
        seo_data = generate_seo_content(entry.title, entry.summary)
        if not seo_data: 
            return
            
        # 광고 코드 및 하단 배너 결합
        final_html = seo_data['blog_content'].replace("[AD_SLOT]", ADSENSE_CODE) + CTA_SECTION
        
        # 블로그스팟 빌드 및 포스팅 API 호출
        service = build('blogger', 'v3', credentials=creds)
        body = {
            'title': seo_data['blog_title'], 
            'content': final_html, 
            'labels': seo_data['labels'], 
            'customMetaData': seo_data['search_description']
        }
        
        service.posts().insert(blogId=BLOG_ID, body=body).execute()
        print(f"✅ 블로그 자동 포스팅 발행 성공 완료: {seo_data['blog_title']}")
        
    except Exception as e: 
        print(f"❌ 포스팅 가공 및 업로드 중 치명적 에러 발생: {e}")

if __name__ == "__main__":
    run_auto_post()
