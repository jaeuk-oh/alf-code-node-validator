// 근거: references/code-node-constraints.md "함수 시그니처 (isSandbox 포함, 별도 예시)" —
// 채널톡 공식 문서(Code-node-fdcd71b4)의 isSandbox 예시 코드를 그대로 사용.
// R1~R6 전 규칙을 준수하는 정상 케이스.
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
