"""
External Tool Executor
负责在工作流中执行外部工具调用
支持参数映射、重试机制、执行日志
"""
import time
from datetime import datetime
from typing import Any, Dict, Optional
import requests

from app import db
from app.models.models import (
    ExternalTool,
    ExternalToolOperation,
    ExternalToolExecution,
    Proposal,
)


class ExternalToolExecutor:
    """
    外部工具执行器
    
    在工作流转换中被调用，负责：
    1. 从 proposal/context 映射参数到 API 请求
    2. 执行 HTTP 请求
    3. 处理响应并映射回 proposal/context
    4. 记录执行日志
    5. 处理重试逻辑
    """
    
    def __init__(self, db_session=None):
        self.db = db_session or db.session
    
    def execute(
        self,
        operation_id: int,
        proposal: Optional[Proposal] = None,
        context: Optional[Dict[str, Any]] = None,
        actor=None,
        triggered_by: str = "manual"
    ) -> Dict[str, Any]:
        """
        执行外部工具操作
        
        Args:
            operation_id: ExternalToolOperation 的 ID
            proposal: 相关的 Proposal（用于参数映射）
            context: 额外的上下文数据
            actor: 执行者（User）
            triggered_by: 触发源（如 transition name）
        
        Returns:
            执行结果，包含 status, response, mapped_output
        """
        operation = ExternalToolOperation.query.get_or_404(operation_id)
        tool = operation.tool
        context = context or {}
        
        # 创建执行日志
        execution = ExternalToolExecution(
            operation_id=operation.id,
            proposal_id=proposal.id if proposal else None,
            triggered_by=triggered_by,
            actor_id=actor.id if actor else None,
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(execution)
        self.db.flush()
        
        try:
            # 构建请求参数
            request_params = self._build_request_params(
                operation, proposal, context
            )
            
            # 记录请求详情
            execution.request_url = request_params['url']
            execution.request_method = operation.method
            execution.request_headers = self._sanitize_headers(request_params['headers'])
            execution.request_body = request_params.get('body', {})
            
            # 执行请求（带重试）
            retry_config = operation.retry_config or {}
            max_retries = retry_config.get('max_retries', 3)
            retry_delay = retry_config.get('retry_delay', 5)
            retryable_codes = retry_config.get('retryable_codes', [500, 502, 503, 504])
            
            response = self._execute_with_retry(
                request_params,
                operation.timeout,
                max_retries,
                retry_delay,
                retryable_codes,
                execution,
            )
            
            # 记录响应
            execution.response_status = response.status_code
            execution.response_headers = dict(response.headers)
            
            try:
                response_body = response.json()
            except:
                response_body = {'raw': response.text}
            execution.response_body = response_body
            
            # 检查 HTTP 状态码
            if response.status_code >= 400:
                execution.status = "failed"
                execution.error_message = f"HTTP {response.status_code}: {response.text[:500]}"
                execution.completed_at = datetime.utcnow()
                self.db.commit()
                
                # 对于验证类工具，区分服务错误和验证失败
                if operation.tool_type == 'validation':
                    validation_config = operation.validation_config or {}
                    block_on_service_error = validation_config.get('block_on_service_error', False)
                    
                    return {
                        'status': 'service_error',
                        'error': execution.error_message,
                        'execution_id': execution.id,
                        'block_transition': block_on_service_error,
                        'error_type': 'service_unavailable',
                    }
                
                return {
                    'status': 'failed',
                    'error': execution.error_message,
                    'execution_id': execution.id,
                }
            
            # 对于验证类工具，检查验证结果
            if operation.tool_type == 'validation':
                validation_result = self._check_validation_result(
                    operation, response_body, response.status_code
                )
                
                if not validation_result['valid']:
                    # 验证失败
                    validation_config = operation.validation_config or {}
                    block_on_failure = validation_config.get('block_on_failure', True)
                    
                    execution.status = "validation_failed"
                    execution.error_message = validation_result['error_message']
                    execution.completed_at = datetime.utcnow()
                    self.db.commit()
                    
                    return {
                        'status': 'validation_failed',
                        'error': validation_result['error_message'],
                        'execution_id': execution.id,
                        'block_transition': block_on_failure,
                        'error_type': 'validation_failed',
                        'response': response_body,  # 保留响应以便前端显示
                    }
            
            # 映射输出到 context
            mapped_output = self._map_output(
                operation.output_mapping, response_body, proposal, context
            )
            
            execution.status = "success"
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                'status': 'success',
                'response': response_body,
                'mapped_output': mapped_output,
                'execution_id': execution.id,
            }
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            raise
    
    def _build_request_params(
        self,
        operation: ExternalToolOperation,
        proposal: Optional[Proposal],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """根据 input_mapping 构建请求参数"""
        tool = operation.tool
        input_mapping = operation.input_mapping or {}
        
        # 构建数据源
        data_source = {
            'context': context,
        }
        if proposal:
            data_source['proposal'] = {
                'id': proposal.id,
                'title': proposal.title,
                'abstract': proposal.abstract,
                'status': proposal.current_state.name if proposal.current_state else None,
                'data': proposal.data or {},
                'author': {
                    'id': proposal.author.id,
                    'username': proposal.author.username,
                    'email': proposal.author.email,
                } if proposal.author else None,
                'phases': [
                    {
                        'phase': p.phase,
                        'status': p.status,
                        'payload': p.payload,
                    }
                    for p in proposal.phases
                ],
                'instruments': [
                    {
                        'code': pi.instrument.code,
                        'status': pi.status,
                        'form_data': pi.form_data,
                        'scheduling_feedback': pi.scheduling_feedback,
                    }
                    for pi in proposal.instruments
                ],
            }
        
        # 构建 URL
        url = tool.base_url + operation.path
        
        # 应用路径参数映射
        path_params = {}
        for param_name, mapping in input_mapping.get('path', {}).items():
            path_params[param_name] = self._resolve_mapping(mapping, data_source)
            url = url.replace(f'{{{param_name}}}', str(path_params[param_name]))
        
        # 应用查询参数映射
        query_params = {}
        for param_name, mapping in input_mapping.get('query', {}).items():
            value = self._resolve_mapping(mapping, data_source)
            if value is not None:
                query_params[param_name] = value
        
        # 应用请求体映射
        body = {}
        for field_name, mapping in input_mapping.get('body', {}).items():
            body[field_name] = self._resolve_mapping(mapping, data_source)
        
        # 构建请求头
        headers = {'Content-Type': 'application/json'}
        
        # 应用认证
        if tool.auth_type == 'bearer':
            token = tool.auth_config.get('token', '')
            headers['Authorization'] = f'Bearer {token}'
        elif tool.auth_type == 'api_key':
            key_name = tool.auth_config.get('key_name', 'X-API-Key')
            key_value = tool.auth_config.get('key_value', '')
            headers[key_name] = key_value
        elif tool.auth_type == 'basic':
            import base64
            username = tool.auth_config.get('username', '')
            password = tool.auth_config.get('password', '')
            credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'
        
        # 自定义请求头
        for header_name, mapping in input_mapping.get('headers', {}).items():
            headers[header_name] = self._resolve_mapping(mapping, data_source)
        
        return {
            'url': url,
            'method': operation.method,
            'headers': headers,
            'params': query_params,
            'body': body,
        }
    
    def _resolve_mapping(self, mapping, data_source: Dict[str, Any]) -> Any:
        """
        解析映射配置，从数据源获取值
        
        映射格式示例：
        - "proposal.id" -> data_source['proposal']['id']
        - "proposal.data.field_name" -> data_source['proposal']['data']['field_name']
        - "context.some_key" -> data_source['context']['some_key']
        - {"literal": "fixed_value"} -> "fixed_value"
        - {"template": "Proposal #{proposal.id}"} -> "Proposal #123"
        """
        if isinstance(mapping, dict):
            if 'literal' in mapping:
                return mapping['literal']
            if 'template' in mapping:
                template = mapping['template']
                # 简单模板替换
                import re
                def replace_var(match):
                    var_path = match.group(1)
                    return str(self._get_nested_value(data_source, var_path.split('.')))
                return re.sub(r'\{([^}]+)\}', replace_var, template)
        
        if isinstance(mapping, str):
            return self._get_nested_value(data_source, mapping.split('.'))
        
        return mapping
    
    def _get_nested_value(self, data: Dict, keys: list) -> Any:
        """从嵌套字典中获取值"""
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif hasattr(current, key):
                current = getattr(current, key)
            else:
                return None
            if current is None:
                return None
        return current
    
    def _execute_with_retry(
        self,
        request_params: Dict[str, Any],
        timeout: int,
        max_retries: int,
        retry_delay: int,
        retryable_codes: list,
        execution: ExternalToolExecution,
    ):
        """带重试机制的请求执行"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.request(
                    method=request_params['method'],
                    url=request_params['url'],
                    headers=request_params['headers'],
                    params=request_params.get('params'),
                    json=request_params.get('body') if request_params.get('body') else None,
                    timeout=timeout,
                )
                
                # 如果状态码不在可重试列表中，直接返回
                if response.status_code not in retryable_codes:
                    return response
                
                # 如果是最后一次尝试，返回结果
                if attempt == max_retries:
                    return response
                
                # 记录重试
                execution.retry_count = attempt + 1
                execution.status = "retrying"
                self.db.commit()
                
                # 等待后重试
                time.sleep(retry_delay * (2 ** attempt))  # 指数退避
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt == max_retries:
                    raise
                
                execution.retry_count = attempt + 1
                execution.status = "retrying"
                self.db.commit()
                time.sleep(retry_delay * (2 ** attempt))
        
        if last_exception:
            raise last_exception
    
    def _map_output(
        self,
        output_mapping: Dict[str, Any],
        response_body: Any,
        proposal: Optional[Proposal],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """将响应映射回 proposal/context"""
        if not output_mapping:
            return {}
        
        result = {}
        
        # 映射到 context
        for target_key, source_path in output_mapping.get('to_context', {}).items():
            if isinstance(source_path, str):
                value = self._get_nested_value({'response': response_body}, source_path.split('.'))
                result[target_key] = value
                context[target_key] = value
        
        # 映射到 proposal.data
        if proposal and 'to_proposal_data' in output_mapping:
            proposal_data = proposal.data or {}
            for target_key, source_path in output_mapping['to_proposal_data'].items():
                if isinstance(source_path, str):
                    value = self._get_nested_value({'response': response_body}, source_path.split('.'))
                    proposal_data[target_key] = value
            proposal.data = proposal_data
        
        return result
    
    def _check_validation_result(
        self,
        operation: ExternalToolOperation,
        response_body: Any,
        status_code: int
    ) -> Dict[str, Any]:
        """
        检查验证类工具的结果
        
        Returns:
            {
                'valid': bool,
                'error_message': str (if not valid)
            }
        """
        validation_config = operation.validation_config or {}
        failure_conditions = validation_config.get('failure_conditions', [])
        error_template = validation_config.get('error_message_template', 'Validation failed')
        
        # 如果没有配置失败条件，默认检查 HTTP 状态码
        if not failure_conditions:
            if status_code >= 200 and status_code < 300:
                return {'valid': True}
            else:
                return {
                    'valid': False,
                    'error_message': f'Validation service returned status {status_code}'
                }
        
        # 检查每个失败条件
        for condition in failure_conditions:
            path = condition.get('path', '')
            operator = condition.get('operator', '==')
            expected_value = condition.get('value')
            
            # 从响应中获取值
            actual_value = self._get_nested_value({'response': response_body}, path.split('.'))
            
            # 评估条件
            condition_met = False
            if operator == '==':
                condition_met = actual_value == expected_value
            elif operator == '!=':
                condition_met = actual_value != expected_value
            elif operator == '>':
                condition_met = actual_value > expected_value
            elif operator == '<':
                condition_met = actual_value < expected_value
            elif operator == 'in':
                condition_met = actual_value in expected_value
            elif operator == 'not_in':
                condition_met = actual_value not in expected_value
            
            # 如果条件满足，说明验证失败
            if condition_met:
                # 生成错误消息
                error_message = self._format_error_message(
                    error_template, response_body, path, actual_value
                )
                return {
                    'valid': False,
                    'error_message': error_message
                }
        
        return {'valid': True}
    
    def _format_error_message(
        self,
        template: str,
        response_body: Any,
        failed_path: str,
        failed_value: Any
    ) -> str:
        """格式化错误消息，支持模板变量"""
        import re
        
        # 替换 {response.xxx} 格式的变量
        def replace_var(match):
            var_path = match.group(1)
            value = self._get_nested_value({'response': response_body}, var_path.split('.'))
            return str(value) if value is not None else 'N/A'
        
        message = re.sub(r'\{([^}]+)\}', replace_var, template)
        
        # 如果没有替换任何变量，添加默认信息
        if message == template:
            message = f"Validation failed: {failed_path} = {failed_value}"
        
        return message
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """脱敏请求头（隐藏认证信息）"""
        sanitized = {}
        sensitive_keys = ['authorization', 'x-api-key', 'api-key']
        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = '***REDACTED***'
            else:
                sanitized[key] = value
        return sanitized



