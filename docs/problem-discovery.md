# 채널톡 문제 발굴 (공개 자료 기반) — 후보 표 & 점수

> AX 해커톤 예선용. 모든 근거는 심사 AI가 URL로 직접 열어 확인 가능한 공개 자료만 사용.
> 확인하지 못한 항목은 "확인 실패"로 명시. 최종 추천은 아직 하지 않음 — 표와 점수만.
> 조사일: 2026-07-09

---

## 조사 대상(실제로 열어본 소스)

| 소스 | URL | 열람 결과 |
|---|---|---|
| 개발자 문서 홈 | https://developers.channel.io/ | ✅ 로드됨 (SDK 4종·Open API 56문서·Webhook·FrontALF 구조 확인) |
| 인증 및 권한 | https://developers.channel.io/ko/articles/인증-및-권한-e7c2fb6f | ✅ 로드됨 (토큰 rate limit 확인) |
| 웹 SDK 시작하기 | https://developers.channel.io/reference/web-quickstart-kr | ✅ 로드됨 (boot·HMAC member hash 확인) |
| 웹훅 생성 | https://developers.channel.io/docs/create-a-webhook-1 | ✅ 로드됨 (엔드포인트 확인, 페이로드·검증·재시도 문서 없음) |
| 공식 예제 레포 | https://github.com/channel-io/channel-challengers-example | ✅ 로드됨 (ngrok 필요성 명시) |
| ALF Code node | https://developers.channel.io/en/articles/Code-node-fdcd71b4 | ✅ 로드됨 (JS·60초·axios 전용·memory.save 함정) |
| 팀블로그(CTO 인터뷰) | https://channel.io/ko/team/blog | ✅ 로드됨 (CTO/모바일팀 리더 인터뷰, AI 개발 주제) |
| 기술블로그 | https://tech.channel.io/ko | ✅ 로드됨 (Cursor 전사도입·Ralph Loop·AI 에이전트 등 에이전틱 개발 콘텐츠 다수) |
| App Store(채널톡/채널웍스) | https://apps.apple.com/kr/app/채널톡/id1088828788 | ✅ 로드됨 (3.5/5, 143개 평점, 특정 버그 리뷰) |
| **Open API 명세** api-doc.channel.io | https://api-doc.channel.io/ | ⚠️ **확인 실패** — SPA로 제목만 렌더링, 본문 미확인 |
| **중앙 rate-limit 문서** | https://developers.channel.io/docs/rate-limit | ⚠️ **404** — 통합 rate-limit 페이지 없음(제한이 문서 곳곳에 분산) |
| **Play 스토어 리뷰** | play.google.com/store/apps/details?id=com.zoyi.channel.desk.android | ⚠️ **확인 실패** — 페이지 truncate, 평점/리뷰 본문 미확보 |

---

## 문제 후보

### 후보 A — Open API 토큰/Rate limit 대응이 까다로워 연동 서버가 쉽게 막힘

| 항목 | 내용 |
|---|---|
| **문제** | Open API 토큰 발급이 `10 tokens / 30분(Fixed window)`으로 제한되고, 재발급 시 기존 토큰이 즉시 무효화되어, 채널톡을 연동하는 고객사 개발자가 토큰 캐싱·갱신·동시성을 잘못 다루면 운영 중 인증이 통째로 막힌다. 게다가 rate limit이 한곳에 정리돼 있지 않아 엔드포인트마다 흩어진 문서를 찾아야 한다. |
| **공개근거** | https://developers.channel.io/ko/articles/인증-및-권한-e7c2fb6f — "issueToken/refreshToken: **10 tokens / 30 minute, Fixed window**", 초과 시 발급 거부, "재발급 시 이전 토큰 무효화", channelId는 해당 채널에 앱이 사전 설치돼야 함. + 통합 rate-limit 페이지(`/docs/rate-limit`)는 **404**(제한이 분산됨). |
| **AI검증법** | 심사 AI가 인증 및 권한 URL을 열면 "10 tokens / 30 minute, Fixed window" 문구와 재발급 무효화 규칙을 그대로 확인 가능. `/docs/rate-limit`을 열어 404를 확인하면 "중앙 문서 부재"도 검증됨. |

