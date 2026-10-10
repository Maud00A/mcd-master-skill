# WorkBuddy 开发上下文（联动奖励核验用）

本作品 **「麦麦秘籍 · 麦当劳创意抽签」** 全程使用 **腾讯 WorkBuddy** 辅助开发与调试，符合本次大赛"使用 WorkBuddy 开发参赛"的联动奖励条件。以下为开发上下文记录，用于核验。

## 一、开发环境与工具链路

- **开发平台**：WorkBuddy（左侧栏【专家·技能·连接器】→【连接器】→【自定义连接器】→【配置 MCP】载入 `mcd-mcp`）。
- **麦当劳 MCP**：`mcd-mcp`，Server 地址 `https://mcp.mcd.cn`，认证方式 `Bearer <Token>`（Token 由开发者在 open.mcd.cn/mcp 登录后控制台激活获取，仅本地使用，未提交仓库）。
- **本地引擎**：`scripts/local_engine.py`（纯标准库 Python），负责抽签随机、秘籍存档（JSON）、成就判定、HTML 卷轴渲染——这些逻辑不依赖网络，保证无 Token 也能跑通抽签解签。
- **模板**：`assets/scroll_template.html`（古风宣纸+木轴卷轴，四卷：秘籍 / 门店 / 订单 / 成就）。

## 二、开发过程中的关键迭代（对话上下文摘要）

1. **需求澄清**：明确作品为"上传即通用"的 Skill，任何人安装无需任何 Token 即可抽签解签；签筒放最前（抽签→解签→才开卷轴）；确认套餐信息回 WorkBuddy；最后走麦当劳点单并弹支付确认页，绝不代付。
2. **通用性落地**：卷轴顶部的签筒内置离线菜单池（`DATA.menu`，由 `local_engine.py render` 注入），不依赖麦当劳 / 百度 Token。
3. **门禁修正**：迭代中发现"确认套餐"会顺带自动展开卷轴，与"点解签才是四卷"的设定冲突，已改为「解签」为展开四卷的唯一入口。
4. **隐私红线**：真实门店 / 订单 / 坐标只存本地 `data/secrets.json` 等，全部 `.gitignore` 排除；仓库仅分发脱敏示例（`secrets_demo.json` / `scroll_demo.html`），投稿前用 `scripts/sanitize.py` 校验无真实地名 / 坐标 / 姓名 / 手机 / 订单号。
5. **依赖修复**：签筒口味偏好标签原为「牛肉 / 辣」中文，菜单标签为 `beef / spicy` 英文导致过滤静默失效；已统一为英文标签并加 `PREF_ALIAS` 同时接受中英文。
6. **文档对齐官方要求**：将仓库文档文件名对齐大赛强制规范——`README.md`、`CONTEST_DECLARATION.md`（采用官方模板，内容未改）、`MCP_INTEGRATION.md`。

## 三、实际调用的麦当劳 MCP 工具（对应 `MCP_INTEGRATION.md`）

- `auto-bind-coupons` / `query-my-coupons`：领券与卡包汇总
- `delivery-query-addresses`：获取用户常用配送地址（用于门店定位锚点）
- `query-nearby-stores`：附近门店检索
- `query-meals`：门店可售餐品
- `list-nutrition-foods`：营养成分 / 热量
- `calculate-price`：含优惠到手价
- `create-order`：仅生成预订单，支付由用户在麦当劳 App 自行完成
- `query-order`：订单状态与进度

## 四、核验要点

- 仓库为 GitHub 公开仓库（`Public`），含全部强制文件：`README.md`、`CONTEST_DECLARATION.md`、`MCP_INTEGRATION.md`、源代码（`scripts/` + `assets/`）。
- Token / 真实地理位置 / 个人信息均未进入公开仓库。
- 作品为原创，使用 WorkBuddy 开发，满足联动奖励资格。

> 本文件用于大赛"WorkBuddy 联动奖励"核验，记录了使用 WorkBuddy 进行创意构思、开发与调试的过程。
