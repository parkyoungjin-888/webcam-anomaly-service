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

## 현재 상태

GitHub Actions 는 **아직 없다.** 지금은 로컬에서 수동 빌드·푸시한다.

```bash
cd hello
docker build -t img234/hello:0.1.0 .
docker push img234/hello:0.1.0
```

다음 세션에서 CI 를 붙일 때 이전 프로젝트 워크플로 대비 다음을 바꾼다.

| 항목 | 이전 | 변경 |
|---|---|---|
| 이미지 태그 | `pyproject.toml` 의 version | `<version>-<git sha 7자리>` |
| 빌드 실패 처리 | `\|\| true` 로 실패가 성공 처리됨 | `if docker build; then` 으로 교체 |
| 테스트 게이트 | 없음 | ruff + pytest 를 빌드 앞에 배치 |
| 빌드 캐시 | 없음 | `cache-from: type=gha` |
| 동시 실행 | 제어 없음 | `concurrency` 그룹 지정 |

`|| true` 는 단순한 버그가 아니다. 뒤따르는 `if [ $? -eq 0 ]` 이 항상 참이 되어
**빌드에 실패한 이미지 이름이 푸시 목록에 올라간다.**
