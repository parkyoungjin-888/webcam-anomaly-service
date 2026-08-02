FROM python:3.12-slim

# uv 는 버전을 고정한다. latest 를 쓰면 빌드 재현성이 깨진다.
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# 의존성만 먼저 설치해 레이어 캐시를 살린다. 코드만 바뀌면 이 레이어는 재사용된다.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY main.py ./
COPY src/ ./src/

ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home --uid 1000 app
USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
