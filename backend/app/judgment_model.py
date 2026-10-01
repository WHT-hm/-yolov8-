"""JEV 判断模型客户端：对 YOLOv8 检测结果做自动复核。

整体流水线（见 `routers/detections.py::create_detection`）：

    用户输入（上传图片 + 可选作物类型）
            │
            ▼
    YOLOv8 检测（当前由 mock_data.create_mock_detection 占位，
                 产出 pest_types / severity / avg_confidence / boxes）
            │
            ▼
    JEV 复核（本模块 judge_yolo_result，对 YOLO 的候选识别结果做
             独立的"第二意见"判断，不改写检测结果本身）
            │
            ▼
    结果输出（DetectionRecord：YOLO 检测字段保持不变，
             JEV 复核结论写入 remark 一并返回并持久化）

设计思路：把"YOLO 这次识别得准不准"抽象成对一组类型化问题
（Choice / Score / Noul）的并行判断，而不是自由文本生成式调用。这与
TypeSafe AI 的 Jev（"System One" 判断模型）对外呈现的调用方式一致：
一次请求传入 `state`（待判断的上下文）和若干 `questions`，模型并行给出
带置信度的结构化答案。这正是 Jev 文档列出的典型用例之一——校验另一个
模型/工具的输出，而不是替它生成结果。

接入点复用了项目已有的"模型接口设置"（见 `routers/settings.py` /
`UserSettings`：`api_base_url` + `api_key` + `model_name`），不新增配置项：
用户在设置页把 `api_base_url` 填成 Jev 服务根地址（如
`https://api.typesafe.ai`），`create_detection()` 就会在每次检测后自动
触发复核；未配置、网络错误、响应格式不符预期等任何情况都会静默跳过，
不影响检测结果本身的返回（复核是增强，不是前提）。

请求/响应契约已对照官方文档确认：https://docs.typesafe.ai/introduction/quickstart
与 https://docs.typesafe.ai/primitives （2026-10 访问）。核心约定：
- 端点固定为 `POST {api_base_url}/v1/systemone`，鉴权用 `Authorization: Bearer <api_key>`。
- 请求体：`{"model", "state", "questions": {key: {"type", "instructions", "criteria"}}}`。
  `choice` 的 `criteria` 是"选项名 -> 说明"的字典；`score` 的 `criteria` 是
  按顺序排列的等级说明数组；`noul` 的 `criteria` 是可选的澄清说明字符串
  （不是字典，也不需要给"是/否"各一条）。
- 响应体：`{"model", "answers": {key: {...}}, "usage"}`；`choice` 返回
  `choice` / `confidence` / `probabilities`；`score` 返回 `score`（**数值**，
  可以落在两个等级之间，不是等级文本本身）/ `confidence` / `legend`
  （下标 -> 等级文本）/ `probabilities`；`noul` 只返回 `noul`（0~1 的概率），
  没有 `confidence` 字段。

另外需要说明：Jev 这类判断模型只做"分类/打分"式的结构化判断，不具备
目标检测模型（如 YOLOv8）的像素级定位能力，因此只负责对 YOLO 已经给出的
`pest_types` / `avg_confidence` 做复核判断，不涉及 `boxes`（检测框坐标）。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union

import httpx

from . import models


# ------------------ 通用判断模型原语（Choice / Score / Noul） ------------------

class QuestionType(str, Enum):
    CHOICE = "choice"  # 从一组互斥选项中选择一个
    SCORE = "score"  # 在一组有序等级中打分，返回值可落在两个等级之间
    NOUL = "noul"  # 是非命题的概率


@dataclass
class JudgmentQuestion:
    type: QuestionType
    instructions: str
    # choice: {选项名: 说明}；score: 按顺序排列的等级说明；noul: 可选的澄清说明（纯字符串）
    criteria: Union[Dict[str, str], List[str], str, None] = None


@dataclass
class JudgmentAnswer:
    type: QuestionType
    value: Union[str, float]  # choice: 选中的选项名；score: 等级区间上的数值位置；noul: 0~1 概率
    confidence: Optional[float] = None  # noul 类型没有此字段
    probabilities: Optional[Dict[str, float]] = None
    legend: Optional[Dict[str, str]] = None  # 仅 score 类型：下标 -> 等级文本


class JudgmentModelError(Exception):
    """判断模型未配置、不可达，或响应格式不符合预期时抛出，调用方应捕获并视为"未复核"。"""


class JudgmentModelClient:
    """基于用户在设置页配置的接口信息发起判断请求。

    对照 https://docs.typesafe.ai/introduction/quickstart 确认：端点固定为
    `{api_base_url}/v1/systemone`，与具体问题无关——`api_base_url` 应填 Jev
    服务的根地址（如 `https://api.typesafe.ai`），不是某个自定义路径。
    """

    _ENDPOINT_PATH = "/v1/systemone"

    def __init__(self, api_base_url: str, api_key: Optional[str], model_name: Optional[str]):
        if not api_base_url:
            raise JudgmentModelError("未配置判断模型接口地址（api_base_url）")
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name or "jev-latest"

    def _build_payload(self, state: str, questions: Dict[str, JudgmentQuestion]) -> dict:
        def question_body(q: JudgmentQuestion) -> dict:
            body = {"type": q.type.value, "instructions": q.instructions}
            if q.criteria is not None:
                body["criteria"] = q.criteria
            return body

        return {
            "model": self.model_name,
            "state": state,
            "questions": {key: question_body(q) for key, q in questions.items()},
        }

    def _parse_response(self, data: dict, questions: Dict[str, JudgmentQuestion]) -> Dict[str, JudgmentAnswer]:
        answers_raw = data.get("answers")
        if answers_raw is None:
            raise JudgmentModelError("判断模型响应缺少 answers 字段")
        results: Dict[str, JudgmentAnswer] = {}
        for key, question in questions.items():
            item = answers_raw.get(key)
            if item is None:
                raise JudgmentModelError(f"判断模型响应缺少字段：{key}")
            if question.type == QuestionType.CHOICE:
                value = item.get("choice")
            elif question.type == QuestionType.SCORE:
                value = item.get("score")
            else:
                value = item.get("noul")
            if value is None:
                raise JudgmentModelError(f"判断模型响应字段 {key} 缺少预期取值")
            results[key] = JudgmentAnswer(
                type=question.type,
                value=value,
                confidence=item.get("confidence"),
                probabilities=item.get("probabilities"),
                legend=item.get("legend"),
            )
        return results

    async def evaluate(self, state: str, questions: Dict[str, JudgmentQuestion]) -> Dict[str, JudgmentAnswer]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = self._build_payload(state, questions)
        url = f"{self.api_base_url}{self._ENDPOINT_PATH}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise JudgmentModelError(f"判断模型返回错误状态码 {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise JudgmentModelError(f"判断模型请求失败：{exc}") from exc
        except ValueError as exc:  # JSON 解析失败
            raise JudgmentModelError(f"判断模型响应不是合法 JSON：{exc}") from exc

        return self._parse_response(data, questions)


# ------------------ 复核 YOLO 识别结果 ------------------
#
# JEV 扮演的是"第二意见"角色：YOLO（目前由 mock_data 占位）先给出一个候选
# 识别结果（pest_name + confidence），再把这个候选结果连同图片上下文交给
# JEV 复核，判断该结果是否可信、YOLO 报出的置信度是否与证据强度相符，
# 以及如果不可信，更可能是哪一种。复核结论不会反过来修改 YOLO 的输出，
# 只作为旁路信息（`DetectionRecord.remark`）供人工参考。

def build_yolo_verification_questions(
    predicted_pest: str,
    predicted_confidence: float,
    alternative_candidates: List[str],
) -> Dict[str, JudgmentQuestion]:
    """构造"复核 YOLO 识别结果"所需的类型化问题。

    设计上的优化点：
    - 三个问题合并成一次请求（而不是三次串行调用），对应 Jev "一次调用
      并行且独立地回答多个类型化问题"的能力，减少往返延迟。
    - `result_plausible` 单独用 Noul 判断"这个结果本身站不站得住脚"，不与
      "该不该信任这个置信度数值"混在一起——置信度校准不佳（比如模型对某些
      类别系统性过度自信）是比"识别错类"更隐蔽的失败模式，值得单独量化。
    - `likely_alternative` 的候选集按 `crop_type` 预先过滤、且**排除了 YOLO
      已选中的类别**，缩小选项范围、降低歧义；它只在 `result_plausible`
      判定为不可信时才有业务意义，但仍与其他问题一起并行问出，避免
      "先判断是否可信、再决定要不要问替代项"这种需要两次往返的串行调用。
    """
    return {
        "result_plausible": JudgmentQuestion(
            type=QuestionType.NOUL,
            instructions=(
                f"YOLO 模型将图中目标识别为「{predicted_pest}」（报告置信度 "
                f"{predicted_confidence:.2f}）。结合作物类型与图片内容，这个识别结果本身是否可信？"
            ),
        ),
        "confidence_alignment": JudgmentQuestion(
            type=QuestionType.SCORE,
            instructions="YOLO 报出的置信度数值，与图片中证据的清晰/充分程度相符吗？",
            criteria=["明显不符（高估或低估）", "大致相符", "高度吻合"],
        ),
        "likely_alternative": JudgmentQuestion(
            type=QuestionType.CHOICE,
            instructions=f"如果「{predicted_pest}」这个识别结果不可信，图中更可能是以下哪一种？",
            criteria={name: name for name in alternative_candidates},
        ),
    }


@dataclass
class YoloVerificationResult:
    is_plausible: bool
    confidence_alignment: str  # "明显不符（高估或低估）" / "大致相符" / "高度吻合"
    suggested_alternative: Optional[str]  # 仅当 is_plausible 为 False 时有意义
    note: str  # 适合直接写入 DetectionRecord.remark 的复核结论摘要


async def judge_yolo_result(
    settings: Optional["models.UserSettings"],
    predicted_pest: str,
    predicted_confidence: float,
    crop_type: Optional[str],
    pest_crop_map: Dict[str, str],
) -> Optional[YoloVerificationResult]:
    """对 YOLO（当前由 mock_data 占位）给出的候选识别结果做一次独立复核。

    调用方：
    - `routers/detections.py::create_detection` —— 每次检测后自动调用一次，
      是整条流水线里"JEV 复核"这一步的唯一实现。
    - `routers/judgment.py::verify_detection`（`POST
      /api/judgment/detections/{id}/verify`）—— 对已有记录手动重新触发一次，
      用于补发判断模型配置之前创建的旧记录，或单纯想要一次新的复核意见。

    未配置判断模型接口，或请求/响应出现任何异常时返回 None——复核是增强，
    不应阻塞检测流程本身，调用方应在拿到 None 时按"未复核"处理（既不展示
    复核结论，也不因此拒绝或修改 YOLO 的原始结果）。
    """
    if settings is None or not settings.api_base_url:
        return None

    alternatives = [p for p, c in pest_crop_map.items() if p != predicted_pest and crop_type in (None, c)]
    if not alternatives:
        alternatives = [p for p in pest_crop_map if p != predicted_pest]

    questions = build_yolo_verification_questions(predicted_pest, predicted_confidence, alternatives)
    state = (
        f"作物类型：{crop_type or '未指定'}；"
        f"YOLO 候选识别结果：{predicted_pest}（置信度 {predicted_confidence:.2f}）；"
        f"请复核该识别结果是否可信。"
    )

    client = JudgmentModelClient(settings.api_base_url, settings.api_key, settings.model_name)

    try:
        answers = await client.evaluate(state, questions)
    except JudgmentModelError:
        return None

    plausible_answer = answers["result_plausible"]
    is_plausible = bool(isinstance(plausible_answer.value, (int, float)) and plausible_answer.value >= 0.5)

    alignment_answer = answers["confidence_alignment"]
    alignment_levels = ["明显不符（高估或低估）", "大致相符", "高度吻合"]
    alignment_index = round(float(alignment_answer.value))
    alignment_index = max(0, min(alignment_index, len(alignment_levels) - 1))
    confidence_alignment = alignment_levels[alignment_index]

    if is_plausible:
        note = f"判断模型复核：识别结果可信（置信度校准：{confidence_alignment}）"
        suggested_alternative = None
    else:
        suggested_alternative = str(answers["likely_alternative"].value)
        note = (
            f"判断模型复核：对「{predicted_pest}」的识别结果持怀疑态度"
            f"（置信度校准：{confidence_alignment}），更可能是「{suggested_alternative}」，建议人工复核"
        )

    return YoloVerificationResult(
        is_plausible=is_plausible,
        confidence_alignment=confidence_alignment,
        suggested_alternative=suggested_alternative,
        note=note,
    )
