#!/usr/bin/env python3
"""ALF Code node JS 정적 검사기.

references/code-node-constraints.md 근거 기반 4가지 패턴만 확인한다:
1. fetch( 사용 (axios 위반 후보)
2. memory.put( 있는데 memory.save( 없음 (유실 경고)
3. isSandbox 분기 내 http 호출 흔적 (샌드박스 위반 후보)
4. 명백한 과도 루프 (60초 초과 위험 경고)

이 스크립트는 정적 텍스트/패턴 매칭만 수행한다. R1(언어), R3의 금지 함수 전체 목록
(process/global/Buffer/eval/Function/setTimeout 등), R6(함수 시그니처)은 검사하지
않는다 — SKILL.md의 수동 R1~R6 절차에서 확인해야 한다.
"""
import argparse
import re
import sys

HTTP_CALL_RE = re.compile(r"\baxios\s*\.\s*(get|post|put|delete|patch|request)\s*\(|\bfetch\s*\(")


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def check_fetch(text):
    findings = []
    for m in re.finditer(r"\bfetch\s*\(", text):
        ln = line_of(text, m.start())
        findings.append({
            "규칙": "R3 금지 함수·라이브러리 (HTTP는 axios만 허용)",
            "라인 힌트": f"{ln}번째 줄 근처: fetch(",
            "근거요약": '"HTTP requests inside the node must use axios." (code-node-constraints.md)',
            "수정안": "fetch(...) 호출을 axios.get(...)/axios.post(...) 등으로 교체",
        })
    return findings


def check_memory_save(text):
    findings = []
    put_matches = list(re.finditer(r"\bmemory\.put\s*\(", text))
    if put_matches and not re.search(r"\bmemory\.save\s*\(", text):
        first = put_matches[0]
        ln = line_of(text, first.start())
        findings.append({
            "규칙": "R5 memory.put() 뒤 memory.save() 필수",
            "라인 힌트": f"{ln}번째 줄 근처: memory.put( (파일 전체에 memory.save( 없음)",
            "근거요약": '"If you only call memory.put() without calling save(), changes will not be saved." (code-node-constraints.md)',
            "수정안": "memory.put(...) 이후 해당 실행 경로 끝에 memory.save() 호출 추가",
        })
    return findings


def _find_brace_block(text, open_brace_index):
    """open_brace_index가 가리키는 '{' 와 짝이 맞는 '}' 직전까지의 범위(end index, 배타적)를 반환."""
    depth = 1
    i = open_brace_index + 1
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return i - 1  # '}' 위치


def check_isSandbox_http(text):
    findings = []
    for m in re.finditer(r"if\s*\(\s*isSandbox(?:\s*===?\s*true)?\s*\)\s*\{", text):
        open_brace = m.end() - 1
        block_end = _find_brace_block(text, open_brace)
        block = text[open_brace + 1:block_end]
        http_call = HTTP_CALL_RE.search(block)
        if http_call:
            ln = line_of(text, open_brace + 1 + http_call.start())
            findings.append({
                "규칙": "R4 isSandbox 분기 내 외부 네트워크 호출 금지",
                "라인 힌트": f"{ln}번째 줄 근처: isSandbox 분기 내부 HTTP 호출 흔적",
                "근거요약": '"external network requests made through axios are blocked when isSandbox is set to true." (code-node-constraints.md)',
                "수정안": "isSandbox 분기 안에서는 axios/fetch 호출을 제거하고 memory 조작만 수행, 실제 외부 호출은 else 경로로 이동(공식 isSandbox 예시 참고)",
            })
    return findings


