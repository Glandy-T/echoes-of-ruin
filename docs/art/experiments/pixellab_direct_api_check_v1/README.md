# PixelLab 官方直接 API 接入验证 v1

2026-10-13。用户授权直接接入，减少浏览器／桌面操作。

## 实际验证结果

- 官方 `GET https://api.pixellab.ai/v2/balance` 认证成功。
- 官方 `POST /create-image-pixen` 成功回传一张 32×32 PNG，已保存 [原始结果](wall_response.png)。
- 接口 `usage` 实际返回 `type: generations`、`generations: 1.0`；调用前后订阅剩余次数减少 1，美元余额无变化。此次没有充值、购买或升级。
- 使用已连接的官方 Aseprite PixelLab 扩展账号；密钥仅在进程内读取，发送至同一 PixelLab 官方 HTTPS 服务，未复制到项目、命令参数、日志或提交。
- 本轮未接管桌面，也未修改 Aseprite 插件／Codex 配置。**已验证的是 REST API 脚本连接，不是已安装 MCP 工具。**

成本结论只针对本次调用。Pro、编辑、补绘与其他模型的价格、响应结构及扣费方式需按各自文档与实际响应确认，不能全部推定为 1 次。

## 为什么原始结果没有用作墙面

[请求](source/wall_request.json) 明确要求单色、无纹理，但模型仍输出了边界／斑纹，故只作为接口成功证据。没有把它称为合格纯色贴图。后续 [连续纯色墙地小样](../room1_wall_floor_solid_v1/README.md) 使用确定性生成的单色图，不额外消费 AI 次数。

## 后续使用

[pixellab_direct.py](source/pixellab_direct.py) 使用 Python 标准库，无需额外 SDK，支持余额、同步图像请求与任务状态查询。默认读取本机环境变量 `PIXELLAB_API_TOKEN`；仅显式指定 `--use-aseprite-account` 时才读取现有官方扩展的凭证。不要把密钥填进脚本、JSON、命令行参数或 Git。

```powershell
# 在项目根目录执行；输出余额仅保存在本机临时目录。
python docs/art/experiments/pixellab_direct_api_check_v1/source/pixellab_direct.py balance --use-aseprite-account --output "$env:TEMP/pixellab_balance.json"

# 付费生成命令：仅在确实需要新的生成时执行，不是安装／检查命令。
python docs/art/experiments/pixellab_direct_api_check_v1/source/pixellab_direct.py generate --use-aseprite-account --payload docs/art/experiments/pixellab_direct_api_check_v1/source/wall_request.json --output "$env:TEMP/pixellab_new_wall.json"
```

学校电脑需自行登录该官方扩展，或通过本机安全配置提供环境变量。仓库不包含可搬运的账号密钥。当前助手可以用脚本直接请求、保存 PNG，再用 Aseprite 批处理生成母版和 Blender 试贴；Aseprite 可编辑文件与 PixelLab 账号连接是两个独立环节。

脚本对生成 POST 不自动重试，避免不明确结果下重复计费；异步结果的下载与各种 Pro 接口尚未验证，不把本次小请求当作全部功能通过。

## 文件与公开来源

- [使用记录](wall_response.json)：公开的请求成本与图片文件名，不含账号认证信息。
- [请求参数](source/wall_request.json)、[原始 PNG](wall_response.png)、[接口脚本](source/pixellab_direct.py)。
- 调用前后余额与完整公开 OpenAPI 下载仅作本机检查，不上传。
- [官方 REST API 文档](https://api.pixellab.ai/v2/docs)、[机器可读参考](https://api.pixellab.ai/v2/llms.txt)、[OpenAPI](https://api.pixellab.ai/v2/openapi.json)。

检查时 GitHub main 基准为 `e40d4c46876a50be49e4649900ff297479cc41d0`。
