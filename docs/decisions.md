# 의사결정 기록 (Decisions)

프로젝트: 채널톡 AX 해커톤 — Codex 플러그인
관련 조사: [problem-discovery.md](./problem-discovery.md)

---

## D-001 · 문제 후보 최종 선택 — 후보 C (ALF Code node 검증기)

- **일자**: 2026-07-10
- **결정**: **후보 C 채택** — ALF Code node용 JavaScript 코드가 채널톡 공식 제약을 지키는지 검증하는 Codex 플러그인.

### 검증 대상 제약 5개 (공식 문서 명문화)
1. **JavaScript 전용** — 다른 언어 미지원.
2. **실행 60초 제한** — Maximum execution time 60 seconds.
3. **HTTP는 axios 전용** — 노드 내부 HTTP 요청은 반드시 axios 사용.
4. **isSandbox=true면 외부 네트워크 차단** — 샌드박스/프리뷰 모드에서 외부 요청 불가.
5. **`memory.put()` 후 `memory.save()` 누락 시 데이터 유실** — put만 호출하면 저장 안 됨, save() 필수.

### 근거 URL
- https://developers.channel.io/en/articles/Code-node-fdcd71b4 (위 5개 제약 원문 확인)

### 선택 이유
- **검증 규칙 매핑성**: 제약이 문서에 명문화돼 있어 그대로 린트/가드레일 규칙으로 변환 가능.
- **현업 적합성**: ALF는 채널톡 AI 플랫폼의 핵심 → 실제 운영자/개발자 수요가 높음.
- **테스트 선명성**: 정상 케이스 / 예외 케이스(제약 위반) 테스트 예시가 뚜렷해 데모·검증이 쉬움.

### 탈락 후보와 사유
- **A (Open API 토큰/Rate limit)** — 검증 규칙이 흐릿함(수치는 있으나 가드레일화 애매).
- **B (웹훅 수신·검증)** — 검증·재시도에 대한 공식 문서가 부재해 근거 기반 규칙화 어려움.
- **D (프론트엔드 SDK 연동)** — 가드레일 표면이 좁음(1회성 스캐폴딩 성격).

---

## D-002 · SKILL 규칙 R1~R5 → R1~R6 확장 (금지 함수·함수 시그니처 규칙 추가)

- **일자**: 2026-07-10
- **계기**: 사용자가 초안(R1~R5)을 검토한 뒤 두 가지 누락/부정확을 지적함.
  1. 금지 함수(특히 `require` 남용, `setTimeout`/`setInterval` 등)를 검사하는 독립 규칙이 없었음.
  2. 함수 시그니처의 인자 순서(`memory, context`, `isSandbox`는 세 번째) 검사가 없었음.

### 변경 내용
- **근거 확인**: `references/code-node-constraints.md`에 두 항목 모두 원문 근거가 이미 있었음(문서 재조회 불필요). 대신 상단에 "SKILL 규칙(R1~R6) ↔ 근거 매핑" 표를 추가해 규칙마다 근거 위치를 명시적으로 연결함.
- **R3 확장**: 기존 R3("HTTP는 axios만")를 "금지 함수·라이브러리" 규칙으로 흡수 통합.
  - 금지: `require`(단, `axios`·`crypto` 임포트는 예외), `process`, `global`, `Buffer`, `eval`, `Function`, `setTimeout`, `setInterval`, `clearTimeout`, `clearInterval`, `setImmediate`, `clearImmediate`.
  - `setTimeout`/`setInterval`은 60초 제한을 우회하려는 목적으로 흔히 쓰이지만, 목적과 무관하게 금지 목록에 있어 그 자체로 위반이라고 명시.
  - HTTP는 axios만(기존 R3 내용 흡수).
- **R6 신설**: 함수 시그니처 — `(memory, context)` 순서 필수, `isSandbox` 사용 시 세 번째 인자.
- **결과**: R1~R6 총 6규칙, 각 규칙이 references의 특정 원문 문장에 1:1로 연결됨.

### 검증 — 공식 예시 코드 3건 × R1~R6

references에 있는 채널톡 공식 예시 코드(Memory 예시, Context 예시, isSandbox 예시)를 새 규칙 전체에 대입해, 공식 예제가 오탐 없이 통과하는지 확인함.

| 공식 예시 | R1 언어 | R2 60초 | R3 금지함수·라이브러리 | R4 isSandbox 외부호출 | R5 memory.save | R6 시그니처 |
|---|---|---|---|---|---|---|
| Memory 예시 (`put`→`save`, isSandbox 없음) | 위반없음 | 위반없음 | 대상아님(require 없음) | 대상아님(isSandbox 없음) | 위반없음 | 위반없음 |
| Context 예시 (`context["user"]["id"]`) | 위반없음 | 위반없음 | 대상아님 | 대상아님 | 대상아님(put 없음) | 위반없음 |
| isSandbox 예시 (`require('axios')`, 분기별 처리) | 위반없음 | 위반없음 | 위반없음(axios만 require) | 위반없음(isSandbox=true 분기 안엔 axios 호출 없음) | 위반없음(두 분기 모두 save 호출) | 위반없음(`(memory, context, isSandbox)` 순서 정확) |

