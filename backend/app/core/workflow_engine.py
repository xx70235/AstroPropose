from datetime import datetime
from typing import Any, Dict, List, Optional

from app import db
from app.models.models import Proposal, ProposalPhase, ProposalInstrument, WorkflowState


class WorkflowEngine:
    """
    基于 Workflow.definition JSON 描述的轻量级工作流引擎。

    约定 Workflow.definition 的结构如下：
    {
        "transitions": [
            {
                "name": "submit_phase1",
                "label": "提交 Phase-1",
                "from": "Draft",
                "to": "Submitted",
                "roles": ["Proposer"],
                "conditions": {
                    "phase_status": {"phase": "phase1", "status": "draft"}
                },
                "effects": {
                    "phase": "phase1",
                    "set_phase_status": "submitted",
                    "record_submission_time": true
                }
            }
        ]
    }
    """

    def __init__(self, db_session=None):
        self.db = db_session or db.session

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    def execute_transition(self, proposal_id: int, action_name: str, actor, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        proposal = Proposal.query.get_or_404(proposal_id)
        transition = self._find_transition(proposal, action_name, context or {})
        self._authorize(transition, actor)
        self._apply_transition(proposal, transition, context or {})
        self.db.commit()
        return {
            "status": "success",
            "proposal_id": proposal.id,
            "action": action_name,
            "new_state": proposal.current_state.name if proposal.current_state else None,
        }

    def get_allowed_actions(self, proposal_id: int, actor) -> List[Dict[str, Any]]:
        proposal = Proposal.query.get_or_404(proposal_id)
        workflow = self._load_workflow(proposal)
        current_state = proposal.current_state.name if proposal.current_state else None
        actor_roles = {role.name for role in getattr(actor, "roles", [])}
        allowed: List[Dict[str, Any]] = []
        for transition in workflow.get("transitions", []):
            if transition.get("from") != current_state:
                continue
            if not self._has_required_role(transition, actor_roles):
                continue
            if not self._evaluate_conditions(transition.get("conditions"), proposal):
                continue
            allowed.append(
                {
                    "name": transition.get("name"),
                    "label": transition.get("label", transition.get("name")),
                    "to": transition.get("to"),
                }
            )
        return allowed

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #
    def _load_workflow(self, proposal: Proposal) -> Dict[str, Any]:
        workflow = proposal.proposal_type.workflow
        if workflow is None or workflow.definition is None:
            raise ValueError("Workflow definition missing.")
        return workflow.definition

    def _find_transition(self, proposal: Proposal, action_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        workflow = self._load_workflow(proposal)
        current_state = proposal.current_state.name if proposal.current_state else None
        for transition in workflow.get("transitions", []):
            if transition.get("name") != action_name:
                continue
            if transition.get("from") != current_state:
                raise ValueError(f"Transition {action_name} invalid from {current_state}")
            if not self._evaluate_conditions(transition.get("conditions"), proposal, context):
                raise ValueError(f"Transition {action_name} conditions unmet.")
            return transition
        raise ValueError(f"Action {action_name} not defined in workflow.")

    def _authorize(self, transition: Dict[str, Any], actor) -> None:
        roles_required = transition.get("roles") or []
        if not roles_required:
            return
        actor_roles = {role.name for role in getattr(actor, "roles", [])}
        if actor_roles.isdisjoint(roles_required):
            raise PermissionError("Insufficient role to execute transition.")

    def _apply_transition(self, proposal: Proposal, transition: Dict[str, Any], context: Dict[str, Any]) -> None:
        target_state_name = transition.get("to")
        if target_state_name is None:
            raise ValueError("Transition target state missing.")
        target_state = WorkflowState.query.filter_by(
            workflow_id=proposal.proposal_type.workflow_id, name=target_state_name
        ).first()
        if target_state is None:
            raise ValueError(f"Workflow state {target_state_name} not found.")
        proposal.current_state = target_state
        self._apply_effects(proposal, transition.get("effects") or {}, context)

    def _apply_effects(self, proposal: Proposal, effects: Dict[str, Any], context: Dict[str, Any]) -> None:
        if not effects:
            return
        now = datetime.utcnow()
        if phase_name := effects.get("phase"):
            phase = proposal.phases.filter_by(phase=phase_name).first()
            if not phase:
                phase = ProposalPhase(proposal=proposal, phase=phase_name)
                self.db.add(phase)
            if status := effects.get("set_phase_status"):
                phase.status = status
            if effects.get("record_submission_time"):
                phase.submitted_at = now
            if effects.get("record_confirmation_time"):
                phase.confirmed_at = now
        if instrument_effect := effects.get("instrument"):
            assignment = proposal.instruments.filter_by(
                instrument_id=instrument_effect.get("instrument_id"), phase=instrument_effect.get("phase", "phase1")
            ).first()
            if assignment:
                if status := instrument_effect.get("set_status"):
                    assignment.status = status
                if "update_feedback" in instrument_effect:
                    assignment.scheduling_feedback = instrument_effect.get("update_feedback") or {}
                if instrument_effect.get("record_feedback_time"):
                    assignment.feedback_submitted_at = now
                if instrument_effect.get("record_confirm_time"):
                    assignment.confirmed_at = now
                if instrument_effect.get("record_applicant_confirm_time"):
                    assignment.applicant_confirmed_at = now

    def _evaluate_conditions(self, conditions: Dict[str, Any], proposal: Proposal, context: Optional[Dict[str, Any]] = None) -> bool:
        if not conditions:
            return True
        context = context or {}
        for key, expected in conditions.items():
            if key == "phase_status":
                phase = proposal.phases.filter_by(phase=expected.get("phase")).first()
                if not phase or phase.status != expected.get("status"):
                    return False
            elif key == "instrument_status":
                assignment = proposal.instruments.filter_by(
                    instrument_id=expected.get("instrument_id"),
                    phase=expected.get("phase", "phase1"),
                ).first()
                if not assignment or assignment.status != expected.get("status"):
                    return False
            elif key.startswith("context."):
                ctx_key = key.split(".", 1)[1]
                if context.get(ctx_key) != expected:
                    return False
            else:
                return False
        return True

    def _has_required_role(self, transition: Dict[str, Any], actor_roles: set) -> bool:
        roles_required = transition.get("roles") or []
        if not roles_required:
            return True
        return not actor_roles.isdisjoint(set(roles_required))
*** End Patch