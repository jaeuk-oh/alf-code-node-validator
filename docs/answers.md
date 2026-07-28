# 예선 답안 초안

> 근거: `docs/decisions.md`, `src/skills/verify-alf-code-node/SKILL.md`, `tests/results.md`, `README.md`, `src/skills/verify-alf-code-node/references/code-node-constraints.md`
> 파일에 없는 내용은 지어내지 않고 "보완 필요"로 표시. 각 문항 글자수(공백 포함)는 실제 측정값.

---

## 문항1. 무엇을 / 누가 / 어떤 상황에서 겪는 문제인가 (제한 800자, 실측 740자)

채널톡 ALF Code node에 커스텀 JavaScript를 넣는 고객사 개발자·운영자가, 문서에 명문화된 숨은 제약을 어겨도 작성 시점엔 에러가 나지 않아 배포 후에야 조용히 실패하는 문제다.

채널톡 ALF는 워크플로 자동화 안에서 Code node를 제공해, 고객사가 응답 가공·외부 시스템 연동·대화 상태 저장 같은 로직을 JavaScript로 직접 작성하게 한다. 문제는 이 Code node가 일반 Node.js 환경이 아니라 여러 제약이 걸린 샌드박스라는 점이다. 실행 시간은 60초로 제한되고, HTTP 요청은 axios만 허용되며, require는 axios·crypto 두 라이브러리로만 한정된다. process·eval·setTimeout 같은 함수는 아예 금지돼 있고, 함수 시그니처도 (memory, context, isSandbox) 순서를 지켜야 한다. 노드 간 데이터를 넘기는 memory 객체도 put()만 호출하고 save()를 빠뜨리면 값이 저장되지 않는다.

문제는 이 제약들이 문법 오류를 일으키지 않는다는 점이다. setTimeout으로 지연 로직을 짜거나, 함수 인자 순서를 (context, memory)로 뒤바꾸거나, if/else 중 한쪽 분기에서만 save()를 호출해도 코드는 정상 실행된다. 그 결과 개발자는 샌드박스 테스트를 통과했다고 믿고 배포하지만, 실제 대화에서 특정 분기를 탈 때만 데이터가 유실되거나 외부 호출이 조용히 막히는 식으로 뒤늦게 문제를 발견한다.

---

## 문항2. 왜 이 문제인가 + 출처 URL (제한 800자, 실측 653자)

이 문제를 고른 이유는 두 가지다.

