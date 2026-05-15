import os
import pickle
import feedparser
import json
import base64
from google import genai
from google.genai import types
from googleapiclient.discovery import build

API_KEY = os.environ.get('API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')
TOKEN_BASE64 = os.environ.get('TOKEN_PICKLE_BASE64')
RSS_URL = "https://www.google.co.kr/alerts/feeds/13793017153619247481/11360882853986229297"

ADSENSE_CODE = '''<div style="text-align:center; margin:20px 0;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4292478378917157" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-4292478378917157" data-ad-slot="5317754949" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>'''

CTA_SECTION = '''<div style="background:#f9f9f9; padding:25px; border-radius:10px; margin-top:30px; border:1px solid #eee; text-align:center;">
    <h3 style="color:#333; margin:0 0 10px 0;">💡 오늘의 투자 인사이트</h3>
    <p style="color:#666; line-height:1.6;">본문의 내용에 대해 궁금한 점이나 여러분의 소중한 의견이 있다면 <b>아래 댓글</b>로 자유롭게 남겨주세요!</p>
</div>'''

creds = pickle.loads(base64.b64decode(TOKEN_BASE64))
client = genai.Client(api_key=API_KEY)

def generate_seo_content(news_title, news_summary):
    prompt = f"당신은 주식 전문 칼럼니스트입니다. 아래 뉴스를 바탕으로 블로그 글을 작성하되, 반드시 JSON 형식으로 응답하세요. 제목: {news_title} / 요약: {news_summary}"
    try:
        response = client.models.generate_content(model="models/gemini-1.5-flash", contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json"))
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini 에러: {e}"); return None

def run_auto_post():
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries: return
        entry = feed.entries[0]
        seo_data = generate_seo_content(entry.title, entry.summary)
        if not seo_data: return
        final_html = seo_data['blog_content'].replace("[AD_SLOT]", ADSENSE_CODE) + CTA_SECTION
        service = build('blogger', 'v3', credentials=creds)
        body = {'title': seo_data['blog_title'], 'content': final_html, 'labels': seo_data['labels'], 'customMetaData': seo_data['search_description']}
        service.posts().insert(blogId=BLOG_ID, body=body).execute()
        print("✅ 포스팅 성공")
    except Exception as e: print(f"에러: {e}")

if __name__ == "__main__":
    run_auto_post()
