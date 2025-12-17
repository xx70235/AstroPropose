# AstroPropose CSST Updates Summary

## Overview

This document summarizes the major updates made to AstroPropose to support CSST (China Space Station Telescope) observation proposal requirements. These updates significantly enhance the system's capabilities for managing complex astronomical observation workflows with external tool integration, dynamic forms, and flexible state management.

## Major Updates

### 1. Workflow Editor Migration: ReactFlow → XyFlow

**Date**: Recent updates  
**Impact**: High

- Migrated from ReactFlow to XyFlow (v12.0.0) for better performance and maintainability
- Updated all workflow editor components to use XyFlow APIs
- Improved drag-and-drop edge connections with proper Handle components
- Enhanced node selection and editing capabilities

**Files Modified**:
- `frontend/components/WorkflowEditor.js`
- `frontend/package.json`

### 2. External Tool Integration System

**Date**: Recent updates  
**Impact**: Critical

#### 2.1 Database Models
- Added `ExternalTool` model for tool registration
- Added `ExternalToolOperation` model for individual operations
- Added `ExternalToolExecution` model for execution tracking
- Added `tool_type` and `validation_config` fields for enhanced error handling

#### 2.2 Two-Level Tool Invocation
- **Form Field Level**: Users can call external tools interactively while filling forms (e.g., visibility checker)
- **Workflow Transition Level**: External tools are automatically called during state transitions (e.g., scheduling, notifications)

#### 2.3 Visual Representation
- Nodes display associated external tools (from form fields)
- Edges display external tools called during transitions (green color + tool icons)
- Tool associations visible in both workflow editor and form editor

**Files Modified**:
- `backend/app/models/models.py`
- `backend/app/api/external_tools.py`
- `backend/app/core/external_tool_executor.py`
- `backend/app/core/workflow_engine.py`
- `frontend/app/admin/external-tools/page.js`
- `frontend/app/admin/forms/page.js`
- `frontend/components/WorkflowEditor.js`
- `frontend/app/proposals/new/page.js`

### 3. Enhanced Form Builder

**Date**: Recent updates  
**Impact**: High

#### 3.1 Repeatable Field Groups
- Support for repeatable field groups (e.g., multiple observation targets)
- Configurable min/max entries
- Nested sub-fields within repeatable groups

#### 3.2 Instrument-Specific Parameters
- Special "Instrument Parameters" field type
- Automatically loads instrument-specific form templates
- Embedded within repeatable groups for observation parameters

#### 3.3 External Tool Association in Forms
- Fields can be associated with external tool operations
- Visual indicators in form editor
- Interactive tool calls from form fields during proposal creation

**Files Modified**:
- `frontend/app/admin/forms/page.js`
- `frontend/app/proposals/new/page.js`
- `backend/app/api/form_templates.py`

### 4. Workflow Editor Enhancements

**Date**: Recent updates  
**Impact**: High

#### 4.1 Node and Edge Editing
- Click nodes to edit properties (form association, description)
- Click edges to configure transitions (roles, conditions, effects, external tools)
- Visual feedback for selected nodes and edges
- Delete transitions with confirmation

#### 4.2 UI Improvements
- Terminology updated: "State" → "Node" throughout the interface
- Improved panel heights and layout
- Better visual organization of node and transition editors
- Enhanced help text and documentation

#### 4.3 Form-Template Association
- Nodes can be associated with form templates
- Required/optional form completion settings
- Visual display of associated forms on nodes

**Files Modified**:
- `frontend/components/WorkflowEditor.js`
- `backend/app/models/models.py` (added `form_template_id`, `form_required`, `description` to `WorkflowState`)

### 5. External Tool Failure Handling

**Date**: Recent updates  
**Impact**: Critical

#### 5.1 Tool Type Classification
- **Validation Tools**: Check proposal validity (e.g., target visibility)
- **Notification Tools**: Send notifications
- **Data Processing Tools**: Process proposal data
- **Other Tools**: General purpose tools

#### 5.2 Validation Configuration
- `block_on_failure`: Block workflow transition if validation fails
- `block_on_service_error`: Block on service errors
- `failure_conditions`: Define what constitutes a failure
- `error_message_template`: Custom error messages

#### 5.3 Error Handling
- Detailed error messages for validation failures
- Retry mechanisms for transient failures
- Execution logging and tracking

**Files Modified**:
- `backend/app/core/external_tool_executor.py`
- `backend/app/core/workflow_engine.py`
- `backend/app/api/proposals.py`
- `docs/reviewer_response_external_tools.md`

### 6. CSST-Specific Test Data

**Date**: Recent updates  
**Impact**: High

