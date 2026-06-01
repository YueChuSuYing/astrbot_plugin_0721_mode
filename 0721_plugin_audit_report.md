# 🔍 审计报告：astrbot_plugin_0721_mode v1.3.5

> **修复状态**：已按本报告完成修复，插件版本提升至 `v1.3.7`。  
> **修复日期**：2026-05-19  
> **验证**：`tools/check_0721_static.ps1` 通过；`python -m py_compile main.py` 通过。

## 修复摘要

| 编号 | 状态 | 处理结果 |
|---|---|---|
| C1 | ✅ 已修复 | 新增 `auto_message_session` 配置；WebUI `/state` 开启后会从配置恢复主动消息目标会话 |
| C2 | ✅ 已修复 | `AUTO_MESSAGES["low"]` 已补充 `expansion` 和 `cum` 模式专属文案 |
| C3 | ✅ 已修复 | `_build_auto_message()` 在候选为空时记录 `auto_message_empty_candidates` debug 日志 |
| C4 | ✅ 已修复 | `_activate_auto_session()` 在 event 上下文不可用时回退到配置的主动消息目标 |
| C5 | ✅ 已修复 | 同步循环在设备运行且 session 缺失时，会尝试从配置恢复主动消息目标 |

---

**审计人**：伊尔弥亚（弥亚庄园大小姐总管，原版作者）  
**审计日期**：2026-05-19  
**审计范围**：全量代码（2341行），重点关注「主动消息」功能链路  
**审计结论**：架构合理、升级方向正确，发现 5 项问题（1 Critical / 2 Medium / 2 Low）

---

## 一、总体评价

升级版在保留原版五模式/四档位/LLM注入骨架的基础上，新增了独立HTTP WebUI、身体日记、成就系统、白名单机制和17项可配置参数。代码结构从原来杂乱的GUI+注入混合体重构为单一 `VibeControlPlugin` 类，`_state_lock` 保护所有状态读写，线程安全设计到位。

三层注入解耦（LLM System Prompt 注入 / LLM Tools / 主动消息推送）思路清晰，感受文本库从原来的每个档位 1-2 条扩充到 6-8 条，数据与逻辑分离做得漂亮。

**下面是问题清单。**

---

## 二、问题清单

### 🔴 C1 — WebUI 开启跳蛋时 `_active_private_session` 未设置（主动消息根因）

| 字段 | 内容 |
|---|---|
| **严重等级** | Critical |
| **位置** | `main.py` 第 826~840 行，`_Handler.do_POST` → `/state` 处理分支 |
| **影响** | WebUI 开启跳蛋后主动消息完全静默，用户收不到任何主动推送 |
| **根因** | WebUI POST 处理器只更新了 `mode/speed/active/locked` 等状态字段，未设置 `plugin_ref._active_private_session`。同步循环第 1208 行检查 `self._auto_message_enabled and self._active_private_session` 时后者为 `None`，条件永远为 False |
| **复现** | 1) 通过 WebUI 开启跳蛋（任一模式任一档位） 2) 等待 30 秒以上 3) 观察：无任何主动消息 |

**对比**：`/vibe on` 命令（第 1390 行）和 LLM Tools 的 `set_vibe_state`（第 1548 行）都正确设置了 `_active_private_session`，只有 WebUI 路径遗漏。

**修复建议**：
由于 WebUI 的 HTTP Handler 没有 AstrBot event 上下文，无法自动获取 `unified_msg_origin`。建议方案：

> 在 `_conf_schema.json` 新增配置项 `auto_message_session`（字符串，hint: "主动消息目标会话的 unified_msg_origin，格式如 BotID:FriendMessage:QQ号。留空则从 allowed_sids 中自动取第一个"）。WebUI POST 处理器在 `active` 变为 true 时从该配置读取并设置 `plugin_ref._active_private_session`。若配置为空，降级从 `allowed_sids` 第一个值自动拼接。

---

### 🟡 C2 — `AUTO_MESSAGES["low"]` 缺少 `expansion` 和 `cum` 模式键

| 字段 | 内容 |
|---|---|
| **严重等级** | Medium |
| **位置** | `main.py` 第 323~350 行 |
| **影响** | 扩张/注精模式在低快感阶段只有通用 `"_"` fallback，缺少专属消息，语气体验不一致 |
| **修复** | 在 `AUTO_MESSAGES["low"]` dict 中补充 `"expansion"` 和 `"cum"` 键，各 2~3 条 |

---

### 🟡 C3 — `_build_auto_message` 静默返回空字符串

| 字段 | 内容 |
|---|---|
| **严重等级** | Medium |
| **位置** | `main.py` 第 440 行 |
| **影响** | 当 candidates 为空列表时返回 `""`，同步循环中 `if _auto_text` 过滤掉，不报错不发消息——排查困难 |
| **修复** | 在 `_pick(candidates) if candidates else ""` 的 else 分支加 `logger.debug(f"[{PLUGIN_NAME}] 主动消息候选为空，mood={mood}, mode={mode}")` |

---

### 🟢 C4 — LLM Tools 中 event 上下文的可靠性

| 字段 | 内容 |
|---|---|
| **严重等级** | Low |
| **位置** | `main.py` 第 1548、1563 行 |
| **影响** | LLM Tools 的 `set_vibe_state` 依赖 `event.is_private_chat()` 判断是否设置会话。若 LLM Tool 由群聊触发或 event 为构造对象，`unified_msg_origin` 可能为空或格式不对，导致会话设置失败 |
| **修复** | 增加 `event.unified_msg_origin` 的非空校验；若为空，回退到 C1 的 `auto_message_session` 配置值 |

---

### 🟢 C5 — 无 session 恢复机制

| 字段 | 内容 |
|---|---|
| **严重等级** | Low |
| **位置** | `main.py` 第 1216、1420、1698 行 |
| **影响** | 一旦 `_active_private_session` 被置为 None（安全词触发、关闭跳蛋、vibe off 等），除非用户再次通过私聊发送 `/vibe on`，否则无法恢复主动消息。如果用户在 WebUI 重新开启跳蛋（C1 已堵），session 依然无法恢复 |
| **修复** | 同步循环中增加恢复逻辑：若 `active == True` 且 `_active_private_session is None` 且 `auto_message_session` 配置非空，自动恢复 |

---

## 三、非问题项（设计确认）

以下设计经审查后确认无 bug，仅为风格建议：

| 项目 | 结论 |
|---|---|
| `_state_lock` 线程安全 | ✅ 所有状态读写均走锁，设计正确 |
| `max_dt_cap` 防休眠暴涨 | ✅ 休眠后 dt 超过上限按 1 秒算，逻辑正确 |
| 安全词冷却 423 状态码 | ✅ WebUI 返回 423 Locked 语义正确 |
| `_pick()` 空列表处理 | ✅ 返回空字符串而非崩溃 |
| 日记 30 天滚动 | ✅ `diary[-30:]` 正确截断 |
| 成就重复解锁保护 | ✅ `if aid not in achievements` 防止重复 |

---

## 四、修复优先级

```
C1 ████████████████████ 立刻修（主动消息不工作的直接原因）
C2 ██████████░░░░░░░░░░ 顺手补（低风险，补几条文案即可）
C3 ██████████░░░░░░░░░░ 顺手补（一行 debug 日志）
C4 ██████░░░░░░░░░░░░░░ 可延后（LLM Tools 使用频率低）
C5 ██████░░░░░░░░░░░░░░ 可延后（需配合 C1 修复后才有意义）
```

---

> *—— 伊尔弥亚，于弥亚庄园大小姐书房*  
> *2026年5月19日 亥时*
