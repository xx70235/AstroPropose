'use client';

import { useEffect, useState } from 'react';
import { listInstruments, createInstrument, updateInstrument } from '@/lib/api';

export default function InstrumentsPage() {
  const [instruments, setInstruments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Create new instrument
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCode, setNewCode] = useState('');
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');

  // Edit instrument
  const [editingCode, setEditingCode] = useState(null);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');

  useEffect(() => {
    fetchInstruments();
  }, []);

  const fetchInstruments = async () => {
    setIsLoading(true);
    try {
      const data = await listInstruments();
      setInstruments(data);
    } catch (err) {
      setError('Failed to load instruments');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!newCode.trim() || !newName.trim()) {
      setError('Instrument code and name are required');
      return;
    }

    try {
      await createInstrument({
        code: newCode.toUpperCase(),
        name: newName,
        description: newDescription,
        is_active: true,
      });
      setSuccess(`Instrument "${newCode.toUpperCase()}" created successfully!`);
      setNewCode('');
      setNewName('');
      setNewDescription('');
      setShowCreateForm(false);
      fetchInstruments();
    } catch (err) {
      setError(err.info?.message || 'Failed to create instrument');
      console.error(err);
    }
  };

  const handleUpdate = async (code) => {
    setError('');
    setSuccess('');

    try {
      await updateInstrument(code, {
        name: editName,
        description: editDescription,
      });
      setSuccess(`Instrument "${code}" updated successfully!`);
      setEditingCode(null);
      fetchInstruments();
    } catch (err) {
      setError(err.info?.message || 'Failed to update instrument');
      console.error(err);
    }
  };

  const handleToggleActive = async (instrument) => {
    setError('');
    setSuccess('');

    try {
      await updateInstrument(instrument.code, {
        is_active: !instrument.is_active,
      });
      setSuccess(`Instrument "${instrument.code}" status updated`);
      fetchInstruments();
    } catch (err) {
      setError(err.info?.message || 'Failed to update instrument status');
      console.error(err);
    }
  };

  const startEdit = (instrument) => {
    setEditingCode(instrument.code);
    setEditName(instrument.name);
    setEditDescription(instrument.description || '');
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Instrument Management</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          {showCreateForm ? 'Cancel' : '+ Add Instrument'}
        </button>
      </div>

      <p className="text-gray-600">
        Manage the telescope's instrument list here. Instruments can be associated with form templates
        to collect instrument-specific observation parameters. This system supports any telescope and instrument configuration.
      </p>

      {error && <p className="text-red-500 bg-red-100 p-3 rounded">{error}</p>}
      {success && <p className="text-green-500 bg-green-100 p-3 rounded">{success}</p>}

      {/* Create new instrument form */}
      {showCreateForm && (
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Add New Instrument</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Instrument Code * <span className="text-gray-400">(unique identifier)</span>
                </label>
                <input
                  type="text"
                  required
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 uppercase"
                  placeholder="e.g., IFU, MCI, HSTDM"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Recommended: use short uppercase abbreviations
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Instrument Name *
                </label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="e.g., Integral Field Unit"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                rows={3}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Brief description of the instrument..."
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Create Instrument
            </button>
          </form>
        </div>
      )}

      {/* Instrument list */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Code
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  Loading...
                </td>
              </tr>
            ) : instruments.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No instruments configured. Click "Add Instrument" to get started.
                </td>
              </tr>
            ) : (
              instruments.map((instrument) => (
                <tr key={instrument.code}>
                  {editingCode === instrument.code ? (
                    // Edit mode
                    <>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {instrument.code}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        />
                      </td>
                      <td className="px-6 py-4">
                        <input
                          type="text"
                          value={editDescription}
                          onChange={(e) => setEditDescription(e.target.value)}
                          className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            instrument.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {instrument.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                        <button
                          onClick={() => handleUpdate(instrument.code)}
                          className="text-green-600 hover:text-green-900"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingCode(null)}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          Cancel
                        </button>
                      </td>
                    </>
                  ) : (
                    // Display mode
                    <>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {instrument.code}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {instrument.name}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                        {instrument.description || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            instrument.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {instrument.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                        <button
                          onClick={() => startEdit(instrument)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleToggleActive(instrument)}
                          className={
                            instrument.is_active
                              ? 'text-red-600 hover:text-red-900'
                              : 'text-green-600 hover:text-green-900'
                          }
                        >
                          {instrument.is_active ? 'Disable' : 'Enable'}
                        </button>
                      </td>
                    </>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Usage instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-800 mb-2">💡 Usage Guide</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• <strong>Instrument Code</strong>: Unique identifier, cannot be changed after creation. Use short uppercase abbreviations.</li>
          <li>• <strong>Associated Forms</strong>: When creating form templates, you can associate them with specific instruments to collect instrument-specific parameters.</li>
          <li>• <strong>General Forms</strong>: Forms not associated with any instrument apply to all proposals.</li>
          <li>• <strong>Disable Instrument</strong>: Disabled instruments will not appear in the proposal creation selection list.</li>
        </ul>
      </div>
    </div>
  );
}
