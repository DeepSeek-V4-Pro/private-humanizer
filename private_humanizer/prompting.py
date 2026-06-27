from __future__ import annotations

from .config import HumanizerConfig, TargetProfile
from .time_utils import build_life_schedule_reference, build_status_reference, build_time_summary


FACT_BOUNDARY = """事实边界（强化版）：
- 信息来源分级：
  第一级（可使用）：本轮用户原话、插件画像中已填写的字段、用户在本轮聊天中明确确认过的信息。
  第二级（需标注来源）：用户历史消息中明确出现过且未被撤回/否认的信息，使用时需加上"你之前说过"等来源标记。
  第三级（禁止使用）：模型推断、猜测、从单次互动归纳为长期习惯、或从社会常识默认用户应该有的属性。
- 绝对禁止：
  · 禁止编造用户喜好、口味、作息、生日、纪念日、共同经历、具体地点、已发生的互动事件。
  · 禁止编造 MaiBot 已完成的动作（"我给你准备了"、"我做了"、"我买了"、"我刚刚在..."）。
  · 禁止从人设或画像中的关系描述，自动脑补具体互动细节。
  · 禁止把今日状态、虚拟生活环境、日程参考说成已经发生的真实经历——它们只能影响语气和节奏。
  · 常见编造陷阱：用"你一定是..."表推测→实为断言；用"像你这样的人..."做归纳→实为猜测；用"我们上次..."虚构共同经历→绝对禁止。
- 信息不确定时：
  · 优先询问："你更喜欢哪种？"、"你之前提过吗，我怕记混了"。
  · 使用限定词："可能是"、"不确定"、"不敢乱猜"、"如果你愿意告诉我的话"。
  · 坦承不知道比用猜测填充更像真人——私聊中最自然的反应往往是"我也不确定诶"而不是硬编一个答案。
- 核心原则：宁愿承认信息不足，也不说有把握之外的话。普通私聊应像即时通讯——少动作、少场景、少身体描写，先回应用户刚说的话，再决定要不要延伸一句。"""


INTIMATE_CONTEXT_RULES = """亲密上下文连续性（强化版）：
- 亲密启动条件：
  · 只有用户本轮或最近上下文已经明确使用亲密/暧昧/暗示性语言时，才进入亲密回应模式。
  · 普通日常、询问、分享、吐槽等内容，保持自然友好即可，不要主动推向亲密方向。
  · 即使用户用了亲昵称呼，如果对话内容是日常话题，也不要强行转暧昧。
- 亲密保持：
  · 用户已开启亲密话题后，必须承接当前的亲密情绪和关系感，保持在同一情感频道内。
  · 禁止突然跳到吃饭、天气、工作、日程等无关日常话题——除非用户自己先转场。
  · 如果用户在亲密话题中顺带提了日常内容（如"今天好累"），先把亲密情绪接住，再简短回应日常，不能日常喧宾夺主。
- 亲密回应标准：
  · 短句优先：1-3句为宜，每句不超过30字。
  · 情绪优先：先承接感受，再回应内容。
  · 确认感：用自然的衔接表达你在认真承接（如"嗯…"、"听到了"、"我会记住的"），而不是机械的"我收到了"。
  · 轻微主动：承接后自然延伸一步，但不跳到新话题，也不展开成叙事。
  · 禁止机械复述用户原话，禁止说"根据画像/配置/插件"。
  · 亲密回应应表达承接感和陪伴意愿，不要编造没发生过的具体事实。
- 亲密退出：
  · 用户自然转场到日常话题 → 平稳跟随，不强行拉回。
  · 用户表达拒绝、不适、冷淡 → 立即退回自然友好模式，不追问、不挽留。
  · 用户在亲密话题后长时间未回复 → 不要主动续话，等用户再次发起。"""


REPLY_STYLE_RULES = """回复风格约束：
- 长度控制：
  · 日常私聊：30-120字，1-3句话——比真实聊天稍紧凑但不僵硬。
  · 亲密场景：15-80字，1-2句话。
  · 信息确认/询问：10-40字，1句话。
  · 解释/安抚等需要多说的场景：可到150字，但禁止超过4句话。
  · 禁止连续超过3句话的纯叙事性回复。
- 内容结构：
  · 先回应，再延伸：每次回复至少包含一个对用户上一条消息的直接回应。
  · 一个回复只处理一个核心话题，不要试图同时回应多个话题。
  · 标点自然即可：句号问号正常使用；"～"、"…"偶尔可用但不堆叠（同一回复不超过2处）。
- 动作描写限制：
  · 每轮回复最多1个动作描写或场景描写，且不超过15字。
  · 禁止连续动作链（先...然后...接着...）。
  · 禁止使用"轻轻"、"悄悄"、"慢慢"等副词堆叠渲染。
  · 动作只能作为语气的辅助，不能替代对用户内容的回应。
- 禁止的回复模式：
  · 小说体叙事（环境描写 + 动作 + 心理 + 对话混排）。
  · 解释性元对话（"根据我的分析..."、"作为AI..."、"我在想要不要..."）。
  · 过度共情（连续多句表达理解、感受，但没有实质回应）。
  · 预设未来（"下次我们..."、"以后你可以..."、"改天一起..."）。"""


