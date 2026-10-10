# 麦当劳 MCP 接入说明

本 Skill 依赖麦当劳中国官方 MCP 服务（`mcd-mcp`）。WorkBuddy 原生支持 MCP，
按以下步骤接入后，Skill 即可调用麦当劳的点餐 / 领券 / 门店 / 订单能力。

## 1. 获取 MCP Token

1. 打开 https://mcp.mcd.cn
2. 点击右上角 **Login**，用**中国大陆手机号 + 验证码**登录
3. 进入 **Console**，点击 **Activate** 申请 MCP Token
4. 阅读并同意服务协议，复制你的 Token（Bearer）

> 认证限制：仅支持中国大陆手机号；MCP 限流约 600 次/分钟/Token。

## 2. 在 WorkBuddy 配置 mcd-mcp

打开 WorkBuddy → 插件/MCP → 自定义连接器，添加：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer 你的_TOKEN"
      }
    }
  }
}
```

保存后启用，**首次需在 WorkBuddy 弹窗点「信任」**。

## 3. 可用工具（本 Skill 用到）

| 工具 | 用途 |
| --- | --- |
| `auto-bind-coupons` | 一键领取所有可用麦麦省券 |
| `query-my-coupons` | 查询卡包已有券 |
| `query-nearby-stores` | 查询附近门店（需地址/坐标） |
| `query-meals` | 查询指定门店可售餐品（需 storeCode + beCode） |
| `list-nutrition-foods` | 查询餐品营养成分（热量等） |
| `calculate-price` | 计算含优惠价格（需完整 items/storeCode/beCode/addressId） |
| `query-order` | 查询订单状态与进度（34 位订单号） |

## 4. 无 Token 调试

不接 MCP 也能试跑本地引擎（见 README 本地试跑）。
若需在 WorkBuddy 之外验证接口，可用：

```bash
python scripts/mcp_wrapper.py --token 你的_TOKEN list
python scripts/mcp_wrapper.py --token 你的_TOKEN call available-coupons '{}'
```

## 5. 安全说明

- 本 Skill **绝不代用户支付**。`create-order` 仅生成预订单并提醒去 App 支付。
- Token 属个人凭据，请勿提交到公开仓库；建议用环境变量或本地配置。
