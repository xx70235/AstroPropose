# CSST 工作流关联关系图

## 工作流状态与表单关联

```
┌─────────────────────────────────────────────────────────────────┐
│                    CSST Observation Workflow                    │
└─────────────────────────────────────────────────────────────────┘

Draft (草稿)
  ├─ 关联表单: Proposal Info (提示)
  ├─ 自动加载表单:
  │   ├─ Proposal Info (通用, phase1)
  │   ├─ Proposer Info (通用, phase1)
  │   └─ Basic Observation Parameters (CSST_IM, phase1)
  └─ 说明: 创建提案时，系统根据 phase 和 instrument 自动加载所有相关表单

    ↓ [submit_phase1] (Proposer)

Phase1Submitted (Phase1 已提交)
  └─ 说明: 等待技术编排

    ↓ [start_scheduling] (Technical Expert)
    └─ 🔧 调用外部工具: CSST Scheduling Tool (编排工具)

Scheduling (编排中)
  └─ 说明: 技术专家正在编排观测目标

    ↓ [complete_scheduling] (Technical Expert)
    └─ 🔧 调用外部工具: CSST Notification Service (通知工具)

Phase1Confirmed (Phase1 已确认)
  └─ 说明: 编排完成，等待用户确认

    ↓ [start_phase2] (Proposer)

Phase2Draft (Phase2 草稿)
  ├─ 关联表单: Basic Observation Parameters (提示)
  └─ 说明: 用户根据编排反馈调整观测目标

    ↓ [submit_phase2] (Proposer)

Phase2Submitted (Phase2 已提交)
  └─ 说明: 等待科学评审

    ↓ [start_review] (Panel Chair)

UnderReview (评审中)
  ├─ 关联表单: Review Form (必填) ⚠️
  └─ 说明: 评审员必须填写评审表单

    ↓ [complete_review] (Reviewer)

ReviewComplete (评审完成)
  └─ 说明: 等待最终决定

    ↓ [finalize_decision] (Panel Chair)
    └─ 🔧 调用外部工具: CSST Notification Service (通知工具)

FinalDecision (最终决定)
  └─ 说明: 最终决定已做出
```

## 表单加载机制

### Phase1 创建提案时

系统自动加载以下表单（基于 phase 和 instrument）：

| 表单名称 | 类型 | Phase | Instrument | 说明 |
|---------|------|-------|------------|------|
| Proposal Info | 通用 | phase1 | - | 基本信息（标题、摘要、科学类别） |
| Proposer Info | 通用 | phase1 | - | 提案人信息 |
| Basic Observation Parameters | 仪器特定 | phase1 | CSST_IM | 观测目标（支持重复组） |

### Phase2 编辑提案时

系统显示关联的表单：

| 状态 | 关联表单 | 必填 | 说明 |
|------|----------|------|------|
| Phase2Draft | Basic Observation Parameters | 否 | 用于调整观测目标 |

### 评审时

系统显示关联的表单：

| 状态 | 关联表单 | 必填 | 说明 |
|------|----------|------|------|
| UnderReview | Review Form | **是** | 评审员必须填写 |

## 外部工具调用点

### 1. 编排工具 (CSST Scheduling Tool)

**调用位置**: `start_scheduling` 转换

**触发时机**: Phase1 提交后，技术专家开始编排

**功能**:
- 接收观测目标列表
- 进行观测编排
- 返回编排结果和反馈

**配置**:
```json
{
  "operation_id": <scheduling_op_id>,
  "on_failure": "continue"
}
```

**输入映射**:
- `proposal_id` ← `proposal.id`
- `targets` ← `proposal.data.observation_targets`

**输出映射**:
- `scheduling_feedback` ← `response.feedback`
- `schedule_id` ← `response.schedule_id`

### 2. 通知工具 - 编排完成 (CSST Notification Service)

**调用位置**: `complete_scheduling` 转换

**触发时机**: 编排完成后

**功能**:
- 通知提案人编排已完成
- 提醒查看编排反馈

**配置**:
```json
{
  "operation_id": <notification_op_id>,
  "on_failure": "continue"
}
```

### 3. 通知工具 - 最终决定 (CSST Notification Service)

**调用位置**: `finalize_decision` 转换

**触发时机**: 评审完成，做出最终决定后

**功能**:
- 通知提案人最终决定结果

