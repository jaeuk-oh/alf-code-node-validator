# 검증 결과 (tests/)

> 규칙 기준: `src/skills/verify-alf-code-node/SKILL.md` 최종 R1~R6.
> 근거: `src/skills/verify-alf-code-node/references/code-node-constraints.md`
> 자동검사: `python3 src/scripts/validate_code_node.py <파일>` 실제 실행 결과를 그대로 옮김(가공 없음).
> 수동검사: SKILL.md R1~R6 절차를 사람이 코드에 직접 적용한 결과.

---

## 1) tests/pass_example.js — 정상 케이스 (공식 isSandbox 예시 기반)

### 입력 파일
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

### 자동검사 출력 (validate_code_node.py 실행 결과)
```
파일: tests/pass_example.js
검사 결과: 0건 발견

정적 검사에서 위반 후보를 찾지 못함.
한계 (정적 분석):
- 실제 실행 시간(60초 초과 여부)은 런타임에서만 확정 가능. while(true)/for(;;)/대량 반복 상수 같은 구조적 패턴만 경고하며, 60초 초과 여부 자체를 단정하지 않는다.
- isSandbox 분기 탐지는 `if (isSandbox) { ... }` / `if (isSandbox === true) { ... }` 형태의 중괄호 블록만 인식한다. 삼항 연산자, 중괄호 없는 단문 if 등 다른 문법 변형은 탐지하지 못할 수 있다.
- fetch(/axios 호출 탐지는 텍스트 패턴 매칭이다. 문자열 리터럴이나 주석 안에 있는 텍스트도 함께 걸릴 수 있어(오탐 가능) 최종 판단은 사람이 확인해야 한다.
- memory.put()/memory.save() 검사는 분기 단위가 아니라 파일 전체 기준이다: 파일 어딘가에 memory.save(가 하나라도 있으면, 그것이 다른 분기의 것이라도 위반으로 보고하지 않는다. 일부 if/else 분기에만 save()가 빠진 경우는 이 스크립트가 놓치므로 SKILL.md의 R5 수동 검사에서 분기별로 확인해야 한다.
- R1(언어=JavaScript 여부), R3의 금지 함수 전체 목록(require 남용/process/global/Buffer/eval/Function/setTimeout/setInterval/clearTimeout/clearInterval/setImmediate/clearImmediate), R6(함수 시그니처 인자 순서)은 이 스크립트가 검사하지 않는다 — SKILL.md의 수동 R1~R6 절차에서 확인한다.
```

### 수동검사 리포트 (R1~R6)
- R1: 위반없음 — JavaScript 문법.
- R2: 위반없음 — 무한 루프·대량 반복 없음.
- R3: 위반없음 — `require('axios')`만 사용(허용 예외), 금지 함수(`process`/`global`/`Buffer`/`eval`/`Function`/`setTimeout`/`setInterval`/`clearTimeout`/`clearInterval`/`setImmediate`/`clearImmediate`) 없음, HTTP는 `axios.get`만 사용.
- R4: 위반없음 — `if (isSandbox) { ... }` 분기 내부에는 `memory.put`/`console.log`/`memory.save`만 있고 axios/fetch 호출 없음. 실제 `axios.get` 호출은 else 경로(13번째 줄)에만 있음.
- R5: 위반없음 — isSandbox 분기(6~10번째 줄)와 else 분기(13~16번째 줄) 양쪽 모두 `memory.put` 뒤에 `memory.save`가 있음.
- R6: 위반없음 — `(memory, context, isSandbox)` 순서 정확, `isSandbox`는 세 번째 인자.

### 해석
자동검사·수동검사 모두 위반 없음으로 일치. 채널톡 공식 예시 코드가 이 스킬의 R1~R6 규칙과 스크립트 양쪽에서 오탐 없이 "정상"으로 판정됨을 확인.

---

## 2) tests/fail_script_example.js — 스크립트가 자동으로 잡는 위반 모음

### 입력 파일
```javascript
export const handler = async (memory, context, isSandbox) => {
  if (isSandbox) {
    fetch("https://example.com/test");
    memory.put('smallTalk', 'bigResult');
  }

  while (true) {
    console.log('polling');
  }
}
```

> 각주: 초기 실행 시 주석 내 while(true) 문자열로 오탐 1건 발생 → 정적 매칭의 주석 미구분 한계 확인 → 시연 명확성 위해 주석 수정 후 재실행(4건). 상세 경위는 docs/decisions.md 참조.

