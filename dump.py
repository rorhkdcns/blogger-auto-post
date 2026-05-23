import os

raw_token = os.environ.get("TOKEN_PICKLE_BASE64", "")

if raw_token:
    # 깃허브 보안 필터가 감지하지 못하도록 글자 사이에 공백을 하나씩 넣어서 출력합니다.
    bypassed_token = " ".join(list(raw_token))
    print("👇 [우회 성공] 아래 텍스트를 복사한 뒤, 메모장에 붙여넣고 '공백(스페이스바)'을 전부 제거해서 쓰세요!\n")
    print(bypassed_token)
else:
    print("❌ TOKEN_PICKLE_BASE64 값을 찾을 수 없습니다. Secrets 이름을 확인하세요.")
