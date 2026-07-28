# alf-code-node-validator

채널톡 ALF(FrontALF) Code node용 JavaScript 코드가 공식 문서의 제약을 지키는지 검증하는 Codex 플러그인.

## 한눈에 보기

**한 줄 요약**: 채널톡 챗봇 자동화(ALF)에 들어가는 커스텀 JS 코드를, 배포하기 전에 "숨겨진 규칙 어긴 거 없어?"라고 자동으로 검사해주는 도구.

| | |
|---|---|
| **언제 쓰나** | ALF의 Code node(코드 블록)에 JS 코드를 작성하고, 실제로 배포하기 **전** |
| **누가 쓰나** | 채널톡을 도입한 회사에서 챗봇 자동화 로직을 직접 코딩하는 개발자 |
| **왜 쓰나** | 아래 "왜 필요한가" 참고 — 규칙을 어겨도 코드가 에러 없이 그냥 실행돼서, 배포 후에야 조용히 문제가 드러나기 때문 |
| **어떻게 쓰나** | Codex 플러그인으로 설치하고, 코드를 `@verify-alf-code-node`에 넘기면 위반 여부 + 근거 + 수정안을 리포트로 받음 |

## 1. 왜 필요한가

채널톡 ALF Code node는 겉보기엔 그냥 JS를 쓰는 코드 블록이지만, [공식 문서](https://developers.channel.io/en/articles/Code-node-fdcd71b4)에 아래처럼 일반 Node.js와 다른 제약이 정해져 있다.

- JavaScript만 가능
- 실행은 60초 안에 끝나야 함
- HTTP 요청은 axios로만 (fetch 안 됨)
- `require`는 `axios`·`crypto`만 허용
- 이 함수들은 아예 금지: `process`/`global`/`Buffer`/`eval`/`Function`/`setTimeout`/`setInterval`/`clearTimeout`/`clearInterval`/`setImmediate`/`clearImmediate`
- `isSandbox=true`(테스트 모드)일 땐 axios 외부 네트워크 요청이 막힘
- 데이터를 저장하려면 `memory.put()` 다음에 `memory.save()`까지 반드시 호출해야 함(안 하면 저장 자체가 안 됨)
- 함수는 `(memory, context[, isSandbox])` 순서로 인자를 받아야 함

**문제는 이 규칙들을 어겨도 코드가 문법적으로는 멀쩡해서, 작성 시점엔 에러가 전혀 안 뜬다는 것.** 대신 배포하고 나서야 조용히 문제가 터진다 — 예를 들어 `memory.save()`를 빼먹으면 데이터가 그냥 저장이 안 되고, 테스트(샌드박스)는 통과했는데 실제 대화 중 특정 분기를 탈 때만 깨지기도 한다. 이런 함정을 사람이 코드리뷰로 매번 잡기는 번거로우니, 이 플러그인이 그 역할을 대신한다.

## 2. 이 플러그인이 하는 일

Code node용 JS 코드를 받아서 아래 R1~R6 규칙 6개를 검사하고, 위반이 있을 때마다 다음 4가지를 알려준다.

- 무엇이 (위반한 코드 부분)
- 왜 위반인지
- references 근거 문장 (공식 문서 원문 그대로 인용 — 지어내지 않음)
- 수정안

| 규칙 | 내용 |
|---|---|
| R1 | 언어 = JavaScript인가 |
| R2 | 60초 안에 끝날 구조인가 |
| R3 | 금지 함수·라이브러리를 사용하지 않는가 |
| R4 | isSandbox 분기에서 외부 네트워크 호출을 안 하는가 |
| R5 | `memory.put()` 뒤 `memory.save()`가 있는가 |
| R6 | 함수 시그니처(인자 순서)가 올바른가 |

각 규칙은 `위반` / `위반 없음` / `확인 불가` / `해당 규칙 대상 아님` 네 가지 상태 중 하나로 표기된다. ("확인 불가"·"해당 규칙 대상 아님"이 왜 따로 있는지는 아래 "3. 어떻게 검사하나 — 폴백" 참고.)

## 3. 어떻게 검사하나 (2단계 구조)

이 플러그인은 자동 스크립트 하나만 믿지 않고, 두 단계로 나눠서 검사한다.

**1단계 — 보조 정적 스크립트** (`src/scripts/validate_code_node.py`)
빠르게 텍스트 패턴만 자동으로 훑는다.
- 잡는 것: `fetch(` 사용(R3 일부), isSandbox 분기 안의 http 호출(R4), `memory.put(` 뒤 `memory.save(` 없음(R5, **파일 전체 기준**), `while(true)`/`for(;;)` 같은 무한/과도 반복(R2 일부)
- 못 잡는 것: R1(언어 판별), R3의 금지 함수 전체 목록, R6(인자 순서), 분기별 `memory.save` 누락

**2단계 — SKILL(`verify-alf-code-node`)의 R1~R6 수동 검사**
1단계 스크립트가 아예 못 보는 부분(R1·R3 전체·R6)과, 구조적으로 놓치는 부분(분기별 `save` 누락)을 공식 문서와 직접 대조해서 채운다. **1단계는 참고용 1차 스캔일 뿐이고, 최종 판정은 반드시 이 2단계에서 내린다.**

**폴백 — 판단이 애매하거나 근거가 없을 때는 추측하지 않는다**
- 공식 문서(`references/code-node-constraints.md`)에 근거 문장이 없으면 위반이라고 단정하지 않고 "문서 근거 없음 — 확인 불가"라고만 답한다. 채널톡 API·제약을 지어내지 않는다.
- 정적 분석으로 알 수 없는 것(예: 실제 실행 시간)도 위반 단정 대신 `확인 불가`로 표기한다.
- 애초에 해당 규칙이 적용될 상황이 아니면(예: `isSandbox` 분기가 아예 없는 코드에 R4를 적용) `해당 규칙 대상 아님`으로 표기해 `위반 없음`과 구분한다.
- R1~R6과 상관없는 코드 스타일·품질 지적은 하지 않는다 — 딱 6개 규칙 준수 여부만 본다.

## 4. 설치·사용법

저장소 루트에서 Codex 로컬 마켓플레이스 등록 (마켓플레이스 정의 파일: `.agents/plugins/marketplace.json`):
```
codex plugin marketplace add ./.agents/plugins/marketplace.json
```

Codex 실행 후 플러그인 설치:
```
/plugins
```
목록에서 `alf-code-node-validator`를 찾아 설치한다.

호출:
```
@verify-alf-code-node
```
로 검사할 Code node JS 코드(파일 경로 또는 붙여넣기)를 전달한다.

## 5. 실제로 검증해본 예시

`tests/results.md`에 실제 실행 로그 전체가 있다. 요약하면:

| 케이스 | 1단계(자동 스크립트) | 2단계(수동 R1~R6) | 무엇을 확인했나 |
|---|---|---|---|
| `tests/pass_example.js` (공식 isSandbox 예시 기반) | 0건 | 전 규칙 위반 없음 | 정상 코드에서 자동·수동 모두 오탐 없음 |
| `tests/fail_script_example.js` | 4건 (R2·R3·R4·R5) | 동일하게 R2·R3·R4·R5 위반 | 자동 스크립트가 잡아야 할 위반을 놓치지 않음 |
| `tests/fail_manual_example.js` | **0건** | **R3(setTimeout)·R5(분기별 save 누락)·R6(인자 순서) 3건 위반** | 자동검사만으론 놓치는 위반을 2단계 수동 검사가 잡아냄 |
| 문서에 없는 함수(`someInternalHelper`) 포함 코드 ※ | — | "공식 문서에 근거 없어 판단하지 않음" | 폴백 규칙이 위반을 지어내지 않고 정직하게 동작 |

특히 `fail_manual_example.js` 사례가 이 플러그인이 왜 2단계 구조인지를 잘 보여준다: **자동 스크립트만 돌리면 "0건 발견"으로 통과한 것처럼 보이지만**, 실제로는 `setTimeout` 사용(금지 함수), `memory.save` 분기별 누락, 인자 순서 `(context, memory)` 뒤바뀜까지 3건의 진짜 위반이 숨어 있었다. 자동 스크립트 하나만 썼다면 이 3건은 그대로 배포됐을 것이다.

※ 폴백 사례는 Codex CLI 로컬 실행(D-005 기록)에서 실제로 관측된 결과다. 위 세 케이스(`pass_example.js`/`fail_script_example.js`/`fail_manual_example.js`)는 이 저장소 안에서 스크립트를 직접 재실행해 확인한 것이고, 폴백 사례는 그와 동일 세션이 아닌 별도의 Codex 실행에서 나온 결과다. 추정이나 예상이 아니라 실제 실행에서 관측된 동작이다.

## 6. 한계 (이 도구가 못 하는 것)

- 정적 분석만으로는 실제 실행 시간(60초 초과 여부)을 단정할 수 없다. 런타임에서만 확정 가능하므로 애매한 구조는 위반 단정 대신 `확인 불가`로 표기한다.
- 1단계의 자동 검사 4가지는 텍스트/정규식 패턴 매칭이라 주석이나 문자열 리터럴 안의 키워드도 실제 코드와 구분하지 못하고 매칭될 수 있다(오탐 가능). 실제로 테스트 파일 작성 중 주석에 적어둔 `while(true)`라는 문구가 오탐으로 잡힌 적이 있다.
- 1단계 스크립트의 `memory.save` 검사는 분기 단위가 아니라 파일 전체 기준이다. 파일 어딘가에 `save()`가 하나라도 있으면 다른 분기의 누락을 놓친다 — 이 부분은 반드시 2단계 R5 수동 검사로 분기별 확인이 필요하다.
- R1(언어 판별), R3의 금지 함수 전체 목록(`process`/`global`/`Buffer`/`eval`/`Function`/`setTimeout`/`setInterval`/`clearTimeout`/`clearInterval`/`setImmediate`/`clearImmediate`, `XMLHttpRequest` 포함), R6(함수 시그니처 인자 순서)은 1단계 스크립트가 검사하지 않고 2단계 수동 절차에서만 확인한다.

## 참고

- 근거 문서: `src/skills/verify-alf-code-node/references/code-node-constraints.md`
- 검증 절차: `src/skills/verify-alf-code-node/SKILL.md`
- 보조 스크립트: `src/scripts/validate_code_node.py`
- 테스트/실행 로그: `tests/results.md`
- 개발 경위·의사결정 기록: `docs/decisions.md`
