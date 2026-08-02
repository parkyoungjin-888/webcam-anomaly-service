# webcam-anomaly-service

`webcam-anomaly-mlops` 프로젝트의 **CI 레포**(서비스 코드 모노레포).
배포 정의는 [webcam-anomaly-deployment](https://github.com/parkyoungjin-888/webcam-anomaly-deployment) 에 있다.

## 구조

최상위 디렉터리 하나가 서비스 하나이고, 그대로 이미지 하나가 된다.
디렉터리명은 kebab-case, 이미지 태그는 각 `pyproject.toml` 의 `version` 을 따른다.

```
hello/    파이프라인 검증용 더미 (FastAPI /health)
```

## 서비스 추가하기

1. `<name>/` 디렉터리에 `pyproject.toml`(version 필수)과 `Dockerfile` 을 둔다
2. 빌드·푸시 후 배포 레포의 `manifests/<name>/values.yaml` 에서 이미지를 참조한다

CI 는 변경된 디렉터리만 감지해 빌드한다(모노레포 + 변경 폴더만 빌드).
이미지 이름을 기준으로 values 를 치환하므로, 한 이미지를 여러 차트가 공유해도 동시에 갱신된다.

## CI

`main` 에 push 하면 `.github/workflows/main.yml` 이 **변경된 서비스 디렉터리만** 빌드해
Docker Hub 로 푸시한다. 판정 기준은 "최상위 디렉터리에 `pyproject.toml` 이 있는가"다.

필요한 레포 시크릿:

| 이름 | 용도 |
|---|---|
| `DOCKER_USERNAME` | Docker Hub 네임스페이스 (`img234`) |
| `DOCKER_PASSWORD` | Docker Hub 액세스 토큰 |

> 시크릿은 레포마다 따로 등록해야 한다. 이전 프로젝트 레포에 있던 값은 따라오지 않는다.

변경 감지에 `tj-actions/changed-files` 를 쓰지 않고 `git diff` 로 직접 한다.
그 액션은 태그 하이재킹으로 워크플로 시크릿이 유출된 전례가 있어,
시크릿을 다루는 잡에는 서드파티 액션을 최소화한다.

`|| true` 도 쓰지 않는다. 이전 프로젝트는 `docker build ... || true` 뒤에 `if [ $? -eq 0 ]` 을 뒀는데,
`|| true` 가 종료 코드를 0 으로 덮어써서 조건이 항상 참이 됐다.
**빌드에 실패한 이미지 이름이 푸시 목록에 올라가는** 구조였다. 지금은 `set -e` 로 실패가 잡을 세운다.

## 다음 세션 CI 개선 항목

| 항목 | 현재 | 변경 예정 |
|---|---|---|
| 이미지 태그 | `pyproject.toml` 의 version | `<version>-<git sha 7자리>` |
| 테스트 게이트 | 없음 | ruff + pytest 를 빌드 앞에 배치 |
| 빌드 캐시 | 없음 | `cache-from: type=gha` |
| 배포 레포 갱신 | 수동 | values.yaml 이미지 태그 자동 커밋 |

**태그에 SHA 를 붙이는 것이 가장 중요하다.** version 을 안 올리고 코드만 고치면 이미지 태그가 같아
배포 레포에 커밋이 생기지 않는다. 파이프라인은 전부 초록불인데 클러스터에는 옛날 코드가 남는,
가장 디버깅하기 까다로운 실패 모드다.
