'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  getProposals,
  getCurrentUser,
  listInstruments,
  submitInstrumentFeedbackAPI,
} from '@/lib/api';

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [instrumentOptions, setInstrumentOptions] = useState([]);
  const [selectedInstrument, setSelectedInstrument] = useState('');
  const [instrumentQueue, setInstrumentQueue] = useState([]);
  const [feedbackDrafts, setFeedbackDrafts] = useState({});
  const [feedbackMessage, setFeedbackMessage] = useState('');

  const router = useRouter();

  const isScheduler = useMemo(
    () => user?.roles?.includes('Instrument Scheduler'),
    [user]
  );
  const isAdmin = useMemo(() => user?.roles?.includes('Admin'), [user]);

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
      router.push('/login');
      return;
    }

    const fetchData = async () => {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
        const proposalsData = await getProposals();
        setProposals(proposalsData);

        if (userData.roles.includes('Instrument Scheduler') || userData.roles.includes('Admin')) {
          const instruments = await listInstruments();
          setInstrumentOptions(instruments);
          if (instruments.length > 0) {
            setSelectedInstrument((prev) => prev || instruments[0].code);
          }
        }
      } catch (err) {
        console.error(err);
        setError('数据获取失败，可能需要重新登录。');
        if (err.status === 401) {
            localStorage.removeItem('token');
            router.push('/login');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  useEffect(() => {
    const loadInstrumentQueue = async () => {
      if (!selectedInstrument || (!isScheduler && !isAdmin)) {
        setInstrumentQueue([]);
        return;
      }
      try {
        const data = await getProposals({ instrument_code: selectedInstrument });
        setInstrumentQueue(data);
      } catch (err) {
        console.error(err);
        setError('获取仪器排程队列失败');
      }
    };
    loadInstrumentQueue();
  }, [selectedInstrument, isScheduler, isAdmin]);

  const handleFeedbackChange = (proposalId, field, value) => {
    setFeedbackDrafts((prev) => ({
      ...prev,
      [proposalId]: {
        ...(prev[proposalId] || { status: 'under_assessment', payload: {} }),
        [field]: value,
      },
    }));
  };

  const handleFeedbackPayloadChange = (proposalId, key, value) => {
    setFeedbackDrafts((prev) => {
      const draft = prev[proposalId] || { status: 'under_assessment', payload: {} };
      return {
        ...prev,
        [proposalId]: {
          ...draft,
          payload: {
            ...draft.payload,
            [key]: value,
          },
        },
      };
    });
  };

  const submitFeedback = async (proposalId) => {
    if (!selectedInstrument) {
      return;
    }
    const draft = feedbackDrafts[proposalId];
    if (!draft) {
      setFeedbackMessage('请填写反馈信息');
      return;
    }

    try {
      await submitInstrumentFeedbackAPI(proposalId, selectedInstrument, {
        status: draft.status || 'under_assessment',
        comment: draft.comment,
        payload: draft.payload,
      });
      setFeedbackMessage('反馈已提交');
      const data = await getProposals({ instrument_code: selectedInstrument });
      setInstrumentQueue(data);
    } catch (err) {
      console.error(err);
      setFeedbackMessage(err.info?.message || '提交反馈失败');
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold">欢迎，{user ? user.username : '用户'}</h1>
        <p className="text-sm text-gray-600">角色：{user?.roles?.join(', ')}</p>
      </header>

      {error && <p className="text-red-500 bg-red-100 p-3 rounded mb-4">{error}</p>}

      <section className="bg-white shadow-md rounded p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">我的提案</h2>
          <Link
            href="/proposals/new"
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded"
          >
            创建 Phase 1 提案
            </Link>
        </div>

        {proposals.length ? (
          <ul className="divide-y divide-gray-200">
            {proposals.map((proposal) => (
              <li key={proposal.id} className="py-3">
                <p className="font-semibold">
                  {proposal.title}
                  <span className="ml-2 text-xs font-mono bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded">
                    {proposal.status}
                  </span>
                </p>
                <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600">
                  <div>
                    <h4 className="font-medium">阶段进度</h4>
                    <ul className="list-disc list-inside">
                      {proposal.phases.map((phase) => (
                        <li key={`${proposal.id}-${phase.phase}`}>
                          {phase.phase}：{phase.status}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium">涉及仪器</h4>
                    <ul className="list-disc list-inside">
                      {proposal.instruments.map((inst) => (
                        <li key={`${proposal.id}-${inst.instrument}`}>
                          {inst.instrument}：{inst.status}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p>尚未创建提案。</p>
        )}
      </section>

      {(isScheduler || isAdmin) && (
        <section className="bg-white shadow-md rounded p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">仪器排程工作台</h2>
            <select
              value={selectedInstrument}
              onChange={(evt) => setSelectedInstrument(evt.target.value)}
              className="border border-gray-300 rounded px-3 py-2"
            >
              {instrumentOptions.map((instrument) => (
                <option key={instrument.code} value={instrument.code}>
                  {instrument.code} — {instrument.name}
                </option>
              ))}
            </select>
          </div>

          {!instrumentQueue.length && <p className="text-sm text-gray-500">暂无待排程提案。</p>}
          {instrumentQueue.length > 0 && (
            <div className="space-y-6">
              {instrumentQueue.map((proposal) => {
                const draft = feedbackDrafts[proposal.id] || { status: 'under_assessment', payload: {} };
                return (
                  <div key={`queue-${proposal.id}`} className="border rounded-lg p-4">
                    <header className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{proposal.title}</p>
                        <p className="text-xs text-gray-500">状态：{proposal.status}</p>
                      </div>
                      <span className="text-xs font-mono bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                        阶段：{proposal.assignment?.status || '未开始'}
                      </span>
                    </header>
                    <div className="mt-3 text-sm text-gray-700">
                      <p className="font-medium">提案方提交的表单数据：</p>
                      <pre className="bg-gray-100 rounded p-3 overflow-x-auto text-xs mt-2">
                        {JSON.stringify(proposal.assignment?.form_data || {}, null, 2)}
                      </pre>
                    </div>

                    <div className="mt-4 space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">排程状态</label>
                        <select
                          value={draft.status}
                          onChange={(evt) => handleFeedbackChange(proposal.id, 'status', evt.target.value)}
                          className="mt-1 border border-gray-300 rounded px-3 py-2"
                        >
                          <option value="under_assessment">评估中</option>
                          <option value="scheduled">已排程</option>
                          <option value="needs_revision">需修改</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">可观测窗口</label>
                        <input
                          type="text"
                          value={draft.payload?.visibility_window || ''}
                          onChange={(evt) => handleFeedbackPayloadChange(proposal.id, 'visibility_window', evt.target.value)}
                          className="mt-1 w-full border border-gray-300 rounded px-3 py-2"
                          placeholder="示例：2025-05-01 ~ 2025-05-07"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">资源占用说明</label>
                        <textarea
                          rows={3}
                          value={draft.payload?.resource_notes || ''}
                          onChange={(evt) => handleFeedbackPayloadChange(proposal.id, 'resource_notes', evt.target.value)}
                          className="mt-1 w-full border border-gray-300 rounded px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">评估备注</label>
                        <textarea
                          rows={3}
                          value={draft.comment || ''}
                          onChange={(evt) => handleFeedbackChange(proposal.id, 'comment', evt.target.value)}
                          className="mt-1 w-full border border-gray-300 rounded px-3 py-2"
                        />
                      </div>
                      <div className="flex justify-end">
                        <button
                          type="button"
                          onClick={() => submitFeedback(proposal.id)}
                          className="bg-green-600 hover:bg-green-700 text-white font-medium px-4 py-2 rounded"
                        >
                          提交排程结果
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
      </div>
          )}
          {feedbackMessage && <p className="text-sm text-gray-600">{feedbackMessage}</p>}
        </section>
      )}
    </div>
  );
}
