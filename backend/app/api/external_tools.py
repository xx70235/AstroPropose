"""
External Tool API endpoints
支持 OpenAPI 规范导入和手动配置
"""
import json
from flask import Blueprint, jsonify, request
import requests

from app import db
from app.models.models import ExternalTool, ExternalToolOperation
from app.api.auth import token_required

bp = Blueprint('external_tools', __name__)


@bp.route('/', methods=['GET'])
@token_required
def list_tools(current_user):
    """List all registered external tools"""
    tools = ExternalTool.query.filter_by(is_active=True).all()
    return jsonify([
        {
            'id': tool.id,
            'name': tool.name,
            'description': tool.description,
            'base_url': tool.base_url,
            'auth_type': tool.auth_type,
            'operations_count': tool.operations.count(),
            'created_at': tool.created_at.isoformat() if tool.created_at else None,
        }
        for tool in tools
    ])


@bp.route('/', methods=['POST'])
@token_required
def create_tool(current_user):
    """
    Register a new external tool
    
    Supports two modes:
    1. Import from OpenAPI spec URL
    2. Manual configuration
    """
    if not current_user.has_role('Admin'):
        return jsonify({'message': 'Admin role required'}), 403

    data = request.get_json() or {}
    name = data.get('name')
    base_url = data.get('base_url')
    openapi_spec_url = data.get('openapi_spec_url')

    if not name or not base_url:
        return jsonify({'message': 'Name and base_url are required'}), 400

    # Check for duplicate
    if ExternalTool.query.filter_by(name=name).first():
        return jsonify({'message': 'Tool with this name already exists'}), 400

    tool = ExternalTool(
        name=name,
        description=data.get('description', ''),
        base_url=base_url.rstrip('/'),
        openapi_spec_url=openapi_spec_url,
        auth_type=data.get('auth_type', 'none'),
        auth_config=data.get('auth_config', {}),
    )

    # If OpenAPI spec URL is provided, try to import
    if openapi_spec_url:
        try:
            spec = _fetch_openapi_spec(openapi_spec_url)
            tool.openapi_spec = spec
            db.session.add(tool)
            db.session.flush()  # Get tool.id
            _import_operations_from_spec(tool, spec)
        except Exception as e:
            return jsonify({'message': f'Failed to import OpenAPI spec: {str(e)}'}), 400
    else:
        db.session.add(tool)

    db.session.commit()
    return jsonify({
        'message': 'Tool registered successfully',
        'id': tool.id,
        'operations_imported': tool.operations.count(),
    }), 201


@bp.route('/<int:tool_id>', methods=['GET'])
@token_required
def get_tool(current_user, tool_id):
    """Get detailed info about a tool including its operations"""
    tool = ExternalTool.query.get_or_404(tool_id)
    return jsonify({
        'id': tool.id,
        'name': tool.name,
        'description': tool.description,
        'base_url': tool.base_url,
        'openapi_spec_url': tool.openapi_spec_url,
        'auth_type': tool.auth_type,
        'is_active': tool.is_active,
        'operations': [
            {
                'id': op.id,
                'operation_id': op.operation_id,
                'name': op.name,
                'description': op.description,
                'method': op.method,
                'path': op.path,
                'parameters': op.parameters,
                'request_body': op.request_body,
                'input_mapping': op.input_mapping,
                'output_mapping': op.output_mapping,
                'timeout': op.timeout,
                'retry_config': op.retry_config,
                'tool_type': op.tool_type,
                'validation_config': op.validation_config,
            }
            for op in tool.operations
        ],
    })


@bp.route('/<int:tool_id>', methods=['PATCH'])
@token_required
def update_tool(current_user, tool_id):
    """Update tool configuration"""
    if not current_user.has_role('Admin'):
        return jsonify({'message': 'Admin role required'}), 403

    tool = ExternalTool.query.get_or_404(tool_id)
    data = request.get_json() or {}

    if 'name' in data:
        tool.name = data['name']
    if 'description' in data:
        tool.description = data['description']
    if 'base_url' in data:
        tool.base_url = data['base_url'].rstrip('/')
    if 'auth_type' in data:
        tool.auth_type = data['auth_type']
    if 'auth_config' in data:
        tool.auth_config = data['auth_config']
    if 'is_active' in data:
        tool.is_active = data['is_active']

    db.session.commit()
    return jsonify({'message': 'Tool updated successfully'})


