# webcam-anomaly-service

`webcam-anomaly-mlops` 프로젝트의 **CI 레포**(서비스 코드 모노레포).
배포 정의는 [webcam-anomaly-deployment](https://github.com/parkyoungjin-888/webcam-anomaly-deployment) 에 있다.

## 구조

최상위 디렉터리 하나가 서비스 하나이고, 그대로 이미지 하나가 된다.
디렉터리명은 kebab-case, 이미지 태그는 각 `pyproject.toml` 의 `version` 을 기반으로 한다.

```
hello/    파이프라인 검증용 더미 (FastAPI /health)
```

## CI 파이프라인

`main` 에 push 하면 변경된 서비스 디렉터리에 대해 순서대로 돈다.

```
변경 감지 → ruff + pytest → 이미지 빌드/푸시 → 배포 레포 values.yaml 갱신
                  ↓ 실패                              ↓
              이미지 안 만들어짐                  ArgoCD 가 3분 내 반영
```

서비스 판정 기준은 "최상위 디렉터리에 `pyproject.toml` 이 있는가"다.

### 필요한 레포 시크릿

| 이름 | 용도 |
|---|---|
| `DOCKER_USERNAME` | Docker Hub 네임스페이스 |
| `DOCKER_PASSWORD` | Docker Hub 액세스 토큰 |
| `MY_GITHUB_TOKEN` | 배포 레포에 커밋을 push 하기 위한 PAT (`repo` 스코프) |

`MY_GITHUB_TOKEN` 이 따로 필요한 이유는, 워크플로 기본 `GITHUB_TOKEN` 은 자기 레포에만 권한이 있어
다른 레포(배포 레포)에 push 할 수 없기 때문이다.

시크릿은 레포마다 따로 등록해야 한다. 다른 레포의 값은 따라오지 않는다.

### 이미지 태그

```
<registry-user>/<service>:<version>-<git sha 7자리>
```

**SHA 를 붙이는 것이 핵심이다.** version 만 쓰면 version 을 올리지 않고 코드만 고쳤을 때
이미지 태그가 그대로라 배포 레포의 sed 결과가 동일해지고, 커밋이 생기지 않는다.
파이프라인은 전부 초록불인데 클러스터에는 옛날 코드가 남는다.
가장 디버깅하기 까다로운 실패 모드라 처음부터 막는다.

### 설계상 지킨 것

**`|| true` 를 쓰지 않는다.** 이전 프로젝트는 `docker build ... || true` 뒤에 `if [ $? -eq 0 ]` 을 뒀는데,
`|| true` 가 종료 코드를 0 으로 덮어써서 조건이 항상 참이 됐다.
빌드에 실패한 이미지 이름이 푸시 목록에 올라가는 구조였다. 지금은 `set -euo pipefail` 로 실패가 잡을 세운다.

**테스트를 빌드 앞에 둔다.** ruff 나 pytest 가 떨어지면 이미지 자체가 만들어지지 않는다.

**변경 감지는 `git diff` 로 직접 한다.** `tj-actions/changed-files` 는 태그 하이재킹으로
워크플로 시크릿이 유출된 전례가 있어, 시크릿을 다루는 잡에서는 커뮤니티 액션을 쓰지 않는다.
`actions/*`, `docker/*`, `astral-sh/*` 처럼 벤더가 직접 관리하는 것만 쓴다.

**빌드 캐시는 레지스트리에 둔다**(`<image>:buildcache`).
`type=gha` 는 루프 안에서 쓰려면 런타임 토큰을 노출하는 별도 액션이 필요하고,
Phase 2 의 멀티아치 빌드에서도 레지스트리 캐시가 그대로 쓰인다.

## 코드 규칙

백엔드 코드 컨벤션(`project_manager/code-conventions.md`)을 따른다.
네이밍, 타입 힌트(3.10+ 문법), 서식, 주석 원칙, 디렉터리 구조는 그대로다.

강제 가능한 부분은 각 서비스의 `pyproject.toml` 에 ruff 설정으로 넣었다.
자동으로 잡히는 것은 네이밍(N), `Optional`/`List`/`Dict` 금지(UP), 작은따옴표(Q),
한 줄 안의 trailing comma(COM819), 줄 길이 140(E501) 정도다.

compact 스타일, 인자 추출, 가드절 뒤 빈 줄 같은 서식 규칙은 ruff 로 표현할 수 없다.
`ruff format` 은 쓰지 않는다 — compact 스타일을 컨벤션이 금지한 expanded 로 바꾸고
따옴표를 큰따옴표로 뒤집는다. 린터(`ruff check`)만 쓴다.

### 컨벤션과 다르게 가는 것

컨벤션은 systemd 로 도는 서버를 전제로 쓰였다. 여기는 컨테이너라 아래 셋은 따르지 않는다.

| 컨벤션 | 여기서는 | 이유 |
|---|---|---|
| `ConfigSingleton` + `config.toml` | ConfigMap → 환경변수 | 설정을 Git(Helm values)에 두어야 ArgoCD 가 변경을 diff 로 보여준다. 설정이 컨테이너 안에 있으면 Phase 1 에서 gRPC 설정 서버를 뺀 이유가 그대로 되살아난다 |
| `LoggerSingleton` 의 파일 로깅(`log/`) | stdout | 파드가 죽으면 파일이 사라지고 `kubectl logs` 에 잡히지 않는다. 스토리지가 `local-path` 뿐이라 노드를 옮기면 더 확실히 잃는다 |
| 사내 공용 패키지(`my_module`) | 사용하지 않음 | 비공개 레포라 Public 레포 + Actions 빌드에서 PAT 시크릿과 Dockerfile secret mount 가 추가로 필요하다 |

`config.toml.example` 은 로컬 실행 참고용으로 남겨 둔다.
README 템플릿의 systemd 배포 절차도 해당 없다 — 배포는 ArgoCD 가 한다.

## 로컬 개발

```bash
cd hello
uv sync
uv run uvicorn main:app --reload --port 8000
uv run ruff check .
uv run pytest -q
```

## 다음에 할 것

- 멀티아치 빌드 (buildx + QEMU) — Phase 2, arm64 엣지 디바이스 대응