세 예시 모두 6규칙 전체에서 위반 없음/대상 아님만 나와, 새로 추가한 R3·R6이 공식 정답 코드를 잘못 위반 처리하지 않음을 확인함.

---

## D-003 · R5 문서-스크립트 불일치 발견 및 문구 수정 (로직 변경 없음)

- **일자**: 2026-07-10
- **계기**: 사용자가 SKILL.md R1~R6과 `validate_code_node.py`의 커버리지를 규칙 번호로 매핑해 달라고 요청. 매핑표 작성 중 R5("memory.put() 뒤 memory.save() 필수")에서 SKILL.md 설명과 스크립트 실제 동작이 어긋나는 것을 발견.

### 재현 (검증 근거)
아래 코드로 재현함 — isSandbox 분기는 `save()`를 정상 호출하고, 이후 else 경로 격의 분기는 `memory.put()`만 있고 `save()`가 없음:
```javascript
export const handler = async (memory, context, isSandbox) => {
  if (isSandbox) {
    memory.put('a', 1);
    memory.save();
    return;
  }
  memory.put('b', 2);
  // 이 분기엔 save() 없음 — SKILL.md R5("if/else 각 분기마다 확인")대로면 위반
}
```
`validate_code_node.py`에 이 파일을 넣은 결과: **"검사 결과: 0건 발견"**. 스크립트의 `check_memory_save`는 파일 전체를 기준으로 "`memory.put(`이 하나라도 있고 `memory.save(`가 파일에 전혀 없을 때만" 위반 처리하므로, 다른 분기에 `save()`가 존재하면 이 분기의 누락을 놓친다. SKILL.md "보조 검증 도구" 절은 이 스크립트가 "R5 위반 후보"를 잡아준다고만 적혀 있어, 분기 단위로는 놓칠 수 있다는 제약이 문서에 없었음.

### 조치 (문구만 수정, 스크립트 로직은 변경하지 않음)
- `src/skills/verify-alf-code-node/SKILL.md` "보조 검증 도구" 절에 R5 탐지 범위를 정확히 명시하는 문장 추가: "스크립트는 파일 전체에 memory.save(가 하나도 없는 경우만 R5 위반으로 자동 탐지한다. 일부 분기에만 save()가 없는 경우는 스크립트가 놓치므로, 반드시 R5 수동 검사에서 if/else 각 분기별로 확인해야 한다."
- `src/scripts/validate_code_node.py`의 `LIMITATIONS` 목록에 동일 취지("분기 단위 검사는 하지 않음, 파일 전체 기준")를 추가.
- `check_memory_save` 함수 자체는 그대로 둠(요청 범위 밖) — 필요하면 후속 작업으로 분기 단위 검사로 개선 가능.

### 검증
- 문구 수정 후 동일한 재현 코드로 재실행 → 로직 결과는 그대로 "0건 발견"(의도대로 변경 없음 확인), 실행 시 출력되는 "한계" 섹션에 새 문구가 정상 노출됨을 확인.
- `bad_example.js`(fetch/isSandbox/loop/memory 4건 위반 포함) 재실행 → 기존과 동일하게 4건 그대로 탐지되어 회귀 없음 확인.

---

## D-004 · 주석 텍스트 오탐 발견 (tests/fail_script_example.js 작성 중)

- **일자**: 2026-07-10
- **계기**: `tests/` 검증용 예시 3종을 만들고 `validate_code_node.py`를 실행하는 과정에서 발생.

### 증상
`tests/fail_script_example.js`는 원래 4가지 위반(fetch 사용/R3, isSandbox 분기 내 외부호출/R4, 파일 전체 save 없음/R5, while(true)/R2)만 담을 의도였는데, 스크립트 실행 결과 **5건**이 나옴. 원인은 파일 상단 주석에 위반 목록을 설명하며 "while(true)(R2)"라는 문구를 실제 코드처럼 그대로 적어놓은 것 — 이 주석 텍스트를 `check_excessive_loop`의 정규식이 코드로 오인해 2번째 줄(주석)과 9번째 줄(실제 `while(true)` 코드) 두 곳에서 중복 탐지함.

### 원인
정적 문자열/정규식 패턴 매칭은 주석·문자열 리터럴과 실제 실행 코드를 구분하지 못한다. `fetch(`, `memory.put(`/`memory.save(`, `isSandbox` 분기, 루프 패턴 4가지 검사 모두 동일한 구조적 한계를 가짐 — 기존에는 이 한계가 "fetch(/axios 호출" 사례에만 좁게 명시돼 있었고, 이번에 실제로 걸린 것은 루프 검사였다는 점에서 한계 문구가 4가지 검사 전체를 포괄하지 못하고 있었음.

