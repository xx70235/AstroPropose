# CSST 提案系统需求与AstroPropose架构映射

> 本文档用于 Phase 1 需求澄清。部分仪器及流程信息基于公开资料整理，请与 CSST 科学团队确认后更新。

## 1. 项目背景与角色职责

- **核心目标**：基于 AstroPropose 框架实现 CSST 双阶段（Phase 1/Phase 2）多仪器提案管理系统，覆盖提案提交、仪器排程、申请人确认与科学评审。
- **主要角色**
  - `Proposer`：提交多仪器提案，Phase 1 提交科学构想，Phase 2 确认排程并提交详细技术参数。
  - `Instrument Scheduler`（各仪器团队）：接收对应仪器提案，进行排程与资源评估，反馈时间窗和技术意见。
  - `Science Admin`：统筹提案季、分配仪器团队、监控流程状态。
  - `Panel Chair / Reviewer`：Phase 2 进入科学评审后查看评分、意见，主持议程。
  - `System Admin`：维护模板、工作流、外部工具接入。

## 2. CSST 仪器清单（待确认）

| 仪器代号 | 功能描述 | Phase 1 关注字段 | Phase 2 补充字段 |
| --- | --- | --- | --- |
| SC（Survey Camera） | 7 色深度巡天成像 | 科学目标、波段需求、目标列表 | 详细观测计划、曝光配置、时间窗 |
| MSS（Multi-Slit Spectroscopy） | 多缝光谱巡天 | 目标源、分辨率需求 | 光谱策略、排程窗口、校准方案 |
| IFS（Integral Field Spectrograph） | 视场光谱成像 | 科学场景、天空区域 | 切片配置、积分时间、姿态约束 |
| NIR（Near-Infrared Imager/Spectrometer） | 近红外成像/光谱 | 目标波段、灵敏度目标 | 滤光片选择、冷却/热条件 |
| MCI（Multi-Channel Imager） | 多通道快速成像 | 观测目标、快速触发需求 | 时序计划、技术联系人 |

> 若 CSST 最新仪器命名/配置不同，请在确认后更新表格。

## 3. 双阶段流程概述

1. **Phase 1：提案征集**
   - Proposer 提交科学构想（多仪器组合），需选择参与仪器并填写对应表单。
   - 系统根据 `ProposalType` + `Instrument` 生成动态表单，写入 `Proposal` 与子项数据。
   - 提交后进入“待仪器排程”状态。

2. **仪器排程环节**
   - 各仪器 `Instrument Scheduler` 登录仪器门户，查看待评估提案。
   - 填写排程反馈（可含时间窗、冲突说明、建议），提交后状态更新。
   - 汇总后，系统通知 Proposer 查看结果。

3. **Phase 2：申请人确认与科学评审**
   - Proposer 查看仪器排程反馈，可进行确认/修改/撤回。
   - 当所有仪器确认完成后，进入 Phase 2 正式提交，补充详细技术参数。
   - 科学管理员锁定提案，进入科学评审工作流（评审分配、评分、决策）。

4. **评审与决策**
   - Panel Chair/Reviewers 使用评审界面进行打分、评论。
   - 最终决策生成并通知各方。

## 4. 需求与现有架构映射

| CSST 需求 | AstroPropose 现状 | 差距与扩展方向 |
| --- | --- | --- |
| 多仪器配置与数据分离 | `Proposal` 单实体，缺少仪器维度 | 新增 `Instrument`、`ProposalInstrument`、`InstrumentFeedback` 等模型；扩展 API |
| 双阶段状态管理 | `WorkflowEngine` 为占位实现 | 实装工作流引擎，支持 Phase 迁移、并行状态与条件分支 |
| 动态表单（按仪器/Phase 区分） | `FormTemplate` 仅支持单模板 | 扩展模板元数据（仪器/阶段标签、版本）；前端支持多步骤表单 |
| 仪器排程反馈接口 | 无对应 API | 新增仪器门户 API：列表、反馈提交、状态改变 |
| 申请人确认流程 | 无 | 为 Proposer 提供确认接口与界面，写入 Phase 2 状态 |
| 科学评审权限 | RBAC 支持基础角色 | 拓展角色类型（Panel Chair、Reviewer）、权限校验与仪表板 |
| 通知/外部系统集成 | 未实现 | 设计通知钩子与外部排程系统接入占位 |
| 提案季与时间节点管理 | `ProposalSeason` 基础模型 | 补充 Phase 里程碑、截止日期校验与界面配置 |

## 5. 后续交付物

- 经确认的仪器与流程信息更新至此文档。
- 需求—架构映射表驱动后续模型、API、前端改造。
- 在 Stage 2 开始前，与 CSST 干系人评审并冻结需求基线。


