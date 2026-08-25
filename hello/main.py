import os

from fastapi import FastAPI

APP_NAME = os.getenv('APP_NAME', 'hello')

app = FastAPI(title=APP_NAME)


# ArgoCD 가 Healthy 를 판정하는 근거이자 k8s liveness/readiness probe 의 대상이다.
@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok', 'app': APP_NAME}


@app.get('/')
def root() -> dict[str, str]:
    return {'app': APP_NAME, 'version': '0.1.0'}
