// 의도적 위반 모음 — validate_code_node.py가 자동으로 잡아야 하는 4가지:
// fetch 사용(R3) / isSandbox 분기 내 외부호출(R4) / 파일 전체에 save 없음(R5) / 종료조건 없는 무한 루프(R2)
export const handler = async (memory, context, isSandbox) => {
  if (isSandbox) {
    fetch("https://example.com/test");
    memory.put('smallTalk', 'bigResult');
  }

  while (true) {
    console.log('polling');
  }
}
