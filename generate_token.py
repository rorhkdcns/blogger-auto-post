from google_auth_oauthlib.flow import InstalledAppFlow
import json

# 구글 블로그 권한
SCOPES = ['https://www.googleapis.com/auth/blogger']

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

# 토큰 정보 저장
token_data = {
    'token': creds.token,
    'refresh_token': creds.refresh_token,
    'token_uri': creds.token_uri,
    'client_id': creds.client_id,
    'client_secret': creds.client_secret,
    'scopes': creds.scopes
}

with open('token.json', 'w') as f:
    json.dump(token_data, f)
print("성공! 같은 폴더에 token.json 파일이 생겼습니다.")
