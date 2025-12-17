# CSST 观测申请测试数据使用指南

## 概述

本文档说明如何使用已创建的 CSST 观测申请测试数据，包括工作流、表单模板、外部工具和测试用户。

## 运行种子脚本

```bash
cd backend
uv run python seed_csst_test_data.py
```

## 创建的数据

### 1. 角色 (6个)

- **Admin**: 管理员
- **Proposer**: 提案人
- **Instrument Scheduler**: 仪器调度员
- **Panel Chair**: 评审主席
- **Reviewer**: 评审员
- **Technical Expert**: 技术专家

### 2. 测试用户 (5个)

所有用户密码均为 `password`：

| 用户名 | 邮箱 | 角色 |
|--------|------|------|
| admin | admin@csst.org | Admin |
| proposer | proposer@csst.org | Proposer |
| tech_expert | tech_expert@csst.org | Technical Expert, Instrument Scheduler |
| reviewer | reviewer@csst.org | Reviewer |
| chair | chair@csst.org | Panel Chair, Admin |

### 3. 仪器 (1个)

- **CSST_IM**: CSST 多波段成像相机

### 4. 表单模板 (4个)

#### 4.1 Proposal Info (基本信息表)
- **阶段**: Phase1
- **类型**: 通用表单
- **字段**:
  - Proposal Title (文本，必填)
  - Abstract (文本域，必填)
  - Scientific Category (下拉选择，必填)

#### 4.2 Basic Observation Parameters (观测参数表)
- **阶段**: Phase1
- **类型**: 仪器特定表单 (CSST_IM)
- **特点**: 支持重复填写多个观测目标
- **字段** (在重复组中):
  - Target Name (文本，必填)
  - Right Ascension (文本，必填)
  - Declination (文本，必填)
  - Exposure Time (数字，必填)
  - Filter (下拉选择，必填)
  - Repeat Count (数字，可选)

#### 4.3 Proposer Info (提案人信息表)
- **阶段**: Phase1
- **类型**: 通用表单
- **字段**:
  - Principal Investigator (文本，必填)
  - Institution (文本，必填)
  - Email (文本，必填)
  - Phone (文本，可选)
  - Co-Investigators (文本域，可选)

#### 4.4 Review Form (评审表)
- **阶段**: Phase2
- **类型**: 通用表单
- **字段**:
  - Score (数字 0-10，必填)
  - Comment (文本域，必填)
  - Familiarity with Scientific Field (下拉选择，必填)
    - Expert
    - Familiar
    - Basic
    - Unfamiliar

### 5. 外部工具 (2个)

#### 5.1 CSST Scheduling Tool (编排工具)
- **Base URL**: `https://api.csst.org/scheduling`
- **认证**: API Key (`X-API-Key: mock_scheduling_key_12345`)
- **操作**: `scheduleTargets`
  - **方法**: POST
  - **路径**: `/api/v1/schedule`
  - **功能**: 编排观测目标并生成编排结果
  - **输入映射**: 
    - `proposal_id` ← `proposal.id`
    - `targets` ← `proposal.data.observation_targets`
  - **输出映射**:
    - `scheduling_feedback` ← `response.feedback`
    - `schedule_id` ← `response.schedule_id`

#### 5.2 CSST Notification Service (通知服务)
- **Base URL**: `https://api.csst.org/notifications`
- **认证**: Bearer Token (`mock_notification_token_67890`)
- **操作**: `sendNotification`
  - **方法**: POST
  - **路径**: `/api/v1/notify`
  - **功能**: 发送通知给用户
  - **输入映射**:
    - `recipient_email` ← `proposal.author.email`
    - `subject` ← `"CSST Proposal Update: {proposal.title}"`
    - `message` ← `"Your proposal #{proposal.id} has been updated. Status: {proposal.status}"`

### 6. 工作流: CSST Observation Workflow

#### 6.1 状态流程

```
Draft → Phase1Submitted → Scheduling → Phase1Confirmed 
  → Phase2Draft → Phase2Submitted → UnderReview 
  → ReviewComplete → FinalDecision
```

#### 6.2 状态说明

