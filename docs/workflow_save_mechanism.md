# 工作流保存机制说明

## 概述

工作流的保存是一个多步骤的过程，涉及前端编辑器、API 调用和数据库存储。本文档详细说明整个保存流程。

## 保存流程

### 1. 前端编辑器（WorkflowEditor.js）

当用户点击 "Save Workflow" 按钮时，`handleSave` 函数会被调用：

```javascript
const handleSave = () => {
  try {
    // 1. 解析 Transitions JSON 配置
    const parsed = JSON.parse(transitionsDraft || '[]');
    
    // 2. 构建完整的 definition 对象
    const definition = {
      nodes,              // 节点数组（状态节点）
      edges,              // 边数组（状态转换）
      initial_state: initialState,  // 初始状态名称
      transitions: parsed, // 转换配置（JSON 格式）
    };
    
    // 3. 调用父组件传入的 onSave 回调
    setError('');
    onSave(definition);
  } catch (err) {
    console.error(err);
    setError('Failed to parse Transitions JSON. Please check the format.');
  }
};
```

### 2. Definition 对象结构

保存的 `definition` 对象包含以下部分：

#### 2.1 Nodes（节点）
- **id**: 节点唯一标识符（如 `"draft"`, `"submitted"`）
- **type**: 节点类型（固定为 `"stateNode"`）
- **position**: 节点在画布上的位置 `{x, y}`
- **data**: 节点数据
  - `label`: 状态名称（如 "Draft", "Submitted"）
  - `formTemplateId`: 关联的表单模板 ID（可选）
  - `formTemplateName`: 表单模板名称（显示用）
  - `formRequired`: 表单是否必填
  - `description`: 状态描述（可选）

#### 2.2 Edges（边）
- **id**: 边的唯一标识符（格式：`"edge-{source}-{target}"`）
- **source**: 源节点 ID
- **target**: 目标节点 ID
- **animated**: 是否显示动画效果
- **style**: 边的样式（颜色、宽度等）

#### 2.3 initial_state
- 字符串，表示新提案的初始状态名称
- 必须与某个节点的 `data.label` 完全匹配（区分大小写）

#### 2.4 transitions
- JSON 数组，定义所有可用的状态转换
- 每个转换包含：
  - `name`: 转换的唯一标识符（如 `"submit_phase1"`）
  - `label`: 转换的显示名称
  - `from`: 源状态名称（必须匹配某个节点的 `data.label`）
  - `to`: 目标状态名称（必须匹配某个节点的 `data.label`）
  - `roles`: 允许触发此转换的角色数组（如 `["Proposer", "Admin"]`）
  - `conditions`: （可选）转换条件
  - `effects`: （可选）转换效果（如调用外部工具、更新阶段状态等）

### 3. 父组件处理（workflows/page.js）

`WorkflowEditor` 组件通过 `onSave` prop 接收保存回调：

```javascript
const handleSave = async (definition) => {
  setSuccess('');
  setError('');
  try {
    // 调用 API 保存工作流
    await saveWorkflow(selectedWorkflowId, { 
      ...currentWorkflow,  // 保留现有属性（name, description）
      definition           // 更新 definition
    });
    setSuccess('Workflow saved successfully!');
  } catch (err) {
    setError('Failed to save workflow.');
    console.error(err);
  }
};
```

### 4. API 调用（lib/api.js）

前端通过 `saveWorkflow` 函数调用后端 API：

```javascript
export async function saveWorkflow(id, definition) {
  return fetcher(`/api/workflows/${id}`, {
    method: 'PUT',
    body: JSON.stringify(definition),
  });
}
```

### 5. 后端处理（api/workflows.py）

后端接收 PUT 请求并更新数据库：

