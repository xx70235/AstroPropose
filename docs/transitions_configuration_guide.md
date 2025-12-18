# Transitions Configuration 使用指南

## 什么是 Transitions Configuration？

**Transitions Configuration（转换配置）** 是工作流编辑器中最重要的部分之一。它定义了**提案如何从一个状态转换到另一个状态**的详细规则。

## 简单理解

### 图形 vs 配置

- **图形部分（Nodes & Edges）**：定义了工作流的**结构**（有哪些状态，状态之间如何连接）
- **Transitions Configuration**：定义了工作流的**规则**（谁可以转换、什么时候可以转换、转换时会发生什么）

### 类比

想象一个门禁系统：
- **图形**：定义了有哪些房间和门
- **Transitions Configuration**：定义了谁有钥匙、什么时候可以开门、开门后会发生什么

## Transitions 的作用

当用户想要改变提案状态时（比如从 "Draft" 提交到 "Submitted"），系统会：

1. **查找对应的 transition**：根据当前状态和要执行的操作名称
2. **检查权限**：用户是否有 `roles` 中定义的角色
3. **检查条件**：是否满足 `conditions` 中定义的条件
4. **执行效果**：应用 `effects` 中定义的操作（如更新阶段状态、调用外部工具等）
5. **改变状态**：将提案从 `from` 状态转换到 `to` 状态

## Transitions JSON 结构

每个 transition 是一个 JSON 对象，包含以下字段：

```json
{
  "name": "submit_phase1",           // 转换的唯一标识符（必填）
  "label": "Submit Phase-1",         // 显示给用户的名称（必填）
  "from": "Draft",                   // 源状态名称（必填，必须匹配某个节点的 label）
  "to": "Submitted",                 // 目标状态名称（必填，必须匹配某个节点的 label）
  "roles": ["Proposer"],             // 允许触发此转换的角色数组（必填）
  "conditions": { ... },             // 转换条件（可选）
  "effects": { ... }                  // 转换效果（可选）
}
```

## 字段详解

### 1. name（必填）
- **作用**：转换的唯一标识符
- **用途**：在代码中通过这个名称来触发转换
- **示例**：`"submit_phase1"`, `"approve_proposal"`, `"reject_proposal"`
- **注意**：必须是唯一的，不能重复

### 2. label（必填）
- **作用**：显示给用户的友好名称
- **用途**：在界面上显示为按钮或操作名称
- **示例**：`"Submit Phase-1"`, `"Approve Proposal"`, `"Reject Proposal"`

### 3. from（必填）
- **作用**：源状态名称
- **要求**：必须与某个节点的 `data.label` **完全匹配**（区分大小写）
- **示例**：如果节点标签是 `"Draft"`，这里也必须是 `"Draft"`

### 4. to（必填）
- **作用**：目标状态名称
- **要求**：必须与某个节点的 `data.label` **完全匹配**（区分大小写）
- **示例**：如果节点标签是 `"Submitted"`，这里也必须是 `"Submitted"`

### 5. roles（必填）
- **作用**：定义哪些角色的用户可以触发此转换
- **格式**：字符串数组
- **可用角色**：
  - `"Admin"`：管理员
  - `"Proposer"`：提案人
  - `"Instrument Scheduler"`：仪器调度员
  - `"Panel Chair"`：评审主席
  - `"Reviewer"`：评审员
- **示例**：
  ```json
  "roles": ["Proposer"]                    // 只有提案人可以
  "roles": ["Admin", "Panel Chair"]        // 管理员或评审主席可以
  "roles": []                               // 任何人都可以（不推荐）
  ```

### 6. conditions（可选）
- **作用**：定义转换必须满足的条件
- **格式**：对象，包含各种条件检查
- **常用条件**：
  ```json
  "conditions": {
    "phase_status": {
      "phase": "phase1",
      "status": "draft"
    }
  }
  ```
  这表示：只有当提案的 phase1 阶段状态是 "draft" 时，才能执行此转换

### 7. effects（可选）
- **作用**：定义转换执行时的副作用（自动执行的操作）
- **格式**：对象，包含各种效果
- **常用效果**：
  ```json
  "effects": {
    "phase": "phase1",                      // 操作哪个阶段
    "set_phase_status": "submitted",       // 设置阶段状态
    "record_submission_time": true,         // 记录提交时间
    "external_tools": [                     // 调用外部工具
      {
        "operation_id": 1,
        "on_failure": "abort"
      }
    ]
  }
  ```

