import base64
import datetime
import html
import json
import os
import pickle
import random
import re
import subprocess
import sys
import time
import urllib.parse
import warnings

# [추가] 보기 싫은 구글 API 파이썬 버전 경고문 강제 차단
warnings.filterwarnings("ignore", category=FutureWarning)

# [1단계] 라이브러리 자동 설치 및 검증
required_modules = [
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

from googleapiclient.discovery import build
from google import genai
from google.genai import types

# =====================================================================
# ⚙️ 고유 설정 정보
# =====================================================================
BLOG_ID = "347204372769511011"
GOOGLE_ADSENSE_CLIENT = "ca-pub-4292478378917157"
GOOGLE_ADSENSE_SLOT = "5317754949"

# [수정] 하루 최대 발행 수 (기존 2 → 1)
MAX_POSTS_PER_DAY = 1

# [수정] 글당 라벨 최대 개수 (기존 5~6개 → 2개)
MAX_LABELS = 2

STOCK_INFO_KEYWORDS = [
    "주식초보", "주린이 첫걸음", "주식투자 시작하기", "주식 계좌 개설 방법", "증권사 추천",
    "주식 거래 시간", "시간외 단일가 매매", "주식 용어 정리", "예수금 뜻", "미수금 위험성",
    "증거금 100%", "신용융자", "D+2 예수금", "주식 매수 매도", "호가창 보는 법",
    "지정가 주문", "시장가 주문", "조건부 지정가", "최유리 지정가", "LOC 주문",
    "VWAP 매매", "주식 수수료 비교", "유관기관 제비용", "세금 거래세", "양도소득세 기준",
    "배당소득세율", "종합소득세 주식", "금융투자소득세 금투세", "ISA 계좌 장점", "비과세 만능통장",
    "연금저축펀드 주식", "주식 차트 보는 법", "봉차트 양봉 음봉", "이동평균선 정배열", "이평선 역배열",
    "골든크로스 매수", "데드크로스 매도", "거래량의 비밀", "지지선과 저항선", "추세선 그리기",
    "MACD 보조지표", "RSI 과매수 과매도", "스토캐스틱 활용", "볼린저밴드 매매법", "일목균형표 기초",
    "재무제표 보는 법", "시가총액 순위", "매출액 영업이익", "당기순이익 뜻", "EPS 주당순이익",
    "PER 주가수익비율", "PBR 주가순자산비율", "ROE 자기자본이익률", "EV/EBITDA", "부채비율 적정선",
    "유동비율이란", "배당 성향", "배당수익률 높은 주식", "고배당주 추천", "배당금 지급일 확인",
    "배당락일 매수", "분기배당 주식", "월배당 ETF", "미국주식 시작하기", "소수점 투자",
    "환전 수수료 우대", "환율 주가 관계", "미국 증시 개장시간", "서학개미 인기주식", "양도세 절세 팁",
    "W-8BEN 작성", "애프터마켓 거래", "프리마켓 시간", "S&P500 지수", "나스닥 100",
    "다우존스 지수", "러셀2000", "ETF 투자 방법", "레버리지 ETF 위험성", "인버스 ETF 곱버스",
    "ETN 차이점", "자산배분 전략", "올웨더 포트폴리오", "바벨 전략", "분할매수 분할매도",
    "적립식 투자 장점", "물타기 불타기", "손절매 기준", "익절 타이밍", "가치투자 대가",
    "워런 버핏 명언", "피터 린치 성장주", "모멘텀 투자", "퀀트 투자 기초", "주식 리포트 읽는 법",
    "공시 확인 방법", "DART 전자공시", "유상증자 주가 호재 악재", "무상증자 권리락", "전환사채 CB",
    "신주인수권부사채 BW", "주식분할 액면분할", "액면병합 효과", "자사주 매입 소각", "내부자 거래 지분",
    "대주주 매도", "공매도 숏커버링", "숏스퀴즈 뜻", "신규상장 IPO", "따따블 기준",
    "공모주 청약 방법", "균등배정 비례배정", "의무보유확약 기관", "주총 참석 방법", "전자투표 권리 행사",
    "테마주 매매 리스크", "정치테마주 현실", "세력주 작전주 구별", "뇌동매매 고치기", "포모(FOMO) 증후군",
    "주식 일지 작성", "투자 원칙 세우기", "거시경제 지표", "금리와 주가 관계", "인플레이션 수혜주",
    "스태그플레이션 자산", "Fed 연준 금리인하", "FOMC 일정", "CPI 소비자물가지수", "고용지표 발표",
    "환율 상승 수혜주", "유가 상승 관련주", "경기방어주 종류", "경기민감주 사이클", "주도주 찾는 법",
    "대형주 중소형주 차이", "우선주 보통주 차이", "괴리율이란", "주식 리스크 관리", "복리 효과 계산",
    "주식 책 추천", "주식 유튜브 채널 추천", "가상계좌 모의투자"
]

GITHUB_USER_ID = "rorhkdcns"
GITHUB_REPO_NAME = "blogger-auto-post"
GITHUB_IMAGE_BASE_URL = "https://raw.githubusercontent.com/rorhkdcns/blogger-auto-post/main/blog_images/stock/"

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

# [수정] 제목에 들어가면 안 되는 과장/수익보장 표현
BANNED_TITLE_WORDS = [
    "수익 극대화", "수익률 극대화", "극대화", "비법", "완벽 분석", "완벽 마스터",
    "완벽 정리", "완벽 이해", "필승", "치명적", "2배", "경제적 자유",
    "무조건", "보장", "대박", "폭등", "급등주", "반드시 알아야"
]

ADSENSE_CODE = """
<div class="adsense-container" style="text-align:center; margin: 30px 0;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={CLIENT}" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="{CLIENT}" data-ad-slot="{SLOT}" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
""".replace("{CLIENT}", GOOGLE_ADSENSE_CLIENT).replace("{SLOT}", GOOGLE_ADSENSE_SLOT)

# [신규] 면책 문구 박스 — 모든 글 하단에 자동 삽입
DISCLAIMER_CODE = """
<div class="disclaimer-box" style="border:1px solid #e2e8f0; background:#f8fafc; border-radius:10px; padding:18px 20px; margin-top:35px;">
    <p style="margin:0 0 8px 0; font-size:15px; font-weight:700; color:#475569;">투자 유의사항</p>
    <p style="margin:0; font-size:15px; color:#64748b; line-height:1.7;">
        이 글은 공개된 자료를 정리한 정보 제공용이며, 특정 종목의 매매를 권유하거나 투자를 자문하지 않습니다.
        투자 판단과 그에 따른 책임은 투자자 본인에게 있습니다.
        게재된 정보는 작성 시점 기준이며 이후 제도나 수치가 변경될 수 있으므로,
        실제 거래 전에는 반드시 거래 증권사와 금융감독원 전자공시시스템(DART) 등에서 최신 내용을 확인하시기 바랍니다.
    </p>
</div>
"""

CTA_CODE = """
<div class="cta-box" style="border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; background-color: #f8fafc; margin-top: 40px; text-align: center;">
    <p style="font-size: 17px; color: #334155; font-weight: 700; margin-bottom: 8px; display: inline-block; background: #e2e8f0; padding: 4px 12px; border-radius: 6px;">참고 자료 안내</p>
    <p style="font-size: 16px; color: #475569; line-height: 1.7; margin: 0 0 15px 0; font-weight: 500;">
        본문에 배치된 <b>[주식 계산기 모음판]</b>에서 평단가와 목표 수익률을 직접 계산해 볼 수 있습니다.
    </p>
    <a href="#calc-board-top" style="display: inline-block; background: #334155; color: white; font-weight: bold; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 16px; transition: background 0.2s;">계산기로 이동하기</a>
</div>
"""

CALCULATOR_BOARD_CODE = f"""
<div id="calc-board-top" class="calc-board-container" style="margin: 35px 0; padding: 20px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
    <p style="margin: 0 0 15px 0; font-size: 17px; font-weight: 700; color: #1e293b; text-align: left; border-left: 4px solid #475569; padding-left: 8px;">주식 계산기 모음판</p>
    <div class="calc-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
        <a href="{URL_물타기}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 16px; font-weight: 700; color: #1e40af;">주식 물타기 계산기</span>
        </a>
        <a href="{URL_손절익절}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 16px; font-weight: 700; color: #0f766e;">익절/손절 기준 계산기</span>
        </a>
        <a href="{URL_복리}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 16px; font-weight: 700; color: #4338ca;">연복리 자산 시뮬레이터</span>
        </a>
        <a href="{URL_환율}" target="_blank" style="display: block; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px; text-align: center; text-decoration: none;">
            <span style="display: block; font-size: 16px; font-weight: 700; color: #334155;">미국주식 환율 계산</span>
        </a>
    </div>
</div>
"""

# =====================================================================
# 🛠️ 보조 함수들
# =====================================================================
def get_image_tag(alt_text=""):
    safe_alt = html.escape(alt_text or "주식 투자 관련 이미지")
    return (
        f'<div style="text-align:center; margin:25px 0;">'
        f'<img src="{GITHUB_IMAGE_BASE_URL}{random.choice(github_images_pool)}" '
        f'alt="{safe_alt}" loading="lazy" style="max-width:100%; border-radius:8px;"/>'
        f'</div>'
    )

def format_paragraphs(text):
    if not text or not text.strip(): return ""

    # 마크다운 볼드체(**)를 HTML 강조 태그로 안전 변환
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color:#2563eb;">\1</strong>', text)

    processed_chunks = []
    in_table = False
    table_html = []
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        if line.startswith('|') and line.endswith('|'):
            if not in_table:
                in_table = True
                table_html = ['<div style="overflow-x:auto; margin: 20px 0;"><table style="width:100%; border-collapse:collapse; border:1px solid #cbd5e1;">']
            if not re.match(r'^\|(?:[\s\-:]+\|)+$', line):
                tds = ''.join([f'<td style="border:1px solid #cbd5e1; padding:10px; font-size:16px;">{c.strip()}</td>' for c in line.split('|')[1:-1]])
                table_html.append(f'<tr>{tds}</tr>')
        else:
            if in_table:
                in_table = False
                table_html.append('</table></div>')
                processed_chunks.append("".join(table_html))
                table_html = []
            processed_chunks.append(f'<p style="margin-bottom:20px; line-height:1.7; font-size:17px; color:#334155;">{line}</p>')
    if in_table:
        table_html.append('</table></div>')
        processed_chunks.append("".join(table_html))
    return "".join(processed_chunks)

# 목차(TOC) 박스 생성
def build_toc_html(sub1, sub2, sub3):
    return f'''
<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:20px 24px; margin:25px 0;">
    <p style="font-weight:700; font-size:17px; color:#1e293b; margin:0 0 12px 0;">목차</p>
    <ul style="margin:0; padding-left:20px; font-size:16px; color:#334155; line-height:2;">
        <li><a href="#sec1" style="color:#2563eb; text-decoration:none;">{sub1}</a></li>
        <li><a href="#sec2" style="color:#2563eb; text-decoration:none;">{sub2}</a></li>
        <li><a href="#sec3" style="color:#2563eb; text-decoration:none;">{sub3}</a></li>
        <li><a href="#faq" style="color:#2563eb; text-decoration:none;">자주 묻는 질문</a></li>
        <li><a href="#conclusion" style="color:#2563eb; text-decoration:none;">정리</a></li>
    </ul>
</div>
'''

# 섹션별 요약 박스
def make_section_summary(text):
    if not text or not text.strip(): return ""
    return f'''
<div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:14px 18px; margin:15px 0 30px 0;">
    <p style="margin:0; font-size:16px; color:#1e3a8a; font-weight:700;">요약</p>
    <p style="margin:6px 0 0 0; font-size:16px; color:#334155; line-height:1.6;">{text}</p>
</div>
'''

# FAQ 섹션
def build_faq_html(faq_list):
    if not faq_list: return ""
    items = ""
    for item in faq_list:
        q = (item.get("question") or "").strip()
        a = (item.get("answer") or "").strip()
        if not q or not a: continue
        items += f'''
        <div style="margin-bottom:18px;">
            <p style="font-weight:700; font-size:17px; color:#1e293b; margin:0 0 6px 0;">Q. {q}</p>
            <p style="font-size:16px; color:#475569; line-height:1.7; margin:0;">A. {a}</p>
        </div>'''
    if not items: return ""
    return f'''
<h2 id="faq" style="border-left:5px solid #3b82f6; padding-left:10px; margin-top:45px; font-size:21px;">자주 묻는 질문</h2>
<div style="margin-top:20px;">{items}</div>
'''

# 결론 섹션
def build_conclusion_html(conclusion_text):
    if not conclusion_text or not conclusion_text.strip(): return ""
    return f'<h2 id="conclusion" style="border-left:5px solid #3b82f6; padding-left:10px; margin-top:45px; font-size:21px;">정리</h2>{format_paragraphs(conclusion_text)}'


# =====================================================================
# [수정] 중복 방지 강화 — 최근 30개가 아니라 전체 글 제목을 대조
# =====================================================================
def fetch_all_post_titles(blogger, blog_id):
    """페이지네이션으로 블로그의 모든 글 제목을 가져온다."""
    titles = []
    page_token = None
    try:
        while True:
            params = {
                'blogId': blog_id,
                'maxResults': 500,
                'fetchBodies': False,
                'fields': 'items(title),nextPageToken'
            }
            if page_token:
                params['pageToken'] = page_token
            res = blogger.posts().list(**params).execute()
            for item in res.get('items', []):
                titles.append(re.sub(r'\s+', '', item.get('title', '')))
            page_token = res.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        print(f"⚠️ 기존 글 목록 조회 중 오류(계속 진행): {e}")
    print(f"📚 기존 글 제목 {len(titles)}개 확보 — 중복 대조에 사용합니다.")
    return titles


def get_unique_target_keyword(blogger, blog_id):
    existing_titles = fetch_all_post_titles(blogger, blog_id)

    shuffled_keywords = STOCK_INFO_KEYWORDS.copy()
    random.shuffle(shuffled_keywords)

    # 1차: 키워드 전체가 기존 제목에 없는 것
    for keyword in shuffled_keywords:
        compact = re.sub(r'\s+', '', keyword)
        if not any(compact in t for t in existing_titles):
            print(f"🎯 선택된 키워드: {keyword}")
            return keyword

    # 2차: 키워드 첫 단어 기준으로도 겹치지 않는 것
    for keyword in shuffled_keywords:
        short_keyword = re.sub(r'\s+', '', keyword.split(" ")[0])
        if not any(short_keyword in t for t in existing_titles):
            print(f"🎯 선택된 키워드(2차): {keyword}")
            return keyword

    # 전부 소진된 경우 — 발행 중단이 맞다
    print("🛑 사용 가능한 새 키워드가 없습니다. 키워드 목록을 보강해야 합니다.")
    return None


def sanitize_title(title, target_keyword):
    """제목에서 과장 표현이 들어간 경우 정리한다."""
    cleaned = title.strip()
    for word in BANNED_TITLE_WORDS:
        if word in cleaned:
            print(f"⚠️ 제목에 금지 표현 '{word}' 발견 — 제거합니다.")
            cleaned = cleaned.replace(word, "").strip()
    # 정리 과정에서 남은 구두점 뒷정리
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = re.sub(r'[,:\-]\s*$', '', cleaned).strip()
    if len(cleaned) < 8:
        cleaned = f"{target_keyword} 개념과 확인 방법 정리"
    return cleaned


def normalize_labels(tags):
    """라벨을 최대 MAX_LABELS개로 제한한다."""
    if not tags:
        return ["주식투자"]
    cleaned = [str(t).strip() for t in tags if str(t).strip()]
    return cleaned[:MAX_LABELS] if cleaned else ["주식투자"]


def generate_blog_content(target_keyword):
    api_key_direct = os.environ.get("API_KEY")
    client = genai.Client(api_key=api_key_direct, http_options=types.HttpOptions(api_version="v1beta"))

    # [수정] 허위 경력 페르소나 제거 + 제목 규칙 변경
    prompt = (
        "너는 공개된 자료를 바탕으로 주식·재테크 정보를 정확하게 정리하는 작성자야. "
        "본인의 투자 경력이나 수익 경험을 언급하지 말고, 확인 가능한 사실과 제도 설명 위주로 써라.\n\n"
        f"[{target_keyword}]에 대해 검색한 사용자가 궁금증을 실제로 해결할 수 있는 정보성 글을 작성해줘.\n\n"
        "[필수 작성 지침]\n"
        "1. [제목]: 사람들이 실제로 검색창에 입력하는 형태로 작성하라. 핵심 키워드를 맨 앞에 두고, "
        "그 뒤에 이 글이 무엇을 설명하는지 담백하게 붙여라.\n"
        "   - 좋은 예: '미수금이란? 발생 조건과 반대매매 절차 정리'\n"
        "   - 좋은 예: '예수금 뜻과 D+2 출금 가능 시점 확인 방법'\n"
        "   - 절대 사용 금지: 수익 극대화, 극대화, 비법, 완벽 분석, 완벽 마스터, 완벽 정리, "
        "필승, 치명적, 2배, 경제적 자유, 무조건, 보장, 대박, 반드시 알아야\n"
        "   - 수익을 약속하거나 암시하는 표현을 쓰지 마라.\n"
        "2. [분량 및 깊이]: 각 소제목 본문(body_1, body_2, body_3)은 각각 450자~600자 이상으로 "
        "상세하게 작성하라. 제도와 원리를 설명하고, 실제 거래 상황에서 어떻게 적용되는지 예시를 포함하라.\n"
        "3. [정확성]: 수치나 제도를 언급할 때는 '제도가 변경될 수 있으므로 거래 증권사에서 확인이 필요하다'는 "
        "취지를 자연스럽게 포함하라. 확실하지 않은 수치는 단정하지 마라.\n"
        "4. [모바일 가독성]: 문장은 25자 내외로 호흡을 짧게 끊어라. 정보 나열은 글머리기호(-, 1. 2.)를 쓰고 "
        "비교 분석은 마크다운 표(|제목|내용|)로 구현하라.\n"
        "5. [인트로]: intro 항목에는 이 글이 어떤 궁금증을 다루는지 3~4문장으로 담백하게 작성하라. "
        "과장된 훅이나 공포 조성 표현을 쓰지 마라.\n"
        "6. [핵심 요약]: global_summary 항목에는 이 글의 핵심을 한글 3줄로 요약하라.\n"
        "7. [섹션별 요약]: summary_1, summary_2, summary_3에는 각 섹션 내용을 2줄(60~80자)로 압축하라.\n"
        "8. [FAQ]: faq 항목에는 독자들이 실제로 궁금해할 만한 질문 4개와 각 답변(2~3문장)을 작성하라.\n"
        "9. [결론]: conclusion 항목에는 전체 내용을 정리하는 문단(200~300자)을 작성하라. "
        "핵심 재확인 위주로 쓰고, 매수·매도를 권유하는 표현은 쓰지 마라.\n"
        "10. [금지어]: '파소나', 'PASONA', '카피라이팅', 'AI', '인공지능', '자동화', '프로그램', "
        "'전업 투자자', '전문가의 비법' 절대 금지.\n"
        "11. [URL 슬러그 생성]: 이 글의 웹 주소(URL)로 쓸, 주제를 그대로 나타내는 소문자 영어 단어 "
        "2~4개를 하이픈(-)으로 연결하여 'slug' 값에 작성하라. (예: 'unpaid-balance-margin-call')\n\n"
        "반드시 아래의 JSON 규격에 맞춰서 작성하고, JSON 데이터 외에 다른 설명 텍스트나 마크다운 문법은 일절 출력하지 마라.\n"
        "{\n"
        '  "title": "검색어 형태의 담백한 제목",\n'
        '  "slug": "unpaid-balance-margin-call",\n'
        '  "intro": "글을 시작하는 인트로 3~4문장",\n'
        '  "global_summary": "한글 핵심 요약 3줄 내용",\n'
        '  "tags": ["주식투자", "관련키워드"],\n'
        '  "sub_title_1": "1번 소제목 (개념과 정의)",\n'
        '  "body_1": "1번 본문 내용 (최소 450자 이상)",\n'
        '  "summary_1": "1번 핵심 요약 2줄",\n'
        '  "sub_title_2": "2번 소제목 (실제 거래에서의 적용과 주의점)",\n'
        '  "body_2": "2번 본문 내용 (비교 분석용 마크다운 표 반드시 삽입)",\n'
        '  "summary_2": "2번 핵심 요약 2줄",\n'
        '  "sub_title_3": "3번 소제목 (확인 방법과 대응 절차)",\n'
        '  "body_3": "3번 본문 내용 (구체적인 확인 절차 제시)",\n'
        '  "summary_3": "3번 핵심 요약 2줄",\n'
        '  "faq": [\n'
        '    {"question": "질문1", "answer": "답변1"},\n'
        '    {"question": "질문2", "answer": "답변2"},\n'
        '    {"question": "질문3", "answer": "답변3"},\n'
        '    {"question": "질문4", "answer": "답변4"}\n'
        '  ],\n'
        '  "conclusion": "전체 내용을 정리하는 문단"\n'
        "}"
    )

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.7
    )

    for model in ['gemini-2.5-flash', 'gemini-2.5-pro']:
        for attempt in range(3):
            try:
                print(f"🤖 Gemini API 원고 생성 중... (모델: {model}, 시도: {attempt+1}/3)")
                response = client.models.generate_content(model=model, contents=prompt, config=config)
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"⚠️ 지연 발생: {e}")
                if attempt < 2: time.sleep(10)
    raise RuntimeError("🚨 데이터 생성 실패")


