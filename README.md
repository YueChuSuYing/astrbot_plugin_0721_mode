# astrbot_plugin_0721_mode

0721 模式 AstrBot 插件仓库，当前主版本为 `1.4.3`。  
仓库内包含插件源码目录、打包 zip、审计/检查脚本与相关文档。

## 目录说明

- `astrbot_plugin_0721_mode/`：插件主目录（可用于部署）
- `_review_unzip/astrbot_plugin_0721_mode/`：解包后的审阅副本
- `astrbot_plugin_0721_mode.zip`：发布包
- `tools/check_0721_static.ps1`：静态检查脚本
- `0721_plugin_audit_report.md`：审计报告

## 主要能力

- `/vibe` 指令体系（状态、开关、锁定、安全词等）
- 中文短指令：`/0721 抽任务`、`/0721 完成`、`/0721 跳过`、`/0721 状态`、`/0721 骰子`
- WebUI 控制（含 token 登录、玩法快捷按钮）
- 主动消息与 LLM 生成策略（可开关）
- SID 白名单与 UMO/UID 路由支持

## 开发与检查

推荐在改动后执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\check_0721_static.ps1
```

```powershell
python -m py_compile .\astrbot_plugin_0721_mode\main.py
```

## 版本与发布

- 当前标签建议：`v1.4.3`
- 发布时建议确保 zip 与源码版本一致，且不包含 `__pycache__`