첫째, 제약이 추측이 아니라 채널톡 공식 문서(https://developers.channel.io/en/articles/Code-node-fdcd71b4)에 문장 단위로 명문화돼 있어, 그대로 검증 규칙으로 옮길 수 있다. 문서는 "Maximum execution time: 60 seconds"라고 실행 시간 제한을 못박고, memory 사용법에 대해서도 "If you only call memory.put() without calling save(), changes will not be saved."라고 실패 조건을 명시한다. 이런 문장은 해석의 여지가 거의 없어 각 문장을 규칙(R1~R6) 하나에 1:1로 대응시킬 수 있었다. 근거가 흐릿한 문제(예: 수치는 있지만 가드레일화가 애매한 rate limit)보다 실제 코드로 옮기기 쉬웠다.

둘째, ALF는 채널톡이 밀고 있는 AI 자동화 플랫폼의 핵심 기능이다. Code node는 그 안에서 고객사가 자체 로직을 끼워 넣는 통로이므로, 여기서 발생하는 조용한 실패는 단순 버그가 아니라 AI 워크플로 전체의 신뢰성 문제로 이어진다. 검증기가 배포 전에 이런 위반을 잡아주면, 채널톡의 핵심 제품 위에서 실제로 반복될 수 있는 실패를 예방하는 효과가 크다고 판단했다.

---

## 문항3. 어떻게 작동하는가 (제한 1000자, 실측 995자)

이 플러그인은 Code node용 JS 코드를 R1~R6 6개 규칙으로 검사한다. R1 언어(JavaScript인가), R2 60초 안에 끝날 구조인가, R3 금지 함수·라이브러리(require는 axios·crypto만, HTTP는 axios만, process·eval·setTimeout 등 금지), R4 isSandbox 분기에서 외부 네트워크 호출을 안 하는가, R5 memory.put() 뒤 memory.save()가 있는가, R6 함수 시그니처 인자 순서(memory, context, isSandbox)가 맞는가다. 각 규칙은 위반/위반 없음/확인 불가/해당 규칙 대상 아님 네 상태로 표기되고, 위반이면 무엇이·왜 위반·문서 근거 문장·수정안 네 항목으로 리포트한다.

검증은 두 층으로 동작한다. 1차는 보조 정적 스크립트(validate_code_node.py)로, fetch( 사용, isSandbox 분기 내부 http 호출, memory.put 뒤 save 없음(파일 전체 기준), 과도한 루프 네 가지만 자동 탐지한다. 이 스크립트는 R1, R3 전체 금지 목록, R6 인자 순서, 분기별 save 누락은 검사하지 못한다. 2차는 SKILL의 R1~R6 수동 검사로, 스크립트가 다루지 않거나 놓치는 부분을 문서(references/code-node-constraints.md)와 대조해 채운다. 스크립트 결과는 참고용 1차 스캔일 뿐이며, 최종 리포트는 이 수동 절차로 작성한다.

정보가 부족하거나 판단이 서지 않을 때는 추측하지 않는다. 문서에 근거 문장이 없으면 위반으로 단정하지 않고 "문서 근거 없음 — 확인 불가"라고만 답하며, 존재하지 않는 채널톡 API·제약을 지어내지 않는다. 실제 실행 시간처럼 정적으로 판단 불가능한 것은 "확인 불가"로, isSandbox 분기가 없는 코드의 R4처럼 규칙이 해당하지 않는 경우는 "해당 규칙 대상 아님"으로 표기해 위반 없음과 구분한다. R1~R6과 무관한 코드 스타일 문제는 지적하지 않는다.

---

## 문항4. AI를 어떻게 썼는가 (제한 800자, 실측 720자)

AI(Claude)에게는 실행·조사가 필요한 작업을 맡겼다. 채널톡 공식 문서를 URL로 직접 열어 제약 문장을 원문 그대로 추출해 references/code-node-constraints.md로 정리하는 일, SKILL.md 검증 절차와 validate_code_node.py 스크립트의 초안 작성, tests/ 아래 정상·위반 예시 코드와 실행 로그 정리를 모두 AI가 수행했다.

반면 문제를 무엇으로 할지, 검증 범위를 어디까지로 한정할지, 정보가 부족할 때 어떻게 답하게 할지는 내가 판단했다. 조사된 후보 A~D 중 근거가 명문화돼 검증 규칙으로 옮기기 쉬운 C(ALF Code node)를 골랐고, 검증 스크립트는 로직을 건드리지 않고 딱 네 가지 패턴 매칭만 하도록 범위를 고정했으며, 문서에 없는 내용은 위반으로 단정하지 말고 "확인 불가"로만 답하도록 폴백 규칙을 SKILL.md에 명시하게 했다.

막혔던 지점은 AI가 처음 제안한 검증 규칙(R1~R5: 언어/60초/HTTP axios/isSandbox 차단/memory.save)이었다. 검토해보니 require 제한을 포함한 금지 함수 검사와 함수 인자 순서 검사가 빠져 있었다. 이를 지적하자 AI는 기존 R3(HTTP axios)를 "금지 함수·라이브러리" 규칙으로 확장하고 R6(함수 시그니처)을 신설해 R1~R6로 갱신했다(docs/decisions.md D-002, "거절/수정한 AI 제안" 기록).

---

## 문항5. 어떻게 검증했는가 (제한 800자, 실측 778자)

검증은 tests/ 아래 세 예시 파일과 실행 로그(tests/results.md)로 확인했다.

pass_example.js는 채널톡 공식 isSandbox 예시 코드 그대로다. 자동 스크립트 0건, 수동 R1~R6 전체 위반 없음으로 자동·수동이 일치해, 정상 코드에서 오탐이 없음을 확인했다.

fail_script_example.js는 fetch 사용, isSandbox 분기 내 외부 호출, 파일 전체에 save 없음, while(true) 네 가지를 의도적으로 넣었다. 자동 스크립트가 정확히 4건(R2·R3·R4·R5)을 탐지했고 수동 검사와도 일치해, 설계된 범위 안에서는 위반을 놓치지 않았다.

fail_manual_example.js는 스크립트가 못 잡는 위반만 모았다: setTimeout(금지 함수), 인자 순서 (context, memory) 뒤바뀜, isSandbox 분기에만 save()가 있고 다른 분기엔 없는 경우다. 자동 스크립트는 0건을 반환해 겉보기엔 통과였지만, 수동 R1~R6은 R3·R5·R6 세 건을 정확히 잡아냈다. 이 대비(자동 0건 vs 수동 3건)가 이중 검증 구조가 실제로 필요함을 보여주는 핵심 증거다.

검증 중 스크립트의 한계도 드러났다. fail_script_example.js 초안에서는 주석에 적어둔 "while(true)"라는 문구까지 코드로 오인해 의도한 4건 대신 5건이 나온 적이 있다(docs/decisions.md D-004) — 정적 패턴 매칭이 주석·문자열을 코드와 구분 못한다는 한계를 실행 중 확인한 사례다.

---

## 보완 필요

- 없음 — 5개 문항 모두 기존 파일(decisions.md, SKILL.md, tests/results.md, README.md, references/)에 있는 사실만으로 작성 가능했음.