### 후보 B — 웹훅 수신·검증 구현이 번거롭고 실패/검증 문서가 빈약

| 항목 | 내용 |
|---|---|
| **문제** | 고객사 개발자가 채널톡 이벤트를 받으려면 웹훅 수신 서버를 직접 구현해야 하는데, 로컬 개발에서 바로 수신이 안 되어 ngrok/heroku로 터널링해야 하고, 공식 문서에는 페이로드 구조·서명 검증·재시도(실패 처리)가 정리돼 있지 않아 시행착오가 크다. |
| **공개근거** | https://github.com/channel-io/channel-challengers-example — README: "로컬 서버로는 웹훅을 받을 수 없으니 ngrok/heroku 등으로 로컬 서버를 인터넷에 노출한 뒤 URL 등록", `.env`에 access-key/secret 설정, `packages/webhook/index.ts` 수동 편집 필요(TypeScript). + https://developers.channel.io/docs/create-a-webhook-1 — `POST https://api.channel.io/open/v5/webhooks`(name·url만 명시), **페이로드/서명검증/재시도 문서는 없음**. |
| **AI검증법** | GitHub README를 열면 ngrok 문구·수동 설정 스텝을 직접 확인. 웹훅 생성 문서 URL을 열면 엔드포인트만 있고 검증/재시도 항목이 비어 있음을 확인 가능. |

### 후보 C — ALF Code node 자동화 작성이 좁은 샌드박스 제약에 걸려 실패하기 쉬움

| 항목 | 내용 |
|---|---|
| **문제** | 채널톡 고객(운영자/개발자)이 ALF 워크플로에 Code node로 커스텀 로직을 넣을 때, JavaScript 전용·60초 실행 제한·HTTP는 axios만 허용·`isSandbox`일 때 네트워크 차단·`memory.put()` 후 `memory.save()`를 빠뜨리면 데이터 유실 같은 숨은 제약이 많아, 문서를 안 읽으면 조용히 실패하거나 배포 후 깨진다. |
| **공개근거** | https://developers.channel.io/en/articles/Code-node-fdcd71b4 — "Supported language: **JavaScript**", "Maximum execution time: **60 seconds**", 함수 시그니처 `(context, memory, isSandbox)`, "HTTP requests inside the node must use **axios**", "`isSandbox`가 true면 외부 네트워크 요청 차단", "`memory.put()`만 호출하면 저장 안 됨 → **`memory.save()` 필수**". |
| **AI검증법** | Code node 문서 URL을 열면 60초 제한·axios 전용·isSandbox 차단·memory.save 규칙이 원문으로 확인됨. 이 제약들은 그대로 플러그인의 검증 규칙(가드레일)로 매핑 가능. |

### 후보 D — 프론트엔드 SDK 초기 연동(HMAC 포함)이 파편적이라 온보딩 시행착오가 큼

| 항목 | 내용 |
|---|---|
| **문제** | 채널톡 위젯을 붙이는 고객사 프론트엔드 개발자가 SDK 4종(JS·iOS·Android·React Native)과 56개 Open API 문서를 스스로 엮어야 하고, 보안상 권장되는 member hash(HMAC) 인증을 별도로 서버에서 구현해야 하며, SPA에서는 `setPage`/`track`을 추가로 호출해야 워크플로/마케팅 기능이 동작한다. 최소 설치는 쉬우나 "제대로 된 설치"는 흩어져 있다. |
| **공개근거** | https://developers.channel.io/reference/web-quickstart-kr — `boot()`에 `memberId` 유무로 익명/회원 구분, "member hash(HMAC) 인증을 **강력히 권장**"(이메일 등 예측가능 식별자 사용 시 제3자가 개인정보·대화이력 접근 위험), SPA는 `setPage`·`track` 필요. + https://developers.channel.io/ — SDK 4종·Open API 56문서·Snippet 13문서 등 문서 표면이 넓음. |
| **AI검증법** | 웹 quickstart URL을 열면 HMAC 권장 문구와 SPA 추가 호출 요구가 확인됨. 개발자 문서 홈 URL을 열면 SDK 4종·문서 개수(연동 표면 넓이)가 확인됨. |

