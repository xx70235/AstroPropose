## CSST 提案系统管理员操作手册（摘要）

### 1. 配置提案季
1. 登陆 AstroPropose 管理端，创建新的 `ProposalSeason`，设置 Phase-1/Phase-2 截止时间。
2. 在 “Proposal Types” 绑定季节与工作流版本，并指定可选仪器集合。

### 2. 管理表单模板
- 通用 Phase-1 字段：更新 `FormTemplate`（无 instrument 关联）。
- 仪器字段：在每个仪器的模板中维护必填参数、校验提示及附件说明。
- 模板更新后刷新前端缓存，确保提案人实时获取最新字段。

### 3. 工作流调控
- 通过 Workflow Editor 维护状态、角色与条件，推荐使用“CSST 示例”模板快速建模。
- 常用动作：
  - `submit_phase1`：提案人提交
  - `enter_scheduling`：管理员启动排程
  - `request_revision`：仪器反馈需修改
  - `promote_phase2`：确认后进入 Phase-2

### 4. 仪器排程协作
- 仪器团队从仪表板中查看待处理队列，提交排程窗口与备注。
- 反馈成功后，系统自动更新 ProposalInstrument 状态并记录时间戳。
- 需要修改申请人数据时，管理员可触发退回动作以解锁 Phase-1。

### 5. Phase-2 启动
- 所有仪器完成排程并获得 PI 确认后，管理员触发 `promote_phase2`。
- 系统自动为每个提案生成 Phase-2 表单与截止提醒。

### 6. 安全与审计
- 定期回顾 `ProposalStateHistory` 与仪器反馈日志，确认关键操作。
- 通过 RBAC 分配最小权限：管理员 (Admin)、仪器排程 (Instrument Scheduler)、评审主席 (Panel Chair)。
- 建议启用 HTTPS、轮换 JWT 密钥，并将后台访问日志存档。

