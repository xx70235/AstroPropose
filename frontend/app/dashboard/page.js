'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getProposals, getCurrentUser } from '@/lib/api';

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    const fetchData = async () => {
      try {
        const [userData, proposalsData] = await Promise.all([
          getCurrentUser(),
          getProposals(),
        ]);
        setUser(userData);
        setProposals(proposalsData);
      } catch (err) {
        console.error(err);
        setError('Failed to fetch data. You may be logged out.');
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

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">
        Welcome, {user ? user.username : 'Proposer'}!
      </h1>
      {error && <p className="text-red-500 bg-red-100 p-3 rounded mb-4">{error}</p>}
      <div className="bg-white shadow-md rounded p-6">
        <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-semibold">My Proposals</h2>
            <Link href="/proposals/new" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                Create New Proposal
            </Link>
        </div>
        {proposals.length > 0 ? (
          <ul className="divide-y divide-gray-200">
            {proposals.map((p) => (
              <li key={p.id} className="py-2">
                {p.title} - <span className="font-mono bg-green-100 text-green-800 text-sm font-medium mr-2 px-2.5 py-0.5 rounded">{p.status || 'Draft'}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>You have not created any proposals yet.</p>
        )}
      </div>
    </div>
  );
}
