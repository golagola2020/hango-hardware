import os       # 시스템 모듈

# 데이터 요청 Domain 선언
URL = str(os.environ['hangoURL'])

# 서버 요청 및 응답 API
READ_DRINKS_PATH = URL + '/rasp/drink/read'
UPDATE_DRINKS_PATH = URL + '/rasp/drink/update'