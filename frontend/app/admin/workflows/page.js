'use client';

import { useEffect, useState } from 'react';
import { getWorkflows, getWorkflow, saveWorkflow } from '@/lib/api';
import WorkflowEditor from '@/components/WorkflowEditor';

export default function WorkflowPage() {
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState('');
  const [currentWorkflow, setCurrentWorkflow] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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
    <div>
      <h1 className="text-3xl font-bold mb-4">Visual Workflow Editor</h1>
      <div className="mb-4">
        <label htmlFor="workflow-select" className="block text-sm font-medium text-gray-700 mb-1">
          Select Workflow to Edit:
        </label>
        <select
          id="workflow-select"
          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          value={selectedWorkflowId}
          onChange={(e) => setSelectedWorkflowId(e.target.value)}
        >
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
        <p>Loading workflow...</p>
      ) : currentWorkflow ? (
        <WorkflowEditor
          initialDefinition={currentWorkflow.definition}
          onSave={handleSave}
        />
      ) : (
        <p>Select a workflow to begin editing.</p>
      )}
    </div>
  );
}
