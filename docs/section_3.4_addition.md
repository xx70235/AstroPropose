# Suggested Addition to Section 3.4: Error Handling and Validation

## Text to Add After the Output Schema Description

The following text should be added to Section 3.4 after describing the standard interface contract, to address the reviewer's concerns about error handling:

---

### Error Handling and Validation Mechanisms

While the standard interface contract defines the communication protocol, AstroPropose also implements robust error handling and validation mechanisms to ensure reliable integration with external tools, particularly for critical validation operations such as visibility checks.

**Tool Type Classification and Failure Handling**

External tools are classified into categories based on their role in the workflow: validation tools (e.g., visibility calculators, feasibility checkers), notification tools, data processing tools, and general-purpose integrations. Each category has distinct failure handling behaviors.

For validation tools, the framework distinguishes between two types of failures:

1. **Service Failures** (network errors, timeouts, HTTP 5xx responses): By default, service failures do not block proposal submission (`block_on_service_error: false`), preventing temporary service outages from blocking legitimate proposals. However, administrators can configure validation tools to block on service errors if strict validation is required.

2. **Validation Failures** (tool returns a response indicating validation failure): These are evaluated against configurable failure conditions. For example, a visibility calculator might return `{"visible": false, "reason": "Sun angle constraint violated"}`. The framework checks these conditions using a flexible expression system:
   ```json
   {
     "failure_conditions": [
       {"path": "response.visible", "operator": "==", "value": false}
     ],
     "error_message_template": "Target is not visible: {response.reason}"
   }
   ```

**Blocking Behavior for Validation Failures**

By default, validation failures block workflow transitions (`block_on_failure: true`). This means that if a visibility check fails, the proposal cannot be submitted until the issue is resolved. The user receives a detailed error message that can include specific details from the tool's response, such as the reason for failure and any relevant constraints.

When a proposal contains multiple targets and only some fail validation, the framework collects all validation errors and blocks the transition if any target fails. The error message includes details for all failed targets, allowing the proposer to see which specific targets have issues. For example:
```
Validation failed:
- Target 1 (RA: 279.23, Dec: -29.01): Not visible - Sun angle constraint
- Target 3 (RA: 45.12, Dec: 12.34): Not visible - Moon interference
```

**Retry Mechanisms and Error Logging**

All external tool calls support configurable retry policies with exponential backoff. Administrators can configure the maximum number of retry attempts, retry delay, and which HTTP status codes should trigger retries. Every external tool execution is logged in the `ExternalToolExecution` table, including request parameters (with sensitive authentication data sanitized), response status and body, execution duration, retry attempts, and error messages. This comprehensive logging enables administrators to diagnose issues and provides a complete audit trail.

**Integration with Workflow Engine**

Validation tools are integrated into workflow transitions through the `effects` configuration. When a validation tool fails, the workflow engine catches the validation error, rolls back the transition (no state change occurs), and returns a detailed error response to the user. The proposal remains in its current state, allowing the proposer to correct issues and retry the submission.

This error handling design ensures that critical validations (such as visibility checks) can prevent invalid proposals from being submitted, while also providing flexibility for administrators to configure behavior based on their specific requirements and tolerance for service outages.

---

## Placement in Paper

This text should be inserted after the Output Schema description in Section 3.4, before the discussion of how external tools are used in EOPS (Section 4.3).

