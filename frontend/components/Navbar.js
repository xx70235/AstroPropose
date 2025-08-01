'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const Navbar = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      setIsLoggedIn(!!token);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    router.push('/login');
  };

  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-xl font-bold">AstroPropose</Link>
        <div>
          <Link href="/dashboard" className="px-3 py-2 rounded hover:bg-gray-700">Dashboard</Link>
          <Link href="/admin/workflows" className="px-3 py-2 rounded hover:bg-gray-700">Admin</Link>
          {isLoggedIn ? (
            <button onClick={handleLogout} className="px-3 py-2 rounded hover:bg-gray-700">Logout</button>
          ) : (
            <Link href="/login" className="px-3 py-2 rounded hover:bg-gray-700">Login</Link>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
