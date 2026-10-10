# 投稿清单 · M-CODE 2026 麦当劳程序员创意开发大赛

> 本清单供「麦麦秘籍」Skill 投稿前逐项核对。活动截止 **2026-10-25 23:59**，主办 WorkBuddy × 麦当劳中国。

## 一、赛前确认（来自 SKILL.md 调研结论）
- [ ] 已在 https://mcp.mcd.cn 登录拿 Token，并在 WorkBuddy 信任 `mcd-mcp`（url `https://mcp.mcd.cn`，Authorization 头 `Bearer <Token>`）。
- [ ] （可选但推荐）百度地图 Agent Plan 的 `BAIDU_MAP_AUTH_TOKEN` 已配（门店坐标 / 到店导航用）。
- [ ] 奖品预期对齐：公开赛道是「汉堡回车键」实体周边 + 积分，无现金、无实习直通卡；用 WorkBuddy 开发自带 +3000 积分。

## 二、建仓三件套（仓库根目录必备）
- [ ] **项目介绍**：`README.md`（已有，含功能清单 / 使用方式 / 架构）。
- [ ] **参赛声明**：在仓库根新增 `STATEMENT.md`（或写入 README 一节），声明「本作品为 M-CODE 2026 参赛作品，作者 沙沙 & 阿砚，基于麦当劳官方 MCP 开发，未存储任何用户个人隐私」。
- [ ] **MCP 接入说明**：`MCP_SETUP.md`（已有）。

## 三、隐私脱敏（红线，必须做）
- [ ] 运行 `python scripts/sanitize.py` 确认 `data/secrets_demo.json` 已脱敏（无 LIVE- 订单、无真实地名/坐标、无姓名/手机/地址）。
- [ ] 确认 `data/secrets.json`（真实存档）、`data/scroll.html`（真实卷轴）、`data/stores_geo.json`（真实坐标）**未被跟踪** —— 已被 `.gitignore` 排除。
- [ ] 搜索仓库内是否残留 `长沙 / 五一路 / 真实手机号 / 真实姓名` 等字样；演示页 `scroll_demo.html` 应为示例门店。

## 四、提交
- [ ] 提交到个人 GitHub **公开**仓库（如 `mcd-master-skill`）。
- [ ] 在麦当劳 GitHub 活动页（搜 `McDonald's China / M-China`）用**指定 Issue 模板**提交，附仓库链接与一句话说明。

## 五、提交后可继续打磨（可选）
- [ ] 真机联调：用真实 Token 跑一遍 `draw → archive → render`，点亮更多隐藏成就。
- [ ] 部署到 WorkBuddy 云端 / 任意 HTTPS，解锁手机陀螺仪与 `navigator.geolocation` 体感/定位（localhost 预览无法在手机上触发这些传感器）。
- [ ] 想要「摇一摇抽签」（devicemotion）或更多反向彩蛋成就，可在 `local_engine.py` 的 `ACHIEVEMENTS` 扩展。
