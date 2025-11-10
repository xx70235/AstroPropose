from flask import Blueprint, jsonify, request

from app import db
from app.api.auth import token_required
from app.models.models import Instrument

bp = Blueprint('instruments', __name__)


@bp.route('/', methods=['GET'])
@token_required
def list_instruments(current_user):
    """List instruments; non-admins只返回启用的仪器。"""
    query = Instrument.query
    if not current_user.has_role('Admin'):
        query = query.filter_by(is_active=True)
    instruments = query.order_by(Instrument.code).all()
    return jsonify(
        [
            {
                'code': instrument.code,
                'name': instrument.name,
                'description': instrument.description,
                'is_active': instrument.is_active,
            }
            for instrument in instruments
        ]
    )


@bp.route('/', methods=['POST'])
@token_required
def create_instrument(current_user):
    if not current_user.has_role('Admin'):
        return jsonify({'message': 'Admin role required'}), 403

    data = request.get_json() or {}
    code = data.get('code')
    name = data.get('name')
    if not code or not name:
        return jsonify({'message': 'code and name are required'}), 400

    instrument = Instrument(
        code=code,
        name=name,
        description=data.get('description', ''),
        is_active=data.get('is_active', True),
    )
    db.session.add(instrument)
    db.session.commit()
    return jsonify({'message': 'Instrument created', 'code': instrument.code}), 201


@bp.route('/<string:code>', methods=['PATCH'])
@token_required
def update_instrument(current_user, code):
    if not current_user.has_role('Admin'):
        return jsonify({'message': 'Admin role required'}), 403

    instrument = Instrument.query.filter_by(code=code).first_or_404()
    data = request.get_json() or {}
    if 'name' in data:
        instrument.name = data['name']
    if 'description' in data:
        instrument.description = data['description']
    if 'is_active' in data:
        instrument.is_active = data['is_active']
    db.session.commit()
    return jsonify({'message': 'Instrument updated'})