```python
@bp.route('/<int:id>', methods=['PUT'])
@token_required
@admin_required
def update_workflow(current_user, id):
    """Updates an existing workflow."""
    workflow = Workflow.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No payload provided'}), 400

    # 更新工作流属性
    workflow.name = data.get('name', workflow.name)
    workflow.description = data.get('description', workflow.description)
    
    # 更新 definition（JSON 格式）
    if 'definition' in data:
        workflow.definition = data['definition']
    
    db.session.commit()
    return jsonify({'message': 'Workflow updated successfully'})
```

### 6. 数据库存储（models.py）

工作流的 `definition` 字段以 JSON 格式存储在数据库中：

```python
class Workflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.Text)
    definition = db.Column(db.JSON)  # JSON 格式存储完整的定义
    # ...
```

## 数据流图

```
用户点击 "Save Workflow"
    ↓
WorkflowEditor.handleSave()
    ↓
构建 definition 对象 {nodes, edges, initial_state, transitions}
    ↓
调用 onSave(definition)
    ↓
workflows/page.js.handleSave()
    ↓
调用 saveWorkflow(id, {definition})
    ↓
PUT /api/workflows/{id}
    ↓
backend/api/workflows.py.update_workflow()
    ↓
更新 Workflow.definition = data['definition']
    ↓
db.session.commit()
    ↓
保存到数据库（JSON 格式）
```

## 重要注意事项

### 1. 状态名称匹配
- `initial_state` 必须与某个节点的 `data.label` 完全匹配
- `transitions` 中的 `from` 和 `to` 也必须与节点的 `data.label` 匹配
- 匹配是**区分大小写**的

### 2. Transitions JSON 格式
- 必须是一个有效的 JSON 数组
- 如果格式错误，保存会失败并显示错误消息

### 3. 节点和边的同步
- `edges` 数组中的 `source` 和 `target` 必须对应 `nodes` 数组中存在的节点 ID
- 删除节点时，相关的边也会被自动删除

### 4. 权限要求
- 只有具有 `Admin` 角色的用户才能保存工作流
- 后端 API 使用 `@admin_required` 装饰器进行权限检查

## 示例：保存的 Definition 对象

```json
{
  "nodes": [
    {
      "id": "draft",
      "type": "stateNode",
      "position": { "x": 100, "y": 50 },
      "data": {
        "label": "Draft",
        "formTemplateId": null,
        "formRequired": false
      }
    },
    {
      "id": "submitted",
      "type": "stateNode",
      "position": { "x": 300, "y": 50 },
      "data": {
        "label": "Submitted",
        "formTemplateId": 1,
        "formTemplateName": "Phase-1 Submission Form",
        "formRequired": true
      }
    }
  ],
  "edges": [
    {
      "id": "edge-draft-submitted",
      "source": "draft",
      "target": "submitted",
      "animated": true,
      "style": { "stroke": "#6366f1", "strokeWidth": 2 }
    }
  ],
  "initial_state": "Draft",
  "transitions": [
    {
      "name": "submit_phase1",
      "label": "Submit Phase-1",
      "from": "Draft",
      "to": "Submitted",
      "roles": ["Proposer"],
      "conditions": {
        "phase_status": { "phase": "phase1", "status": "draft" }
      },
      "effects": {
        "phase": "phase1",
        "set_phase_status": "submitted",
        "record_submission_time": true
      }
    }
  ]
}
```

## 加载工作流

当编辑现有工作流时，流程相反：

1. 从数据库读取 `Workflow.definition`
2. 传递给 `WorkflowEditor` 的 `initialDefinition` prop
3. `WorkflowEditor` 使用 `useEffect` 初始化 `nodes` 和 `edges`
4. 用户可以在编辑器中查看和修改

## 总结

工作流的保存是一个完整的前后端流程：
- **前端**：收集用户编辑的节点、边和配置，构建 definition 对象
- **API**：通过 RESTful API 将 definition 发送到后端
- **后端**：验证权限，更新数据库中的 JSON 字段
- **数据库**：以 JSON 格式持久化存储

这种设计使得工作流定义非常灵活，可以存储复杂的图形结构和配置信息。

