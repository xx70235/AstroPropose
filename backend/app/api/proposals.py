from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.core.workflow_engine import WorkflowEngine
from app.models.models import (
    Instrument,
    InstrumentFeedback,
    Proposal,
    ProposalInstrument,
    ProposalPhase,
    ProposalType,
    WorkflowState,
)
from app.api.auth import token_required

bp = Blueprint('proposals', __name__)


@bp.route('/', methods=['GET'])
@token_required
def get_proposals(current_user):
    """Returns proposals for the current user or instrument queues."""
    instrument_code = request.args.get('instrument_code')
    scheduler_mode = instrument_code and (
        current_user.has_role('Instrument Scheduler') or current_user.has_role('Admin')
    )

    if scheduler_mode:
        instrument = Instrument.query.filter_by(code=instrument_code).first()
        if instrument is None:
            return jsonify({'message': 'Instrument not found'}), 404
        assignments = ProposalInstrument.query.filter_by(instrument_id=instrument.id).all()
        proposals = [assignment.proposal for assignment in assignments]
    elif current_user.has_role('Panel Chair') or current_user.has_role('Admin'):
        proposals = Proposal.query.all()
    else:
        proposals = Proposal.query.filter_by(user_id=current_user.id).all()

    output = []
    for proposal in proposals:
        proposal_data = {
            'id': proposal.id,
            'title': proposal.title,
            'abstract': proposal.abstract,
            'status': proposal.current_state.name if proposal.current_state else 'N/A',
            'phases': [
                {
                    'phase': phase.phase,
                    'status': phase.status,
                    'submitted_at': phase.submitted_at.isoformat() if phase.submitted_at else None,
                }
                for phase in proposal.phases.order_by(ProposalPhase.id)
            ],
            'instruments': [
                {
                    'instrument': pi.instrument.code,
                    'status': pi.status,
                    'phase': pi.phase,
                    'confirmed_at': pi.confirmed_at.isoformat() if pi.confirmed_at else None,
                }
                for pi in proposal.instruments.order_by(ProposalInstrument.id)
            ],
        }
        if scheduler_mode:
            assignment = proposal.instruments.filter_by(instrument_id=instrument.id).first()
            proposal_data['assignment'] = {
                'status': assignment.status,
                'form_data': assignment.form_data,
                'scheduling_feedback': assignment.scheduling_feedback,
            }
        output.append(proposal_data)
    return jsonify(output)


def _resolve_initial_state(proposal_type: ProposalType):
    initial = (
        WorkflowState.query.filter_by(workflow_id=proposal_type.workflow_id)
        .order_by(WorkflowState.id)
        .first()
    )
    if initial is None:
        raise ValueError('Workflow has no states configured')
    return initial


