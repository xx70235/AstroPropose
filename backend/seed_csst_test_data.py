#!/usr/bin/env python3
"""
CSST 观测申请测试数据种子脚本

创建完整的工作流、表单模板、外部工具和测试用户
"""

from app import create_app, db
from app.models.models import (
    User, Role, Workflow, WorkflowState, ProposalType, FormTemplate, Instrument,
    ExternalTool, ExternalToolOperation, roles_users
)
from datetime import datetime

app = create_app()

def seed_csst_data():
    """创建 CSST 观测申请的完整测试数据"""
    
    print("🌱 开始创建 CSST 测试数据...")
    
    with app.app_context():
        # 清理现有数据（可选，根据需要）
        # db.session.execute(roles_users.delete())
        # db.session.query(ProposalType).delete()
        # db.session.query(WorkflowState).delete()
        # db.session.query(Workflow).delete()
        # db.session.query(FormTemplate).delete()
        # db.session.query(ExternalToolOperation).delete()
        # db.session.query(ExternalTool).delete()
        # db.session.commit()
        
        # ============================================
        # 1. 创建角色
        # ============================================
        print("📋 创建角色...")
        roles = {}
        role_names = ['Admin', 'Proposer', 'Instrument Scheduler', 'Panel Chair', 'Reviewer', 'Technical Expert']
        for role_name in role_names:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name)
                db.session.add(role)
            roles[role_name] = role
        db.session.commit()
        print(f"   ✓ 创建了 {len(roles)} 个角色")
        
        # ============================================
        # 2. 创建测试用户
        # ============================================
        print("👥 创建测试用户...")
        users = {}
        
        # Admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@csst.org')
            admin.set_password('password')
            admin.roles.append(roles['Admin'])
            db.session.add(admin)
        users['admin'] = admin
        
        # Proposer
        proposer = User.query.filter_by(username='proposer').first()
        if not proposer:
            proposer = User(username='proposer', email='proposer@csst.org')
            proposer.set_password('password')
            proposer.roles.append(roles['Proposer'])
            db.session.add(proposer)
        users['proposer'] = proposer
        
        # Technical Expert
        tech_expert = User.query.filter_by(username='tech_expert').first()
        if not tech_expert:
            tech_expert = User(username='tech_expert', email='tech_expert@csst.org')
            tech_expert.set_password('password')
            tech_expert.roles.append(roles['Technical Expert'])
            tech_expert.roles.append(roles['Instrument Scheduler'])
            db.session.add(tech_expert)
        users['tech_expert'] = tech_expert
        
        # Reviewer
        reviewer = User.query.filter_by(username='reviewer').first()
        if not reviewer:
            reviewer = User(username='reviewer', email='reviewer@csst.org')
            reviewer.set_password('password')
            reviewer.roles.append(roles['Reviewer'])
            db.session.add(reviewer)
        users['reviewer'] = reviewer
        
        # Panel Chair
        chair = User.query.filter_by(username='chair').first()
        if not chair:
            chair = User(username='chair', email='chair@csst.org')
            chair.set_password('password')
            chair.roles.append(roles['Panel Chair'])
            chair.roles.append(roles['Admin'])
            db.session.add(chair)
        users['chair'] = chair
        
        db.session.commit()
        print(f"   ✓ 创建了 {len(users)} 个测试用户")
        
        # ============================================
        # 3. 创建仪器
        # ============================================
        print("🔬 创建仪器...")
        instrument = Instrument.query.filter_by(code='CSST_IM').first()
        if not instrument:
            instrument = Instrument(
                code='CSST_IM',
                name='CSST Imaging Camera',
                description='CSST 多波段成像相机',
                is_active=True
            )
            db.session.add(instrument)
        db.session.commit()
        print(f"   ✓ 创建了仪器: {instrument.code}")
        
        # ============================================
        # 4. 创建外部工具（需要在表单模板之前创建，以便表单可以引用）
        # ============================================
        print("🔧 创建外部工具...")
        
        # 4.1 Target Visibility Tool (目标可见性检查工具)
        visibility_tool = ExternalTool.query.filter_by(name='CSST Target Visibility Calculator').first()
        visibility_op_id = None
        if not visibility_tool:
            visibility_tool = ExternalTool(
                name='CSST Target Visibility Calculator',
                description='CSST 目标可见性计算工具，用于检查观测目标是否可见',
                base_url='https://api.csst.org/visibility',
                auth_type='api_key',
                auth_config={
                    'key_name': 'X-API-Key',
                    'key_value': 'mock_visibility_key_abc123'
                },
                is_active=True
            )
            db.session.add(visibility_tool)
            db.session.commit()
            
            # 创建可见性检查操作
            visibility_op = ExternalToolOperation(
                tool_id=visibility_tool.id,
                operation_id='checkVisibility',
                name='Check Target Visibility',
                description='检查目标可见性并返回观测窗口',
                method='POST',
                path='/api/v1/check',
                parameters={
                    "query": [],
                    "path": [],
                    "header": []
                },
                request_body={
                    "type": "object",
                    "properties": {
                        "ra": {"type": "string", "description": "Right Ascension"},
                        "dec": {"type": "string", "description": "Declination"},
                        "target_name": {"type": "string", "description": "Target name"},
                        "start_date": {"type": "string", "format": "date"},
                        "end_date": {"type": "string", "format": "date"}
                    },
                    "required": ["ra", "dec"]
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "visible": {"type": "boolean"},
                        "reason": {"type": "string"},
                        "observation_window": {"type": "string"},
                        "elevation_range": {"type": "object"}
                    }
                },
                input_mapping={
                    "body": {
                        "ra": "context.ra",
                        "dec": "context.dec",
                        "target_name": "context.target_name"
                    }
                },
                output_mapping={
                    "to_context": {
                        "visibility_result": "response"
                    }
                },
                timeout=30,
                retry_config={
                    "max_retries": 2,
                    "retry_delay": 3,
                    "retryable_codes": [500, 502, 503, 504]
                },
                tool_type='validation',
                validation_config={
                    "block_on_failure": False,  # 填表时不阻止，仅显示结果
                    "block_on_service_error": False,
                    "failure_conditions": [
                        {"path": "response.visible", "operator": "==", "value": False}
                    ],
                    "error_message_template": "Target is not visible: {response.reason}"
                }
            )
            db.session.add(visibility_op)
            db.session.commit()
            visibility_op_id = visibility_op.id
        else:
            existing_op = ExternalToolOperation.query.filter_by(
                tool_id=visibility_tool.id,
                operation_id='checkVisibility'
            ).first()
            if existing_op:
                visibility_op_id = existing_op.id
        print("   ✓ CSST Target Visibility Calculator")
        
        # 4.2 Scheduling Tool (编排工具)
        scheduling_tool = ExternalTool.query.filter_by(name='CSST Scheduling Tool').first()
        scheduling_op_id = None
        if not scheduling_tool:
            scheduling_tool = ExternalTool(
                name='CSST Scheduling Tool',
                description='CSST 观测编排工具，用于技术专家编排观测目标',
                base_url='https://api.csst.org/scheduling',
                auth_type='api_key',
                auth_config={
                    'key_name': 'X-API-Key',
                    'key_value': 'mock_scheduling_key_12345'
                },
                is_active=True
            )
            db.session.add(scheduling_tool)
            db.session.commit()
            
            # 创建编排操作
            scheduling_op = ExternalToolOperation(
                tool_id=scheduling_tool.id,
                operation_id='scheduleTargets',
                name='Schedule Observation Targets',
                description='编排观测目标并生成编排结果',
                method='POST',
                path='/api/v1/schedule',
                parameters={
                    "query": [],
                    "path": [],
                    "header": []
                },
                request_body={
                    "type": "object",
                    "properties": {
                        "proposal_id": {"type": "integer"},
                        "targets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "target_name": {"type": "string"},
                                    "ra": {"type": "string"},
                                    "dec": {"type": "string"},
                                    "exposure_time": {"type": "number"},
                                    "filter": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "schedule_id": {"type": "string"},
                        "feedback": {"type": "string"},
                        "scheduled_targets": {"type": "array"}
                    }
                },
                input_mapping={
                    "body": {
                        "proposal_id": "proposal.id",
                        "targets": "proposal.data.observation_targets"
                    }
                },
                output_mapping={
                    "to_proposal_data": {
                        "scheduling_feedback": "response.feedback",
                        "schedule_id": "response.schedule_id"
                    }
                },
                timeout=60,
                retry_config={
                    "max_retries": 3,
                    "retry_delay": 5,
                    "retryable_codes": [500, 502, 503, 504]
                },
                tool_type='data_processing'
            )
            db.session.add(scheduling_op)
            db.session.commit()
            scheduling_op_id = scheduling_op.id
        else:
            existing_op = ExternalToolOperation.query.filter_by(
                tool_id=scheduling_tool.id,
                operation_id='scheduleTargets'
            ).first()
            if existing_op:
                scheduling_op_id = existing_op.id
        print("   ✓ CSST Scheduling Tool")
        
        # 4.3 Notification Tool (通知工具)
        notification_tool = ExternalTool.query.filter_by(name='CSST Notification Service').first()
        notification_op_id = None
        if not notification_tool:
            notification_tool = ExternalTool(
                name='CSST Notification Service',
                description='CSST 通知服务，用于发送邮件和系统通知',
                base_url='https://api.csst.org/notifications',
                auth_type='bearer',
                auth_config={
                    'token': 'mock_notification_token_67890'
                },
                is_active=True
            )
            db.session.add(notification_tool)
            db.session.commit()
            
            # 创建通知操作
            notification_op = ExternalToolOperation(
                tool_id=notification_tool.id,
                operation_id='sendNotification',
                name='Send Notification',
                description='发送通知给用户',
                method='POST',
                path='/api/v1/notify',
                parameters={
                    "query": [],
                    "path": [],
                    "header": []
                },
                request_body={
                    "type": "object",
                    "properties": {
                        "recipient_email": {"type": "string"},
                        "subject": {"type": "string"},
                        "message": {"type": "string"},
                        "notification_type": {"type": "string"}
                    }
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "notification_id": {"type": "string"}
                    }
                },
                input_mapping={
                    "body": {
                        "recipient_email": "proposal.author.email",
                        "subject": {"template": "CSST Proposal Update: {proposal.title}"},
                        "message": {"template": "Your proposal #{proposal.id} has been updated. Status: {proposal.status}"},
                        "notification_type": {"literal": "proposal_update"}
                    }
                },
                timeout=30,
                retry_config={
                    "max_retries": 2,
                    "retry_delay": 3,
                    "retryable_codes": [500, 502, 503, 504]
                },
                tool_type='notification'
            )
            db.session.add(notification_op)
            db.session.commit()
            notification_op_id = notification_op.id
        else:
            existing_op = ExternalToolOperation.query.filter_by(
                tool_id=notification_tool.id,
                operation_id='sendNotification'
            ).first()
            if existing_op:
                notification_op_id = existing_op.id
        print("   ✓ CSST Notification Service")
        
        print(f"   ✓ 创建了 3 个外部工具")
        
        # ============================================
        # 5. 创建表单模板
        # ============================================
        print("📝 创建表单模板...")
        
        # 5.1 Proposal Info (基本信息表)
        proposal_info = FormTemplate.query.filter_by(name='Proposal Info').first()
        if not proposal_info:
            proposal_info = FormTemplate(
                name='Proposal Info',
                phase='phase1',
                version=1,
                definition={
                    "fields": [
                        {
                            "name": "proposal_title",
                            "label": "Proposal Title",
                            "type": "text",
                            "required": True,
                            "placeholder": "Enter your proposal title"
                        },
                        {
                            "name": "abstract",
                            "label": "Abstract",
                            "type": "textarea",
                            "required": True,
                            "rows": 5,
                            "placeholder": "Provide a brief abstract of your proposal"
                        },
                        {
                            "name": "scientific_category",
                            "label": "Scientific Category",
                            "type": "select",
                            "required": True,
                            "options": [
                                {"value": "galaxy", "label": "Galaxy Evolution"},
                                {"value": "cosmology", "label": "Cosmology"},
                                {"value": "stellar", "label": "Stellar Physics"},
                                {"value": "exoplanet", "label": "Exoplanet"},
                                {"value": "solar", "label": "Solar System"},
                                {"value": "other", "label": "Other"}
                            ]
                        }
                    ]
                }
            )
            db.session.add(proposal_info)
        print("   ✓ Proposal Info 表单")
        
        # 5.2 Basic Observation Parameters (观测参数表 - 支持重复组)
        observation_params = FormTemplate.query.filter_by(name='Basic Observation Parameters').first()
        if not observation_params:
            observation_params = FormTemplate(
                name='Basic Observation Parameters',
                phase='phase1',
                version=1,
                instrument_id=instrument.id,
                definition={
                    "fields": [
                        {
                            "name": "observation_targets",
                            "label": "Observation Targets",
                            "type": "repeatable",
                            "required": True,
                            "min_entries": 1,
                            "max_entries": 100,
                            "sub_fields": [
                                {
                                    "name": "target_name",
                                    "label": "Target Name",
                                    "type": "text",
                                    "required": True,
                                    "placeholder": "e.g., NGC 1234"
                                },
                                {
                                    "name": "ra",
                                    "label": "Right Ascension (RA)",
                                    "type": "text",
                                    "required": True,
                                    "placeholder": "HH:MM:SS.ss",
                                    "external_tool_operation_id": visibility_op_id  # 关联可见性检查工具
                                },
                                {
                                    "name": "dec",
                                    "label": "Declination (Dec)",
                                    "type": "text",
                                    "required": True,
                                    "placeholder": "+/-DD:MM:SS.s",
                                    "external_tool_operation_id": visibility_op_id  # 关联可见性检查工具
                                },
                                {
                                    "name": "exposure_time",
                                    "label": "Exposure Time (seconds)",
                                    "type": "number",
                                    "required": True,
                                    "placeholder": "3600"
                                },
                                {
                                    "name": "filter",
                                    "label": "Filter",
                                    "type": "select",
                                    "required": True,
                                    "options": [
                                        {"value": "u", "label": "u-band"},
                                        {"value": "g", "label": "g-band"},
                                        {"value": "r", "label": "r-band"},
                                        {"value": "i", "label": "i-band"},
                                        {"value": "z", "label": "z-band"}
                                    ]
                                },
                                {
                                    "name": "repeat_count",
                                    "label": "Repeat Count",
                                    "type": "number",
                                    "required": False,
                                    "placeholder": "1"
                                }
                            ]
                        }
                    ]
                }
            )
            db.session.add(observation_params)
        else:
            # 如果表单已存在，更新它以包含外部工具关联
            if observation_params.definition and visibility_op_id:
                updated = False
                for field in observation_params.definition.get('fields', []):
                    if field.get('name') == 'observation_targets' and field.get('type') == 'repeatable':
                        for sub_field in field.get('sub_fields', []):
                            if sub_field.get('name') in ['ra', 'dec']:
                                if not sub_field.get('external_tool_operation_id'):
                                    sub_field['external_tool_operation_id'] = visibility_op_id
                                    updated = True
                if updated:
                    db.session.commit()
        print("   ✓ Basic Observation Parameters 表单")
        
        # 5.3 Proposer Info (提案人信息表)
        proposer_info = FormTemplate.query.filter_by(name='Proposer Info').first()
        if not proposer_info:
            proposer_info = FormTemplate(
                name='Proposer Info',
                phase='phase1',
                version=1,
                definition={
                    "fields": [
                        {
                            "name": "principal_investigator",
                            "label": "Principal Investigator",
                            "type": "text",
                            "required": True,
                            "placeholder": "Full name"
                        },
                        {
                            "name": "institution",
                            "label": "Institution",
                            "type": "text",
                            "required": True,
                            "placeholder": "Your institution name"
                        },
                        {
                            "name": "email",
                            "label": "Email",
                            "type": "text",
                            "required": True,
                            "placeholder": "your.email@institution.edu"
                        },
                        {
                            "name": "phone",
                            "label": "Phone",
                            "type": "text",
                            "required": False,
                            "placeholder": "+86-xxx-xxxx-xxxx"
                        },
                        {
                            "name": "co_investigators",
                            "label": "Co-Investigators",
                            "type": "textarea",
                            "required": False,
                            "rows": 3,
                            "placeholder": "One per line: Name (Institution)"
                        }
                    ]
                }
            )
            db.session.add(proposer_info)
        print("   ✓ Proposer Info 表单")
        
        # 5.4 Review Form (评审表)
        review_form = FormTemplate.query.filter_by(name='Review Form').first()
        if not review_form:
            review_form = FormTemplate(
                name='Review Form',
                phase='phase2',
                version=1,
                definition={
                    "fields": [
                        {
                            "name": "score",
                            "label": "Score",
                            "type": "number",
                            "required": True,
                            "min": 0,
                            "max": 10,
                            "placeholder": "0-10"
                        },
                        {
                            "name": "comment",
                            "label": "Comment",
                            "type": "textarea",
                            "required": True,
                            "rows": 6,
                            "placeholder": "Provide detailed review comments"
                        },
                        {
                            "name": "familiarity",
                            "label": "Familiarity with Scientific Field",
                            "type": "select",
                            "required": True,
                            "options": [
                                {"value": "expert", "label": "Expert"},
                                {"value": "familiar", "label": "Familiar"},
                                {"value": "basic", "label": "Basic"},
                                {"value": "unfamiliar", "label": "Unfamiliar"}
                            ]
                        }
                    ]
                }
            )
            db.session.add(review_form)
        print("   ✓ Review Form 表单")
        
        db.session.commit()
        print(f"   ✓ 创建了 4 个表单模板")
        
        # ============================================
        # 6. 创建工作流
        # ============================================
        print("🔄 创建工作流...")
        
        # 获取外部工具操作ID（已在第4部分创建）
        scheduling_tool = ExternalTool.query.filter_by(name='CSST Scheduling Tool').first()
        scheduling_op_id = None
        if scheduling_tool:
            existing_op = ExternalToolOperation.query.filter_by(
                tool_id=scheduling_tool.id,
                operation_id='scheduleTargets'
            ).first()
            if existing_op:
                scheduling_op_id = existing_op.id
        
        visibility_tool = ExternalTool.query.filter_by(name='CSST Target Visibility Calculator').first()
        visibility_op_id = None
        if visibility_tool:
            existing_op = ExternalToolOperation.query.filter_by(
                tool_id=visibility_tool.id,
                operation_id='checkVisibility'
            ).first()
            if existing_op:
                visibility_op_id = existing_op.id
        
        notification_tool = ExternalTool.query.filter_by(name='CSST Notification Service').first()
        notification_op_id = None
        if notification_tool:
            existing_op = ExternalToolOperation.query.filter_by(
                tool_id=notification_tool.id,
                operation_id='sendNotification'
            ).first()
            if existing_op:
                notification_op_id = existing_op.id
        
        csst_workflow = Workflow.query.filter_by(name='CSST Observation Workflow').first()
        if not csst_workflow:
            # 创建工作流定义，包含节点和表单关联
            csst_workflow = Workflow(
                name='CSST Observation Workflow',
                description='CSST 观测申请完整工作流，包括 Phase1 提交、技术编排、Phase2 提交和科学评审',
                definition={
                    "nodes": [
                        {
                            "id": "draft",
                            "type": "stateNode",
                            "data": {
                                "label": "Draft",
                                "formTemplateId": proposal_info.id if proposal_info.id else None,
                                "formRequired": False,
                                "description": "草稿状态，需要填写基本信息、观测目标和提案人信息"
                            },
                            "position": {"x": 100, "y": 50}
                        },
                        {
                            "id": "phase1_submitted",
                            "type": "stateNode",
                            "data": {"label": "Phase1Submitted", "description": "Phase1 已提交，等待技术编排"},
                            "position": {"x": 300, "y": 50}
                        },
                        {
                            "id": "scheduling",
                            "type": "stateNode",
                            "data": {"label": "Scheduling", "description": "技术专家正在编排观测目标"},
                            "position": {"x": 500, "y": 50}
                        },
                        {
                            "id": "phase1_confirmed",
                            "type": "stateNode",
                            "data": {"label": "Phase1Confirmed", "description": "Phase1 编排完成，等待用户确认并开始 Phase2"},
                            "position": {"x": 700, "y": 50}
                        },
                        {
                            "id": "phase2_draft",
                            "type": "stateNode",
                            "data": {
                                "label": "Phase2Draft",
                                "formTemplateId": observation_params.id if observation_params.id else None,
                                "formRequired": False,
                                "description": "Phase2 草稿，用户根据编排反馈调整观测目标"
                            },
                            "position": {"x": 500, "y": 180}
                        },
                        {
                            "id": "phase2_submitted",
                            "type": "stateNode",
                            "data": {"label": "Phase2Submitted", "description": "Phase2 已提交，等待科学评审"},
                            "position": {"x": 700, "y": 180}
                        },
                        {
                            "id": "under_review",
                            "type": "stateNode",
                            "data": {
                                "label": "UnderReview",
                                "formTemplateId": review_form.id if review_form.id else None,
                                "formRequired": True,
                                "description": "评审中，评审员需要填写评审表单"
                            },
                            "position": {"x": 900, "y": 180}
                        },
                        {
                            "id": "review_complete",
                            "type": "stateNode",
                            "data": {"label": "ReviewComplete", "description": "评审完成，等待最终决定"},
                            "position": {"x": 1100, "y": 180}
                        },
                        {
                            "id": "final_decision",
                            "type": "stateNode",
                            "data": {"label": "FinalDecision", "description": "最终决定已做出"},
                            "position": {"x": 1100, "y": 310}
                        }
                    ],
                    "edges": [
                        {"id": "e1", "source": "draft", "target": "phase1_submitted", "animated": True},
                        {"id": "e2", "source": "phase1_submitted", "target": "scheduling", "animated": True},
                        {"id": "e3", "source": "scheduling", "target": "phase1_confirmed", "animated": True},
                        {"id": "e4", "source": "phase1_confirmed", "target": "phase2_draft", "animated": True},
                        {"id": "e5", "source": "phase2_draft", "target": "phase2_submitted", "animated": True},
                        {"id": "e6", "source": "phase2_submitted", "target": "under_review", "animated": True},
                        {"id": "e7", "source": "under_review", "target": "review_complete", "animated": True},
                        {"id": "e8", "source": "review_complete", "target": "final_decision", "animated": True}
                    ],
                    "initial_state": "Draft",
                    "transitions": [
                        {
                            "name": "submit_phase1",
                            "label": "Submit Phase-1",
                            "from": "Draft",
                            "to": "Phase1Submitted",
                            "roles": ["Proposer"],
                            "conditions": {
                                "phase_status": {"phase": "phase1", "status": "draft"}
                            },
                            "effects": {
                                "phase": "phase1",
                                "set_phase_status": "submitted",
                                "record_submission_time": True
                            }
                        },
                        {
                            "name": "start_scheduling",
                            "label": "Start Scheduling",
                            "from": "Phase1Submitted",
                            "to": "Scheduling",
                            "roles": ["Technical Expert", "Instrument Scheduler"],
                            "effects": {
                                "external_tools": [
                                    {
                                        "operation_id": scheduling_op_id if scheduling_op_id else 1,
                                        "on_failure": "continue"
                                    }
                                ]
                            }
                        },
                        {
                            "name": "complete_scheduling",
                            "label": "Complete Scheduling",
                            "from": "Scheduling",
                            "to": "Phase1Confirmed",
                            "roles": ["Technical Expert", "Instrument Scheduler"],
                            "effects": {
                                "external_tools": [
                                    {
                                        "operation_id": notification_op_id if notification_op_id else 2,
                                        "on_failure": "continue"
                                    }
                                ]
                            }
                        },
                        {
                            "name": "start_phase2",
                            "label": "Start Phase-2",
                            "from": "Phase1Confirmed",
                            "to": "Phase2Draft",
                            "roles": ["Proposer"],
                            "effects": {
                                "phase": "phase2",
                                "set_phase_status": "draft"
                            }
                        },
                        {
                            "name": "submit_phase2",
                            "label": "Submit Phase-2",
                            "from": "Phase2Draft",
                            "to": "Phase2Submitted",
                            "roles": ["Proposer"],
                            "conditions": {
                                "phase_status": {"phase": "phase2", "status": "draft"}
                            },
                            "effects": {
                                "phase": "phase2",
                                "set_phase_status": "submitted",
                                "record_submission_time": True
                            }
                        },
                        {
                            "name": "start_review",
                            "label": "Start Review",
                            "from": "Phase2Submitted",
                            "to": "UnderReview",
                            "roles": ["Panel Chair", "Admin"],
                            "effects": {
                                "phase": "phase2",
                                "set_phase_status": "under_review"
                            }
                        },
                        {
                            "name": "complete_review",
                            "label": "Complete Review",
                            "from": "UnderReview",
                            "to": "ReviewComplete",
                            "roles": ["Reviewer", "Panel Chair"],
                            "effects": {
                                "phase": "phase2",
                                "set_phase_status": "reviewed"
                            }
                        },
                        {
                            "name": "finalize_decision",
                            "label": "Finalize Decision",
                            "from": "ReviewComplete",
                            "to": "FinalDecision",
                            "roles": ["Panel Chair", "Admin"],
                            "effects": {
                                "phase": "phase2",
                                "set_phase_status": "finalized",
                                "external_tools": [
                                    {
                                        "operation_id": notification_op.id if 'notification_op' in locals() else 2,
                                        "on_failure": "continue"
                                    }
                                ]
                            }
                        }
                    ]
                }
            )
            db.session.add(csst_workflow)
            db.session.flush()
            
            # 创建工作流状态
            # 注意：表单关联说明：
            # 1. 在创建提案时，系统会根据 phase 和 instrument 自动加载所有相关表单
            #    - Phase1 通用表单：Proposal Info, Proposer Info
            #    - Phase1 仪器表单：Basic Observation Parameters (根据选择的仪器)
            # 2. WorkflowState.form_template_id 主要用于在编辑已有提案时，提示需要填写的表单
            # 3. 一个状态可以关联一个主要表单作为提示，但实际显示时会加载所有相关表单
            
            states_data = [
                # (状态名称, 关联的表单ID, 表单是否必填, 状态描述)
                ("Draft", proposal_info.id, False, "草稿状态，需要填写基本信息、观测目标和提案人信息"),
                ("Phase1Submitted", None, False, "Phase1 已提交，等待技术编排"),
                ("Scheduling", None, False, "技术专家正在编排观测目标"),
                ("Phase1Confirmed", None, False, "Phase1 编排完成，等待用户确认并开始 Phase2"),
                ("Phase2Draft", observation_params.id if observation_params.id else None, False, "Phase2 草稿，用户根据编排反馈调整观测目标"),
                ("Phase2Submitted", None, False, "Phase2 已提交，等待科学评审"),
                ("UnderReview", review_form.id, True, "评审中，评审员需要填写评审表单"),
                ("ReviewComplete", None, False, "评审完成，等待最终决定"),
                ("FinalDecision", None, False, "最终决定已做出")
            ]
            
            for state_name, form_template_id, form_required, description in states_data:
                state = WorkflowState(
                    name=state_name,
                    workflow_id=csst_workflow.id,
                    form_template_id=form_template_id,
                    form_required=form_required,
                    description=description
                )
                db.session.add(state)
            
            db.session.commit()
        else:
            # 如果工作流已存在，更新其 definition 以确保节点包含正确的表单关联
            if csst_workflow.definition and csst_workflow.definition.get('nodes'):
                updated = False
                for node in csst_workflow.definition['nodes']:
                    state_name = node.get('data', {}).get('label')
                    if state_name == 'Draft':
                        if node.get('data', {}).get('formTemplateId') != proposal_info.id:
                            if 'data' not in node:
                                node['data'] = {}
                            node['data']['formTemplateId'] = proposal_info.id
                            node['data']['formRequired'] = False
                            updated = True
                    elif state_name == 'Phase2Draft':
                        expected_id = observation_params.id if observation_params.id else None
                        if node.get('data', {}).get('formTemplateId') != expected_id:
                            if 'data' not in node:
                                node['data'] = {}
                            node['data']['formTemplateId'] = expected_id
                            node['data']['formRequired'] = False
                            updated = True
                    elif state_name == 'UnderReview':
                        if node.get('data', {}).get('formTemplateId') != review_form.id:
                            if 'data' not in node:
                                node['data'] = {}
                            node['data']['formTemplateId'] = review_form.id
                            node['data']['formRequired'] = True
                            updated = True
                
                if updated:
                    # 需要标记 definition 字段为已修改，以便 SQLAlchemy 检测到变化
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(csst_workflow, 'definition')
                    db.session.commit()
                    print("   ✓ 已更新工作流定义中的表单关联")
        print("   ✓ CSST Observation Workflow")
        
        # ============================================
        # 7. 创建提案类型
        # ============================================
        print("📄 创建提案类型...")
        proposal_type = ProposalType.query.filter_by(name='CSST Observation').first()
        if not proposal_type:
            proposal_type = ProposalType(
                name='CSST Observation',
                description='CSST 观测申请',
                workflow_id=csst_workflow.id
            )
            db.session.add(proposal_type)
        db.session.commit()
        print("   ✓ CSST Observation 提案类型")
        
        print("\n✅ CSST 测试数据创建完成！")
        print("\n📊 数据摘要：")
        print(f"   - 角色: {len(roles)} 个")
        print(f"   - 用户: {len(users)} 个")
        print(f"   - 仪器: 1 个")
        print(f"   - 表单模板: 4 个")
        print(f"   - 外部工具: 2 个")
        print(f"   - 工作流: 1 个")
        print(f"   - 提案类型: 1 个")
        print("\n🔑 测试账户：")
        print("   - admin / password (管理员)")
        print("   - proposer / password (提案人)")
        print("   - tech_expert / password (技术专家)")
        print("   - reviewer / password (评审员)")
        print("   - chair / password (评审主席)")
        print("\n📋 表单与状态关联说明：")
        print("   - Draft 状态：关联 Proposal Info（提示表单）")
        print("   - Phase2Draft 状态：关联 Basic Observation Parameters（提示表单）")
        print("   - UnderReview 状态：关联 Review Form（必填表单）")
        print("   注意：创建提案时，系统会根据 phase 和 instrument 自动加载所有相关表单")
        print("\n🔧 外部工具关联说明：")
        print("   - 外部工具有两种调用方式：")
        print("     1. 在表单字段中调用（如可见性检查）：字段配置 external_tool_operation_id")
        print("     2. 在工作流转换中调用（如编排、通知）：在 transition.effects.external_tools 中配置")
        print("   - 表单字段调用：")
        print("     - RA/Dec 字段关联了可见性检查工具")
        print("     - 用户填写坐标后可以点击 'Check Visibility' 按钮")
        print("   - 转换调用：")
        print("     - start_scheduling 转换：调用编排工具")
        print("     - complete_scheduling 转换：调用通知工具")
        print("     - finalize_decision 转换：调用通知工具")

if __name__ == '__main__':
    seed_csst_data()