#### 6.1 Complete CSST Workflow
Created comprehensive test data including:
- **Roles**: Admin, Proposer, Instrument Scheduler, Panel Chair, Technical Expert, Reviewer
- **Users**: Test accounts for each role
- **Instruments**: CSST instrument definitions
- **Form Templates**:
  - Proposal Info (Phase 1, General Form)
  - Basic Observation Parameters (Phase 2, with repeatable targets)
  - Proposer Info
  - Review Form
- **External Tools**:
  - CSST Scheduling Tool
  - CSST Notification Service
  - CSST Target Visibility Calculator (mock)
- **Workflow**: Complete CSST observation workflow with Phase 1 and Phase 2 submissions

#### 6.2 Workflow States
- Draft → Phase1Submitted → TechnicalReview → Phase1Confirmed
- Phase2Draft → Phase2Submitted → UnderReview → Approved/Rejected




### 7. Database Schema Updates

**Date**: Recent updates  
**Impact**: High

#### 8.1 WorkflowState Enhancements
- `form_template_id`: Link forms to workflow states
- `form_required`: Require form completion before leaving state
- `description`: State descriptions

#### 8.2 External Tool Models
- Complete external tool management system
- Operation-level configuration
- Execution tracking and logging

**Files Modified**:
- `backend/app/models/models.py`
- `backend/migrations/versions/*.py`

### 9. API Enhancements

**Date**: Recent updates  
**Impact**: High

#### 9.1 External Tools API
- `GET /api/external-tools/`: List all tools
- `POST /api/external-tools/`: Register new tool
- `GET /api/external-tools/<id>`: Get tool details with operations
- `POST /api/external-tools/<id>/operations`: Add operation
- `POST /api/external-tools/operations/<id>/execute`: Execute from frontend

#### 9.2 Form Templates API
- Enhanced form template creation/update
- Support for repeatable groups and instrument parameters
- External tool operation association

**Files Modified**:
- `backend/app/api/external_tools.py`
- `backend/app/api/form_templates.py`
- `frontend/lib/api.js`

### 10. Documentation

**Date**: Recent updates  
**Impact**: Medium

Created comprehensive documentation:
- `docs/workflow_form_tool_association.md`: How forms and tools associate with workflows
- `docs/workflow_save_mechanism.md`: How workflows are saved
- `docs/transitions_configuration_guide.md`: Understanding transitions
- `docs/multi_form_association_design.md`: Design discussion for multiple forms per node
- `docs/csst_test_data_guide.md`: Guide for CSST test data
- `docs/reviewer_response_external_tools.md`: Response to reviewer comments

## Technical Improvements

### Frontend
- Improved component organization and reusability
- Better error handling and user feedback
- Enhanced visual design and UX
- Consistent styling and layout

### Backend
- Robust error handling for external tool failures
- Comprehensive validation and retry mechanisms
- Better separation of concerns
- Improved API design

### Database
- Proper foreign key relationships
- Migration support for schema changes
- Efficient querying with proper indexes

## CSST Workflow Support

The system now fully supports CSST observation proposal workflows:

1. **Phase 1 Submission**: Basic proposal information and scientific category
2. **Technical Review**: Technical experts review and provide feedback
3. **Phase 2 Submission**: Detailed observation parameters with multiple targets
4. **Scientific Review**: Panel review with scoring and comments
5. **Approval/Rejection**: Final decision with notifications

### Key Features for CSST
- ✅ Multi-phase proposal submission
- ✅ Repeatable observation targets
- ✅ Instrument-specific parameter forms
- ✅ External tool integration (scheduling, visibility, notifications)
- ✅ Role-based access control
- ✅ Workflow state management
- ✅ Form validation and requirements

## Migration Notes

### For Existing Installations
1. Run database migrations: `flask db upgrade`
2. Install new dependencies: `uv sync` (backend), `npm install` (frontend)
3. Seed CSST test data: `python seed_csst_test_data.py`
4. Update environment variables if needed

### Breaking Changes
- Workflow editor now uses XyFlow (ReactFlow removed)
- External tool models added (requires migration)
- Form template structure enhanced (backward compatible)

## Future Enhancements

Potential areas for further improvement:
- Support for multiple forms per workflow node
- Enhanced external tool configuration UI
- Workflow versioning and history
- Advanced condition builder UI
- Real-time collaboration features
- Mobile-responsive design improvements

## Conclusion

These updates significantly enhance AstroPropose's capabilities, making it a robust platform for managing CSST observation proposals. The system now supports complex workflows with external tool integration, dynamic forms, and flexible state management, meeting the requirements for modern astronomical observation proposal systems.

---

**Last Updated**: December 2025  
**Version**: 2.0 (CSST Support)

