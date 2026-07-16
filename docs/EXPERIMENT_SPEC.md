# 实验规范

## M9

M9 是固定任务、固定模型的四组消融：G1 Text、G2 Protocol、G3 Protocol + StateVector、G4 Protocol + StateVector + SharedMemory。有效 freeze 为 `cc7aac0417afb6acab47baaf7449459692fa9444`，共 240 条 final records，模型参数包含 `temperature=0`、`max_tokens=256`、`timeout_seconds=300`、三组 seed 与 2000 次 Bootstrap。

## M9.1

M9.1 是独立补充实验：S1 Text baseline、S2 CompactProtocol V2、S3 CompactProtocol V2 + StateVector V2、S4 CompactProtocol V2 + StateVector V2 + GatedSharedMemory V2。有效 freeze 为 `c79fd4826627bf61faf5d90540a014d243a59edd`，Spec SHA 为 `3ad520c75bb66e8a4617daa64d6824183cbeaa5a1e1cb01dcd50035f145231f6`。

正式 Spec、任务顺序、模型、参数、评测边界和统计方法在运行前冻结。private tests 只在 Sandbox 内使用，不能进入 Agent 上下文。