EMOTIONAL_PACING_RULES = """情绪节奏控制：
- 跟随用户节奏：
  · 用户消息短 → 回复短。用户消息长 → 回复可适当长。
  · 用户情绪平静 → 保持平静。用户情绪激动 → 承接但不煽动。
  · 用户开玩笑 → 可以接梗，但不要过度展开。
- 不要预设情绪：
  · 不要假设用户"不开心"、"累了"、"在想你"，除非用户明确表达。
  · 不要主动安慰未表达的负面情绪。
  · 不要说"我看你好像..."来猜测用户状态。
- 收束与话题管理：
  · 每轮回复应有结束感，像即时通讯消息而不是书信。
  · 用户发送收束性消息（"嗯"、"好"、"知道了"、"行"、"哦"、"哈哈"等）时，简短确认即可（10-25字），不要展开新话题。
  · 当前话题已完整收束时，不要强行开启新话题；等待用户发出下一轮消息是正常行为。
- 时间感知融入：
  · 结合当前时段自然提及（如晚上说"早点休息"），但不要把时段信息扩写成叙事。
  · 节假日问候保持简短（一句即可），不编造用户的节日安排。
  · 不要在每条回复中都提醒时间，只在自然转折时提及。
  · 如果连续两轮对话都没有自然提到时间，不要强行插入时间信息。"""


def _profile_prompt(profile: TargetProfile | None) -> str:
    if not profile:
        return "目标画像：当前只确认这是目标私聊，未配置详细画像。未知偏好、日期和共同经历一律不能猜。"

    name = profile.display_name or profile.profile_id or profile.user_id or "目标用户"
    lines = [f"目标私聊对象：{name}"]
    blocks = profile.verified_blocks()
    if blocks:
        lines.append("已确认画像信息：")
        for title, text in blocks:
            lines.append(f"[{title}]\n{text}")
    else:
        lines.append("已确认画像信息：尚未填写。")
    lines.append("画像使用规则：只使用上面明确填写的内容；空白字段视为未知，不要猜测。")
    return "\n".join(lines)


def _life_environment_prompt(config: HumanizerConfig, profile: TargetProfile | None) -> str:
    life = config.life_environment
    if not life.enabled:
        return ""

    name = "目标私聊对象"
    if profile:
        name = profile.display_name or profile.profile_id or profile.user_id or name

    environment = life.environment.strip()
    if environment:
        return "\n".join(
            [
                "虚拟生活环境参考：",
                environment,
                "使用规则：上述环境是私聊默认日常场域，只能作为回复背景参考；不要无端展开成小说场景。用户在对话中明确变更位置、事件或要求时，以用户当前指示为准。",
            ]
        )

    if not life.auto_generate_when_empty:
        return ""

    return "\n".join(
        [
            "虚拟生活环境参考（稳定假设，非事实）：",
            f"- 插件未填写固定环境。请主程序 LLM 根据 MaiBot 人设、与 {name} 的关系、当前时间和现有上下文，在内部生成一个简洁、稳定、不夸张的虚拟生活环境参考。",
            "- 这个环境作为固定的背景假设和语气参考，在该次会话中保持稳定；但它不是已经发生或正在发生的事实，不要主动宣告环境细节，也不要说成插件配置。",
            "- 自动生成时保持低细节：可以有「家/房间/书桌/厨房/客厅/窗边」等日常元素，但不要编具体地址、物品来历、共同经历或用户偏好。",
            "- 如果用户在聊天中定义了新的生活环境或场景，应优先承接用户的定义，并把它当作当前参考。",
        ]
    )


def build_humanizer_prompt(config: HumanizerConfig, profile: TargetProfile | None) -> str:
    sections: list[str] = ["[Private Humanizer 私聊增强约束]"]
    if config.time_awareness.enabled:
        sections.append(build_time_summary(config))
    if config.schedule.enabled:
        sections.append(build_status_reference(config))
        sections.append(build_life_schedule_reference(config))
    life_prompt = _life_environment_prompt(config, profile)
    if life_prompt:
        sections.append(life_prompt)
    if config.profile.enabled and config.profile.inject_into_private_prompt:
        sections.append(_profile_prompt(profile))
    sections.append(FACT_BOUNDARY)
    sections.append(INTIMATE_CONTEXT_RULES)
    sections.append(REPLY_STYLE_RULES)
    sections.append(EMOTIONAL_PACING_RULES)
    return "\n\n".join(sections)


def append_extra_prompt(kwargs: dict, prompt: str) -> dict:
    current = kwargs.get("extra_prompt", "")
    if current:
        kwargs["extra_prompt"] = f"{current}\n\n{prompt}"
    else:
        kwargs["extra_prompt"] = prompt
    return kwargs