**配置**:
```json
{
  "operation_id": <notification_op_id>,
  "on_failure": "continue"
}
```

## 数据流示例

### 示例：从 Draft 到 Phase1Submitted

```
1. 用户创建提案
   ├─ 选择提案类型: CSST Observation
   ├─ 选择仪器: CSST_IM
   └─ 系统自动加载表单:
       ├─ Proposal Info
       ├─ Proposer Info
       └─ Basic Observation Parameters

2. 用户填写表单
   ├─ Proposal Info: 填写标题、摘要、科学类别
   ├─ Proposer Info: 填写 PI 信息、机构等
   └─ Basic Observation Parameters: 添加多个观测目标
       ├─ Target 1: NGC 1234, RA: 12:34:56.7, Dec: +12:34:56
       ├─ Target 2: M31, RA: 00:42:44.3, Dec: +41:16:09
       └─ ...

3. 用户提交 Phase1
   ├─ 触发转换: submit_phase1
   ├─ 检查权限: 用户是否有 Proposer 角色
   ├─ 检查条件: phase1 状态是否为 draft
   └─ 执行效果:
       ├─ 设置 phase1 状态为 submitted
       └─ 记录提交时间

4. 状态转换
   └─ Draft → Phase1Submitted
```

### 示例：从 Phase1Submitted 到 Scheduling

```
1. 技术专家查看待编排提案
   └─ 提案状态: Phase1Submitted

2. 技术专家执行 "Start Scheduling"
   ├─ 触发转换: start_scheduling
   ├─ 检查权限: 用户是否有 Technical Expert 或 Instrument Scheduler 角色
   └─ 执行效果:
       └─ 调用外部工具: CSST Scheduling Tool
           ├─ 构建请求:
           │   ├─ proposal_id: 123
           │   └─ targets: [目标列表]
           ├─ 发送 HTTP POST 请求
           ├─ 接收响应:
           │   ├─ schedule_id: "SCH-2025-001"
           │   ├─ feedback: "编排完成，建议调整目标2的曝光时间"
           │   └─ scheduled_targets: [...]
           └─ 映射输出:
               ├─ proposal.data.scheduling_feedback = "编排完成..."
               └─ proposal.data.schedule_id = "SCH-2025-001"

3. 状态转换
   └─ Phase1Submitted → Scheduling
```

## 关键要点总结

### 表单关联

1. **自动加载机制**（主要）：
   - 基于 `phase` + `instrument` 自动查找
   - 适用于创建新提案时

2. **状态关联机制**（辅助）：
   - `WorkflowState.form_template_id` 关联
   - 用于编辑已有提案时的提示和验证

3. **一个状态可以关联一个表单**：
   - 主要用于提示和验证
   - 实际显示时会加载所有相关表单

### 外部工具关联

1. **通过转换调用**：
   - 在 `transition.effects.external_tools` 中定义
   - 不是直接关联到节点

2. **执行时机**：
   - 在执行转换时调用
   - 在状态转换之前执行

3. **失败处理**：
   - `on_failure: "continue"` - 失败也继续转换
   - `on_failure: "abort"` - 失败则阻止转换

4. **参数映射**：
   - `input_mapping`: 从提案数据映射到 API 请求
   - `output_mapping`: 从 API 响应映射回提案数据

## 查看关联关系

### 在工作流编辑器中

1. **查看节点关联的表单**：
   - 点击节点（State）
   - 在编辑面板中查看 "Associated Form Template"

2. **查看转换调用的外部工具**：
   - 点击箭头（Edge）
   - 在编辑面板中查看 "Effects" 部分的 JSON
   - 查找 `external_tools` 数组

### 在数据库中

```sql
-- 查看状态关联的表单
SELECT ws.name, ft.name as form_name, ws.form_required
FROM workflow_state ws
LEFT JOIN form_template ft ON ws.form_template_id = ft.id
WHERE ws.workflow_id = <workflow_id>;

-- 查看转换调用的外部工具
SELECT 
    wt.name as transition_name,
    wts.name as from_state,
    wtt.name as to_state,
    et.name as tool_name,
    eto.operation_id
FROM workflow w
JOIN workflow_state wts ON w.id = wts.workflow_id
JOIN workflow_state wtt ON w.id = wtt.workflow_id
JOIN workflow_transition wt ON ...
-- 需要解析 workflow.definition JSON 来查找 external_tools
```

