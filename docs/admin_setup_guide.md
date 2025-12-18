# AstroPropose 管理员配置指南

本指南介绍如何创建新的 Proposal 项目，包括工作流配置、提案类型设置和自定义表单创建。

## 📋 目录

1. [前置准备](#前置准备)
2. [步骤1：创建工作流](#步骤1创建工作流)
3. [步骤2：创建提案类型](#步骤2创建提案类型)
4. [步骤3：创建表单模板](#步骤3创建表单模板)
5. [步骤4：创建仪器（可选）](#步骤4创建仪器可选)
6. [步骤5：测试提案流程](#步骤5测试提案流程)

---

## 前置准备

### 1. 确保系统运行
```bash
# 启动后端
cd backend
uv run flask run --port 5001

# 启动前端（新终端）
cd frontend
npm run dev
```

### 2. 使用管理员账户登录
- 访问：`http://localhost:3000/login`
- 用户名：`admin`
- 密码：`password`

---

## 步骤1：创建工作流

### 1.1 访问工作流管理页面
导航到 `http://localhost:3000/admin/workflows`

### 1.2 创建新工作流
在页面顶部"创建新工作流"区域：
- **名称**：如 "CSST Observation Workflow"
- **描述**：如 "CSST两阶段观测提案评审流程"
- 点击 **"创建工作流"** 按钮

### 1.3 可视化配置工作流

#### 添加状态节点
在画布上拖拽创建以下状态节点：
- `Draft` - 草稿
- `Submitted` - 已提交
- `Scheduling` - 排程中
- `Phase1Confirmed` - Phase 1 确认
- `Phase2Submitted` - Phase 2 提交
- `UnderReview` - 评审中
- `Approved` - 通过
- `Rejected` - 拒绝

#### 连接状态转换
用连线定义状态之间的转换关系。

#### 设置初始状态
在"初始状态"输入框中输入：`Draft`

### 1.4 配置转换规则（JSON）

点击"插入 CSST 示例"按钮，或手动输入以下 JSON：

```json
[
  {
    "action": "submit",
    "from": "Draft",
    "to": "Submitted",
    "roles": ["Proposer"],
    "label": "提交提案",
    "effects": {
      "phase": "phase1",
      "set_phase_status": "submitted",
      "record_submission_time": true
    }
  },
  {
    "action": "send_to_scheduling",
    "from": "Submitted",
    "to": "Scheduling",
    "roles": ["Panel Chair", "Admin"],
    "label": "发送至仪器排程",
    "effects": {
      "set_phase_status": "scheduling"
    }
  },
  {
    "action": "confirm_phase1",
    "from": "Scheduling",
    "to": "Phase1Confirmed",
    "roles": ["Panel Chair", "Admin"],
    "label": "确认 Phase 1",
    "conditions": [
      {
        "type": "all_instruments_scheduled",
        "message": "所有仪器必须完成排程"
      }
    ],
    "effects": {
      "phase": "phase1",
      "set_phase_status": "confirmed",
      "record_confirmation_time": true
    }
  },
  {
    "action": "submit_phase2",
    "from": "Phase1Confirmed",
    "to": "Phase2Submitted",
    "roles": ["Proposer"],
    "label": "提交 Phase 2",
    "effects": {
      "phase": "phase2",
      "set_phase_status": "submitted"
    }
  },
  {
    "action": "send_to_review",
    "from": "Phase2Submitted",
    "to": "UnderReview",
    "roles": ["Panel Chair", "Admin"],
    "label": "发送至评审"
  },
  {
    "action": "approve",
    "from": "UnderReview",
    "to": "Approved",
    "roles": ["Panel Chair"],
    "label": "批准提案"
  },
  {
    "action": "reject",
    "from": "UnderReview",
    "to": "Rejected",
    "roles": ["Panel Chair"],
    "label": "拒绝提案"
  }
]
```

### 1.5 保存工作流
点击"保存工作流"按钮。

---

## 步骤2：创建提案类型

⚠️ **当前需要使用 Python 脚本创建**

### 2.1 运行创建脚本

```bash
cd backend
uv run python create_proposal_type.py
```

### 2.2 按提示输入信息

示例输入：
```
名称：CSST-IMG
描述：CSST成像观测提案
关联工作流ID：1
```

### 2.3 验证创建结果

脚本会显示：
```
✅ 提案类型创建成功！
   ID: 4
   名称: CSST-IMG
   描述: CSST成像观测提案
   关联工作流: CSST Observation Workflow
```

---

## 步骤3：创建表单模板

### 3.1 运行创建脚本

```bash
cd backend
uv run python create_form_template.py
```

### 3.2 选择表单类型

1. **通用表单**（所有提案都需填写）
   - 输入仪器ID：`0`
   - 适用阶段：`phase1`

2. **仪器特定表单**（针对某个仪器）
   - 输入仪器ID：如 `1` (CSST_IM)
   - 适用阶段：`phase1` 或 `phase2`

### 3.3 使用示例或自定义表单

#### 选项A：使用示例表单
输入 `y` 使用内置示例（包含科学目标、目标坐标、曝光时间等字段）

#### 选项B：自定义表单
输入 `n`，然后提供JSON定义。

**表单字段类型**：
- `text` - 单行文本
- `textarea` - 多行文本
- `number` - 数字
- `select` - 下拉选择
- `checkbox` - 复选框
- `file` - 文件上传

**示例JSON**：
```json
{
  "fields": [
    {
      "name": "science_goal",
      "label": "科学目标",
      "type": "textarea",
      "required": true,
      "rows": 6,
      "placeholder": "请描述您的科学研究目标..."
    },
    {
      "name": "target_name",
      "label": "目标名称",
      "type": "text",
      "required": true
    },
    {
      "name": "exposure_time",
      "label": "曝光时间 (秒)",
      "type": "number",
      "required": true
    },
    {
      "name": "filter",
      "label": "滤光片",
      "type": "select",
      "required": true,
      "options": [
        {"value": "u", "label": "u波段"},
        {"value": "g", "label": "g波段"},
        {"value": "r", "label": "r波段"}
      ]
    }
  ]
}
```

### 3.4 验证创建结果

脚本会显示：
```
✅ 表单模板创建成功！
   ID: 5
   名称: CSST成像表单
   阶段: phase1
   版本: v1
   关联仪器: CSST_IM
   
表单包含 8 个字段
```

---

## 步骤4：创建仪器（可选）

如果需要添加新仪器：

```bash
cd backend
uv run python -c "
from app import create_app, db
from app.models.models import Instrument

app = create_app()
with app.app_context():
    inst = Instrument(
        code='CSST_NEW',
        name='CSST New Instrument',
        description='新仪器描述',
        is_active=True
    )
    db.session.add(inst)
    db.session.commit()
    print(f'✅ 仪器创建成功！ID: {inst.id}')
"
```

---

## 步骤5：测试提案流程

### 5.1 创建测试提案

1. 使用 `proposer` 账户登录（密码：`proposer123`）
2. 访问 `http://localhost:3000/proposals/new`
3. 填写表单：
   - 选择提案类型（如 CSST-IMG）
   - 填写标题和摘要
   - 选择仪器
   - 填写通用表单
   - 填写各仪器特定表单
4. 点击"提交 Phase 1 提案"

### 5.2 测试工作流转换

1. 使用 `chair` 账户登录（密码：`chair123`）
2. 访问 `http://localhost:3000/dashboard/panel`
3. 查看提案状态
4. 触发工作流转换（如"发送至仪器排程"）

### 5.3 测试仪器排程

1. 使用 `scheduler` 账户登录（密码：`scheduler123`）
2. 访问 `http://localhost:3000/dashboard`
3. 在"仪器排程工作台"选择仪器
4. 查看待排程提案
5. 填写排程反馈并提交

---

## 🎯 快速配置检查清单

- [ ] 工作流已创建并配置完成
- [ ] 提案类型已创建并关联到工作流
- [ ] 通用表单模板已创建（phase1）
- [ ] 各仪器特定表单模板已创建
- [ ] 仪器已配置并激活
- [ ] 测试提案可以成功创建
- [ ] 工作流转换正常工作
- [ ] 仪器排程功能正常

---

## 🔧 常见问题

### Q1: 创建工作流后看不到？
**A**: 刷新页面，或重新选择工作流下拉菜单。

### Q2: 提案类型创建后前端不显示？
**A**: 检查是否已关联到有效的工作流ID。使用以下命令验证：
```bash
cd backend
uv run python -c "
from app import create_app, db
from app.models.models import ProposalType
app = create_app()
with app.app_context():
    types = ProposalType.query.all()
    for t in types:
        print(f'{t.id}: {t.name} -> Workflow {t.workflow_id}')
"
```

### Q3: 表单不显示自定义字段？
**A**: 检查表单模板的JSON格式是否正确，特别注意：
- 必须包含 `fields` 数组
- 每个字段必须有 `name`、`label`、`type` 属性

### Q4: 如何删除错误创建的项目？
**A**: 使用 Python 脚本删除：
```bash
cd backend
uv run python -c "
from app import create_app, db
from app.models.models import ProposalType
app = create_app()
with app.app_context():
    item = ProposalType.query.get(ID)  # 替换ID
    db.session.delete(item)
    db.session.commit()
    print('已删除')
"
```

---

## 📚 相关文档

- [CSST 需求文档](./csst_requirements.md)
- [工作流引擎文档](./workflow_engine.md)
- [API 文档](../README.md#api-endpoints)

---

**更新日期**: 2025-12-01
**版本**: 1.0







