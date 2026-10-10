# 麦麦秘籍 · 麦当劳创意抽签（M-CODE 2026 参赛作品）

> 和 WorkBuddy 一起，脑洞全开。
> 一个基于 **麦当劳官方 MCP** 的创意 Skill：一键领券、附近门店地图、无限次抽签预览，
> 支付后把每一次点单固化成一卷可收藏的「麦麦秘籍」卷轴网页，并带江湖成就系统。

## 它能做什么

| 功能 | 说明 | 数据来源 |
| --- | --- | --- |
| 自助领券 | 一键领取所有可用麦麦省券，汇总卡包 | `auto-bind-coupons` / `query-my-coupons` |
| 麦当劳地图 | 列出附近门店 + 到店导航链接 | `query-nearby-stores` |
| 无限次抽签 | 随机抽 单堡 / 套餐 / 堡+小食，支持口味偏好 | `query-meals` + 本地引擎 |
| 预览 & 确认 | 每次抽签给热量/到手价预览，满意再支付 | `list-nutrition-foods` / `calculate-price` |
| 麦麦秘籍 | 支付后固化为卷轴网页（导航/订单进度/点单详情） | 本地存档 + `query-order` |
| 成就系统 | 初入江湖、十全十美、券王附体… | 本地规则引擎 |

## 玩法

1. 说「帮我领券」→ 一键领券并播报。
2. 说「附近麦当劳」→ 出门店地图。
3. 说「抽签，要牛肉不辣」→ 无限次抽，每次给预览，满意说「就这个」。
4. 在麦当劳 App 完成支付 → 说「记一笔」→ 生成卷轴网页 `scroll.html`。
5. 打开卷轴，看秘籍、门店、订单进度，顺手解锁成就。

## 技术架构

```
麦麦秘籍 (WorkBuddy Skill)
├── SKILL.md              # Skill 元信息 + 工作流指令
├── scripts/
│   ├── local_engine.py   # 本地引擎：抽签/存档/成就/卷轴渲染（纯标准库）
│   └── mcp_wrapper.py    # 麦当劳 MCP 调试客户端（可选）
├── assets/
│   └── scroll_template.html  # 古风卷轴网页模板
└── data/
    ├── menu_sample.json  # 示例菜单（无 Token 兜底）
    ├── secrets.json      # 麦麦秘籍存档（运行时生成）
    └── scroll.html       # 渲染产物（运行时生成）
```

- **WorkBuddy** 原生连接 `mcd-mcp`，Skill 通过 prompt 编排 MCP 工具调用。
- **local_engine.py** 处理不依赖网络的本地逻辑（抽签随机、秘籍 JSON 存档、成就判定、HTML 渲染）。
- **scroll.html** 用宣纸+木轴视觉，分四卷：秘籍卷 / 门店卷 / 订单卷 / 成就墙。

## 本地快速试跑（无需 Token）

```bash
python scripts/local_engine.py draw --pref 牛肉
python scripts/local_engine.py draw --category combo
python scripts/local_engine.py archive --item '{"name":"巨无霸","category":"burger","kcal":563,"price":24}' --store 店名 --order 订单号
python scripts/local_engine.py achievements --coupons 30
python scripts/local_engine.py render --stores '[{"name":"店","nav":"https://uri.amap.com/marker?..."}]' --orders '[{"no":"..","items":"..","status":"制作中"}]'
```

## 接入麦当劳 MCP

见 [MCP_INTEGRATION.md](./MCP_INTEGRATION.md)。

## 参赛提交

- 官方参赛声明（必交，模板不可改）：[CONTEST_DECLARATION.md](./CONTEST_DECLARATION.md)
- 参赛信息、作品简介与原创性说明：[ENTRY.md](./ENTRY.md)
