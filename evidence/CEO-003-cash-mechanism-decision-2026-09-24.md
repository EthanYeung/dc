# CEO-003｜现金机制候选与决策记录

- 决策日：2026-09-24
- 范围：美国低资本现金机制的公开资料比较、独立 Auditor 复核与 Allocator 选择。
- 状态：候选筛选与批准请求；不是市场测试授权。未联系用户、未发帖、未开户、未花费、未收款、未承诺交付，也未建立 active Experiment。
- 当前内部状态：`state/bootstrap.yaml` 记载 `DISCOVERY`、可用/承诺资金均为 $0、无 active experiment。[unverified]

## 1. Allocator 决定

仅保留候选 A——直接面向 B2B 买家的固定范围预付人工服务——作为唯一可继续审查的候选；这不是批准启动测试。独立 Auditor 将 A 评为 `ACCEPT_CONDITIONALLY`，只允许进入后续审批审查；Fiverr 服务、Gumroad 数字商品和 Amazon Associates 联盟营销分别不作为本轮现金测试候选。没有任何候选获准执行；当前真实现金实验数为 0。[unverified]

**不选第二个候选。** 其余机制的公开平台条款可说明结算约束，但没有 DC 的合格买家、支付、提现或复购证据；同时会增加渠道、平台访问和隐私/税务核实工作。[unverified]

## 2. 公开机制比较

| 机制 | 公开现金路径与已记录条款 | Allocator / Auditor 结论 |
|---|---|---|
| A. 直接 B2B 固定范围人工服务、买家预付 | 收款可在机制上先于履约，但具体买家、交付物、获客渠道、支付账户/KYC、提现、退款/拒付路径都尚未核实。Stripe 公开页面列出美国本土卡费率 2.9% + 30¢，其首次 payout 帮助页列出 7–14 天等待；这不证明 DC 有合格账户或同样的实际到账路径。[20][21] | 唯一条件性保留候选；当前未达到可测试门槛。Auditor 提到的 $149 测试价与单笔不超过 2 小时履约仅为方案假设，不是市场证据。[unverified] |
| B. Fiverr 上架服务 | Fiverr 页面称订单完成后自由职业者收到客户已清算款的 80%；另一帮助页称订单完成后需等待 14 天才能提现。[19][25] | Auditor 拒绝作为当前现金测试候选；平台成交与提现规则不证明 DC 有访问资格、买家需求或可重复订单。[unverified] |
| C. Gumroad 数字商品 | Gumroad 公开页面列出自有网站销售 10% + $0.50 + 销售税；市场发现交易另列 30% 费率。其 payout 说明要求销售至少满 7 天，且 chargeback 比例超过销售量 1% 时会自动暂停 payout。[1][2] | Auditor 拒绝作为当前现金测试候选；未证实有可分发受众、成交或可提现账户。[unverified] |
| D. Amazon Associates 联盟营销 | Amazon 页面说明达到前三笔合格销售后会评估申请（发生在加入后前 180 天内）；付款约在每月结束后 60 天，余额至少 USD 10 才付款。[23][16] FTC 指引建议披露靠近推荐内容。[24] | Auditor 拒绝作为当前现金测试候选；较长的归因/支付时滞及未验证的合规获客面不适合当前验证目标。[unverified] |

- Stripe 的定价页列出美国本土卡每笔 2.9% + 30¢。[20]
- Stripe 的首次 payout 帮助页列出 7–14 天等待期。[21]
- Fiverr 说明订单完成后卖家收到客户已清算款的 80%。[19]
- Fiverr 帮助页说明订单完成后需等 14 天才能提现。[25]
- Gumroad 自有网站交易列出 10% + $0.50 加销售税的费率。[1]
- Gumroad 要求待 payout 销售至少满 7 天，并可在 chargeback 比例超过销售量 1% 时暂停 payout。[2]
- Amazon Associates 页面写明至少三笔合格销售后评估申请。[23]
- Amazon Associates 页面写明付款约在月末后 60 天，且最低付款额为 USD 10。[16]
- FTC 指引称披露应尽量靠近推荐内容。[24]

平台费率、资格、结算时限只说明平台规则，不构成需求、成交、付款、净现金或复购证据。[unverified]

## 3. 需求证据与实验边界

本轮只完成公开来源研究与内部审计；没有观察到合格线索、买家承诺、实际付款、重复使用或复购。没有平台账号、渠道许可、支付/KYC资格或提现路径被核实。以上缺口不得由公开报价、卖家宣传、平台费率或推算净额替代。[unverified]