@bp.route('/', methods=['POST'])
@token_required
def create_proposal(current_user):
    """Creates a new proposal with Phase 1 payload and instrument selections."""
    data = request.get_json() or {}
    title = data.get('title')
    proposal_type_id = data.get('proposal_type_id')

    if not title:
        return jsonify({'message': 'Title is required'}), 400
    if not proposal_type_id:
        return jsonify({'message': 'proposal_type_id is required'}), 400

    proposal_type = ProposalType.query.get(proposal_type_id)
    if proposal_type is None:
        return jsonify({'message': 'Invalid proposal type'}), 400

    initial_state = _resolve_initial_state(proposal_type)

    proposal = Proposal(
        title=title,
        abstract=data.get('abstract', ''),
        data=data.get('meta', {}),
        author=current_user,
        proposal_type=proposal_type,
        current_state_id=initial_state.id,
    )
    db.session.add(proposal)

    # Phase payloads（支持多阶段结构）
    raw_phase_payload = data.get('phase_payload', {}) or {}
    if 'phase1' in raw_phase_payload or 'phase2' in raw_phase_payload:
        phase_items = raw_phase_payload.items()
    else:
        phase_items = [('phase1', raw_phase_payload)]

    for phase_name, phase_data in phase_items:
        status = phase_data.get('status', 'draft')
        submitted = datetime.utcnow() if status == 'submitted' else None
        deadline = phase_data.get('deadline')
        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline)
            except ValueError:
                deadline = None
        payload_data = phase_data.get('data', {}) or {}
        attachments = phase_data.get('attachments')
        if attachments:
            payload_data = dict(payload_data)
            payload_data['__attachments__'] = attachments
    phase = ProposalPhase(
        proposal=proposal,
            phase=phase_name,
            status=status,
        opened_at=datetime.utcnow(),
            submitted_at=submitted,
            payload=payload_data,
            notes=phase_data.get('notes'),
            deadline=deadline,
    )
    db.session.add(phase)

    # Instrument entries
    instruments_payload = data.get('instruments', [])
    if not instruments_payload:
        return jsonify({'message': 'At least one instrument payload is required'}), 400

    try:
        for instrument_entry in instruments_payload:
            code = instrument_entry.get('instrument_code')
            instrument = Instrument.query.filter_by(code=code).first()
            if instrument is None:
                raise ValueError(f'Instrument {code} not found')

            form_data = instrument_entry.get('form_data', {}) or {}
            attachments = instrument_entry.get('attachments')
            if attachments:
                form_data['__attachments__'] = attachments

            proposal_instrument = ProposalInstrument(
                proposal=proposal,
                instrument=instrument,
                phase='phase1',
                status=instrument_entry.get('status', 'submitted'),
                form_data=form_data,
            )
            db.session.add(proposal_instrument)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 400

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        return jsonify({'message': 'Failed to create proposal', 'detail': str(exc)}), 500

    return (
        jsonify(
            {
                'message': 'Proposal created successfully',
                'id': proposal.id,
                'initial_state': initial_state.name,
            }
        ),
        201,
    )


@bp.route('/<int:id>', methods=['GET'])
@token_required
def get_proposal(current_user, id):
    """Gets a single proposal, ensuring the user has access."""
    proposal = Proposal.query.get_or_404(id)

    if proposal.user_id != current_user.id and not current_user.has_role('Admin'):
        return jsonify({'message': 'Permission denied'}), 403

    proposal_data = {
        'id': proposal.id,
        'title': proposal.title,
        'abstract': proposal.abstract,
        'data': proposal.data,
        'status': proposal.current_state.name if proposal.current_state else 'N/A',
        'phases': [
            {
                'id': phase.id,
                'phase': phase.phase,
                'status': phase.status,
                'payload': phase.payload,
                'submitted_at': phase.submitted_at.isoformat() if phase.submitted_at else None,
            }
            for phase in proposal.phases.order_by(ProposalPhase.id)
        ],
        'instruments': [
            {
                'id': pi.id,
                'instrument': {'code': pi.instrument.code, 'name': pi.instrument.name},
                'status': pi.status,
                'phase': pi.phase,
                'form_data': pi.form_data,
                'scheduling_feedback': pi.scheduling_feedback,
                'confirmed_at': pi.confirmed_at.isoformat() if pi.confirmed_at else None,
            }
            for pi in proposal.instruments.order_by(ProposalInstrument.id)
        ],
    }
    return jsonify(proposal_data)


@bp.route('/<int:id>/phase', methods=['PATCH'])
@token_required
def update_phase(current_user, id):
    """Update Phase payload or confirmation status."""
    proposal = Proposal.query.get_or_404(id)
    if proposal.user_id != current_user.id:
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json() or {}
    phase_name = data.get('phase')
    if not phase_name:
        return jsonify({'message': 'phase is required'}), 400

    phase = proposal.phases.filter_by(phase=phase_name).first()
    if phase is None:
        return jsonify({'message': f'Phase {phase_name} not found'}), 404

    status = data.get('status')
    if status:
        phase.status = status
        if status == 'submitted' and phase.submitted_at is None:
            phase.submitted_at = datetime.utcnow()
    payload = data.get('payload')
    if payload is not None:
        phase.payload = payload
    phase.notes = data.get('notes', phase.notes)

    db.session.commit()
    return jsonify({'message': 'Phase updated successfully'})


