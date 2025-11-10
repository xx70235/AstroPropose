from datetime import datetime

import pytest

from app import db
from app.core.workflow_engine import WorkflowEngine
from app.models.models import Proposal, ProposalPhase, ProposalType, Role, User, WorkflowState


@pytest.fixture
def proposer(app):
    proposer_role = Role.query.filter_by(name="Proposer").first()
    user = User(username="workflow-user", email="workflow@example.com")
    user.set_password("password123")
    user.roles.append(proposer_role)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def proposal(app, proposer):
    proposal_type = ProposalType.query.first()
    draft_state = WorkflowState.query.filter_by(name="Draft").first()
    proposal = Proposal(
        title="Workflow Test",
        abstract="",
        author=proposer,
        proposal_type=proposal_type,
        current_state=draft_state,
        data={},
    )
    phase = ProposalPhase(
        proposal=proposal,
        phase="phase1",
        status="draft",
        opened_at=datetime.utcnow(),
    )
    db.session.add_all([proposal, phase])
    db.session.commit()
    return proposal


def test_get_allowed_actions_returns_submit_transition(proposal, proposer):
    engine = WorkflowEngine(db.session)
    actions = engine.get_allowed_actions(proposal.id, proposer)
    action_names = {action["name"] for action in actions}
    assert "submit_phase1" in action_names


def test_execute_transition_updates_state_and_phase(proposal, proposer):
    engine = WorkflowEngine(db.session)
    result = engine.execute_transition(proposal.id, "submit_phase1", proposer)
    assert result["new_state"] == "Submitted"

    db.session.refresh(proposal)
    assert proposal.current_state.name == "Submitted"
    phase = proposal.phases.filter_by(phase="phase1").first()
    assert phase.status == "submitted"
    assert phase.submitted_at is not None

