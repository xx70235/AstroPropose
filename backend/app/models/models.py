from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


# --------------------------------------------------------------------------- #
# 用户与权限
# --------------------------------------------------------------------------- #

roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id"), primary_key=True),
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    roles = db.relationship("Role", secondary=roles_users, lazy="subquery", backref=db.backref("users", lazy=True))
    proposals = db.relationship("Proposal", backref="author", lazy="dynamic")
    instrument_feedbacks = db.relationship("InstrumentFeedback", backref="scheduler", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)


# --------------------------------------------------------------------------- #
# 工作流与提案
# --------------------------------------------------------------------------- #

class ProposalSeason(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    phase_one_deadline = db.Column(db.DateTime)
    phase_two_deadline = db.Column(db.DateTime)
    proposal_types = db.relationship("ProposalType", backref="season", lazy="dynamic")


class Workflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.Text)
    definition = db.Column(db.JSON)
    proposal_types = db.relationship("ProposalType", backref="workflow", lazy="dynamic")
    states = db.relationship("WorkflowState", backref="workflow", lazy="dynamic", cascade="all, delete-orphan")
    actions = db.relationship("WorkflowAction", backref="workflow", lazy="dynamic", cascade="all, delete-orphan")


class WorkflowState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    workflow_id = db.Column(db.Integer, db.ForeignKey("workflow.id"))
    proposals = db.relationship("Proposal", backref="current_state", lazy="dynamic")
    transitions_from = db.relationship(
        "WorkflowTransition",
        backref="from_state",
        lazy="dynamic",
        foreign_keys="WorkflowTransition.from_state_id",
        cascade="all, delete-orphan",
    )
    transitions_to = db.relationship(
        "WorkflowTransition",
        backref="to_state",
        lazy="dynamic",
        foreign_keys="WorkflowTransition.to_state_id",
        cascade="all, delete-orphan",
    )


class WorkflowAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey("workflow.id"), nullable=False)
    name = db.Column(db.String(140), nullable=False)
    action_type = db.Column(db.String(64), nullable=False)
    config = db.Column(db.JSON, default=dict)
    transitions = db.relationship("WorkflowTransition", backref="action", lazy="dynamic")


class WorkflowTransition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey("workflow.id"), nullable=False)
    name = db.Column(db.String(140), nullable=False)
    from_state_id = db.Column(db.Integer, db.ForeignKey("workflow_state.id"), nullable=False)
    to_state_id = db.Column(db.Integer, db.ForeignKey("workflow_state.id"), nullable=False)
    allowed_roles = db.Column(db.JSON, default=list)
    condition = db.Column(db.JSON, default=dict)
    action_id = db.Column(db.Integer, db.ForeignKey("workflow_action.id"))


class ProposalType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    workflow_id = db.Column(db.Integer, db.ForeignKey("workflow.id"), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey("proposal_season.id"))
    proposals = db.relationship("Proposal", backref="proposal_type", lazy="dynamic")


class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    abstract = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    proposal_type_id = db.Column(db.Integer, db.ForeignKey("proposal_type.id"), nullable=False)
    current_state_id = db.Column(db.Integer, db.ForeignKey("workflow_state.id"))
    data = db.Column(db.JSON, default=dict)

    phases = db.relationship("ProposalPhase", backref="proposal", lazy="dynamic", cascade="all, delete-orphan")
    instruments = db.relationship(
        "ProposalInstrument", backref="proposal", lazy="dynamic", cascade="all, delete-orphan"
    )
    state_history = db.relationship(
        "ProposalStateHistory", backref="proposal", lazy="dynamic", cascade="all, delete-orphan"
    )


class ProposalStateHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposal.id"), nullable=False)
    from_state = db.Column(db.String(64))
    to_state = db.Column(db.String(64))
    transition_name = db.Column(db.String(140))
    acted_by = db.Column(db.String(64))
    acted_at = db.Column(db.DateTime, default=datetime.utcnow)
    meta = db.Column(db.JSON, default=dict)


class ProposalPhase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposal.id"), nullable=False)
    phase = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(64), default="pending")
    opened_at = db.Column(db.DateTime)
    submitted_at = db.Column(db.DateTime)
    confirmed_at = db.Column(db.DateTime)
    locked_at = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    payload = db.Column(db.JSON, default=dict)
    notes = db.Column(db.Text)
    __table_args__ = (
        db.Index("ix_proposal_phase_unique", "proposal_id", "phase", unique=True),
    )


# --------------------------------------------------------------------------- #
# 表单与仪器
# --------------------------------------------------------------------------- #

class FormTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True, nullable=False)
    definition = db.Column(db.JSON)
    phase = db.Column(db.String(32))
    version = db.Column(db.Integer, default=1)
    instrument_id = db.Column(db.Integer, db.ForeignKey("instrument.id"))
    instrument = db.relationship("Instrument", backref=db.backref("form_templates", lazy="dynamic"))


class Instrument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    proposal_instruments = db.relationship(
        "ProposalInstrument", backref="instrument", lazy="dynamic", cascade="all, delete-orphan"
    )


class ProposalInstrument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposal.id"), nullable=False)
    instrument_id = db.Column(db.Integer, db.ForeignKey("instrument.id"), nullable=False)
    phase = db.Column(db.String(32), nullable=False, default="phase1")
    status = db.Column(db.String(64), default="pending")
    form_data = db.Column(db.JSON, default=dict)
    scheduling_feedback = db.Column(db.JSON, default=dict)
    confirmed_at = db.Column(db.DateTime)
    feedback_submitted_at = db.Column(db.DateTime)
    applicant_confirmed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    feedbacks = db.relationship(
        "InstrumentFeedback", backref="proposal_instrument", lazy="dynamic", cascade="all, delete-orphan"
    )
    __table_args__ = (
        db.UniqueConstraint("proposal_id", "instrument_id", "phase", name="uq_proposal_instrument"),
        db.Index("ix_proposal_instrument_queue", "instrument_id", "phase", "status"),
    )


class InstrumentFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_instrument_id = db.Column(db.Integer, db.ForeignKey("proposal_instrument.id"), nullable=False)
    scheduler_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    payload = db.Column(db.JSON, default=dict)
    status = db.Column(db.String(64), default="draft")
    comment = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