@bp.route('/<int:tool_id>/refresh-spec', methods=['POST'])
@token_required
def refresh_openapi_spec(current_user, tool_id):
    """Re-fetch and update operations from OpenAPI spec"""
    if not current_user.has_role('Admin'):
        return jsonify({'message': 'Admin role required'}), 403

    tool = ExternalTool.query.get_or_404(tool_id)
    if not tool.openapi_spec_url:
        return jsonify({'message': 'No OpenAPI spec URL configured'}), 400

    try:
        spec = _fetch_openapi_spec(tool.openapi_spec_url)
        tool.openapi_spec = spec
        # Clear existing operations and re-import
        ExternalToolOperation.query.filter_by(tool_id=tool.id).delete()
        _import_operations_from_spec(tool, spec)
        db.session.commit()
        return jsonify({
            'message': 'Spec refreshed successfully',
            'operations_imported': tool.operations.count(),
        })
    except Exception as e:
        return jsonify({'message': f'Failed to refresh spec: {str(e)}'}), 400


@bp.route('/<int:tool_id>/operations', methods=['POST'])
@token_required
def create_operation(current_user, tool_id):
    """Manually add an operation to a tool"""
    if not current_user.has_role('Admin'):
        return jsonify({'message': 'Admin role required'}), 403

    tool = ExternalTool.query.get_or_404(tool_id)
    data = request.get_json() or {}

    required_fields = ['operation_id', 'name', 'method', 'path']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'{field} is required'}), 400

    # Check for duplicate operation_id
    if tool.operations.filter_by(operation_id=data['operation_id']).first():
        return jsonify({'message': 'Operation with this ID already exists'}), 400

    operation = ExternalToolOperation(
        tool_id=tool.id,
        operation_id=data['operation_id'],
        name=data['name'],
        description=data.get('description', ''),
        method=data['method'].upper(),
        path=data['path'],
        parameters=data.get('parameters', {}),
        request_body=data.get('request_body', {}),
        response_schema=data.get('response_schema', {}),
        input_mapping=data.get('input_mapping', {}),
        output_mapping=data.get('output_mapping', {}),
        timeout=data.get('timeout', 30),
        retry_config=data.get('retry_config', {}),
        tool_type=data.get('tool_type', 'other'),
        validation_config=data.get('validation_config', {}),
    )
    db.session.add(operation)
    db.session.commit()

    return jsonify({'message': 'Operation created', 'id': operation.id}), 201


@bp.route('/operations/<int:operation_id>', methods=['PATCH'])
@token_required
def update_operation(current_user, operation_id):
    """Update operation configuration (especially mappings)"""
    if not current_user.has_role('Admin'):
        return jsonify({'message': 'Admin role required'}), 403

    operation = ExternalToolOperation.query.get_or_404(operation_id)
    data = request.get_json() or {}

    updatable_fields = [
        'name', 'description', 'method', 'path', 'parameters',
        'request_body', 'response_schema', 'input_mapping',
        'output_mapping', 'timeout', 'retry_config',
        'tool_type', 'validation_config'
    ]
    for field in updatable_fields:
        if field in data:
            setattr(operation, field, data[field])

    db.session.commit()
    return jsonify({'message': 'Operation updated'})