| 状态 | 说明 | 关联表单 | 表单必填 |
|------|------|----------|----------|
| Draft | 草稿状态 | Proposal Info | 否 |
| Phase1Submitted | Phase1 已提交 | - | - |
| Scheduling | 技术编排中 | - | - |
| Phase1Confirmed | Phase1 已确认 | - | - |
| Phase2Draft | Phase2 草稿 | - | - |
| Phase2Submitted | Phase2 已提交 | - | - |
| UnderReview | 评审中 | Review Form | 是 |
| ReviewComplete | 评审完成 | - | - |
| FinalDecision | 最终决定 | - | - |

#### 6.3 转换规则

| 转换名称 | 从 | 到 | 允许角色 | 说明 |
|---------|-----|-----|----------|------|
| submit_phase1 | Draft | Phase1Submitted | Proposer | 提交 Phase1 |
| start_scheduling | Phase1Submitted | Scheduling | Technical Expert, Instrument Scheduler | 开始编排（调用编排工具） |
| complete_scheduling | Scheduling | Phase1Confirmed | Technical Expert, Instrument Scheduler | 完成编排（发送通知） |
| start_phase2 | Phase1Confirmed | Phase2Draft | Proposer | 开始 Phase2 |
| submit_phase2 | Phase2Draft | Phase2Submitted | Proposer | 提交 Phase2 |
| start_review | Phase2Submitted | UnderReview | Panel Chair, Admin | 开始评审 |
| complete_review | UnderReview | ReviewComplete | Reviewer, Panel Chair | 完成评审 |
| finalize_decision | ReviewComplete | FinalDecision | Panel Chair, Admin | 最终决定（发送通知） |

## 使用流程

### 1. 提案人创建提案

1. 使用 `proposer` 账户登录
2. 创建新提案，选择 "CSST Observation" 提案类型
3. 填写表单：
   - **Proposal Info**: 基本信息
   - **Basic Observation Parameters**: 观测目标（可添加多个）
   - **Proposer Info**: 提案人信息
4. 提交 Phase1

### 2. 技术专家编排

1. 使用 `tech_expert` 账户登录
2. 查看待编排的提案
3. 执行 "Start Scheduling" 转换（自动调用编排工具）
4. 完成编排后执行 "Complete Scheduling"（自动发送通知给提案人）

### 3. 提案人调整并提交 Phase2

1. 提案人收到通知后登录
2. 查看编排反馈
3. 调整观测目标（Phase2 会重新显示观测参数表单）
4. 提交 Phase2

### 4. 科学评审

1. 评审主席执行 "Start Review"
2. 评审员使用 `reviewer` 账户登录
3. 填写评审表单（Score, Comment, Familiarity）
4. 完成评审

### 5. 最终决定

1. 评审主席执行 "Finalize Decision"
2. 系统自动发送通知给提案人

## 注意事项

### 重复组字段的使用

**Basic Observation Parameters** 表单使用了 `repeatable` 类型的字段，允许用户添加多个观测目标：

- 最小条目数：1
- 最大条目数：100
- 每个条目包含：目标名称、坐标、曝光时间、滤光片等

在前端界面中，用户可以通过 "+ Add Entry" 按钮添加新的目标。

### 外部工具说明

当前创建的外部工具是 **Mock 工具**，实际不会发送真实的 HTTP 请求。在生产环境中，需要：

1. 配置真实的外部工具 API 地址
2. 更新认证信息
3. 确保 API 端点符合定义的接口规范

### 工作流状态匹配

确保：
- 转换中的 `from` 和 `to` 状态名称与工作流状态完全匹配（区分大小写）
- 初始状态 `Draft` 必须存在

## 测试建议

1. **完整流程测试**: 使用不同角色的账户，完整走一遍从创建到最终决定的流程
2. **重复组测试**: 测试添加多个观测目标的情况
3. **外部工具测试**: 虽然当前是 Mock，但可以测试工具调用的日志记录
4. **权限测试**: 验证不同角色只能执行允许的转换
5. **表单验证**: 测试必填字段的验证

## 数据清理

如果需要重新创建测试数据，可以：

1. 手动删除数据库中的相关记录
2. 或者修改脚本，取消注释清理代码部分

## 后续扩展

可以根据需要添加：
- 更多的测试用户
- 更多的表单模板
- 更多的外部工具
- 更复杂的工作流分支