@bp.route('/<int:id>/instruments/<string:instrument_code>/feedback', methods=['POST'])
@token_required
def submit_instrument_feedback(current_user, id, instrument_code):
    """Instrument schedulers submit scheduling feedback."""
    if not current_user.has_role('Instrument Scheduler') and not current_user.has_role('Admin'):
        return jsonify({'message': 'Instrument Scheduler role required'}), 403

    proposal = Proposal.query.get_or_404(id)
    instrument = Instrument.query.filter_by(code=instrument_code).first()
    if instrument is None:
        return jsonify({'message': 'Instrument not found'}), 404

    proposal_instrument = proposal.instruments.filter_by(instrument_id=instrument.id).first()
    if proposal_instrument is None:
        return jsonify({'message': 'Proposal instrument entry not found'}), 404

    data = request.get_json() or {}
    feedback = InstrumentFeedback(
        proposal_instrument=proposal_instrument,
        scheduler=current_user,
        payload=data.get('payload', {}),
        comment=data.get('comment'),
        status=data.get('status', 'submitted'),
        submitted_at=datetime.utcnow(),
    )
    proposal_instrument.scheduling_feedback = data.get('payload', {})
    proposal_instrument.status = data.get('status', proposal_instrument.status)
    db.session.add(feedback)
    db.session.commit()

    return jsonify({'message': 'Feedback submitted'})


@bp.route('/<int:id>/instruments/<string:instrument_code>/confirm', methods=['POST'])
@token_required
def confirm_instrument_allocation(current_user, id, instrument_code):
    """Proposer confirms instrument scheduling."""
    proposal = Proposal.query.get_or_404(id)
    if proposal.user_id != current_user.id:
        return jsonify({'message': 'Permission denied'}), 403

    instrument = Instrument.query.filter_by(code=instrument_code).first()
    if instrument is None:
        return jsonify({'message': 'Instrument not found'}), 404

    proposal_instrument = proposal.instruments.filter_by(instrument_id=instrument.id).first()
    if proposal_instrument is None:
        return jsonify({'message': 'Proposal instrument entry not found'}), 404

    data = request.get_json() or {}
    proposal_instrument.status = data.get('status', 'confirmed')
    proposal_instrument.confirmed_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Instrument allocation confirmed'})


@bp.route('/<int:id>/transitions', methods=['GET'])
@token_required
def list_transitions(current_user, id):
    proposal = Proposal.query.get_or_404(id)
    if proposal.user_id != current_user.id and not current_user.has_role('Admin'):
        return jsonify({'message': 'Permission denied'}), 403

    engine = WorkflowEngine(db.session)
    transitions = engine.get_allowed_actions(proposal.id, current_user)
    return jsonify({'transitions': transitions})


@bp.route('/<int:id>/transitions', methods=['POST'])
@token_required
def trigger_transition(current_user, id):
    proposal = Proposal.query.get_or_404(id)
    if proposal.user_id != current_user.id and not current_user.has_role('Admin'):
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json() or {}
    transition_name = data.get('transition')
    if not transition_name:
        return jsonify({'message': 'transition is required'}), 400

    engine = WorkflowEngine(db.session)
    try:
        result = engine.execute_transition(
            proposal_id=proposal.id,
            action_name=transition_name,
            actor=current_user,
            context=data.get('context', {}),
        )
    except PermissionError as exc:
        return jsonify({
            'message': str(exc),
            'error_type': 'permission_denied'
        }), 403
    except ValueError as exc:
        # 检查是否是验证错误
        error_msg = str(exc)
        if 'Validation failed' in error_msg or 'validation' in error_msg.lower():
            return jsonify({
                'message': error_msg,
                'error_type': 'validation_failed',
                'details': error_msg.split('\n')[1:] if '\n' in error_msg else []
            }), 400
        return jsonify({
            'message': error_msg,
            'error_type': 'workflow_error'
        }), 400
    except Exception as exc:
        return jsonify({
            'message': f'Unexpected error: {str(exc)}',
            'error_type': 'internal_error'
        }), 500

    return jsonify(result)
