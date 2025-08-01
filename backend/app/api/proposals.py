from flask import Blueprint, jsonify, request
from app import db
from app.models.models import Proposal
from app.api.auth import token_required

bp = Blueprint('proposals', __name__)

@bp.route('/', methods=['GET'])
@token_required
def get_proposals(current_user):
    """Returns proposals for the current user."""
    proposals = Proposal.query.filter_by(user_id=current_user.id).all()
    output = []
    for proposal in proposals:
        proposal_data = {
            'id': proposal.id,
            'title': proposal.title,
            'abstract': proposal.abstract,
            'status': proposal.state.name if proposal.state else 'N/A'
        }
        output.append(proposal_data)
    return jsonify(output)

@bp.route('/', methods=['POST'])
@token_required
def create_proposal(current_user):
    """Creates a new proposal."""
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'message': 'Title is required'}), 400

    # In a real implementation, you would validate against a FormTemplate
    # and assign an initial state from a Workflow.
    new_proposal = Proposal(
        title=data['title'],
        abstract=data.get('abstract', ''),
        data=data.get('data', {}),
        author=current_user
        # workflow_state_id should be set to the initial state of the relevant workflow
    )
    db.session.add(new_proposal)
    db.session.commit()

    return jsonify({'message': 'Proposal created successfully', 'id': new_proposal.id}), 201

@bp.route('/<int:id>', methods=['GET'])
@token_required
def get_proposal(current_user, id):
    """Gets a single proposal, ensuring the user has access."""
    proposal = Proposal.query.get_or_404(id)
    
    # A user can only see their own proposals (unless they are an admin)
    if proposal.user_id != current_user.id and not current_user.has_role('Admin'):
        return jsonify({'message': 'Permission denied'}), 403

    proposal_data = {
        'id': proposal.id,
        'title': proposal.title,
        'abstract': proposal.abstract,
        'data': proposal.data,
        'status': proposal.state.name if proposal.state else 'N/A'
    }
    return jsonify(proposal_data)
