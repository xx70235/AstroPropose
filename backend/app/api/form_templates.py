from flask import Blueprint, jsonify, request

from app.models.models import FormTemplate, Instrument
from app.api.auth import token_required

bp = Blueprint('form_templates', __name__)


@bp.route('/', methods=['GET'])
@token_required
def list_form_templates(current_user):
    """List templates with optional instrument/phase filters."""
    instrument_code = request.args.get('instrument_code')
    phase = request.args.get('phase')

    query = FormTemplate.query
    if instrument_code:
        instrument = Instrument.query.filter_by(code=instrument_code).first()
        if instrument is None:
            return jsonify({'message': 'Instrument not found'}), 404
        query = query.filter_by(instrument_id=instrument.id)
    if phase:
        query = query.filter_by(phase=phase)

    templates = query.order_by(FormTemplate.name, FormTemplate.version.desc()).all()
    return jsonify(
        [
            {
                'id': template.id,
                'name': template.name,
                'version': template.version,
                'phase': template.phase,
                'instrument': template.instrument.code if template.instrument else None,
            }
            for template in templates
        ]
    )


@bp.route('/<int:id>', methods=['GET'])
@token_required
def get_form_template(current_user, id):
    """Returns a single form template definition."""
    template = FormTemplate.query.get_or_404(id)
    return jsonify(
        {
            'id': template.id,
            'name': template.name,
            'phase': template.phase,
            'version': template.version,
            'instrument': template.instrument.code if template.instrument else None,
            'definition': template.definition,
        }
    )
