# Response to Reviewer #2 - Section 3.4: External Tool Error Handling

## Question
The reviewer asks for augmentation of the "standard interface contract" description with details on how AstroPropose handles:
(a) calls to external tools that fail
(b) when the tool reports that a target is not visible
(Can a proposal still be submitted if a visibility check fails? What happens if only one target in a list of targets is not visible?)

## Response

We thank the reviewer for this important question. We have enhanced the framework to provide robust error handling and validation mechanisms for external tool integrations. Below we describe how AstroPropose handles these scenarios.

### (a) Handling Failed External Tool Calls

AstroPropose implements a multi-layered error handling strategy that distinguishes between different types of failures:

**1. Tool Type Classification**
External tools are classified into categories based on their role in the workflow:
- **Validation tools** (e.g., visibility calculators, feasibility checkers): These tools perform critical checks that may block workflow transitions
- **Notification tools**: These send alerts and do not block workflow progression
- **Data processing tools**: These transform or enrich proposal data
- **Other tools**: General-purpose integrations

**2. Service Failure Handling**
When an external tool service is unavailable (network errors, timeouts, HTTP 5xx responses), the framework:

- **For validation tools**: By default, service failures do not block proposal submission (`block_on_service_error: false`). This prevents temporary service outages from blocking legitimate proposals. However, administrators can configure validation tools to block on service errors if strict validation is required.

- **For other tools**: The behavior is controlled by the `on_failure` parameter in the workflow transition configuration:
  - `continue`: Log the error but proceed with the workflow
  - `abort`: Stop the workflow transition and return an error
  - `retry`: Automatically retry with exponential backoff (configurable)

**3. Retry Mechanism**
All external tool calls support configurable retry policies:
- Maximum retry attempts (default: 3)
- Retry delay with exponential backoff
- Configurable retryable HTTP status codes (default: 500, 502, 503, 504)
- All retry attempts are logged in the `ExternalToolExecution` table for audit purposes

**4. Error Logging and Audit**
Every external tool execution is logged with:
- Request parameters (sanitized to remove sensitive authentication data)
- Response status and body
- Execution duration
- Retry attempts
- Error messages

This comprehensive logging enables administrators to diagnose issues and provides a complete audit trail.

### (b) Handling Validation Failures (e.g., Target Not Visible)

**1. Validation Result Checking**
For validation-type tools, AstroPropose performs post-execution validation result checking. The framework evaluates the tool's response against configurable failure conditions defined in the `validation_config`:

```json
{
  "failure_conditions": [
    {"path": "response.visible", "operator": "==", "value": false},
    {"path": "response.status", "operator": "!=", "value": "ok"}
  ],
  "error_message_template": "Target is not visible: {response.reason}"
}
```

**2. Blocking Behavior**
By default, **validation failures block workflow transitions** (`block_on_failure: true`). This means:

- **If a visibility check fails, the proposal cannot be submitted** until the issue is resolved
- The user receives a detailed error message explaining why the validation failed
- The error message can include specific details from the tool's response (e.g., `"Target is not visible: Sun angle constraint violated"`)

However, administrators can configure validation tools to allow proposals to proceed with warnings (`block_on_failure: false`), which are logged but do not prevent submission.

**3. Partial Validation Failures (Multiple Targets)**

When a proposal contains multiple targets and only some fail validation:

- The framework collects **all validation errors** from all targets
- If any target fails and `block_on_failure: true`, the entire workflow transition is blocked
- The error message includes details for **all failed targets**, allowing the proposer to see which specific targets have issues
- Example error message:
  ```
  Validation failed:
  - Target 1 (RA: 279.23, Dec: -29.01): Not visible - Sun angle constraint
  - Target 3 (RA: 45.12, Dec: 12.34): Not visible - Moon interference
  ```

This ensures that proposers receive complete information about all validation issues before resubmission.

**4. Integration with Workflow Engine**

Validation tools are integrated into workflow transitions through the `effects` configuration:

```json
{
  "effects": {
    "external_tools": [
      {
        "operation_id": 1,
        "on_failure": "abort"
      }
    ]
  }
}
```

When a validation tool fails:
1. The workflow engine catches the validation error
2. The transition is rolled back (no state change occurs)
3. A detailed error response is returned to the user
4. The proposal remains in its current state, allowing the proposer to correct issues and retry

### Implementation Example: Visibility Check Integration

In the EOPS implementation, the Target Visibility Calculator is configured as a validation tool with:

```json
{
  "tool_type": "validation",
  "validation_config": {
    "block_on_failure": true,
    "block_on_service_error": false,
    "failure_conditions": [
      {"path": "response.visible", "operator": "==", "value": false}
    ],
    "error_message_template": "Target visibility check failed: {response.reason}. Observation window: {response.observation_window}"
  }
}
```

This configuration ensures that:
- Proposals with non-visible targets cannot be submitted
- Temporary service outages do not block submissions
- Users receive informative error messages with specific reasons

### Summary

To directly answer the reviewer's questions:

1. **Can a proposal still be submitted if a visibility check fails?**
   - **No, by default.** Validation failures block workflow transitions. However, this behavior is configurable per tool.

2. **What happens if only one target in a list of targets is not visible?**
   - The framework collects all validation errors and blocks the transition if any target fails. The error message lists all failed targets with specific reasons, allowing the proposer to address all issues before resubmission.

3. **How are external tool failures handled?**
   - Service failures (network errors, timeouts) are handled with retry mechanisms and configurable blocking behavior. Validation failures are evaluated against configurable conditions and can block workflow transitions. All failures are logged for audit and debugging purposes.

We will update Section 3.4 of the manuscript to include these error handling details, providing administrators and tool developers with clear guidance on configuring robust external tool integrations.