候选 A 尚缺可执行的买家/交付范围、一个具体且获准的触达渠道、完整收款与提现链路、退款/拒付责任上限、数据最小化方案、适用法律/税务边界及实际履约工时上限。SQLite runtime 目前不是可信授权边界：在有权直接写数据库的情况下，可伪造审批/证据或修改 treasury；因此在独立可信写入服务、身份验证和外部凭证核验落地前，不应使用该原型记载真实资金或批准真实 payout。[unverified]

### 候选 A 的待审批实验草案（未启动）

- 假设：某一明确的美国 B2B 买家会为一个固定范围、低数据风险的人工服务预付；实际买家与工作流仍待确定。[unverified]
- 试价：$149 只是 Auditor 复核时看到的工作假设，不是经验证价格，也不是最终报价。[unverified]
- 现金支出：$0；当前没有支出或支付账户授权。
- 执行状态：不得联系潜在客户、公开发布、建账号、收款或承诺交付。
- 成功判据暂不锁定：应在具体买家、交付物、渠道与净现金核验路径确认后，由 Auditor/Allocator 写入独立的正式实验审批请求；至少须以可核验的 settled/withdrawable 或到账净现金扣除退款、拒付和直接成本，而非点击、意向、平台余额或未到账款作为现金证据。[unverified]
- 失败/停止判据：若渠道许可、账户资格/提现链路、法律与税务边界、风险上限任一项无法核实，停止该候选，不联系、不收款、不垫资。[unverified]

## 4. 未决事项与下一触发

1. 先由 Founder 对 `approvals/CEO-003-approval-request-2026-09-24.md` 中的 Stage 0 请求作出决定。该请求只覆盖不超过 2 个 agent-hours、$0、公开来源的前置核验，不授权外联或真实实验。
2. 如获批，核实一个具体、允许使用的渠道及其招募边界；核实可用支付/收款资格、KYC、实际费用、结算/提现、保留款、退款与拒付；确定服务边界、隐私数据最小化与人工损失上限。
3. 任一前置项通过后，另行提交候选 A 的正式实验审批请求；在此之前保持 `DISCOVERY`，不创建 active Experiment。

**最终状态：** 1 个条件性候选（A）进入审批前置审查；B/C/D 本轮排除；0 个获准或运行中的真实现金实验；支出 $0；没有需求或收入已验证。[unverified]

## Sources

[1] https://gumroad.com/help/article/66-gumroads-fees — Gumroad fees
    > "For sales made on Gumroad's website, we charge a 10% + $0.50 fee + sales tax per transaction."
    > "10% + $0.50 fee + sales tax per transaction."
    > "flat 30% fee, which includes all processing fees."
[2] https://gumroad.com/help/article/281-payout-delays — Gumroad payout delays
    > "The money sent out to you has to have come from a sale that is at least 7 days old."
    > "Payouts are also paused automatically when your chargeback rate goes above 1% of your sales volume."
    > "sale that is at least 7 days old."
    > "chargeback rate goes above 1% of your sales volume."
[16] https://affiliate-program.amazon.com/help/node/topic/GKDG94FQSRXSJCGK?linkId=333617465 — Amazon Associates payment timing and minimums
    > "Approximately 60 days after the end of each month"
    > "we will not send payment until the total amount due is at least USD 10."
    > "Approximately 60 days after the end of each month."
    > "at least USD 10."
[19] https://help.fiverr.com/hc/en-us/articles/34069565843985-How-Fiverr-works-for-freelancers — How Fiverr works for freelancers
    > "After an order is completed, freelancers receive 80% of the client’s cleared payment."
[20] https://stripe.com/pricing — Stripe Pricing & Fees
    > "2.9% + 30¢ per successful transaction for domestic cards."
[21] https://support.stripe.com/questions/waiting-on-your-first-stripe-payout-what-you-need-to-know?locale=en-GB — Waiting for your first Stripe payout
    > "There is a 7–14 day waiting period for the first payout."
[23] https://affiliate-program.amazon.com/help/node/topic/G8TW5AE9XL2VX9VM — Amazon Associates Application Review Process
    > "at least three within the first 180 days."
[24] https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking — FTC Endorsement Guides: What People Are Asking
    > "The closer the disclosure is to your recommendation, the better."
[25] https://help.fiverr.com/hc/en-us/articles/360011421198-FAQs-for-freelancers — FAQs for freelancers — Fiverr Help Center
    > "After the order is marked as complete, you have to wait 14 days to withdraw your funds."
