# 麦麦私聊拟人化增强

> 基于 [Fucarlosm/private-humanizer](原项目已删库) 深度修改与优化而来。
>
> 原始作者：[Fucarlosm](https://github.com/Fucarlosm) · 原始许可：MIT

---

## 免责声明

1. **本插件仅供学习、研究和个人娱乐用途。** 不得用于任何违法、违规或侵犯他人权益的场景。
2. 插件通过向 MaiBot 的 LLM 请求注入提示词约束来影响回复风格，**不保证在所有 LLM 模型上生效**。不同模型的指令遵循能力差异较大，部分约束可能被忽略。
3. 插件内置的"事实守卫"和"记忆守卫"均为**基于规则的粗略检查**，无法做到 100% 精确——既可能漏过编造内容（漏报），也可能拦截合理的正常回复（误报）。请根据实际体验调整 `[guard]` 下的开关。
4. 主动续话功能会在 MaiBot 回复后延迟触发低优先级主动任务。**如果目标用户对"机器人主动说话"敏感，请在 `[proactive_followup]` 中关闭 `enabled`。**
5. 插件写入的审计日志默认不包含私聊原文（`save_rewrite_pairs = false`）。**如需排查问题临时开启，排查结束后务必关回 `false`**，保护目标用户隐私。
6. 使用者应自行评估功能对聊天体验的影响，**作者不对因使用本插件产生的任何后果承担责任**。

---

## 优化改动（相对原版）

以下为本次深度优化涉及的改动点，沿用原始架构但做了大量调整：

| 类别 | 改动内容 |
|------|----------|
| **隐私安全** | `save_rewrite_pairs` 默认关闭；新增 `.gitignore` 排除日志与备份目录 |
| **提示词优化** | 10 处提示词重写——放宽回复长度上限、软化了标点规则、补充了 LLM 常见编造陷阱示例、增加了日程变化性引导、澄清了虚拟环境与事实边界的矛盾点 |
| **守卫逻辑** | 移除单字场景词（"躺/蜷/蹭"）减少误匹配；证据验证引入 18 个 stop words；记忆守卫不再检查 dict key（原版误将系统字段当作模型内容拦截）；回退文本缩短至合理长度 |
| **匹配策略** | profile 未指定平台时继承全局 `target_platforms` 约束，防止跨平台误匹配；prompt 文本匹配增加最短候选名过滤 |
| **配置修复** | `config.toml` 重置为代码默认值；`cooldown_seconds` 默认统一为 180 秒；`Asia/Urumqi` 时区偏移修正为 UTC+6 |
| **版本管理** | 版本号升至 `1.0.0`；`config_version` 同步更新 |
| **确定性** | `_intimate_bridge_fallback` 用 `hashlib.sha256` 取代 `hash() ^ id()`，确保同输入可重现 |
| **测试适配** | `test_memory_guard_handles_dict_items` 适配 dict key 不再检查的逻辑 |

---

## 功能概述

本插件**只读取自身目录下的 `config.toml`**，不依赖 MaiBot 主配置。核心能力：

- **私聊匹配**：仅对 `target_user_ids` 或 `target_profiles` 中配置的目标私聊生效，不影响群聊和其他联系人。
- **时间与日程注入**：在回复阶段告知 LLM 当前日期、星期、时段、近期节假日和轻量日程参考，让回复带有真实的时间感。
- **私聊对象画像**：将你填写的基础信息、偏好、重要日期和关系说明注入私聊提示词，LLM 只能使用已确认的内容。
- **回复风格约束**：限制回复长度、动作描写密度、禁止小说体叙事和预设未来，让私聊更像即时通讯而非小说。
- **事实边界守卫**：检查 LLM 回复中的无证据事实、纪念日猜测、过度动作描写，触发后改写为坦承不知道的回复。
- **记忆守卫**：在"表达学习"写入前拦截疑似模型自创的个人事实（如"用户最喜欢桃子汽水"），避免污染长期记忆。
- **主动续话**：回复发出后延迟检查是否需要自然补一句短消息（支持亲密场景的专属续话策略），内置冷却和每小时上限。

---

## 安装

1. 将整个 `private-humanizer` 文件夹放入 MaiBot 的 `plugins/` 目录。
2. **修改 `config.toml`**——这是必须步骤：
   - 在 `[plugin]` 中填写 `target_user_ids`（如 `["123456789"]`）。
   - 在 `[[target_profiles]]` 中至少填写 `user_id` 和 `display_name`。
3. 重启 MaiBot，或在 WebUI 中重新加载插件。

> 默认 `config.toml` 已将 `target_user_ids` 设为空数组 `[]`，插件不会匹配任何用户。未配置前无任何效果。

---

## 最小配置示例

```toml
[plugin]
enabled = true
target_user_ids = ["123456789"]

[[target_profiles]]
profile_id = "target"
platform = "qq"
user_id = "123456789"
display_name = "目标私聊对象"
basic_info = "称呼偏好：目标私聊对象\n所在地区：未知\n作息：未知\n"
preferences = "聊天偏好：自然、简短、有回应感\n"
important_dates = ""
relationship_notes = "不要编造未确认的偏好、礼物、纪念日或共同经历。"
```

**重要：** 未填写的画像字段会被视为"未知"。插件会要求 LLM 保持"不确定/询问/基于当前对话回应"，而不是猜测。

---

## 配置项详解

### `[plugin]` — 基础设置

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | `true` | 插件开关 |
| `private_only` | bool | `true` | 仅私聊生效，建议保持开启 |
| `target_platforms` | list | `["qq"]` | 生效平台，QQ 填写 `"qq"` |
| `target_user_ids` | list | `[]` | **必填**，目标 QQ 号列表 |
| `target_session_ids` | list | `[]` | 通常留空；无法按 user_id 识别时使用 |

### `[time_awareness]` — 时间感知

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | `true` | 注入日期、星期、时段信息 |
| `timezone` | str | `"Asia/Shanghai"` | 时区 |
| `custom_dates` | list | `[]` | 自定义重要日期，格式 `{name, date, description}`，不确定的请留空 |

### `[schedule]` — 日程参考

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `inject_into_replyer` | bool | `true` | 注入 Replyer 阶段（推荐） |
| `inject_into_planner` | bool | `false` | 注入 Planner 阶段（Payload 较大，建议关闭） |
| `manual_status` | str | `""` | 手动今日状态，非空时覆盖自动生成 |
| `manual_schedule` | str | `""` | 手动日程参考，非空时覆盖自动生成 |
| `reference_only` | bool | `true` | 日程仅作语气参考，不是事实 |
| `allow_user_interrupt` | bool | `true` | 用户可打断日程引导 |

### `[life_environment]` — 虚拟生活环境

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | `true` | 注入虚拟生活环境 |
| `environment` | str | `""` | 固定环境描述，留空由 LLM 自动生成 |
| `auto_generate_when_empty` | bool | `true` | 环境为空时自动生成 |
| `use_as_reference_only` | bool | `true` | 仅作背景参考，不主动扩写 |

### `[profile]` — 画像规则

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | `true` | 注入私聊画像 |
| `inject_into_private_prompt` | bool | `true` | 写入私聊提示词 |
| `require_evidence_for_preferences` | bool | `true` | 偏好必须有证据（空白字段视为未知） |

### `[[target_profiles]]` — 私聊对象画像

| 字段 | 类型 | 说明 |
|------|------|------|
| `profile_id` | str | 内部标识，默认 `"target"` |
| `platform` | str | 平台，QQ 填 `"qq"` |
| `user_id` | str | **必填**，目标 QQ 号 |
| `display_name` | str | LLM 识别该对象使用的称呼 |
| `basic_info` | str | 只写确定事实，不知道写"未知" |
| `preferences` | str | 只写确认过的偏好 |
| `important_dates` | str | 只有确认过的日期才填 |
| `relationship_notes` | str | 关系说明与禁忌事项 |

### `[guard]` — 回复守卫

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `fact_guard_enabled` | bool | `true` | 拦截无证据事实 |
| `anniversary_guard_enabled` | bool | `true` | 拦截纪念日/日期猜测 |
| `style_guard_enabled` | bool | `true` | 拦截过长/小说化回复 |
| `memory_guard_enabled` | bool | `true` | 拦截可疑记忆写入 |
| `max_reply_chars_soft` | int | `80` | 软上限，超过后更易触发压缩 |
| `max_reply_chars_hard` | int | `160` | 硬上限 |

### `[proactive_followup]` — 主动续话

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | `true` | 开启主动续话 |
| `delay_seconds` | int | `35` | 延迟秒数（20-60 推荐） |
| `cooldown_seconds` | int | `180` | 同会话最小间隔 |
| `max_per_hour` | int | `6` | 每小时最多触发次数，`0` 不限 |
| `min_reply_chars` | int | `2` | 上条回复短于此不触发 |

### `[logging]` — 日志审计

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | `true` | 记录拦截/改写/续话行为 |
| `log_level` | str | `"info"` | 日志等级 |
| `save_rewrite_pairs` | bool | `false` | **隐私敏感**，建议永远保持 `false` |

---

## Hook 注册清单

插件在 MaiBot 中注册了以下 Hook（均在 `plugin.py` 中定义）：

| Hook 点 | 方法 | 时机 | 行为 |
|---------|------|------|------|
| `maisaka.replyer.before_request` | `inject_replyer_prompt` | 回复请求前 | 注入私聊增强 extra_prompt |
| `maisaka.replyer.before_model_request` | `inject_replyer_model_prompt` | 模型调用前 | 注入私聊增强到最终 messages |
| `maisaka.replyer.after_response` | `guard_reply` | 回复生成后 | 规则守卫 + 调度主动续话 |
| `expression.learn.before_upsert` | `guard_expression_memory` | 表达学习写入前 | 拦截可疑个人事实 |

所有 Hook 均为 `BLOCKING` 模式，出错策略为 `SKIP`（出错时不阻塞主流程）。

---

## 主动续话工作原理

1. 每次守卫检查通过后，`_schedule_followup_if_needed` 判断是否满足条件：
   - 开启且满足最短回复长度
   - 无重试（`retry_count == 0`）
   - 没有该会话的进行中续话任务
   - 未触及每小时上限和冷却
2. 满足条件时创建异步 Task，延迟 `delay_seconds` 秒后执行。
3. 延迟期间检测上下文是否为亲密场景，选择普通续话意图或亲密续话意图。
4. 调用 `ctx.maisaka.trigger_proactive()`，由 Maisaka 自行判断是否真正发送。
5. 发送成功后记录时间戳到冷却历史。

**亲密续话**：上下文中检测到 `INTIMATE_TERMS`（`guards.py` 中定义）时，使用 `INTIMATE_FOLLOWUP_INTENT` 替代默认意图，包含更严格的亲密连续性约束。

---

## 匹配策略

插件采用三级匹配降级策略：

| 优先级 | 策略 | 说明 |
|--------|------|------|
| 1 | 标准字段匹配 | 检查 Hook 传入的 `user_id`、`session_id`、`platform`、`chat_type` |
| 2 | 缓存会话匹配 | 之前成功匹配过的 `session_id` 直接命中 |
| 3 | Prompt 文本匹配 | 扫描 messages 内容中是否出现画像的 `display_name`、`user_id` 或 `profile_id` |

匹配时还会检查：
- **群聊过滤**：`private_only = true` 时拒绝 group/guild/channel 及含 `group_id` 的消息。
- **平台过滤**：`target_platforms` 非空时拒绝不在列表中的平台。
- **Prompt 群信号检测**：第 3 级匹配前先扫描 prompt 中是否包含群聊特征关键词。

---

## 提示词注入机制

每次触发时会构造一个完整约束块（`[Private Humanizer 私聊增强约束]`），按顺序包含：

1. 当前时间信息（日期、星期、时段、明天、近期节假日）
2. 今日状态参考（根据时段自动生成的一段语气描述）
3. 私聊日程参考（当前时段的行为候选）
4. 虚拟生活环境参考（固定或自动生成的稳定假设）
5. 目标私聊对象画像（确认字段 + 使用规则）
6. 事实边界（三级信息源分级 + 绝对禁止项 + 不确定处理）
7. 亲密上下文连续性（启动/保持/回应标准/退出）
8. 回复风格约束（长度/内容/动作/禁止模式）
9. 情绪节奏控制（跟随/预设/收束/时间感知）

这些内容通过 `extra_prompt`（Hook 1）和直接插入模型 `messages`（Hook 2）两种路径注入。

---

## 审计日志

日志文件位于 `logs/private-humanizer-YYYY-MM-DD.jsonl`，每行一条 JSON 记录。包含字段：

```json
{
  "time": "2026-06-28 14:30:00",
  "stage": "replyer_prompt | replyer_model_prompt | reply_guard | memory_guard | followup_triggered | followup_failed | followup_skipped",
  "chat_id": "...",
  "user_id": "...",
  "risk_type": "unsupported_fact,anniversary_guess,novelistic_style,intimate_topic_shift,unverified_memory"
}
```

当 `save_rewrite_pairs = true` 时，`reply_guard` 记录会额外包含 `original_reply` 和 `rewritten_reply` 字段——**仅限排查时临时开启**。

---

## 常见问题

### 插件已启用，但没有任何效果？

检查 `config.toml`：
- `target_user_ids` 和 `[[target_profiles]].user_id` 是否填写了目标 QQ 号？
- `plugin.enabled` 是否为 `true`？
- `schedule.inject_into_replyer` 是否为 `true`？

### 守卫把正常的回复拦截了怎么办？

- 先在 `[logging]` 中临时设置 `save_rewrite_pairs = true`，观察日志中的 `risk_type` 和 `original_reply`。
- 根据被拦截的类型，关闭 `[guard]` 中对应的守卫开关。
- 排查完毕后改回 `save_rewrite_pairs = false`。

### 回复变得太短/太生硬？

- 检查 `[guard]` 中的长度阈值（`max_reply_chars_soft` / `max_reply_chars_hard`），适当调大。
- 关闭 `style_guard_enabled` 可完全禁用风格守卫（不推荐，建议先调阈值）。

### 主动续话太频繁/太打扰？

- 增大 `cooldown_seconds`（如 600-900）。
- 减小 `max_per_hour`（如 1-2）。
- 或直接关闭 `proactive_followup.enabled`。

### 想对另一个私聊对象也生效？

在 `[[target_profiles]]` 中追加一个新条目，填写不同的 `profile_id` 和 `user_id`：

```toml
[[target_profiles]]
profile_id = "target2"
platform = "qq"
user_id = "987654321"
display_name = "另一个对象"
# ... 画像字段
```

同时在 `target_user_ids` 中追加：

```toml
target_user_ids = ["123456789", "987654321"]
```

### 某些模型不遵守提示词约束怎么办？

不同 LLM 的指令遵循能力差异显著。如果发现约束经常被忽略：
- 检查模型的 system prompt 优先级机制（部分模型对"最终消息中的 system 角色文本"响应更好）。
- 尝试使用指令遵循能力更强的模型。
- 插件已同时注入 `extra_prompt` 和模型 `messages` 两条路径以最大化兼容性。

---

## 离线测试

在插件根目录运行：

```bash
python -m unittest discover -s tests
```

当前覆盖：配置加载、私聊匹配、守卫逻辑（事实/纪念日/风格/记忆/亲密话题转移）、提示词构建。
