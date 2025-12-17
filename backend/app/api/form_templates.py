from flask import Blueprint, jsonify, request

from app import db
from app.models.models import FormTemplate, Instrument
from app.api.auth import token_required, admin_required

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


@bp.route('/', methods=['POST'])
@token_required
@admin_required
def create_form_template(current_user):
    """Creates a new form template."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'message': 'Missing name'}), 400
    
    name = data['name']
    phase = data.get('phase', 'phase1')
    definition = data.get('definition', {'fields': []})
    instrument_code = data.get('instrument_code')
    
    # 处理仪器关联
    instrument_id = None
    if instrument_code:
        instrument = Instrument.query.filter_by(code=instrument_code).first()
        if not instrument:
            return jsonify({'message': f'Instrument {instrument_code} not found'}), 404
        instrument_id = instrument.id
    
    # 检查是否已存在同名模板，确定版本号
    existing_templates = FormTemplate.query.filter_by(
        name=name,
        instrument_id=instrument_id,
        phase=phase
    ).order_by(FormTemplate.version.desc()).all()
    
    version = 1
    if existing_templates:
        version = existing_templates[0].version + 1
    
    # 创建新模板
    template = FormTemplate(
        name=name,
        phase=phase,
        version=version,
        instrument_id=instrument_id,
        definition=definition
    )
    db.session.add(template)
    db.session.commit()
    
    return jsonify({
        'message': 'Form template created successfully',
        'id': template.id,
        'version': template.version
    }), 201


@bp.route('/<int:id>', methods=['PUT'])
@token_required
@admin_required
def update_form_template(current_user, id):
    """Updates an existing form template."""
    template = FormTemplate.query.get_or_404(id)
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No payload provided'}), 400
    
    if 'name' in data:
        template.name = data['name']
    if 'definition' in data:
        template.definition = data['definition']
    
    db.session.commit()
    return jsonify({'message': 'Form template updated successfully'})
