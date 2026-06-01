# 0721模式 AstrBot 插件

读取本地状态并注入到 AstrBot LLM 请求中，也提供 `/vibe` 命令和本地 WebUI 控制面板。

## 主要功能

- `/vibe on/off/status/lock/unlock/set/force/deny/undeny/safeword`
- 身体日记与成就：`/vibe diary`、`/vibe achievements`
- 轻量玩法：`/0721 抽任务|完成|跳过|状态|骰子`，也兼容 `/vibe play task|done|skip|status`、`/vibe roll`
- 本地 WebUI 控制面板：默认 `http://localhost:7721`
- LLM 状态注入和 LLM Tools 控制
- 主动私聊消息推送，支持 LLM 实时生成并自动回退内置词库

## 指定用户使用

在插件配置中填写 `allowed_sids` 可以限制可使用用户。

- 留空：不限制，保持默认行为
- 推荐直接填写数字 QQ 号/UID，例如 `123456789`
- 也支持完整 UMO，例如 `BotID:FriendMessage:123456789`
- 多个 UID/UMO：用逗号或换行分隔
- 生效范围：`/vibe` 命令、LLM Tools、LLM 注入、主动消息 session 记录
- WebUI 没有 AstrBot event，仍使用 `webui_password` 控制访问

如果不知道自己的 UID，可以临时不填白名单，在 AstrBot 会话信息里查看 `UID`；插件也会兼容完整 `UMO`，格式通常类似 `BotID:FriendMessage:UID`。

## 主动消息目标

WebUI 没有 AstrBot event 上下文，无法自动知道应该把主动消息发到哪个私聊。需要 WebUI 开启后也主动推送时，在插件配置里填写 `auto_message_session`。

- 推荐格式：完整 UMO，例如 `BotID:FriendMessage:123456789`
- 如果 `auto_message_session` 留空，插件会尝试从 `allowed_sids` 中取第一个完整 UMO
- 只填数字 QQ 号/UID 可以用于白名单，但不能单独作为主动推送路由
- 私聊里使用 `/vibe on` 或 `/vibe automsg on` 时，会自动记录当前私聊为主动消息目标

可用 `/vibe automsg status` 查看当前目标会话和下次最早发送时间，用 `/vibe automsg test` 测试发送链路。

## 轻量玩法

- `/vibe play task`：抽一张任务卡，任务状态会写入 `vibe_state.json`
- `/vibe play done`：完成当前任务，获得少量快感奖励
- `/vibe play skip`：跳过当前任务
- `/vibe play status`：查看任务进度
- `/vibe roll`：随机选择一个已有模式和档位
- 简短中文入口：`/0721 抽任务`、`/0721 完成`、`/0721 跳过`、`/0721 状态`、`/0721 骰子`

玩法层只复用现有状态机，不引入新依赖；WebUI 提供抽任务、完成、跳过、骰子四个轻量按钮。

### 主动消息 LLM 生成

`auto_message_use_llm` 默认开启。主动消息触发时，插件会按 `auto_message_llm_policy` 决定是否调用当前目标会话使用的 chat provider 生成短句，让内容更自然、不像固定词库。若当前 AstrBot 版本没有 `llm_generate`、会话没有可用 provider、LLM 超时或返回空内容，会自动回退到内置词库。

`auto_message_llm_policy` 默认是 `key_states`，比较省 token：

- `key_states`：只在高快感、高潮、余韵、否认、边缘等关键状态使用 LLM
- `every_3`：每 3 条主动消息里 1 条用 LLM
- `always`：每条主动消息都优先用 LLM
- `off`：只用内置词库

`auto_message_llm_timeout` 控制单次等待 LLM 的秒数，默认 8 秒。觉得主动消息延迟明显时可以调低；想要更稳定的实时生成可以适当调高。

## 安全建议

- `webui_password` 不要留空，尤其是 WebUI 绑定到局域网地址时。
- WebUI 登录后会使用临时 token 访问 `/state`，前端不再把密码长期保存到 `localStorage`。
- 更新旧版状态文件时，插件会自动补齐新增字段并写入 `stateVersion`。
- 默认单状态自用；如果多人同时使用，建议配置 `allowed_sids`。
- 状态文件 `vibe_state.json` 是运行态文件，不应提交或打包进仓库。
