---
name: verify-alf-code-node
description: ALF Code node용 JavaScript 코드가 채널톡 공식 제약(JS 전용/60초/axios 전용/isSandbox 네트워크 차단/memory.save 필수)을 지키는지 검증한다
---

# 절차

1. 시작 시 `references/code-node-constraints.md`를 읽는다. 이 문서에 없는 규칙은 적용하지 않는다.
2. 사용자가 다음 중 하나를 요청하면 이 스킬을 실행한다.
   - Code node용 JS 코드 작성 요청
   - 기존 Code node용 JS 코드를 붙여넣고 검사 요청
3. 검사할 코드가 파일로 존재하면(또는 붙여넣은 코드를 임시 파일로 저장할 수 있으면) 먼저 보조 정적 검사 스크립트를 실행한다:
   `python3 src/scripts/validate_code_node.py <파일경로>`
   스크립트 출력(발견된 위반 후보 + 라인 힌트)을 아래 6규칙 검사의 입력으로 참고한다. 스크립트는 보조 도구일 뿐이며 최종 판단·리포트는 4단계 기준으로 직접 작성한다.
4. 코드를 아래 6개 규칙으로 순서대로 검사한다.

## 검사 규칙

**R1. 언어 = JavaScript인가**
- 코드가 JS 문법이 아니거나 다른 언어(Python, TS 전용 타입 구문 등)로 작성됐으면 위반.
- 근거: references "JavaScript 전용 언어" 행.

**R2. 60초 안에 끝날 구조인가**
- 조건 없는 무한 루프(`while(true)` 등), 응답 없는 폴링, 명백히 대량인 동기 순회처럼 60초 초과가 예상되는 구조면 위반.
- `setTimeout`/`setInterval` 자체는 여기서 판단하지 않는다 — 사용 여부와 무관하게 R3(금지 함수)에서 이미 위반이다.
- 코드만으로 실제 실행 시간은 측정 불가하므로 애매하면 위반 단정하지 말고 확인 불가로 표시한다.
- 근거: references "최대 실행 시간 60초" 행.

**R3. 금지 함수·라이브러리를 사용하지 않는가**
- 다음 중 하나라도 호출/참조하면 위반: `process`, `global`, `Buffer`, `eval`, `Function`, `setTimeout`, `setInterval`, `clearTimeout`, `clearInterval`, `setImmediate`, `clearImmediate`.
- `require`는 원칙적으로 금지이며, `axios`와 `crypto`를 불러올 때만 예외로 허용된다. `require('lodash')`, `require('http')`, `require('node-fetch')` 등 그 외 라이브러리를 불러오면 위반.
- HTTP 요청에 `fetch(`, `XMLHttpRequest` 등 axios가 아닌 수단을 쓰면 위반(HTTP는 axios만 허용).
- `setTimeout`/`setInterval`은 60초 제한을 우회하려는 목적으로 흔히 시도되지만, 목적과 무관하게 금지 함수 목록에 있으므로 그 자체로 위반이다.
- 근거: references "`require`는 원칙적으로 금지, 예외만 허용" 행 / "허용 라이브러리는 `axios`, `crypto`뿐" 행 / "HTTP 요청은 axios만 사용" 행.

**R4. isSandbox 분기에서 외부 네트워크 호출을 안 하는가**
- `isSandbox`(예: `if (isSandbox)`) 분기 내부에서 `axios.get/post/...` 등 실제 외부 요청을 호출하면 위반.
- 코드에 `isSandbox` 분기 자체가 없으면 해당 규칙 대상 아님.
- 근거: references "`isSandbox=true`면 axios 외부 네트워크 요청 차단" 행.

**R5. memory.put() 뒤 memory.save()가 있는가**
- `memory.put(...)` 호출이 있는데 같은 실행 경로에서 함수 종료(또는 `return`) 전에 `memory.save()` 호출이 없으면 위반. if/else 각 분기마다 따로 확인한다.
- `memory.put()` 호출이 없는 코드는 해당 규칙 대상 아님.
- 근거: references "`memory.put()`만으로는 저장 안 됨" 행.