> **참고(주 후보에서 제외)** — 앱 UX 버그: App Store 채널톡/채널웍스 **3.5/5(143개 평점)**, "아이패드 가로모드 미회전", "비밀번호 재설정 링크가 로그인 화면으로 감" 리뷰 확인(https://apps.apple.com/kr/app/채널톡/id1088828788). 공개 입증은 강하나 네이티브 앱 버그라 **Codex 플러그인 적합성이 낮아** 주 후보에서 제외.

---

## 4기준 채점 (각 1~3점, 근거 확인 결과에 따라 정직하게)

기준: ① 공개 입증 가능성 · ② Codex 플러그인 적합성 · ③ 검증/가드레일 강점 정합 · ④ 오늘 밤 안에 완성 가능성

| 후보 | ① 공개입증 | ② Codex적합 | ③ 검증/가드레일 | ④ 오늘밤완성 | 합계 |
|---|:---:|:---:|:---:|:---:|:---:|
| **A. Open API 토큰/Rate limit 클라이언트** | 3 | 3 | 3 | 2 | **11** |
| **B. 웹훅 수신·검증 핸들러 생성** | 3 | 3 | 3 | 2 | **11** |
| **C. ALF Code node 작성/검증 플러그인** | 3 | 3 | 3 | 2 | **11** |
| **D. 프론트엔드 SDK 연동 스캐폴딩** | 3 | 2 | 2 | 3 | **10** |
| (참고) 앱 UX 버그 리포트 | 3 | 1 | 1 | 2 | 7 |

### 점수 판단 근거 (정직성 메모)

- **① 공개입증** — A/B/C/D 모두 3: 인용한 핵심 사실을 실제 URL에서 원문으로 확인함. (반대로 api-doc.channel.io 상세 명세, Play 스토어 평점은 확인 실패 → 근거로 쓰지 않음.)
- **② Codex 적합성** — A/B/C는 3: 토큰·백오프 로직, 웹훅 리시버, 샌드박스 제약 준수 코드는 "실제 코드 생성"이 핵심이라 코딩 에이전트에 잘 맞음. D는 2: 위젯 boot·HMAC 스캐폴딩은 유용하나 한 번 붙이면 끝나는 얕은 작업.
- **③ 검증/가드레일 정합** — A/B/C는 3: rate limit 준수·서명 검증·60초/axios/memory.save 같은 **명문화된 제약이 그대로 가드레일 규칙**이 됨(테스트로 검증 가능). D는 2: HMAC 정합성은 검증 가능하나 가드레일 표면이 좁음.
- **④ 오늘밤 완성** — D는 3(범위 작고 문서 명확), A/B/C는 2(클라이언트/핸들러/검증기 + 테스트가 필요해 중간 규모). 앱 UX 버그는 리포트는 쉬우나 플러그인화가 애매해 2.
- **주의** — A·B·C가 11점 동점. 이는 셋 다 "명문화된 제약을 코드+가드레일로 자동화"라는 같은 강점을 공유하기 때문. 최종 선택은 다음 단계에서 진행(현재는 표·점수만).

### 확인 실패 / 미검증 항목 (근거로 사용하지 않음)

- api-doc.channel.io 의 상세 엔드포인트/스키마 구조 — SPA 렌더링으로 **확인 실패**.
- Play 스토어 평점·리뷰 본문 — 페이지 truncate로 **확인 실패** (App Store 데이터만 사용).
- 토큰 API 외 개별 Open API 엔드포인트별 rate limit 수치 — 통합 문서 부재(404)로 개별 수치는 **미검증**.
