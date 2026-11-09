# QwenPaw Platform Keepalive

通过 GitHub Actions 定期调用 AgentScope Platform 的登录与沙箱心跳流程，减少云端 QwenPaw 沙箱因长时间无活动而休眠的情况。

> 此仓库不是 QwenPaw 应用本体，而是个人维护的保活脚本。平台心跳 API 的公开文档与兼容性承诺尚未确认；请把此方案视为尽力而为，并定期检查 Actions 运行记录。

## 设置

在 GitHub 仓库中打开 **Settings → Secrets and variables → Actions**，添加以下 Repository secrets：

- `QP1_ACCOUNT`：AgentScope Platform 登录账号
- `QP1_PASSWORD`：AgentScope Platform 登录密码

请勿把账号、密码或访问令牌写入代码、提交记录或 Actions 日志。

## 运行

- Actions workflow 默认每 6 小时运行一次。
- 可在 **Actions → qwenpaw-keepalive → Run workflow** 手动触发。
- 第一次使用前添加上述 Secrets，并手动运行一次；确认 `heartbeat: HTTP 200` 后再依赖定时任务。
- 成功运行后会更新 `.last-run`，仓库需要允许 Actions 的 `GITHUB_TOKEN` 写入内容（workflow 已声明最小必要的 `contents: write` 权限）。

## 局限与安全

- 这不是 AgentScope 官方维护的集成；平台接口变化、账号策略或休眠规则调整都可能导致任务失败。
- Workflow 不包含外部 URL pinger 或硬编码 sharecode。不要将含访问码的 URL 提交到公开仓库。
- 重要数据仍需独立备份；保活不等于备份，也不保证平台持续提供服务。
