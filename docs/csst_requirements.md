## CSST 提案系统需求整理（阶段 1）

### 1. 干系人与角色
- **提案人（PI/Co-I）**：创建并提交 Phase-1/Phase-2 提案。
- **仪器团队（Instrument Scheduler）**：负责本仪器的排程与资源确认。
- **项目管理员（Mission Admin）**：配置提案季、截止时间、流程与模板。
- **科学评审专家（Reviewer）**：在 Phase-2 后进行科学评审。
- **评审主席（Panel Chair）**：跨仪器汇总评分、组织评审会。
- **系统集成接口（Ops API）**：接收最终排程结果，驱动观测执行。

### 2. 仪器清单（待项目组确认）
- **Survey Module (SM)**：成像主镜，支持多滤光片组合。
- **Multichannel Imaging Instrument (MCI)**：多波段成像，强调波段配置。
- **Integral Field Spectrograph (IFS)**：积分视场光谱。
- **Near-Infrared Spectrometer (NIR Spec)**：近红外高分辨率光谱。
- **可扩展接口**：保留自定义仪器配置以应对后续新增。

> 需确认：各仪器 Phase-1/Phase-2 所需字段、文件附件、约束（如目标数量上限、可用窗口）。

### 3. Phase-1 / Phase-2 时间线（初版假设）
| 阶段 | 目标 | 关键节点 |
| --- | --- | --- |
| Phase-1 | 收集科学目标与粗略观测需求 | 开放：T0；截止：T0+6 周；仪器排程反馈截止：T0+10 周 |
| 排程确认 | 各仪器将可执行窗口反馈给提案人 | 提案人确认截止：反馈后 10 天 |
| Phase-2 | 提交最终技术细节，进入科学评审 | 提交截止：T0+16 周；评审：T0+18〜22 周 |

> 需确认：是否存在滚动 ToO 通道及其与常规流程的交互。

### 4. 现有 AstroPropose 架构映射

| CSST 需求 | AstroPropose 现有能力 | 差距/待实现 |
| --- | --- | --- |
| 多仪器差异化表单 | `FormTemplate` 支持 JSON 定义 | 需支持仪器+Phase 组合、字段条件 |
| 双阶段状态机 | `Workflow`/`WorkflowState` 模型 | `workflow_engine.py` 待实现、需分支与并行任务 |
| 仪器排程反馈 | 提案数据 JSON 承载 | 需新增 `InstrumentAssignment` 模型与 API |
| 提案季管理 | `ProposalSeason` 模型雏形 | 需关联 Phase 截止、模板、通知 |
| 角色体系 | `Role` + RBAC | 需新增仪器团队、评审主席权限控制 |
| 外部系统接口 | 占位说明 | 需定义排程 API、消息触发机制 |

### 5. 输出与下一步
- 需求—架构映射表已形成，后续开发将基于此推进。
- 待项目组确认的事项记录于文中“需确认”条目。
- 建议在阶段 2 开始前召开一次干系人评审会议，敲定仪器字段与时间线。