**R6. 함수 시그니처(인자 순서)가 올바른가**
- 올바른 형식: `export const handler = async (memory, context) => { ... }`. 인자 순서는 반드시 `memory`가 첫 번째, `context`가 두 번째다. `(context, memory)`처럼 순서가 바뀌면 위반.
- `isSandbox`를 사용하는 경우 반드시 세 번째 인자로 받는다: `export const handler = async (memory, context, isSandbox) => { ... }`. 두 번째 자리에 오거나 순서가 틀리면 위반.
- 근거: references "함수 시그니처 (기본형)" / "함수 시그니처 (isSandbox 포함)" 섹션 + "함수 인자 순서: `(memory, context)`" 행.

## 보조 검증 도구: validate_code_node.py

- 경로: `src/scripts/validate_code_node.py`
- 실행: `python3 src/scripts/validate_code_node.py <Code node JS 파일 경로>`
- 정적 패턴 매칭으로 4가지만 확인한다: `fetch(` 사용(R3 위반 후보), `memory.put(` 뒤 `memory.save(` 없음(R5 위반 후보), `isSandbox` 분기 내부 http 호출 흔적(R4 위반 후보), 명백한 과도 루프(R2 관련 경고, `while(true)`/`for(;;)`/대량 반복 상수).
- **R5 탐지 범위(정확히)**: 스크립트는 파일 전체에 `memory.save(`가 하나도 없는 경우만 R5 위반으로 자동 탐지한다. 일부 분기에만 `save()`가 없는 경우는 스크립트가 놓치므로, 반드시 R5 수동 검사에서 if/else 각 분기별로 확인해야 한다.
- 다루지 않는 것(수동으로 확인 필요): R1(언어=JavaScript 여부), R3의 금지 함수 전체 목록(`process`/`global`/`Buffer`/`eval`/`Function`/`setTimeout`/`setInterval`/`clearTimeout`/`clearInterval`/`setImmediate`/`clearImmediate`, `require`의 axios·crypto 외 사용), `XMLHttpRequest`(스크립트는 `fetch(`만 탐지하고 `XMLHttpRequest`는 탐지하지 않으므로 R3 수동 검사로만 잡는다), R6(함수 시그니처 인자 순서).
- 스크립트는 60초 초과 여부를 단정하지 않는다(런타임에서만 확정 가능). 구조적 위험 패턴만 경고한다.
- **주석·문자열 오탐 가능**: 4가지 검사 모두 텍스트/정규식 패턴 매칭이라 주석이나 문자열 리터럴 안의 키워드도 실제 코드와 구분하지 못하고 매칭될 수 있다. 예: 주석에 `while(true)` 문구를 그대로 적으면 실제 코드가 아니어도 R2 위반 후보로 잡힌다. 스크립트가 위반을 보고하면 해당 라인이 실제 코드인지 주석/문자열인지 사람이 먼저 확인한다.
- 스크립트 결과는 참고용 1차 스캔이다. 최종 리포트는 반드시 위 R1~R6 6규칙 검사를 사람(LLM)이 직접 수행해 작성한다 — 스크립트가 "0건"을 반환해도 R1/R3 전체/R6은 스크립트가 검사하지 않으므로 별도 확인이 필요하다.

## 리포트 형식

위반마다 다음 4개 항목을 채운다.

- 무엇이: 위반한 코드 줄/구간 인용
- 왜 위반: R1~R6 중 어느 규칙을 어떻게 어겼는지 한 문장
- references 근거 문장: `code-node-constraints.md`에서 그대로 인용 (새로 작성 금지)
- 수정안: 해당 부분만 고친 코드 조각

위반 없는 규칙: `R{n}: 위반 없음`
대상 아닌 규칙: `R{n}: 해당 규칙 대상 아님`
정적 분석으로 판단 불가: `R{n}: 확인 불가 — (이유)`

## 폴백 규칙 (필수)

- `references/code-node-constraints.md`에 문장으로 없는 주장은 하지 않는다. 판단이 필요하면 "문서 근거 없음 — 확인 불가"라고만 답한다.
- 문서에 없는 채널톡 API·엔드포인트·제약(예: 별도 rate limit 수치, 존재 불확실한 함수)을 지어내지 않는다.
- R1~R6과 무관한 코드 스타일/품질 문제는 지적하지 않는다. 이 스킬의 범위는 6개 규칙 준수 여부뿐이다.
