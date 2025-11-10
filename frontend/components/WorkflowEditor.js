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
  { id: '1', type: 'input', data: { label: 'Draft' }, position: { x: 200, y: 30 } },
  { id: '2', type: 'default', data: { label: 'Submitted' }, position: { x: 450, y: 30 } },
];

const WorkflowEditor = ({ initialDefinition, onSave }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [metadata, setMetadata] = useState({ initial_state: 'Draft', transitions: [] });
  const [transitionsDraft, setTransitionsDraft] = useState('[]');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!initialDefinition) return;
    if (initialDefinition.nodes) {
      setNodes(initialDefinition.nodes);
    }
    if (initialDefinition.edges) {
      setEdges(initialDefinition.edges);
    }
    setMetadata({
      initial_state: initialDefinition.initial_state || 'Draft',
      transitions: initialDefinition.transitions || [],
    });
    setTransitionsDraft(JSON.stringify(initialDefinition.transitions || [], null, 2));
  }, [initialDefinition, setNodes, setEdges]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  const handleSave = () => {
    try {
      const parsed = JSON.parse(transitionsDraft || '[]');
      const definition = {
        nodes,
        edges,
        initial_state: metadata.initial_state,
        transitions: parsed,
      };
      setError('');
      onSave(definition);
    } catch (err) {
      console.error(err);
      setError('Transitions JSON 解析失败，请检查格式。');
    }
  };

  const insertPreset = () => {
    const preset = [
      {
        name: 'submit_phase1',
        label: '提交 Phase-1',
        from: 'Draft',
        to: 'Submitted',
        roles: ['Proposer'],
        conditions: {
          phase_status: { phase: 'phase1', status: 'draft' },
        },
        effects: {
          phase: 'phase1',
          set_phase_status: 'submitted',
          record_submission_time: true,
        },
      },
      {
        name: 'enter_scheduling',
        label: '进入排程',
        from: 'Submitted',
        to: 'Scheduling',
        roles: ['Admin'],
        effects: {
          instrument: { phase: 'phase1', set_status: 'pending' },
        },
      },
      {
        name: 'complete_phase1',
        label: '排程完成',
        from: 'Scheduling',
        to: 'Phase1Confirmed',
        roles: ['Instrument Scheduler'],
        conditions: {
          instrument_status: { status: 'scheduled', phase: 'phase1' },
        },
        effects: {
          phase: 'phase1',
          set_phase_status: 'confirmed',
          record_confirmation_time: true,
        },
      },
    ];
    setTransitionsDraft(JSON.stringify(preset, null, 2));
  };

  return (
    <div className="space-y-6">
      <div className="h-[60vh] rounded-lg border border-gray-200">
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

      <section className="space-y-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div>
          <label className="block text-sm font-medium text-gray-700">初始状态</label>
          <input
            type="text"
            value={metadata.initial_state}
            onChange={(event) => setMetadata((prev) => ({ ...prev, initial_state: event.target.value }))}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
            placeholder="Draft"
          />
          <p className="mt-1 text-xs text-gray-500">系统在创建提案时会将工作流状态初始化为该值。</p>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-gray-700">Transitions 配置（JSON）</label>
            <button
              type="button"
              onClick={insertPreset}
              className="text-xs text-indigo-600 hover:text-indigo-800"
            >
              插入 CSST 示例
            </button>
          </div>
          <textarea
            value={transitionsDraft}
            onChange={(event) => setTransitionsDraft(event.target.value)}
            rows={12}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-xs shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
          />
          <p className="mt-1 text-xs text-gray-500">
            支持 roles、conditions（phase_status、instrument_status、context.*）与 effects（phase、instrument）等字段，用于驱动提案多阶段、多仪器流程。
          </p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end">
          <button
            onClick={handleSave}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            保存工作流
          </button>
        </div>
      </section>
    </div>
  );
};

export default WorkflowEditor;
