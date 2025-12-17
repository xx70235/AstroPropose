# 工作流节点多表单关联设计探讨

## 一、当前设计分析

### 1.1 现状

**数据库模型**：
- `WorkflowState` 只有一个 `form_template_id` 字段（单表单关联）
- 通过 `form_required` 控制是否必填

**实际使用场景**：
- **Draft 状态**：需要填写多个表单
  - Proposal Info（基本信息）
  - Proposer Info（提案人信息）
  - Basic Observation Parameters（观测参数，仪器特定）
  
- **Phase2Draft 状态**：可能需要多个表单
  - Basic Observation Parameters（调整观测目标）
  - 可能还需要其他补充表单

- **UnderReview 状态**：目前只需要一个表单
  - Review Form（评审表单）

### 1.2 当前解决方案

**方式一：Phase + Instrument 自动加载（主要）**
- 创建新提案时，系统根据 `phase` 和 `instrument` 自动查找并加载所有相关表单
- 优点：灵活，自动适应不同仪器
- 缺点：不够明确，无法在工作流编辑器中直观看到

**方式二：WorkflowState.form_template_id（辅助）**
- 每个状态关联一个"主要"表单作为提示
- 优点：简单，易于理解
- 缺点：无法表达"需要多个表单"的需求

## 二、多表单关联的可行性分析

### 2.1 支持多表单关联的优势

1. **更明确的表达**
   - 在工作流编辑器中可以直观看到每个状态需要哪些表单
   - 便于管理员配置和理解工作流

2. **更灵活的验证**
   - 可以为不同表单设置不同的必填要求
   - 例如：Draft 状态下，Proposal Info 必填，Proposer Info 可选

3. **更好的用户体验**
   - 编辑已有提案时，可以明确提示需要填写哪些表单
   - 避免遗漏重要表单

4. **支持复杂场景**
   - 某些状态可能需要填写多个不同类型的表单
   - 例如：评审状态可能需要"技术评审表"和"科学评审表"

### 2.2 多表单关联的挑战

1. **数据库设计**
   - 需要创建关联表（多对多关系）
   - 需要迁移现有数据

2. **前端UI复杂度**
   - 工作流编辑器需要支持选择多个表单
   - 需要显示每个表单的必填状态

3. **表单加载逻辑**
   - 需要决定：是使用"状态关联的表单"还是"phase + instrument 自动加载"？
   - 两者如何协调？

4. **向后兼容**
   - 现有工作流只关联了一个表单
   - 需要确保现有功能不受影响

## 三、设计方案对比

### 方案A：保持当前设计（单表单关联 + 自动加载）

**优点**：
- 简单，易于实现
- 向后兼容
- Phase + Instrument 自动加载已经能覆盖大部分需求

**缺点**：
- 无法明确表达"需要多个表单"
- 工作流编辑器中看不到完整表单列表
- 编辑已有提案时，提示不够明确

**适用场景**：
- 表单主要由 Phase 和 Instrument 决定
- 状态关联表单主要用于"提示"而非"强制"

### 方案B：支持多表单关联（推荐）

**数据库设计**：
```python
# 创建关联表
class WorkflowStateFormTemplate(db.Model):
    __tablename__ = 'workflow_state_form_template'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_state_id = db.Column(db.Integer, db.ForeignKey('workflow_state.id'), nullable=False)
    form_template_id = db.Column(db.Integer, db.ForeignKey('form_template.id'), nullable=False)
    form_required = db.Column(db.Boolean, default=False)  # 该表单是否必填
    display_order = db.Column(db.Integer, default=0)  # 显示顺序
    
    workflow_state = db.relationship('WorkflowState', backref='form_templates_association')
    form_template = db.relationship('FormTemplate', backref='workflow_states_association')
    
    __table_args__ = (
        db.UniqueConstraint('workflow_state_id', 'form_template_id', name='uq_state_form'),
    )
```

**工作流定义（JSON）**：
```json
{
  "nodes": [
    {
      "id": "draft",
      "data": {
        "label": "Draft",
        "formTemplates": [
          {"id": 1, "required": true, "order": 1},   // Proposal Info
          {"id": 2, "required": false, "order": 2},  // Proposer Info
          {"id": 3, "required": true, "order": 3}    // Basic Observation Parameters
        ]
      }
    }
  ]
}
```