## 完整示例

### 示例 1：简单的提交转换

```json
[
  {
    "name": "submit_phase1",
    "label": "Submit Phase-1",
    "from": "Draft",
    "to": "Submitted",
    "roles": ["Proposer"],
    "conditions": {
      "phase_status": {
        "phase": "phase1",
        "status": "draft"
      }
    },
    "effects": {
      "phase": "phase1",
      "set_phase_status": "submitted",
      "record_submission_time": true
    }
  }
]
```

**解释**：
- 提案人可以将提案从 "Draft" 状态转换到 "Submitted" 状态
- 只有当 phase1 阶段状态是 "draft" 时才能执行
- 执行时会自动将 phase1 状态改为 "submitted" 并记录提交时间

### 示例 2：带外部工具调用的转换

```json
[
  {
    "name": "submit_with_visibility_check",
    "label": "Submit with Visibility Check",
    "from": "Draft",
    "to": "Submitted",
    "roles": ["Proposer"],
    "effects": {
      "phase": "phase1",
      "set_phase_status": "submitted",
      "external_tools": [
        {
          "operation_id": 5,
          "on_failure": "abort"
        }
      ]
    }
  }
]
```

**解释**：
- 提交时会自动调用外部工具（如可见性检查）
- 如果外部工具失败，转换会被阻止（`on_failure: "abort"`）

### 示例 3：评审转换

```json
[
  {
    "name": "approve_proposal",
    "label": "Approve Proposal",
    "from": "Under Review",
    "to": "Approved",
    "roles": ["Panel Chair", "Admin"],
    "effects": {
      "phase": "phase1",
      "set_phase_status": "approved"
    }
  },
  {
    "name": "reject_proposal",
    "label": "Reject Proposal",
    "from": "Under Review",
    "to": "Rejected",
    "roles": ["Panel Chair", "Admin"],
    "effects": {
      "phase": "phase1",
      "set_phase_status": "rejected"
    }
  }
]
```

**解释**：
- 评审主席或管理员可以批准或拒绝提案
- 从 "Under Review" 状态可以转换到 "Approved" 或 "Rejected"

## 常见问题

### Q1: 为什么需要同时定义图形和 Transitions？

**A**: 
- **图形**：提供可视化，让管理员直观地看到工作流结构
- **Transitions**：提供详细的业务规则，控制实际的行为

两者必须**保持一致**：
- 如果图形中有从 "Draft" 到 "Submitted" 的箭头，Transitions 中必须有对应的转换定义
- Transitions 中的 `from` 和 `to` 必须与节点的 `label` 匹配

### Q2: 如果图形中有连接但 Transitions 中没有定义会怎样？

**A**: 用户无法执行该转换。系统只会执行 Transitions 中定义的转换。

### Q3: 如果 Transitions 中定义了但图形中没有连接会怎样？

**A**: 虽然技术上可以执行，但图形显示不完整，不推荐这样做。

### Q4: 一个状态可以有多个转换吗？

**A**: 可以！比如从 "Under Review" 可以转换到 "Approved" 或 "Rejected"，只需要定义两个不同的 transition。

### Q5: 如何确保 JSON 格式正确？

**A**: 
- 使用 JSON 验证工具检查格式
- 保存时系统会验证，如果格式错误会显示错误消息
- 建议使用 "Load Example Workflow" 按钮查看示例格式

## 最佳实践

1. **保持一致性**：确保图形中的连接与 Transitions 中的定义一致
2. **使用有意义的名称**：`name` 应该清晰描述转换的目的
3. **明确权限**：总是明确指定 `roles`，不要留空
4. **添加条件**：对于重要的转换，添加 `conditions` 确保数据完整性
5. **测试转换**：保存后在实际提案中测试转换是否按预期工作

## 总结

**Transitions Configuration** 是工作流的"大脑"，它定义了：
- ✅ **谁**可以执行转换（roles）
- ✅ **什么时候**可以转换（conditions）
- ✅ **转换时做什么**（effects）
- ✅ **从哪到哪**（from → to）

没有 Transitions Configuration，图形只是静态的展示，无法实际控制提案的状态转换。


