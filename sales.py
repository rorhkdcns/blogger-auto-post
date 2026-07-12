import os
import json
import google.generativeai as genai
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# ==========================================
# [설정 영역] - Pipeline Scripts 블로그 ID 입력!
# ==========================================
BLOGGER_BLOG_ID = "7850510263929425541"  
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ [오류] GEMINI_API_KEY 환경변수가 설정되지 않았습니다!")

genai.configure(api_key=GEMINI_API_KEY.strip())
model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 1. Blogger API 서버리스 인증 함수 (마스터 토큰 공유)
# ==========================================
def get_blogger_service():
    SCOPES = ['https://www.googleapis.com/auth/blogger']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        raise FileNotFoundError("❌ [오류] token.json 파일이 없습니다.")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        else:
            raise Exception("❌ [오류] 토큰을 갱신할 수 없습니다.")
    return build('blogger', 'v3', credentials=creds)

# ==========================================
# 2. 🧠 B2B 콜드 메일 & 세일즈 아웃바운드 고단가 주제 발굴
# ==========================================
def get_single_topic():
    print("🧠 Pipeline Scripts용 고단가 B2B 세일즈 아웃바운드 주제를 1개 발굴합니다...")
    prompt = """
    You are an elite B2B Sales Director and Enterprise Outbound Consultant targeting US/Global SDRs, BDRs, Account Executives, and Sales Managers.
    Suggest EXACTLY ONE highly actionable B2B cold email sequence, LinkedIn prospecting script, or sales objection-handling framework.
    Focus on high-CPC enterprise sales niches (Apollo.io prospecting workflows, ZoomInfo data enrichment strategies, Salesforce CRM sales automation, Outreach/Salesloft sequences, C-Level Executive Cold Email Templates).
    
    Rules:
    1. Example topics: "5-Step B2B Cold Email Sequence for SaaS C-Level Executives (Apollo & Outreach Optimized)", "Enterprise LinkedIn Prospecting Script & Follow-Up Workflow for IT Buyers", "Handling 'Send Me More Info' Objections: Ready-to-Use B2B Sales Scripts".
    2. Output ONLY a plain text string of the title. Do not add quotes, markdown, or explanation.
    """
    try:
        response = model.generate_content(prompt, request_options={"timeout": 15})
        topic = response.text.strip().replace('"', '').replace("'", "")
        print(f"🎯 발굴 성공! 선정된 주제: {topic}")
        return topic
    except Exception as e:
        print(f"⚠️ 주제 발굴 지연/실패 ({e}) -> 기본 세일즈 주제 사용")
        return "5-Step B2B Cold Email Sequence for SaaS C-Level Executives using Apollo and ZoomInfo"

# ==========================================
# 3. 고수익 B2B 세일즈 스크립트 본문 생성
# ==========================================
def generate_sales_post(topic):
    prompt = f"""
    You are a VP of Sales and Outbound Growth Expert.
    Write a comprehensive, SEO-optimized B2B sales playbook and copy-paste script guide in professional English for: "{topic}".

    Follow these strict formatting and content rules:
    1. Output ONLY valid HTML code inside <article> ... </article> tags. Do not include markdown code blocks (like ```html), explanations, or conversational filler.
    2. Structure the HTML using <h2 style="color:#111827; border-bottom:2px solid #374151; padding-bottom:5px;">, <h3 style="color:#1f2937;">, <p style="line-height:1.6; color:#374151;">, <ul>, <li>, and <strong>.
    3. You MUST provide a 100% ready-to-use 'Copy & Paste' Cold Email / LinkedIn Script wrapped in a styled dark terminal-like box: <div style="background:#0f172a; color:#f8fafc; border:1px solid #334155; border-left:5px solid #10b981; padding:20px; margin:20px 0; font-family:'Courier New', monospace; white-space:pre-wrap; line-height:1.6;"> ... </div> with clear placeholders like [First Name], [Company Name], [Pain Point], [Competitor], and [Value Prop].
    4. Include a Pro-Tip notice box at the top: <div style="background:#ecfdf5; border:1px solid #6ee7b7; color:#065f46; padding:10px; font-size:0.9em; margin-bottom:15px;"><strong>Sales Pro-Tip:</strong> Personalize at least 20% of the first sentence using ZoomInfo or Apollo enrichment data to keep spam rates below 0.3%.</div>
    5. Naturally integrate extremely high-paying CPC keywords related to: "B2B sales intelligence platforms", "ZoomInfo enterprise pricing", "Apollo.io email automation", "Salesforce CRM pipeline management", and "outbound sales engagement software".
    6. Required Sections:
       - Outbound Strategy & Target Persona Breakdown
       - Step-by-Step Sequence Flow (Touchpoints 1 to 5)
       - Ready-to-Use Copy & Paste Scripts (Email Subjects & Body in Dark Box)
       - CRM & DB Automation Best Practices (ZoomInfo, Apollo, Salesforce integration)
       - Frequently Asked Questions on Deliverability & Reply Rates (3 FAQs)
    """
    try:
        response = model.generate_content(prompt, request_options={"timeout": 60})
        return response.text.replace("```html", "").replace("```", "").strip()
    except Exception as e:
        print(f"⚠️ 본문 생성 오류 ({e}) -> 기본 템플릿 대체")
        return f"<article><h1>B2B Sales Guide: {topic}</h1><p>Please utilize advanced B2B sales intelligence platforms like ZoomInfo and Apollo to optimize your outbound workflows.</p></article>"

# ==========================================
# 4. Blogger 실시간 발행 함수
# ==========================================
def publish_to_blogger(service, title, content, is_draft=False):
    body = {"title": title, "content": content}
    try:
        posts = service.posts()
        res = posts.insert(blogId=BLOGGER_BLOG_ID, body=body, isDraft=is_draft).execute()
        print(f"🚀 [Pipeline Scripts 실시간 발행 성공!] 글 제목: {title} (URL: {res.get('url')})")
    except Exception as e:
        print(f"❌ 발행 실패: {e}")

# ==========================================
# 5. 메인 실행부
# ==========================================
if __name__ == "__main__":
    print("⏰ [Pipeline Scripts] B2B 콜드 메일 & 세일즈 스크립트 자동 발행 로봇 가동!")
    service = get_blogger_service()
    
    topic = get_single_topic()
    print(f"\n📝 B2B 세일즈 아웃바운드 포스팅 작성 시작... 주제: {topic}")
    
    html_content = generate_sales_post(topic)
    publish_to_blogger(service, title=topic, content=html_content, is_draft=False)
        
    print("\n🎉 Pipeline Scripts 포스팅 완벽 종료!")