def check_excessive_loop(text):
    findings = []
    loop_patterns = [
        (r"while\s*\(\s*true\s*\)", "while(true) 무한 루프"),
        (r"for\s*\(\s*;\s*;\s*\)", "for(;;) 무한 루프"),
    ]
    for pat, label in loop_patterns:
        for m in re.finditer(pat, text):
            ln = line_of(text, m.start())
            findings.append({
                "규칙": "R2 60초 안에 끝날 구조 (과도 루프 경고)",
                "라인 힌트": f"{ln}번째 줄 근처: {label}",
                "근거요약": '"Maximum execution time: 60 seconds" (code-node-constraints.md) — 종료 조건 없는 루프는 60초 초과 위험',
                "수정안": "루프에 명확한 종료 조건과 반복 상한을 추가",
            })
    for m in re.finditer(r"for\s*\([^)]*?<\s*([0-9]{6,})[^)]*\)", text):
        ln = line_of(text, m.start())
        findings.append({
            "규칙": "R2 60초 안에 끝날 구조 (과도 루프 경고)",
            "라인 힌트": f"{ln}번째 줄 근처: 반복 횟수 상수가 {m.group(1)}로 매우 큼",
            "근거요약": '"Maximum execution time: 60 seconds" (code-node-constraints.md) — 대량 반복은 60초 초과 위험',
            "수정안": "반복 횟수를 줄이거나 배치/페이지네이션으로 분할",
        })
    return findings


def run_checks(text):
    findings = []
    findings += check_fetch(text)
    findings += check_memory_save(text)
    findings += check_isSandbox_http(text)
    findings += check_excessive_loop(text)
    return findings


LIMITATIONS = [
    "실제 실행 시간(60초 초과 여부)은 런타임에서만 확정 가능. while(true)/for(;;)/대량 반복 상수 같은"
    " 구조적 패턴만 경고하며, 60초 초과 여부 자체를 단정하지 않는다.",
    "isSandbox 분기 탐지는 `if (isSandbox) { ... }` / `if (isSandbox === true) { ... }` 형태의"
    " 중괄호 블록만 인식한다. 삼항 연산자, 중괄호 없는 단문 if 등 다른 문법 변형은 탐지하지 못할 수 있다.",
    "네 가지 검사(fetch(, memory.put(/memory.save(, isSandbox 분기 내 http 호출, 과도 루프) 모두"
    " 텍스트/정규식 패턴 매칭이다. 주석이나 문자열 리터럴 안에 있는 키워드도 실제 코드와 구분하지"
    " 못하고 함께 매칭될 수 있다(오탐 가능). 예: 주석에 \"while(true)\"라는 문구를 그대로 적으면"
    " 실제 코드가 아니어도 R2 위반으로 잡힌다. 최종 판단은 사람이 확인해야 한다.",
    "memory.put()/memory.save() 검사는 분기 단위가 아니라 파일 전체 기준이다: 파일 어딘가에"
    " memory.save(가 하나라도 있으면, 그것이 다른 분기의 것이라도 위반으로 보고하지 않는다."
    " 일부 if/else 분기에만 save()가 빠진 경우는 이 스크립트가 놓치므로 SKILL.md의 R5 수동 검사에서"
    " 분기별로 확인해야 한다.",
    "R1(언어=JavaScript 여부), R3의 금지 함수 전체 목록(require 남용/process/global/Buffer/eval/"
    "Function/setTimeout/setInterval/clearTimeout/clearInterval/setImmediate/clearImmediate),"
    " R6(함수 시그니처 인자 순서)은 이 스크립트가 검사하지 않는다 — SKILL.md의 수동 R1~R6 절차에서 확인한다.",
]


def format_report(path, findings):
    lines = []
    lines.append(f"파일: {path}")
    lines.append(f"검사 결과: {len(findings)}건 발견")
    lines.append("")
    if not findings:
        lines.append("정적 검사에서 위반 후보를 찾지 못함.")
    else:
        for i, f in enumerate(findings, 1):
            lines.append(f"[{i}] 규칙: {f['규칙']}")
            lines.append(f"    라인 힌트: {f['라인 힌트']}")
            lines.append(f"    근거요약: {f['근거요약']}")
            lines.append(f"    수정안: {f['수정안']}")
            lines.append("")
    lines.append("한계 (정적 분석):")
    for lim in LIMITATIONS:
        lines.append(f"- {lim}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="ALF Code node JS 정적 검사기")
    parser.add_argument("path", help="검사할 Code node JS 파일 경로")
    args = parser.parse_args(argv)

    with open(args.path, "r", encoding="utf-8") as f:
        text = f.read()

    findings = run_checks(text)
    print(format_report(args.path, findings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
