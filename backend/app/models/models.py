from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    roles = db.relationship('Role', secondary=roles_users, lazy='subquery', backref=db.backref('users', lazy=True))
    proposals = db.relationship('Proposal', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    abstract = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    proposal_type_id = db.Column(db.Integer, db.ForeignKey('proposal_type.id'), nullable=False)
    current_state_id = db.Column(db.Integer, db.ForeignKey('workflow_state.id'))
    data = db.Column(db.JSON)

class ProposalType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'), nullable=False)
    proposals = db.relationship('Proposal', backref='proposal_type', lazy='dynamic')

class ProposalSeason(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

class Workflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.Text)
    definition = db.Column(db.JSON)
    proposal_types = db.relationship('ProposalType', backref='workflow', lazy='dynamic')
    states = db.relationship('WorkflowState', backref='workflow', lazy='dynamic')

class WorkflowState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'))
    proposals = db.relationship('Proposal', backref='current_state', lazy='dynamic')

class FormTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True, nullable=False)
    definition = db.Column(db.JSON)