def check_already_posted(blogger, blog_id):
    """[수정] 하루 1회 발행 상한"""
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst)
    try:
        posts = blogger.posts().list(blogId=blog_id, maxResults=10).execute()
        count = sum(1 for item in posts.get('items', [])
                    if item.get('published', '').startswith(now.strftime('%Y-%m-%d')))
        if count >= MAX_POSTS_PER_DAY:
            print(f"⏸️ 오늘 이미 {count}건 발행됨 (상한 {MAX_POSTS_PER_DAY}건) — 종료합니다.")
            return True
    except Exception as e:
        print(f"⚠️ 발행 이력 확인 중 오류(계속 진행): {e}")
    return False


# =====================================================================
# 🚀 메인 실행 함수
# =====================================================================
def main():
    kst = datetime.timezone(datetime.timedelta(hours=9))
    b64_token = os.environ.get("TOKEN_PICKLE_BASE64")
    if not b64_token:
        print("🚨 TOKEN_PICKLE_BASE64 환경변수가 없습니다.")
        return
    blogger = build('blogger', 'v3', credentials=pickle.loads(base64.b64decode(b64_token)))

    if check_already_posted(blogger, BLOG_ID):
        return

    try:
        posts = blogger.posts().list(blogId=BLOG_ID, maxResults=1).execute()
        if posts.get('items'):
            last_pub_time = datetime.datetime.fromisoformat(
                posts['items'][0].get('published', '').replace('Z', '+00:00')
            ).astimezone(kst)
            if (datetime.datetime.now(kst) - last_pub_time).total_seconds() < 3600:
                print("⏸️ 마지막 발행 후 1시간이 지나지 않았습니다 — 종료합니다.")
                return
    except Exception as e:
        print(f"⚠️ 최근 발행 시각 확인 중 오류(계속 진행): {e}")

    target_keyword = get_unique_target_keyword(blogger, BLOG_ID)
    if not target_keyword:
        return

    ai_json_response = generate_blog_content(target_keyword)

    try:
        clean_json = ai_json_response.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json)
    except Exception as e:
        raise ValueError(
            f"🚨 JSON 파싱 실패! AI가 규격을 어겼습니다.\n[에러]: {e}\n[AI 원본]:\n{ai_json_response[:500]}"
        )

    raw_title = data.get("title", f"{target_keyword} 개념과 확인 방법 정리")
    title = sanitize_title(raw_title, target_keyword)          # [수정] 금지 표현 필터링
    tags = normalize_labels(data.get("tags", ["주식투자"]))      # [수정] 라벨 최대 2개
    intro = data.get("intro", "")

    sub1 = data.get("sub_title_1", f"{target_keyword} 개념 정리")
    body1 = data.get("body_1", "")
    summary_1 = data.get("summary_1", "")

    sub2 = data.get("sub_title_2", "실제 거래에서의 적용과 주의점")
    body2 = data.get("body_2", "")
    summary_2 = data.get("summary_2", "")

    sub3 = data.get("sub_title_3", "확인 방법과 대응 절차")
    body3 = data.get("body_3", "")
    summary_3 = data.get("summary_3", "")

    global_summary = data.get("global_summary", "")
    faq_list = data.get("faq", [])
    conclusion = data.get("conclusion", "")

    raw_slug = data.get("slug", "stock-investment-guide").lower()
    slug = re.sub(r'[^a-z0-9\-]', '', raw_slug).strip('-')
    if not slug:
        slug = "stock-information-guide"

    if len(body1) < 15 or len(body2) < 15:
        raise ValueError(
            f"🚨 본문 실종! 파싱은 성공했으나 본문이 비어있습니다.\n[body1]: {body1}\n[body2]: {body2}"
        )

    gs_html = format_paragraphs(global_summary) if global_summary else ""
    overview_summary_html = (
        f'<div style="background:#eff6ff; border-left:4px solid #2563eb; padding:18px; margin:20px 0; '
        f'border-radius:0 8px 8px 0;"><p style="margin:0 0 8px 0; font-size:15px; font-weight:bold; '
        f'color:#1e40af;">핵심 요약</p><div style="font-size:16px; color:#334155;">{gs_html}</div></div>'
    ) if gs_html else ""

    toc_html = build_toc_html(sub1, sub2, sub3)
    intro_html = format_paragraphs(intro) if intro else ""
    faq_html = build_faq_html(faq_list)
    conclusion_html = build_conclusion_html(conclusion)

    final_html = get_image_tag(title) + toc_html + intro_html + overview_summary_html + ADSENSE_CODE + \
                 get_image_tag(sub1) + \
                 f'<h3 id="sec1" style="border-left:5px solid #3b82f6; padding-left:10px; margin-top:35px; font-size:20px;">{sub1}</h3>{format_paragraphs(body1)}{make_section_summary(summary_1)}' + \
                 CALCULATOR_BOARD_CODE + \
                 get_image_tag(sub2) + \
                 f'<h3 id="sec2" style="border-left:5px solid #3b82f6; padding-left:10px; margin-top:35px; font-size:20px;">{sub2}</h3>{format_paragraphs(body2)}{make_section_summary(summary_2)}' + \
                 get_image_tag(sub3) + \
                 f'<h3 id="sec3" style="border-left:5px solid #3b82f6; padding-left:10px; margin-top:35px; font-size:20px;">{sub3}</h3>{format_paragraphs(body3)}{make_section_summary(summary_3)}' + \
                 faq_html + ADSENSE_CODE + conclusion_html + CTA_CODE + DISCLAIMER_CODE

    # =================================================================
    # [핵심 수정] 발행 방식 단순화
    #
    # 기존: 라이브 발행 → 제목 patch → published를 미래 시각으로 patch (3연타)
    #       세 번째 단계에서 글이 '예약 대기' 상태로 되돌아가면서
    #       해당 URL이 홈으로 리디렉션 → 구글봇이 '리디렉션 오류'로 기록.
    #
    # 변경: 즉시 발행 2단계로 축소. 예약 상태로 되돌리는 단계를 완전히 제거.
    #       (발행 시각은 GitHub Actions의 cron 스케줄로 제어)
    #
    #   1) title에 영문 slug를 넣어 insert → 영문 퍼머링크 확정
    #   2) title만 한글로 patch → URL은 그대로 유지, 글은 계속 라이브 상태
    # =================================================================
    try:
        print(f"🔗 [1단계] 영문 퍼머링크 확정 발행 중... (Target URL: /{slug}.html)")
        res_insert = blogger.posts().insert(
            blogId=BLOG_ID,
            body={'title': slug, 'content': final_html, 'labels': tags},
            isDraft=False
        ).execute()

        created_post_id = res_insert.get('id')
        created_url = res_insert.get('url', '(URL 확인 불가)')

        time.sleep(1.5)

        print(f"✍️ [2단계] 한글 제목으로 교체 중... ('{title}')")
        res_patch = blogger.posts().patch(
            blogId=BLOG_ID,
            postId=created_post_id,
            body={
                'title': title,
                'content': final_html,   # 본문 삭제 버그 방어
                'labels': tags
            }
        ).execute()

        final_url = res_patch.get('url', created_url)

        print("✅ 발행 완료 (즉시 게시 상태)")
        print(f"   제목: {title}")
        print(f"   라벨: {', '.join(tags)}")
        print(f"   주소: {final_url}")

    except Exception as e:
        print(f"❌ 발행 에러: {e}")


if __name__ == "__main__":
    main()
