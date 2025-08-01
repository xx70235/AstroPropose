from flask import Blueprint, jsonify, request
from app import db
from app.models.models import Workflow
from app.api.auth import token_required, admin_required

bp = Blueprint('workflows', __name__)

@bp.route('/', methods=['GET'])
@token_required
def get_workflows(current_user):
    """Returns all available workflows."""
    workflows = Workflow.query.all()
    return jsonify([{'id': w.id, 'name': w.name, 'description': w.description} for w in workflows])

@bp.route('/<int:id>', methods=['GET'])
@token_required
def get_workflow(current_user, id):
    """Returns a single workflow definition."""
    workflow = Workflow.query.get_or_404(id)
    return jsonify({
        'id': workflow.id,
        'name': workflow.name,
        'description': workflow.description,
        'definition': workflow.definition
    })

@bp.route('/', methods=['POST'])
@token_required
@admin_required
def create_workflow(current_user):
    """Creates a new workflow."""
    data = request.get_json()
    if not data or not data.get('name') or not data.get('definition'):
        return jsonify({'message': 'Missing name or definition'}), 400

    new_workflow = Workflow(
        name=data['name'],
        description=data.get('description', ''),
        definition=data['definition']
    )
    db.session.add(new_workflow)
    db.session.commit()
    return jsonify({'message': 'Workflow created successfully', 'id': new_workflow.id}), 201

@bp.route('/<int:id>', methods=['PUT'])
@token_required
@admin_required
def update_workflow(current_user, id):
    """Updates an existing workflow."""
    workflow = Workflow.query.get_or_404(id)
    data = request.get_json()
    if not data or not data.get('definition'):
        return jsonify({'message': 'Missing definition'}), 400
    
    workflow.name = data.get('name', workflow.name)
    workflow.description = data.get('description', workflow.description)
    workflow.definition = data['definition']
    db.session.commit()
    return jsonify({'message': 'Workflow updated successfully'})
