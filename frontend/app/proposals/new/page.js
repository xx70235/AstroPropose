'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getFormTemplate, createProposal } from '@/lib/api';

const DynamicForm = ({ template }) => {
  const [formData, setFormData] = useState({});

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const renderField = (field) => {
    const commonProps = {
      id: field.name,
      name: field.name,
      required: field.required,
      onChange: handleChange,
      className: "w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500",
    };

    switch (field.type) {
      case 'textarea':
        return <textarea {...commonProps} rows="4"></textarea>;
      case 'number':
        return <input type="number" {...commonProps} />;
      case 'text':
      default:
        return <input type="text" {...commonProps} />;
    }
  };
  
  // This function will be passed to the parent component
  const getFormData = () => {
    // The title is a special case as it's part of the main Proposal model
    const { title, ...data } = formData;
    return { title, data };
  };

  // Expose the getFormData function to the parent via a ref or callback
  // For simplicity, we'll rely on the parent to manage the form state via props if needed,
  // but here we make it self-contained and expose the data on submit.
  // This component is now implicitly tied to its parent's submit button.

  return (
    <div className="space-y-4">
      {template.fields.map((field) => (
        <div key={field.name}>
          <label htmlFor={field.name} className="block text-sm font-medium text-gray-700">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {renderField(field)}
        </div>
      ))}
    </div>
  );
};


export default function NewProposalPage() {
  const [template, setTemplate] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const router = useRouter();
  
  // A ref to hold the form data from the child component
  const formRef = React.useRef();


  useEffect(() => {
    const fetchTemplate = async () => {
      try {
        // In a real app, you'd have a way to select which form to use.
        // Here, we'll hardcode fetching template with ID 1.
        const data = await getFormTemplate(1);
        setTemplate(data.definition);
      } catch (err) {
        setError('Failed to load proposal form template.');
        console.error(err);
      }
    };
    fetchTemplate();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // This is a simplified way to get data from a child.
    // A more robust solution might use a state management library or context.
    const formElements = e.target.elements;
    const payload = { title: formElements.title.value, data: {} };
    template.fields.forEach(field => {
        if (field.name !== 'title') {
            payload.data[field.name] = formElements[field.name].value;
        }
    });

    try {
      const result = await createProposal(payload);
      setSuccess(`Proposal created successfully with ID: ${result.id}`);
      setTimeout(() => router.push('/dashboard'), 2000);
    } catch (err) {
      setError(err.info?.message || 'Failed to create proposal.');
      console.error(err);
    }
  };

  if (!template) {
    return <div>Loading form...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Create New Proposal</h1>
      <form onSubmit={handleSubmit} className="p-8 bg-white rounded-lg shadow-md space-y-6">
        {template.fields.map((field) => (
          <div key={field.name}>
            <label htmlFor={field.name} className="block text-sm font-medium text-gray-700">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            {field.type === 'textarea' ? (
              <textarea id={field.name} name={field.name} required={field.required} rows="4" className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
            ) : (
              <input type={field.type} id={field.name} name={field.name} required={field.required} className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
            )}
          </div>
        ))}

        {error && <p className="text-sm text-red-600">{error}</p>}
        {success && <p className="text-sm text-green-600">{success}</p>}

        <div className="pt-4">
          <button
            type="submit"
            className="w-full px-4 py-2 font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Submit Proposal
          </button>
        </div>
      </form>
    </div>
  );
}
