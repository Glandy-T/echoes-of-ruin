# PixelLab → Aseprite 实际联网生成检查 v1

2026-10-13。用户完成扩展更新、重启 Aseprite 后要求实际试一次。

## 结果

**成功。** 已在 Aseprite 的 PixelLab 扩展里使用已解锁的 `Create texture` 提交一次生成。Aseprite 自带 DB32 调色板的读取提示由用户本人允许。完成窗口显示 `Finished - Seed: 31093108.0`，16×16 Sprite 的第2帧实际收到生成像素，预览窗口可见结果。

- 插件：PixelLab 0.4.129，本地已记录 Tier 1。
- Aseprite：1.3.18.2-dev。
- 工具页面标示成本：1 generation。没有重试、购买或升级。
- 参数及提示词见 [generation_record.json](generation_record.json)。
- 实际完成窗口证据见 [evidence/01_finished_in_plugin.png](evidence/01_finished_in_plugin.png)。

本次只确认 `Create texture` 的认证、请求与像素结果回传链路实际跑通。没有测试 Pro 编辑、局部重绘、动画或完整UV母版保留，也没有将这张连接检查图作为项目正式材质。

测试 Sprite 留在当前 Aseprite 中，第1帧为初始帧，第2帧为生成结果；它尚未另存成可编辑文件。保存时电脑控制因持续用户输入而停止；保留了完成窗口截图与本记录。当前休眠舱v2的七份 `.aseprite` 母版、PNG和Blender工程均未改动。

更新过程只使用官方插件入口，账户凭据未写入本目录或提交到仓库。
