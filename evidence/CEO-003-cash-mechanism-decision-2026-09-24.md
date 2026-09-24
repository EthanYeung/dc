# CEO-003｜现金机制候选与决策记录

- 决策日：2026-09-24
- 范围：美国低资本现金机制的公开资料比较、独立 Auditor 复核与 Allocator 选择。
- 状态：Founder 已于 2026-09-25 批准并完成 Stage 0 公开来源前置核验；结果为 HOLD/NO-GO，不是市场测试授权。未联系用户、未发帖、未开户、未花费、未收款、未承诺交付，也未建立 active Experiment。
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

## 4. Founder 批准的 Stage 0 公开来源前置核验（2026-09-25）

- 批准记录：Founder 在聊天中批准 `APR-CEO-003-001`，仅覆盖公开来源、$0、最多 2 agent-hours 的前置核验；不授权外联、开户、发帖/上架、收款或测试。批准状态记入 `approvals/CEO-003-approval-request-2026-09-24.md`。
- 目标买家假设：美国小型独立簿记事务所负责人或实际执行月结的簿记师，使用 QBO、服务多个 SMB 客户。该 ICP 来自 CEO-002 的条件性 Discovery 草案，不是具体具名线索，也没有已观察到的购买意向、承诺或付款。[unverified]
- 服务假设：固定范围的“月末关账异常流程诊断”，只依据不含客户身份、交易、银行、税务或账户数据的流程问卷，交付一页异常分类/下一步清单和一次修改；履约上限 2 小时。$149 仍只是未验证的试价假设，未批准报价、未向买家提出。[unverified]
- 渠道候选：Upwork Project Catalog。官方帮助页描述了建立项目、提交审查、获接受后启用的流程；这只证明平台有一般服务目录路径，不代表 DC 的账户资格、该服务类别、具体 listing 或零成本发布已获确认。[33] Upwork 自由职业者服务费按合同为 0%–15%；DC 的实际合同费率未知。[10]
- 资金路径（平台通用规则，不是 DC 实测）：固定价项目有客户审阅期，提交后最多 14 天批准或要求修改，之后资金进入 5 天安全暂留；因此平台余额/托管款不等同于 DC 已实现或可提现现金。[37] Upwork 帮助页列出美国银行提现流程及提现方式启用等待期，但没有核实 DC 的银行、税务地址、账户资格或本账户的实际到账时间/费用。[39][unverified]
- KYC/税务与反转：Upwork 可能要求核验法定姓名、生日、地址及 SSN/税号等身份资料；没有创建账户，也没有收集或保存这些个人信息。[41] 公开帮助内容显示存在 365 天内付款的退款请求路径，但本轮未能确认 DC 账户的 chargeback 追偿范围、退款后的最大损失或固定责任上限。[43][unverified] 具体法律实体、税务分类、退款/拒付责任上限仍未解决。
- 渠道门槛：尚未核实该确切服务应归入的 Upwork 类别、零现金发布条件、DC 可用的 KYC/收款资格和账户级提现链路；没有实际买家或任何市场行为证据。[unverified] Upwork 是租用平台渠道，平台规则与费率不能证明需求或复购。[unverified]
- 时间记录：本轮没有独立计量 agent-hours；不声称精确用时。因关键门槛仍未核实，按批准范围停止，不继续扩展研究。

### Auditor / Allocator gate

**决定：HOLD / NO-GO。** 目标买家仍是 ICP 假设而非具体买家，服务和价格尚未验证；Upwork 只是通用渠道候选，账号/分类/零成本发布资格和最大退款/拒付损失未通过核验。不得创建账号、发布项目、接触客户或启动真实现金实验。保持 `DISCOVERY`，不提交现金实验批准请求。

**下一触发：** 只有在 Founder 单独决定是否授权下一阶段的账号/渠道验证，并由 Founder 直接处理任何身份、税务和银行验证（不得将凭证或身份号码发到聊天或仓库）后，才可重新评估候选 A；任何上架、外联、收款或实际履约仍需另行、具体的批准。若不愿承担平台资格与退款/拒付不确定性，则关闭 A，回到 CEO-002 的 #5 Discovery 问题，不追加桌面研究。

**最终状态：** Stage 0 已完成但未通过测试门槛；A 仍为条件性候选，B/C/D 本轮排除；0 个获准或运行中的真实现金实验；支出 $0；没有需求、收入或复购证据。[unverified]

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
[10] https://support.upwork.com/hc/en-us/articles/211062538-Learn-about-the-Freelancer-Service-Fee — Upwork Freelancer Service Fee
    > "The fee ranges from 0% to 15% per contract."
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
[33] https://support.upwork.com/hc/en-us/articles/360057397533-How-to-create-a-project-in-Project-Catalog — How to create a project in Project Catalog — Upwork Help
    > "The project moves to your active tab and is switched on automatically."
[37] https://support.upwork.com/hc/en-us/articles/211063718-How-payments-for-milestones-and-fixed-price-contracts-work — How payments for milestones and fixed-price contracts work — Upwork Help
    > "After you submit, your client has 14 days to approve or request changes."
    > "You’ll receive a 5-day security hold on your funds."
[39] https://support.upwork.com/hc/en-us/articles/211063818-How-to-withdraw-earnings-to-your-U-S-bank-on-Upwork — How to withdraw earnings to your U.S. bank on Upwork — Upwork Help
    > "Your new withdrawal method will become active three days after you confirm the account."
[41] https://support.upwork.com/hc/en-us/articles/211067818-Know-Your-Customer-KYC-identity-information — Know Your Customer (KYC) identity information — Upwork Help
    > "legal name, birthday, address, and Social Security or tax identification number"
[43] https://support.upwork.com/hc/en-us/articles/17976486850451--Request-a-refund — Request a refund — Upwork Help
    > "within the past 365 days"
