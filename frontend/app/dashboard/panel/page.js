'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import {
  getCurrentUser,
  getProposals,
  listProposalTransitions,
  triggerProposalTransition,
} from '@/lib/api';

export default function PanelChairDashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [transitionMap, setTransitionMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState('');

  const refreshProposals = async () => {
    const data = await getProposals();
    setProposals(data);
  };

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
      router.push('/login');
      return;
    }

    const init = async () => {
      try {
        const me = await getCurrentUser();
        setUser(me);
        if (!me.roles.includes('Panel Chair') && !me.roles.includes('Admin')) {
          router.push('/dashboard');
          return;
        }
        await refreshProposals();
      } catch (err) {
        console.error(err);
        setError('Unable to fetch proposal information. You may need to log in again.');
        if (err.status === 401) {
          localStorage.removeItem('token');
          router.push('/login');
        }
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [router]);

  const handleLoadTransitions = async (proposalId) => {
    setTransitionMap((prev) => ({
      ...prev,
      [proposalId]: { ...(prev[proposalId] || {}), loading: true },
    }));
    try {
      const data = await listProposalTransitions(proposalId);
      setTransitionMap((prev) => ({
        ...prev,
        [proposalId]: { loading: false, items: data.transitions || [] },
      }));
    } catch (err) {
      console.error(err);
      setStatusMessage(err.info?.message || 'Failed to fetch available actions');
      setTransitionMap((prev) => ({
        ...prev,
        [proposalId]: { loading: false, items: [] },
      }));
    }
  };

  const handleTransition = async (proposalId, transitionName) => {
    try {
      await triggerProposalTransition(proposalId, { transition: transitionName });
      setStatusMessage(`Proposal ${proposalId} action executed: ${transitionName}`);
      await refreshProposals();
      await handleLoadTransitions(proposalId);
    } catch (err) {
      console.error(err);
      setStatusMessage(err.info?.message || 'Failed to execute action');
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold">Panel Chair Dashboard</h1>
        <p className="text-sm text-gray-600">
          View all proposals' phase status, instrument scheduling feedback, and execute workflow actions.
        </p>
      </header>

      {error && <p className="text-red-500 bg-red-100 p-3 rounded">{error}</p>}
      {statusMessage && <p className="text-sm text-gray-600">{statusMessage}</p>}

      <div className="space-y-4">
        {proposals.map((proposal) => {
          const transitionState = transitionMap[proposal.id] || { items: [], loading: false };
          return (
            <div key={proposal.id} className="bg-white shadow rounded-lg p-6 space-y-4">
              <header className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">{proposal.title}</h2>
                  <p className="text-xs text-gray-500">Status: {proposal.status}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleLoadTransitions(proposal.id)}
                  className="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  {transitionState.loading ? 'Loading...' : 'Refresh Available Actions'}
                </button>
              </header>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm text-gray-700">
                <div>
                  <h3 className="font-medium">Phases</h3>
                  <ul className="list-disc list-inside">
                    {proposal.phases.map((phase) => (
                      <li key={`${proposal.id}-phase-${phase.phase}`}>
                        {phase.phase}: {phase.status}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="font-medium">Instrument Progress</h3>
                  <ul className="list-disc list-inside">
                    {proposal.instruments.map((instrument) => (
                      <li key={`${proposal.id}-${instrument.instrument}`}>
                        {instrument.instrument}: {instrument.status}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="font-medium">Scheduling Feedback Overview</h3>
                  <pre className="bg-gray-100 rounded p-3 text-xs overflow-x-auto">
                    {JSON.stringify(
                      proposal.instruments.reduce((acc, inst) => {
                        acc[inst.instrument] = inst.status;
                        return acc;
                      }, {}),
                      null,
                      2
                    )}
                  </pre>
                </div>
              </div>

              <div className="border-t pt-3">
                <h3 className="text-sm font-medium text-gray-700">Available Workflow Actions</h3>
                {transitionState.items.length ? (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {transitionState.items.map((transition) => (
                      <button
                        key={`${proposal.id}-${transition.name}`}
                        type="button"
                        onClick={() => handleTransition(proposal.id, transition.name)}
                        className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
                      >
                        {transition.name}
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500">No available actions, or not yet loaded.</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