### 자동검사 출력 (validate_code_node.py 실행 결과)
```
파일: tests/fail_script_example.js
검사 결과: 4건 발견

[1] 규칙: R3 금지 함수·라이브러리 (HTTP는 axios만 허용)
    라인 힌트: 5번째 줄 근처: fetch(
    근거요약: "HTTP requests inside the node must use axios." (code-node-constraints.md)
    수정안: fetch(...) 호출을 axios.get(...)/axios.post(...) 등으로 교체

[2] 규칙: R5 memory.put() 뒤 memory.save() 필수
    라인 힌트: 6번째 줄 근처: memory.put( (파일 전체에 memory.save( 없음)
    근거요약: "If you only call memory.put() without calling save(), changes will not be saved." (code-node-constraints.md)
    수정안: memory.put(...) 이후 해당 실행 경로 끝에 memory.save() 호출 추가

[3] 규칙: R4 isSandbox 분기 내 외부 네트워크 호출 금지
    라인 힌트: 5번째 줄 근처: isSandbox 분기 내부 HTTP 호출 흔적
    근거요약: "external network requests made through axios are blocked when isSandbox is set to true." (code-node-constraints.md)
    수정안: isSandbox 분기 안에서는 axios/fetch 호출을 제거하고 memory 조작만 수행, 실제 외부 호출은 else 경로로 이동(공식 isSandbox 예시 참고)

[4] 규칙: R2 60초 안에 끝날 구조 (과도 루프 경고)
    라인 힌트: 9번째 줄 근처: while(true) 무한 루프
    근거요약: "Maximum execution time: 60 seconds" (code-node-constraints.md) — 종료 조건 없는 루프는 60초 초과 위험
    수정안: 루프에 명확한 종료 조건과 반복 상한을 추가

한계 (정적 분석):
- 실제 실행 시간(60초 초과 여부)은 런타임에서만 확정 가능. while(true)/for(;;)/대량 반복 상수 같은 구조적 패턴만 경고하며, 60초 초과 여부 자체를 단정하지 않는다.
- isSandbox 분기 탐지는 `if (isSandbox) { ... }` / `if (isSandbox === true) { ... }` 형태의 중괄호 블록만 인식한다. 삼항 연산자, 중괄호 없는 단문 if 등 다른 문법 변형은 탐지하지 못할 수 있다.
- fetch(/axios 호출 탐지는 텍스트 패턴 매칭이다. 문자열 리터럴이나 주석 안에 있는 텍스트도 함께 걸릴 수 있어(오탐 가능) 최종 판단은 사람이 확인해야 한다.
- memory.put()/memory.save() 검사는 분기 단위가 아니라 파일 전체 기준이다: 파일 어딘가에 memory.save(가 하나라도 있으면, 그것이 다른 분기의 것이라도 위반으로 보고하지 않는다. 일부 if/else 분기에만 save()가 빠진 경우는 이 스크립트가 놓치므로 SKILL.md의 R5 수동 검사에서 분기별로 확인해야 한다.
- R1(언어=JavaScript 여부), R3의 금지 함수 전체 목록(require 남용/process/global/Buffer/eval/Function/setTimeout/setInterval/clearTimeout/clearInterval/setImmediate/clearImmediate), R6(함수 시그니처 인자 순서)은 이 스크립트가 검사하지 않는다 — SKILL.md의 수동 R1~R6 절차에서 확인한다.
```

### 수동검사 리포트 (R1~R6)
- R1: 위반없음 — JavaScript 문법.
- R2: 위반 — 9번째 줄 `while (true) { ... }`는 종료 조건이 없어 60초 초과 위험. references: "Maximum execution time: 60 seconds".
- R3: 위반 — 5번째 줄 `fetch(...)`는 axios가 아닌 HTTP 수단. references: "HTTP requests inside the node must use axios."
- R4: 위반 — isSandbox 분기(4~7번째 줄) 내부에서 5번째 줄 `fetch(...)`로 실제 외부 요청을 시도함. references: "external network requests made through axios are blocked when isSandbox is set to true." (원문은 axios를 지칭하지만, isSandbox 분기 안에서 실제 외부 통신을 시도한다는 구조 자체가 공식 isSandbox 예시가 금지하는 패턴과 동일하므로 R4로도 지적함 — R3의 fetch 위반과 별개로 "분기 내 실제 통신 시도"라는 구조적 문제.)
- R5: 위반 — 6번째 줄 `memory.put(...)` 이후 파일 전체 어디에도 `memory.save()` 호출이 없음. references: "If you only call memory.put() without calling save(), changes will not be saved."
- R6: 위반없음 — `(memory, context, isSandbox)` 순서 정확.

### 해석
자동검사와 수동검사가 R2·R3·R4·R5에서 정확히 일치(4건 대 4건). 스크립트가 설계 목적대로 "잡아야 할 위반"을 놓치지 않고 전부 탐지함을 확인.

---

## 3) tests/fail_manual_example.js — 스크립트는 놓치지만 수동 검사가 잡아야 하는 위반 모음

### 입력 파일
```javascript
export const handler = async (context, memory, isSandbox) => {
  if (isSandbox) {
    memory.put('smallTalk', 'bigResult');
    memory.save();
    return;
  }

  setTimeout(() => {
    console.log('polling check');
  }, 100);

  memory.put('smallTalk', 'liveResult');
}
```

