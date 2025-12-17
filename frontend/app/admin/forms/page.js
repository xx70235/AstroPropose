'use client';

import { useEffect, useState } from 'react';
import {
  listFormTemplates,
  getFormTemplate,
  createFormTemplate,
  updateFormTemplate,
  listInstruments,
  listExternalTools,
  getExternalTool,
} from '@/lib/api';

// Field type options
const FIELD_TYPES = [
  { value: 'text', label: 'Single-line Text' },
  { value: 'textarea', label: 'Multi-line Text' },
  { value: 'number', label: 'Number' },
  { value: 'select', label: 'Dropdown Select' },
  { value: 'checkbox', label: 'Checkbox' },
  { value: 'file', label: 'File Upload' },
  { value: 'repeatable', label: 'Repeatable Group (for multiple targets/sources)' },
];

// Phase options
const PHASE_OPTIONS = [
  { value: 'phase1', label: 'Phase 1' },
  { value: 'phase2', label: 'Phase 2' },
];

export default function FormManagementPage() {
  const [templates, setTemplates] = useState([]);
  const [instruments, setInstruments] = useState([]);
  const [externalTools, setExternalTools] = useState([]);
  const [externalToolOperations, setExternalToolOperations] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  const [currentTemplate, setCurrentTemplate] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Create new form state
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newFormName, setNewFormName] = useState('');
  const [newFormPhase, setNewFormPhase] = useState('phase1');
  const [newFormInstrument, setNewFormInstrument] = useState('');
  const [fields, setFields] = useState([]);

  // Editing field state
  const [editingFieldIndex, setEditingFieldIndex] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [templatesData, instrumentsData, toolsData] = await Promise.all([
          listFormTemplates(),
          listInstruments(),
          listExternalTools(),
        ]);
        setTemplates(templatesData);
        setInstruments(instrumentsData);
        setExternalTools(toolsData);
        
        // Load all external tool operations
        const allOperations = [];
        for (const tool of toolsData) {
          try {
            const toolDetail = await getExternalTool(tool.id);
            if (toolDetail.operations && Array.isArray(toolDetail.operations)) {
              toolDetail.operations.forEach(op => {
                allOperations.push({
                  ...op,
                  toolName: tool.name,
                  toolId: tool.id,
                });
              });
            }
          } catch (err) {
            console.error(`Failed to load operations for tool ${tool.id}:`, err);
          }
        }
        console.log('Loaded external tool operations:', allOperations);
        setExternalToolOperations(allOperations);
      } catch (err) {
        setError('Failed to load data');
        console.error(err);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    if (!selectedTemplateId) {
      setCurrentTemplate(null);
      return;
    }
    
    const fetchTemplate = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getFormTemplate(selectedTemplateId);
        setCurrentTemplate(data);
        setFields(data.definition?.fields || []);
      } catch (err) {
        setError(`Failed to load form template`);
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchTemplate();
  }, [selectedTemplateId]);

  const handleCreateTemplate = async (e) => {
    e.preventDefault();
    setSuccess('');
    setError('');

    if (!newFormName.trim()) {
      setError('Form name is required');
      return;
    }

    if (fields.length === 0) {
      setError('At least one field is required');
      return;
    }

    try {
      // Convert subFields to sub_fields for backend compatibility
      const fieldsToSave = fields.map(field => {
        if (field.subFields) {
          const { subFields, ...rest } = field;
          return { ...rest, sub_fields: subFields };
        }
        return field;
      });
      
      const templateData = {
        name: newFormName,
        phase: newFormPhase,
        instrument_code: newFormInstrument || null,
        definition: { fields: fieldsToSave },
      };

      const result = await createFormTemplate(templateData);
      setSuccess(`Form template "${newFormName}" created successfully! (v${result.version})`);
      setNewFormName('');
      setNewFormPhase('phase1');
      setNewFormInstrument('');
      setFields([]);
      setShowCreateForm(false);

      // Refresh template list
      const templatesData = await listFormTemplates();
      setTemplates(templatesData);
      if (result.id) {
        setSelectedTemplateId(result.id);
      }
    } catch (err) {
      setError(err.info?.message || 'Failed to create form template');
      console.error(err);
    }
  };

  const handleUpdateTemplate = async () => {
    if (!currentTemplate) return;
    
    setSuccess('');
    setError('');

    try {
      // Convert subFields to sub_fields for backend compatibility
      const fieldsToSave = fields.map(field => {
        if (field.subFields) {
          const { subFields, ...rest } = field;
          return { ...rest, sub_fields: subFields };
        }
        return field;
      });
      
      await updateFormTemplate(currentTemplate.id, {
        definition: { fields: fieldsToSave },
      });
      setSuccess('Form template updated successfully!');
    } catch (err) {
      setError(err.info?.message || 'Failed to update form template');
      console.error(err);
    }
  };

  const addField = () => {
    const newField = {
      name: `field_${Date.now()}`,
      label: 'New Field',
      type: 'text',
      required: false,
    };
    setFields([...fields, newField]);
    setEditingFieldIndex(fields.length);
  };

  const updateField = (index, updates) => {
    const newFields = [...fields];
    newFields[index] = { ...newFields[index], ...updates };
    setFields(newFields);
  };

  const deleteField = (index) => {
    const newFields = fields.filter((_, i) => i !== index);
    setFields(newFields);
    if (editingFieldIndex === index) {
      setEditingFieldIndex(null);
    }
  };

  const moveField = (index, direction) => {
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === fields.length - 1)
    ) {
      return;
    }
    
    const newFields = [...fields];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    [newFields[index], newFields[targetIndex]] = [newFields[targetIndex], newFields[index]];
    setFields(newFields);
  };

  const addSelectOption = (fieldIndex) => {
    const newFields = [...fields];
    if (!newFields[fieldIndex].options) {
      newFields[fieldIndex].options = [];
    }
    newFields[fieldIndex].options.push({
      value: `option_${Date.now()}`,
      label: 'New Option',
    });
    setFields(newFields);
  };

  const updateSelectOption = (fieldIndex, optionIndex, updates) => {
    const newFields = [...fields];
    newFields[fieldIndex].options[optionIndex] = {
      ...newFields[fieldIndex].options[optionIndex],
      ...updates,
    };
    setFields(newFields);
  };

  const deleteSelectOption = (fieldIndex, optionIndex) => {
    const newFields = [...fields];
    newFields[fieldIndex].options = newFields[fieldIndex].options.filter(
      (_, i) => i !== optionIndex
    );
    setFields(newFields);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Form Template Management</h1>

      {/* Create new form section */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Create New Form Template</h2>
          <button
            onClick={() => {
              setShowCreateForm(!showCreateForm);
              if (!showCreateForm) {
                setFields([]);
                setEditingFieldIndex(null);
              }
            }}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            {showCreateForm ? 'Cancel' : '+ New Form'}
          </button>
        </div>

        {showCreateForm && (
          <form onSubmit={handleCreateTemplate} className="space-y-6">
            {/* Basic info */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Form Name *
                </label>
                <input
                  type="text"
                  required
                  value={newFormName}
                  onChange={(e) => setNewFormName(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="e.g., Imaging Observation Form"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Phase *
                </label>
                <select
                  value={newFormPhase}
                  onChange={(e) => setNewFormPhase(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {PHASE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Associated Instrument (optional)
                </label>
                <select
                  value={newFormInstrument}
                  onChange={(e) => setNewFormInstrument(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">General Form</option>
                  {instruments.map((inst) => (
                    <option key={inst.code} value={inst.code}>
                      {inst.code} - {inst.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Field editor */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium">Form Fields</h3>
                <button
                  type="button"
                  onClick={addField}
                  className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                >
                  + Add Field
                </button>
              </div>

              {fields.length === 0 ? (
                <p className="text-gray-500 text-sm">No fields yet. Click "Add Field" to start.</p>
              ) : (
                <div className="space-y-3">
                  {fields.map((field, index) => (
                    <FieldEditor
                      key={index}
                      field={field}
                      index={index}
                      isEditing={editingFieldIndex === index}
                      onEdit={() => setEditingFieldIndex(index)}
                      onCollapse={() => setEditingFieldIndex(null)}
                      onUpdate={(updates) => updateField(index, updates)}
                      onDelete={() => deleteField(index)}
                      onMoveUp={() => moveField(index, 'up')}
                      onMoveDown={() => moveField(index, 'down')}
                      canMoveUp={index > 0}
                      canMoveDown={index < fields.length - 1}
                      onAddOption={() => addSelectOption(index)}
                      onUpdateOption={(optIdx, updates) =>
                        updateSelectOption(index, optIdx, updates)
                      }
                      onDeleteOption={(optIdx) => deleteSelectOption(index, optIdx)}
                      externalToolOperations={externalToolOperations}
                    />
                  ))}
                </div>
              )}
            </div>

            <button
              type="submit"
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Create Form Template
            </button>
          </form>
        )}
      </div>

      {/* Edit existing form section */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Edit Form Template</h2>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Select a form template to edit:
          </label>
          <select
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
          >
            <option value="">-- Select a form template --</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} (v{t.version}) - {t.phase} 
                {t.instrument && ` - ${t.instrument}`}
              </option>
            ))}
          </select>
        </div>

        {error && <p className="text-red-500 bg-red-100 p-3 rounded mb-4">{error}</p>}
        {success && <p className="text-green-500 bg-green-100 p-3 rounded mb-4">{success}</p>}

        {isLoading ? (
          <p>Loading...</p>
        ) : currentTemplate ? (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded">
              <h3 className="font-medium mb-2">Template Info</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="font-medium">Name:</span> {currentTemplate.name}</div>
                <div><span className="font-medium">Version:</span> v{currentTemplate.version}</div>
                <div><span className="font-medium">Phase:</span> {currentTemplate.phase}</div>
                <div><span className="font-medium">Instrument:</span> {currentTemplate.instrument || 'General'}</div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium">Form Fields</h3>
                <button
                  type="button"
                  onClick={addField}
                  className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                >
                  + Add Field
                </button>
              </div>

              {fields.length === 0 ? (
                <p className="text-gray-500 text-sm">No fields</p>
              ) : (
                <div className="space-y-3">
                  {fields.map((field, index) => (
                    <FieldEditor
                      key={index}
                      field={field}
                      index={index}
                      isEditing={editingFieldIndex === index}
                      onEdit={() => setEditingFieldIndex(index)}
                      onCollapse={() => setEditingFieldIndex(null)}
                      onUpdate={(updates) => updateField(index, updates)}
                      onDelete={() => deleteField(index)}
                      onMoveUp={() => moveField(index, 'up')}
                      onMoveDown={() => moveField(index, 'down')}
                      canMoveUp={index > 0}
                      canMoveDown={index < fields.length - 1}
                      onAddOption={() => addSelectOption(index)}
                      onUpdateOption={(optIdx, updates) =>
                        updateSelectOption(index, optIdx, updates)
                      }
                      onDeleteOption={(optIdx) => deleteSelectOption(index, optIdx)}
                      externalToolOperations={externalToolOperations}
                    />
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleUpdateTemplate}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Save Changes
            </button>
          </div>
        ) : (
          <p className="text-gray-500">Please select a form template to start editing.</p>
        )}
      </div>
    </div>
  );
}

// Field editor component
function FieldEditor({
  field,
  index,
  isEditing,
  onEdit,
  onCollapse,
  onUpdate,
  onDelete,
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown,
  onAddOption,
  onUpdateOption,
  onDeleteOption,
  externalToolOperations = [],
}) {
  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      {!isEditing ? (
        // Preview mode
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="font-medium">{field.label}</div>
            <div className="text-sm text-gray-600">
              Type: {FIELD_TYPES.find(t => t.value === field.type)?.label || field.type} | 
              Field name: {field.name} | 
              {field.required ? 'Required' : 'Optional'}
            </div>
            {field.placeholder && (
              <div className="text-sm text-gray-500">Placeholder: {field.placeholder}</div>
            )}
            {field.type === 'select' && field.options && (
              <div className="text-sm text-gray-600 mt-1">
                Options: {field.options.map(o => o.label).join(', ')}
              </div>
            )}
          </div>
          <div className="flex gap-2">
            {canMoveUp && (
              <button
                type="button"
                onClick={onMoveUp}
                className="px-2 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
                title="Move up"
              >
                ↑
              </button>
            )}
            {canMoveDown && (
              <button
                type="button"
                onClick={onMoveDown}
                className="px-2 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
                title="Move down"
              >
                ↓
              </button>
            )}
            <button
              type="button"
              onClick={onEdit}
              className="px-2 py-1 text-sm bg-blue-100 hover:bg-blue-200 rounded"
            >
              Edit
            </button>
            <button
              type="button"
              onClick={onDelete}
              className="px-2 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded"
            >
              Delete
            </button>
          </div>
        </div>
      ) : (
        // Edit mode
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700">Field Name</label>
              <input
                type="text"
                value={field.name}
                onChange={(e) => onUpdate({ name: e.target.value })}
                className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700">Display Label</label>
              <input
                type="text"
                value={field.label}
                onChange={(e) => onUpdate({ label: e.target.value })}
                className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700">Field Type</label>
              <select
                value={field.type}
                onChange={(e) => onUpdate({ type: e.target.value })}
                className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded"
              >
                {FIELD_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700">
                <input
                  type="checkbox"
                  checked={field.required || false}
                  onChange={(e) => onUpdate({ required: e.target.checked })}
                  className="mr-2"
                />
                Required Field
              </label>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700">Placeholder</label>
            <input
              type="text"
              value={field.placeholder || ''}
              onChange={(e) => onUpdate({ placeholder: e.target.value })}
              className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded"
            />
          </div>

          {/* External Tool Association */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">External Tool (Optional)</label>
            <select
              value={field.external_tool_operation_id || ''}
              onChange={(e) => {
                const opId = e.target.value ? parseInt(e.target.value) : null;
                onUpdate({ external_tool_operation_id: opId });
              }}
              className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded"
            >
              <option value="">-- No external tool --</option>
              {externalToolOperations.map((op) => (
                <option key={op.id} value={op.id}>
                  {op.toolName} - {op.name}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Associate an external tool (e.g., visibility checker) with this field. Users can click a button to call the tool while filling the form.
            </p>
            {field.external_tool_operation_id && (
              <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                <span className="text-blue-700">🔧 Tool associated: </span>
                {externalToolOperations.find(o => o.id === field.external_tool_operation_id)?.name || 'Unknown'}
              </div>
            )}
          </div>

          {field.type === 'textarea' && (
            <div>
              <label className="block text-xs font-medium text-gray-700">Rows</label>
              <input
                type="number"
                value={field.rows || 4}
                onChange={(e) => onUpdate({ rows: parseInt(e.target.value) })}
                className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded"
                min="1"
                max="20"
              />
            </div>
          )}

          {field.type === 'select' && (
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-xs font-medium text-gray-700">Options</label>
                <button
                  type="button"
                  onClick={onAddOption}
                  className="px-2 py-1 text-xs bg-green-100 hover:bg-green-200 rounded"
                >
                  + Add Option
                </button>
              </div>
              {field.options && field.options.length > 0 ? (
                <div className="space-y-2">
                  {field.options.map((option, optIdx) => (
                    <div key={optIdx} className="flex gap-2">
                      <input
                        type="text"
                        value={option.value}
                        onChange={(e) =>
                          onUpdateOption(optIdx, { value: e.target.value })
                        }
                        placeholder="Value"
                        className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded"
                      />
                      <input
                        type="text"
                        value={option.label}
                        onChange={(e) =>
                          onUpdateOption(optIdx, { label: e.target.value })
                        }
                        placeholder="Display text"
                        className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded"
                      />
                      <button
                        type="button"
                        onClick={() => onDeleteOption(optIdx)}
                        className="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded"
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500">No options yet</p>
              )}
            </div>
          )}

          {field.type === 'repeatable' && (
            <div className="border-t pt-3 mt-3">
              <div className="bg-purple-50 p-3 rounded mb-3">
                <p className="text-xs text-purple-700">
                  <strong>Repeatable Group:</strong> Users can add multiple instances of this group.
                  For example, define fields for one target source, and users can add as many sources as needed.
                </p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700">Min Entries</label>
                <input
                  type="number"
                  value={field.minEntries || 1}
                  onChange={(e) => onUpdate({ minEntries: parseInt(e.target.value) || 1 })}
                  className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  min="0"
                  max="100"
                />
              </div>
              <div className="mt-2">
                <label className="block text-xs font-medium text-gray-700">Max Entries (0 = unlimited)</label>
                <input
                  type="number"
                  value={field.maxEntries || 0}
                  onChange={(e) => onUpdate({ maxEntries: parseInt(e.target.value) || 0 })}
                  className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  min="0"
                  max="1000"
                />
              </div>
              <div className="mt-3">
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-xs font-medium text-gray-700">Sub-fields in each entry</label>
                  <button
                    type="button"
                    onClick={() => {
                      const subFields = field.subFields || [];
                      onUpdate({
                        subFields: [
                          ...subFields,
                          { name: `subfield_${Date.now()}`, label: 'New Sub-field', type: 'text', required: false }
                        ]
                      });
                    }}
                    className="px-2 py-1 text-xs bg-purple-100 hover:bg-purple-200 rounded"
                  >
                    + Add Sub-field
                  </button>
                </div>
                <div className="bg-yellow-50 border border-yellow-200 p-2 rounded mb-2">
                  <p className="text-xs text-yellow-700">
                    💡 <strong>Tip:</strong> Use "📋 Instrument Parameters" type to embed the instrument-specific 
                    observation parameters form. The system will automatically load the form template associated 
                    with each instrument selected in the proposal.
                  </p>
                </div>
                {(field.subFields || field.sub_fields) && (field.subFields || field.sub_fields).length > 0 ? (
                  <div className="space-y-2">
                    {(field.subFields || field.sub_fields).map((subField, subIdx) => (
                      <div key={subIdx}>
                        <div className={`flex gap-2 items-center p-2 rounded ${subField.type === 'instrument_params' ? 'bg-indigo-100 border border-indigo-300' : 'bg-gray-100'}`}>
                          <input
                            type="text"
                            value={subField.name}
                            onChange={(e) => {
                              const currentSubFields = field.subFields || field.sub_fields || [];
                              const newSubFields = [...currentSubFields];
                              newSubFields[subIdx] = { ...newSubFields[subIdx], name: e.target.value };
                              onUpdate({ subFields: newSubFields });
                            }}
                            placeholder="Field name"
                            className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded"
                          />
                          <input
                            type="text"
                            value={subField.label}
                            onChange={(e) => {
                              const currentSubFields = field.subFields || field.sub_fields || [];
                              const newSubFields = [...currentSubFields];
                              newSubFields[subIdx] = { ...newSubFields[subIdx], label: e.target.value };
                              onUpdate({ subFields: newSubFields });
                            }}
                            placeholder="Display label"
                            className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded"
                          />
                          <select
                            value={subField.type}
                            onChange={(e) => {
                              const currentSubFields = field.subFields || field.sub_fields || [];
                              const newSubFields = [...currentSubFields];
                              newSubFields[subIdx] = { ...newSubFields[subIdx], type: e.target.value };
                              onUpdate({ subFields: newSubFields });
                            }}
                            className="px-2 py-1 text-xs border border-gray-300 rounded"
                          >
                            <option value="text">Text</option>
                            <option value="number">Number</option>
                            <option value="textarea">Textarea</option>
                            <option value="select">Select</option>
                            <option value="instrument_params">📋 Instrument Parameters</option>
                          </select>
                          <label className="flex items-center text-xs">
                            <input
                              type="checkbox"
                              checked={subField.required || false}
                              onChange={(e) => {
                                const currentSubFields = field.subFields || field.sub_fields || [];
                                const newSubFields = [...currentSubFields];
                                newSubFields[subIdx] = { ...newSubFields[subIdx], required: e.target.checked };
                                onUpdate({ subFields: newSubFields });
                              }}
                              className="mr-1"
                            />
                            Req
                          </label>
                          <button
                            type="button"
                            onClick={() => {
                              const currentSubFields = field.subFields || field.sub_fields || [];
                              const newSubFields = currentSubFields.filter((_, i) => i !== subIdx);
                              onUpdate({ subFields: newSubFields });
                            }}
                            className="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded"
                          >
                            ×
                          </button>
                        </div>
                        {/* Sub-field external tool association */}
                        <div className="mt-1 ml-2 p-2 bg-gray-50 rounded border border-gray-200">
                          <label className="block text-xs text-gray-600 mb-1">External Tool:</label>
                          <select
                            value={subField.external_tool_operation_id || ''}
                            onChange={(e) => {
                              const currentSubFields = field.subFields || field.sub_fields || [];
                              const newSubFields = [...currentSubFields];
                              const opId = e.target.value ? parseInt(e.target.value) : null;
                              newSubFields[subIdx] = { ...newSubFields[subIdx], external_tool_operation_id: opId };
                              onUpdate({ subFields: newSubFields });
                            }}
                            className="w-full px-2 py-1 text-xs border border-gray-300 rounded"
                          >
                            <option value="">-- No tool --</option>
                            {externalToolOperations.map((op) => (
                              <option key={op.id} value={op.id}>
                                {op.toolName} - {op.name}
                              </option>
                            ))}
                          </select>
                          {subField.external_tool_operation_id && (
                            <div className="mt-1 text-xs text-blue-600">
                              🔧 {externalToolOperations.find(o => o.id === subField.external_tool_operation_id)?.name || 'Unknown'}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500">No sub-fields defined. Add fields like: source_name, ra, dec, exposure_time, etc.</p>
                )}
              </div>
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onCollapse}
              className="px-3 py-1 text-sm bg-indigo-600 text-white hover:bg-indigo-700 rounded"
            >
              Done Editing
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