### 조치
1. **테스트 파일 수정**: `tests/fail_script_example.js` 주석 문구를 "종료조건 없는 무한 루프(R2)"로 바꿔 실제 코드 패턴과 겹치지 않게 함 → 재실행 시 의도한 4건만 정확히 탐지되는 것을 확인(`tests/results.md`에 반영된 4건 출력이 이 수정 이후 버전).
2. **한계 문구 일반화(로직 변경 없음)**:
   - `src/scripts/validate_code_node.py`의 `LIMITATIONS`: 기존 "fetch(/axios 호출 탐지는 텍스트 패턴 매칭..." 문구를 "네 가지 검사(fetch(, memory.put(/memory.save(, isSandbox 분기 내 http 호출, 과도 루프) 모두 텍스트/정규식 패턴 매칭이며 주석·문자열 리터럴의 키워드도 매칭될 수 있다"로 확장하고, `while(true)` 주석 오탐을 구체 예시로 명시.
   - `src/skills/verify-alf-code-node/SKILL.md` "보조 검증 도구" 절에 동일 취지의 "**주석·문자열 오탐 가능**" 항목을 신규 추가(기존에는 이 섹션에 이런 항목이 아예 없었음).

### 검증
- 문구 수정 후 `python3 -c "import py_compile; ..."`로 스크립트 문법 확인 — 통과.
- 체크 함수(`check_fetch`/`check_memory_save`/`check_isSandbox_http`/`check_excessive_loop`) 로직은 손대지 않음 — 문구만 수정.
- `tests/fail_script_example.js` 재실행 결과 4건(의도한 것만) 정상 출력, 회귀 없음.

---

## D-005 · 폴백 규칙·3단계 상태 표기 실전 검증 (로컬 Codex 실행)

- **일자**: 2026-07-10
- **실행 환경**: 이 세션의 Bash 실행이 아니라, 사용자가 `.agents/plugins/marketplace.json` 경유로 로컬 Codex CLI에 `alf-code-node-validator` 플러그인을 설치한 뒤 `verify-alf-code-node` 스킬을 실제로 호출해 얻은 결과. Claude가 직접 재현·확인한 것이 아니라 사용자 보고 기준으로 기록함.

### 테스트 1 — 문서에 없는 함수 포함 코드 (폴백 규칙 검증)
- **입력**: `someInternalHelper`처럼 `references/code-node-constraints.md`에 근거가 전혀 없는 함수를 포함한 코드.
- **결과**: 검증기가 이 함수를 임의로 위반 처리하거나 존재하지 않는 규칙을 지어내지 않고, **"공식 문서에 근거 없어 판단하지 않음"**으로 정직하게 응답함.
- **의의**: SKILL.md 폴백 규칙 — "`references/code-node-constraints.md`에 문장으로 없는 주장은 하지 않는다. 판단이 필요하면 '문서 근거 없음 — 확인 불가'라고만 답한다", "문서에 없는 채널톡 API·엔드포인트·제약을 지어내지 않는다" — 가 실제 LLM 실행에서 설계 의도대로 작동함을 확인.

### 테스트 2 — 3단계 상태 표기 구분 확인
- **R2(60초 안에 끝날 구조)**: 정적으로 실행 시간을 측정할 수 없는 코드에 대해 위반으로 단정하지 않고 **"확인 불가"**로 정확히 표기.
- **R4(isSandbox 분기 외부 네트워크 호출 금지)**: 코드에 `isSandbox` 분기 자체가 없는 경우 **"해당 규칙 대상 아님"**으로 정확히 표기(위반없음과 구분).
- **의의**: SKILL.md 리포트 형식에서 정의한 세 가지 상태 — `위반 없음` / `해당 규칙 대상 아님` / `확인 불가` — 가 문서상 정의로만 그치지 않고, 실제 실행에서 서로 다른 상황(측정 불가 vs. 규칙 미해당)에 맞게 정확히 갈라져 출력됨을 확인.

### 종합
D-001~D-004는 이 세션에서 Claude가 직접 스크립트를 실행·재현해 얻은 결과이고, D-005는 실제 로컬 Codex 환경에서 플러그인이 설치·구동된 상태로 사용자가 직접 확인한 첫 실전 검증 사례. 정적 스크립트(자동 4가지)와 SKILL.md 수동 R1~R6 절차, 그리고 폴백 규칙(근거 없는 주장 금지)이 실제 플러그인 형태로도 의도대로 동작함을 뒷받침함.

---

## 거절/수정한 AI 제안

- **[제안]** SKILL.md 검증 규칙을 R1~R5(언어 / 60초 / HTTP는 axios / isSandbox 외부호출 차단 / memory.save)로 설계.
- **[이유]** 사용자가 검토 후 금지 함수 검사(require 제한 포함)와 함수 시그니처(인자 순서) 검사가 빠졌다고 지적. 두 항목 모두 공식 문서에 근거가 있었는데 규칙에 반영되지 않았음.
- **[어떻게 바꿈]** R3를 "금지 함수·라이브러리"로 확장(기존 HTTP-axios 내용 흡수), R6 "함수 시그니처" 신설 → R1~R6로 갱신. 상세는 D-002 참고.

> 형식: **[제안]** / **[이유]** / **[어떻게 바꿈]**
> Claude가 제안했으나 사용자가 거절하거나 수정한 항목을 시간순으로 append.

(아직 없음)
