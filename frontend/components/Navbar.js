'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getCurrentUser } from '@/lib/api';

const Navbar = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [roles, setRoles] = useState([]);
  const router = useRouter();

  useEffect(() => {
    const init = async () => {
      if (typeof window === 'undefined') {
        return;
      }
      const token = localStorage.getItem('token');
      const loggedIn = !!token;
      setIsLoggedIn(loggedIn);
      if (loggedIn) {
        try {
          const me = await getCurrentUser();
          setRoles(me.roles || []);
        } catch (err) {
          console.error(err);
          setRoles([]);
        }
      } else {
        setRoles([]);
      }
    };
    init();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    setRoles([]);
    router.push('/login');
  };

  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-xl font-bold">
          AstroPropose
        </Link>
        <div className="flex items-center gap-2">
          <Link href="/dashboard" className="px-3 py-2 rounded hover:bg-gray-700">
            Dashboard
          </Link>
          {(roles.includes('Instrument Scheduler') || roles.includes('Admin')) && (
            <Link href="/dashboard" className="px-3 py-2 rounded hover:bg-gray-700">
              Scheduler
            </Link>
          )}
          {(roles.includes('Panel Chair') || roles.includes('Admin')) && (
            <Link href="/dashboard/panel" className="px-3 py-2 rounded hover:bg-gray-700">
              Panel
            </Link>
          )}
          <Link href="/admin/workflows" className="px-3 py-2 rounded hover:bg-gray-700">
            Admin
          </Link>
          {isLoggedIn ? (
            <button onClick={handleLogout} className="px-3 py-2 rounded hover:bg-gray-700">
              Logout
            </button>
          ) : (
            <Link href="/login" className="px-3 py-2 rounded hover:bg-gray-700">
              Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
