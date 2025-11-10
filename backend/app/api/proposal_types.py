from flask import Blueprint, jsonify
from app.models.models import ProposalType
from app.api.auth import token_required

bp = Blueprint('proposal_types', __name__)

@bp.route('/', methods=['GET'])
@token_required
def get_proposal_types(current_user):
    """Returns all available proposal types."""
    types = ProposalType.query.all()
    return jsonify([
        {
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'workflow_id': t.workflow_id,
            'season_id': t.season_id,
        }
        for t in types
    ])
