# hello

파이프라인 검증용 더미 서비스. 목적은 기능이 아니라 **GitOps 루프가 도는지 증명하는 것**이다.
`/health` 하나로 ArgoCD 가 Healthy 를 판정할 수 있게 한다.

## 로컬 실행

```bash
uv sync
uv run uvicorn main:app --reload --port 8000
curl http://localhost:8000/health
```

## 이미지 빌드

이미지 태그는 `pyproject.toml` 의 `version` 을 따른다.

```bash
docker build -t img234/hello:0.1.0 .
docker push img234/hello:0.1.0
```

> 다음 세션에서 CI 를 붙일 때 태그를 `<version>-<git sha 7자리>` 로 바꾼다.
> version 만 쓰면, 버전을 안 올리고 코드만 고쳤을 때 배포 레포의 sed 결과가 동일해
> 커밋이 생기지 않는다. 파이프라인은 전부 초록불인데 클러스터에는 옛날 코드가 남는,
> 가장 디버깅하기 까다로운 실패 모드다.

## 설정

설정은 클러스터에서 ConfigMap 으로 주입된다
([webcam-anomaly-deployment](https://github.com/parkyoungjin-888/webcam-anomaly-deployment) 의
`manifests/hello/values.yaml`). 로컬 실행 시에는 `config.toml.example` 을 복사해 쓴다.