### 자동검사 출력 (validate_code_node.py 실행 결과)
```
파일: tests/fail_manual_example.js
검사 결과: 0건 발견

정적 검사에서 위반 후보를 찾지 못함.
한계 (정적 분석):
- 실제 실행 시간(60초 초과 여부)은 런타임에서만 확정 가능. while(true)/for(;;)/대량 반복 상수 같은 구조적 패턴만 경고하며, 60초 초과 여부 자체를 단정하지 않는다.
- isSandbox 분기 탐지는 `if (isSandbox) { ... }` / `if (isSandbox === true) { ... }` 형태의 중괄호 블록만 인식한다. 삼항 연산자, 중괄호 없는 단문 if 등 다른 문법 변형은 탐지하지 못할 수 있다.
- fetch(/axios 호출 탐지는 텍스트 패턴 매칭이다. 문자열 리터럴이나 주석 안에 있는 텍스트도 함께 걸릴 수 있어(오탐 가능) 최종 판단은 사람이 확인해야 한다.
- memory.put()/memory.save() 검사는 분기 단위가 아니라 파일 전체 기준이다: 파일 어딘가에 memory.save(가 하나라도 있으면, 그것이 다른 분기의 것이라도 위반으로 보고하지 않는다. 일부 if/else 분기에만 save()가 빠진 경우는 이 스크립트가 놓치므로 SKILL.md의 R5 수동 검사에서 분기별로 확인해야 한다.
- R1(언어=JavaScript 여부), R3의 금지 함수 전체 목록(require 남용/process/global/Buffer/eval/Function/setTimeout/setInterval/clearTimeout/clearInterval/setImmediate/clearImmediate), R6(함수 시그니처 인자 순서)은 이 스크립트가 검사하지 않는다 — SKILL.md의 수동 R1~R6 절차에서 확인한다.
```

**자동검사 결과: 0건 — 겉으로는 "통과"처럼 보인다.**

### 수동검사 리포트 (R1~R6)
- R1: 위반없음 — JavaScript 문법.
- R2: 위반없음 — 무한 루프·대량 반복 구조 없음 (setTimeout은 R2가 아니라 R3에서 판단).
- **R3: 위반 — 11번째 줄 `setTimeout(...)`은 금지 함수 목록에 있음.** references: "require, process, global, Buffer, eval, Function, setTimeout, setInterval, clearTimeout, clearInterval, setImmediate, clearImmediate,". 목적과 무관하게(단순 지연 실행이라도) 그 자체로 위반.
- R4: 해당 규칙 대상 아님 — isSandbox 분기(2~5번째 줄) 내부에 axios/fetch 등 외부 네트워크 호출이 없음.
- **R5: 위반 — 15번째 줄 `memory.put('smallTalk', 'liveResult')`(else 분기)에는 대응하는 `memory.save()`가 없음.** isSandbox 분기(3~4번째 줄)에는 `memory.put`→`memory.save`가 있지만, else 분기(11~15번째 줄)는 `memory.put`만 있고 `memory.save`가 없음 — "if/else 각 분기마다 따로 확인"해야 하는 R5 규칙 위반. references: "If you only call memory.put() without calling save(), changes will not be saved."
- **R6: 위반 — 4번째 줄 함수 시그니처가 `(context, memory, isSandbox)`로, `memory`가 첫 번째·`context`가 두 번째여야 하는데 순서가 뒤바뀜.** references: "함수 시그니처 (기본형)" — `export const handler = async (memory, context) => { ... }`.

### 해석 — 자동검사와 수동검사의 대비
**자동검사는 "0건 발견"으로 통과처럼 보이지만, 수동검사(R1~R6)는 3건의 실제 위반(R3 setTimeout, R5 분기 단위 save 누락, R6 인자 순서)을 잡아낸다.**

- R3 미탐 이유: 스크립트는 `fetch(`만 확인하고 `setTimeout` 등 금지 함수 전체 목록은 검사하지 않음(SKILL.md "다루지 않는 것" 항목에 이미 명시된 한계).
- R5 미탐 이유: 스크립트의 `memory.save` 검사는 파일 전체 기준이라, isSandbox 분기에 `memory.save()`가 한 번이라도 있으면 else 분기의 누락을 놓침(D-003에서 문서화한 한계).
- R6 미탐 이유: 스크립트는 함수 인자 순서를 아예 검사하지 않음(SKILL.md "다루지 않는 것" 항목에 명시).

이 파일은 "정적 패턴 매칭 보조 도구 하나만으로는 불충분하며, SKILL.md의 R1~R6 수동 검사가 반드시 최종 리포트를 작성해야 한다"는 설계 의도를 실증하는 사례다.