@bp.route('/operations/<int:operation_id>/test', methods=['POST'])
@token_required
def test_operation(current_user, operation_id):
    """Test an operation with sample data"""
    if not current_user.has_role('Admin'):
        return jsonify({'message': 'Admin role required'}), 403

    operation = ExternalToolOperation.query.get_or_404(operation_id)
    data = request.get_json() or {}
    test_params = data.get('params', {})

    try:
        result = _execute_operation(operation, test_params)
        return jsonify({
            'success': True,
            'status_code': result.get('status_code'),
            'response': result.get('response'),
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@bp.route('/operations/<int:operation_id>/execute', methods=['POST'])
@token_required
def execute_operation_from_form(current_user, operation_id):
    """
    Execute an external tool operation from frontend form.
    This is used for interactive tools like visibility checkers.
    
    Request body:
    {
        "context": {
            "field_data": {...},  // Current form field values
            "proposal_id": 123,   // Optional: if editing existing proposal
            ...
        }
    }
    """
    from app.core.external_tool_executor import ExternalToolExecutor
    
    operation = ExternalToolOperation.query.get_or_404(operation_id)
    if not operation.tool.is_active:
        return jsonify({'message': 'Tool is not active'}), 400
    
    data = request.get_json() or {}
    context = data.get('context', {})
    
    # Get proposal if proposal_id is provided
    proposal = None
    if context.get('proposal_id'):
        from app.models.models import Proposal
        proposal = Proposal.query.get(context['proposal_id'])
        if proposal and proposal.user_id != current_user.id and not current_user.has_role('Admin'):
            return jsonify({'message': 'Permission denied'}), 403
    
    executor = ExternalToolExecutor(db.session)
    
    try:
        result = executor.execute(
            operation_id=operation_id,
            proposal=proposal,
            context=context,
            actor=current_user,
            triggered_by='form_interaction'
        )
        
        return jsonify({
            'success': result.get('status') == 'success',
            'status': result.get('status'),
            'response': result.get('response'),
            'mapped_output': result.get('mapped_output', {}),
            'error': result.get('error'),
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def _fetch_openapi_spec(url):
    """Fetch and parse OpenAPI spec from URL"""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    content_type = response.headers.get('Content-Type', '')
    if 'yaml' in content_type or url.endswith(('.yaml', '.yml')):
        import yaml
        return yaml.safe_load(response.text)
    return response.json()


def _import_operations_from_spec(tool, spec):
    """Import operations from OpenAPI spec"""
    paths = spec.get('paths', {})
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() not in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
                continue
            
            operation_id = details.get('operationId', f'{method}_{path.replace("/", "_")}')
            name = details.get('summary', operation_id)
            
            # Parse parameters
            parameters = {}
            for param in details.get('parameters', []):
                param_in = param.get('in', 'query')
                if param_in not in parameters:
                    parameters[param_in] = []
                parameters[param_in].append({
                    'name': param.get('name'),
                    'required': param.get('required', False),
                    'schema': param.get('schema', {}),
                    'description': param.get('description', ''),
                })
            
            # Parse request body
            request_body = {}
            if 'requestBody' in details:
                content = details['requestBody'].get('content', {})
                if 'application/json' in content:
                    request_body = content['application/json'].get('schema', {})
            
            # Parse response schema
            response_schema = {}
            responses = details.get('responses', {})
            if '200' in responses:
                content = responses['200'].get('content', {})
                if 'application/json' in content:
                    response_schema = content['application/json'].get('schema', {})
            
            operation = ExternalToolOperation(
                tool_id=tool.id,
                operation_id=operation_id,
                name=name,
                description=details.get('description', ''),
                method=method.upper(),
                path=path,
                parameters=parameters,
                request_body=request_body,
                response_schema=response_schema,
            )
            db.session.add(operation)


def _execute_operation(operation, params):
    """Execute an external tool operation"""
    tool = operation.tool
    
    # Build URL
    url = tool.base_url + operation.path
    
    # Apply path parameters
    path_params = params.get('path', {})
    for key, value in path_params.items():
        url = url.replace(f'{{{key}}}', str(value))
    
    # Build headers
    headers = {'Content-Type': 'application/json'}
    
    # Apply authentication
    if tool.auth_type == 'bearer':
        token = tool.auth_config.get('token', '')
        headers['Authorization'] = f'Bearer {token}'
    elif tool.auth_type == 'api_key':
        key_name = tool.auth_config.get('key_name', 'X-API-Key')
        key_value = tool.auth_config.get('key_value', '')
        headers[key_name] = key_value
    
    # Build request
    query_params = params.get('query', {})
    body = params.get('body', {})
    
    # Execute request
    response = requests.request(
        method=operation.method,
        url=url,
        headers=headers,
        params=query_params,
        json=body if body else None,
        timeout=operation.timeout,
    )
    
    return {
        'status_code': response.status_code,
        'headers': dict(response.headers),
        'response': response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
    }



