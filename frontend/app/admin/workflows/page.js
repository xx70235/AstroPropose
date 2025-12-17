'use client';

import { useEffect, useState } from 'react';
import { getWorkflows, getWorkflow, saveWorkflow, createWorkflow } from '@/lib/api';
import WorkflowEditor from '@/components/WorkflowEditor';

export default function WorkflowPage() {
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState('');
  const [currentWorkflow, setCurrentWorkflow] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // 新建工作流的状态
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState('');
  const [newWorkflowDescription, setNewWorkflowDescription] = useState('');

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        const data = await getWorkflows();
        setWorkflows(data);
        if (data.length > 0) {
          setSelectedWorkflowId(data[0].id);
        }
      } catch (err) {
        setError('Failed to fetch workflows.');
        console.error(err);
      }
    };
    fetchWorkflows();
  }, []);

  useEffect(() => {
    if (!selectedWorkflowId) return;
    const fetchWorkflowDef = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getWorkflow(selectedWorkflowId);
        setCurrentWorkflow(data);
      } catch (err) {
        setError(`Failed to load workflow ${selectedWorkflowId}.`);
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchWorkflowDef();
  }, [selectedWorkflowId]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSuccess('');
    setError('');
    
    if (!newWorkflowName.trim()) {
      setError('Workflow name is required.');
      return;
    }
    
    try {
      const result = await createWorkflow({
        name: newWorkflowName,
        description: newWorkflowDescription,
      });
      setSuccess(`Workflow "${newWorkflowName}" created successfully!`);
      setNewWorkflowName('');
      setNewWorkflowDescription('');
      setShowCreateForm(false);
      
      // 刷新工作流列表
      const data = await getWorkflows();
      setWorkflows(data);
      if (result.id) {
        setSelectedWorkflowId(result.id);
      }
    } catch (err) {
      setError(err.info?.message || 'Failed to create workflow.');
      console.error(err);
    }
  };

  const handleSave = async (definition) => {
    setSuccess('');
    setError('');
    try {
      await saveWorkflow(selectedWorkflowId, { ...currentWorkflow, definition });
      setSuccess('Workflow saved successfully!');
    } catch (err) {
      setError('Failed to save workflow.');
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Workflow Management</h1>
      
      {/* Create new workflow section */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Create New Workflow</h2>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            {showCreateForm ? 'Cancel' : '+ New Workflow'}
          </button>
        </div>
        
        {showCreateForm && (
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label htmlFor="workflow-name" className="block text-sm font-medium text-gray-700">
                Workflow Name *
              </label>
              <input
                id="workflow-name"
                type="text"
                required
                value={newWorkflowName}
                onChange={(e) => setNewWorkflowName(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="e.g., CSST Observation Workflow"
              />
            </div>
            <div>
              <label htmlFor="workflow-description" className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                id="workflow-description"
                rows={3}
                value={newWorkflowDescription}
                onChange={(e) => setNewWorkflowDescription(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Describe the purpose of this workflow..."
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Create Workflow
            </button>
          </form>
        )}
      </div>

      {/* Edit existing workflow section */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Edit Workflow</h2>
        <div className="mb-4">
          <label htmlFor="workflow-select" className="block text-sm font-medium text-gray-700 mb-1">
            Select a workflow to edit:
          </label>
          <select
            id="workflow-select"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            value={selectedWorkflowId}
            onChange={(e) => setSelectedWorkflowId(e.target.value)}
          >
            <option value="">-- Select a workflow --</option>
            {workflows.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </div>

        {error && <p className="text-red-500 bg-red-100 p-3 rounded mb-4">{error}</p>}
        {success && <p className="text-green-500 bg-green-100 p-3 rounded mb-4">{success}</p>}

        {isLoading ? (
          <p>Loading...</p>
        ) : currentWorkflow ? (
          <WorkflowEditor
            initialDefinition={currentWorkflow.definition}
            onSave={handleSave}
          />
        ) : (
          <p className="text-gray-500">Please select a workflow to start editing.</p>
        )}
      </div>
    </div>
  );
}
