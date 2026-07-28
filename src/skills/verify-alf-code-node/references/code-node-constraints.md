# ALF Code Node 제약 조건 (공식 문서 원문 기준)

> 근거 URL: https://developers.channel.io/en/articles/Code-node-fdcd71b4
> 원문 언어: 영문(공식 문서). 아래 "문서 근거 문장"은 해당 페이지의 원문 텍스트를 그대로 인용한 것이며, 문서에 없는 내용은 추가하지 않았음.
> 검증 방법: WebFetch로 렌더링된 요약이 코드 블록·목록을 누락하여, 페이지의 Next.js RSC(raw HTML) 페이로드를 직접 fetch한 뒤 관련 텍스트를 원문 그대로 추출해 대조 검증함.

---

## SKILL 규칙(R1~R6) ↔ 이 문서 근거 매핑

| SKILL 규칙 | 근거 위치(이 문서 내) |
|---|---|
| R1 언어 = JavaScript | "JavaScript 전용 언어" 행 |
| R2 60초 안에 끝날 구조 | "최대 실행 시간 60초" 행 |
| R3 금지 함수·라이브러리 사용 금지 | "`require`는 원칙적으로 금지, 예외만 허용" 행 / "허용 라이브러리는 `axios`, `crypto`뿐" 행 / "HTTP 요청은 axios만 사용" 행 |
| R4 isSandbox 분기 외부 네트워크 호출 금지 | "`isSandbox=true`면 axios 외부 네트워크 요청 차단" 행 |
| R5 memory.put() 뒤 memory.save() 필수 | "`memory.put()`만으로는 저장 안 됨" 행 |
| R6 함수 시그니처(인자 순서) | "함수 시그니처 (기본형)" / "함수 시그니처 (isSandbox 포함)" 섹션 + "함수 인자 순서: `(memory, context)`" 행 |

---

## 함수 시그니처 (기본형)

```javascript
export const handler = async (memory, context) => {
  // Write your code here
}
```

> 원문: "All code must be written inside the function format shown above."
> 인자 순서: **memory가 첫 번째, context가 두 번째**. (`context, memory` 아님 — 순서 주의)

## 함수 시그니처 (isSandbox 포함, 별도 예시)

```javascript
export const handler = async (memory, context, isSandbox) => {
  const axios = require('axios');
  if (isSandbox) {
    memory.put('smallTalk', 'bigResult');
    console.log(memory.get('smallTalk')); // "bigResult"
    memory.save();
    return;
  }

  const response = await axios.get("https://example.com");
  memory.put('smallTalk', response.data.substring(0, 10));
  console.log(memory.get('smallTalk')); // "<!DOCTYPE "
  memory.save();
}
```

> `isSandbox`는 "isSandbox" 섹션의 별도 예시에서 **세 번째 인자**로 전달됨(기본형에는 없음).

---

## 제약 규칙 표

| 규칙 | 문서 근거 문장 (원문 인용) | 위반 시 증상 |
|---|---|---|
| **JavaScript 전용 언어** | "Supported language: `JavaScript`" | 다른 언어(Python 등)로 작성 시 Code Node가 실행 자체를 지원하지 않음(문서에 다른 언어 지원 언급 없음). |
| **최대 실행 시간 60초** | "Maximum execution time: `60 seconds`" | 60초를 초과하는 로직(긴 폴링, 대량 반복, 느린 외부 응답 대기 등)은 타임아웃으로 실행 실패. |
| **함수 인자 순서: `(memory, context)`** | 기본 예시 코드: `export const handler = async (memory, context) => { ... }` (Memory/Context 섹션 Example 2건 모두 이 순서) | 인자 순서를 `(context, memory)`로 바꾸면 `memory`에 실제로는 context 객체가, `context`에는 memory 객체가 바인딩되어 `memory.get/put/save` 호출 시 런타임 오류 또는 예기치 않은 동작 발생. |
| **`require`는 원칙적으로 금지, 예외만 허용** | Restricted Functions 코드 블록: "`require, process, global, Buffer, eval, Function, setTimeout, setInterval, clearTimeout, clearInterval, setImmediate, clearImmediate,`" | `require`로 목록 외 라이브러리(예: `lodash`, `fs`)를 불러오면 차단/오류. |
| **허용 라이브러리는 `axios`, `crypto`뿐** | Supported External Libraries 코드 블록: "`axios, crypto`" | `axios`/`crypto` 외 외부 라이브러리를 require하면 실행 실패(위 Restricted Functions의 `require` 제한과 결합해 "이 두 개만 예외적으로 허용"이 성립). |
| **HTTP 요청은 axios만 사용** | "HTTP requests inside the node must use `axios`." | `fetch`, `XMLHttpRequest`, 기타 HTTP 라이브러리 사용 시 지원되지 않거나 실패. |
| **`isSandbox=true`면 axios 외부 네트워크 요청 차단** | "To prevent unintended API calls, external network requests made through `axios` are blocked when `isSandbox` is set to `true`." | 샌드박스/테스트 실행에서 실제 외부 API 호출(`axios.get(...)` 등)을 기대하면 응답을 받지 못하거나 호출이 무시됨 — 반드시 `isSandbox` 분기로 테스트용 로직과 실제 로직을 분리해야 함(예시 코드 참고). |
| **`memory.put()`만으로는 저장 안 됨 — `memory.save()` 필수** | "If you only call `memory.put()` without calling `save()`, changes will not be saved." / 표: "`save()` — Permanently saves the changes. (Must be called)" | `put()` 후 `save()`를 호출하지 않으면 변경사항이 유실되어, 다음 노드 실행이나 재실행 시 이전 값(또는 undefined)이 그대로 조회됨. 테스트 환경에서는 Diff에 변경사항이 아예 나타나지 않음: "If `memory.save()` is not called, changed data will not be saved, and no changes will appear in Diff." |

---

## 참고: 허용된 빌트인 (금지 목록에 없지만 명시적으로 문서화된 것)

| 항목 | 문서 근거 문장 (원문 인용) |
|---|---|
| Built-in JavaScript Objects | "`JSON, Math, Date, Array, Object, String, Number, Boolean, RegExp, Error, TypeError, ReferenceError, SyntaxError,`" |
| Utility Functions | "`parseInt, parseFloat, isNaN, isFinite, encodeURIComponent, decodeURIComponent, encodeURI, decodeURI,`" |
| `memory` 인터페이스 메서드 | `get(key)` — Retrieves the value for the specified key. / `put(key, value)` — Stores a value for the specified key. / `save()` — Permanently saves the changes. (Must be called) |
| `context` 구조 | "context contains environment information where the code node is executed." → `user`(Customer information), `userChat`(Consultation session information). "All data is **read-only**. → Modifying values inside context will not affect the actual data." |
| 추가 기능 요청 절차 | "The Code Node environment provides a limited set of functions and libraries. If you need additional functionality, please contact the Channel team. We will review your request and inform you whether support can be added." |

---

## 문서에 없어서 추가하지 않은 것

- 페이로드/응답 크기 제한, 메모리(RAM) 용량 제한 수치 — 문서에 언급 없음.
- `require, process, global, ...` 각 항목이 왜 금지되는지에 대한 개별 사유 설명 — 문서는 목록만 제공하고 사유는 설명하지 않음.
- Restricted Functions 목록에 `Buffer`가 포함되어 있으나, 그럼에도 `crypto`가 허용 라이브러리로 명시되어 있음(문서 원문 그대로 병기, 해석·수정 없이 사실만 기록).