**优点**：
- 明确表达每个状态需要哪些表单
- 支持为不同表单设置不同的必填要求
- 在工作流编辑器中可以直观看到所有表单
- 编辑提案时可以明确提示需要填写的表单

**缺点**：
- 需要数据库迁移
- 前端UI需要更新
- 需要处理与"自动加载"的协调

**实现建议**：
1. **表单加载优先级**：
   - 如果状态关联了表单，优先使用关联的表单
   - 如果没有关联，则使用 Phase + Instrument 自动加载
   - 两者可以结合：关联表单 + 自动加载的补充表单

2. **向后兼容**：
   - 保留 `form_template_id` 字段（标记为 deprecated）
   - 迁移脚本：将现有的 `form_template_id` 转换为关联表记录

3. **前端UI**：
   - 工作流编辑器：支持多选表单，显示必填状态
   - 提案编辑页面：显示所有关联表单，标记必填项

### 方案C：混合方案（推荐用于过渡）

**设计**：
- 保留 `form_template_id` 作为"主要表单"（向后兼容）
- 添加 `form_templates` JSON 字段存储多个表单关联
- 逐步迁移到关联表

**优点**：
- 向后兼容
- 可以逐步迁移
- 灵活性高

**缺点**：
- 数据结构不够规范
- 需要维护两套逻辑

## 四、推荐方案

### 推荐：方案B（多表单关联）

**理由**：
1. **更符合实际需求**：一个状态确实可能需要多个表单
2. **更清晰的表达**：在工作流编辑器中可以直观看到所有表单
3. **更好的验证**：可以为不同表单设置不同的必填要求
4. **未来扩展性**：支持更复杂的工作流场景

### 实施步骤

1. **数据库迁移**：
   - 创建 `WorkflowStateFormTemplate` 关联表
   - 迁移现有 `form_template_id` 数据
   - 保留 `form_template_id` 字段（标记为 deprecated，用于向后兼容）

2. **后端API更新**：
   - 更新 `WorkflowState` 模型，添加 `form_templates` 关系
   - 更新工作流API，支持多表单关联
   - 更新表单加载逻辑，优先使用状态关联的表单

3. **前端UI更新**：
   - 工作流编辑器：支持多选表单，显示必填状态和顺序
   - 提案编辑页面：显示所有关联表单，标记必填项

4. **文档更新**：
   - 更新设计文档
   - 更新用户手册

## 五、具体实现建议

### 5.1 表单加载逻辑

```python
def get_forms_for_state(proposal, state):
    """
    获取状态关联的表单列表
    
    优先级：
    1. 状态关联的表单（WorkflowStateFormTemplate）
    2. Phase + Instrument 自动加载的表单（如果没有关联）
    3. 两者结合（如果配置了"允许补充表单"）
    """
    forms = []
    
    # 1. 获取状态关联的表单
    if state.form_templates_association:
        for assoc in state.form_templates_association.order_by(WorkflowStateFormTemplate.display_order):
            forms.append({
                'template': assoc.form_template,
                'required': assoc.form_required,
                'order': assoc.display_order
            })
    
    # 2. 如果没有关联表单，使用自动加载
    if not forms:
        forms = auto_load_forms_by_phase_instrument(proposal.phase, proposal.instruments)
    
    return forms
```

### 5.2 工作流编辑器UI

```jsx
// 节点编辑面板
<div>
  <label>Associated Form Templates</label>
  <div className="space-y-2">
    {selectedNode.data.formTemplates?.map((form, index) => (
      <div key={form.id} className="flex items-center gap-2">
        <select value={form.id} onChange={...}>
          {formTemplates.map(t => <option value={t.id}>{t.name}</option>)}
        </select>
        <input type="checkbox" checked={form.required} />
        <button onClick={() => removeForm(index)}>Remove</button>
      </div>
    ))}
    <button onClick={addForm}>+ Add Form</button>
  </div>
</div>
```

## 六、总结

**当前设计的问题**：
- 单表单关联无法表达"需要多个表单"的需求
- 工作流编辑器中看不到完整表单列表
- 编辑提案时提示不够明确

**推荐改进**：
- 支持多表单关联（方案B）
- 使用关联表存储多对多关系
- 保留自动加载作为补充机制
- 逐步迁移，保持向后兼容

**实施优先级**：
- 高优先级：如果系统需要支持复杂工作流，建议实施
- 中优先级：如果当前设计已满足需求，可以暂缓
- 低优先级：如果只是"提示"用途，当前设计已足够

