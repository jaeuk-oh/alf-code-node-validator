// 의도적 위반 모음 — validate_code_node.py는 놓치지만 SKILL.md R1~R6 수동 검사가 잡아야 하는 3가지:
// setTimeout 사용(R3, 금지 함수) / 인자 순서 (context, memory)로 뒤바뀜(R6) /
// memory.save가 isSandbox 분기에만 있고 else 분기엔 없음(R5, 분기 단위 누락)
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
