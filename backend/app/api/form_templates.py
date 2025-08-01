from flask import Blueprint, jsonify
from app.models.models import FormTemplate
from app.api.auth import token_required

bp = Blueprint('form_templates', __name__)

@bp.route('/<int:id>', methods=['GET'])
@token_required
def get_form_template(current_user, id):
    """Returns a single form template definition."""
    template = FormTemplate.query.get_or_404(id)
    return jsonify({
        'id': template.id,
        'name': template.name,
        'definition': template.definition
    })
