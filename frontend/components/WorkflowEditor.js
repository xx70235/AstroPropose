'use client';

import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  addEdge,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';

const initialNodes = [
  { id: '1', type: 'input', data: { label: 'Start' }, position: { x: 250, y: 5 } },
];

const WorkflowEditor = ({ initialDefinition, onSave }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (initialDefinition && initialDefinition.nodes) {
      setNodes(initialDefinition.nodes);
      setEdges(initialDefinition.edges || []);
    }
  }, [initialDefinition, setNodes, setEdges]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleSaveClick = () => {
    const definition = { nodes, edges };
    onSave(definition);
  };

  return (
    <div>
      <div style={{ height: '70vh', border: '1px solid #ccc', borderRadius: '8px' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <MiniMap />
          <Controls />
          <Background />
        </ReactFlow>
      </div>
      <button
        onClick={handleSaveClick}
        className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded"
      >
        Save Workflow
      </button>
    </div>
  );
};

export default WorkflowEditor;
