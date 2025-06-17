# celery config 를 저장하는 모듈

import os

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1") # 브로커 설정 메시지큐 기반으로 동작을 하기위해 큐저장용 (broker)
result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1") # task 실행 결과를 추적하기 위해서 저장하기 위한 공간 (backend)

task_serializer = "json" # 작업을 직렬화할 때 사용할 형식을 지정
accept_content = ["json"] # 허용할 메시지 형식의 리스트. 여기서는 JSON 형식만 허용
result_serializer = "json" # 결과를 직렬화할 때 사용할 형식을 지정
enable_utc = True # UTC 시간대 사용을 활성화
timezone = "Asia/Seoul" # Celery가 사용할 기본 시간대를 설정
broker_connection_retry_on_startup = True # 시작 시 브로커 연결 재시도를 활성화