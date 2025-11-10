'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';

import {
  createProposal,
  getFormTemplate,
  getProposalTypes,
  listFormTemplates,
  listInstruments,
} from '@/lib/api';

const FIELD_RENDERERS = {
  text: ({ field, value, onChange }) => (
    <input
      type="text"
      id={field.name}
      name={field.name}
      required={field.required}
      value={value ?? ''}
      onChange={onChange}
      className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
    />
  ),
  number: ({ field, value, onChange }) => (
    <input
      type="number"
      id={field.name}
      name={field.name}
      required={field.required}
      value={value ?? ''}
      onChange={onChange}
      className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
    />
  ),
  textarea: ({ field, value, onChange }) => (
    <textarea
      id={field.name}
      name={field.name}
      rows={field.rows || 4}
      required={field.required}
      value={value ?? ''}
      onChange={onChange}
      className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
    />
  ),
  select: ({ field, value, onChange }) => (
    <select
      id={field.name}
      name={field.name}
      required={field.required}
      value={value ?? ''}
      onChange={onChange}
      className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
    >
      <option value="">请选择</option>
      {field.options?.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  ),
  checkbox: ({ field, value, onChange }) => (
    <input
      type="checkbox"
      id={field.name}
      name={field.name}
      checked={Boolean(value)}
      onChange={(event) =>
        onChange({
          target: {
            name: field.name,
            value: event.target.checked,
            type: 'checkbox',
          },
        })
      }
      className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
    />
  ),
  file: ({ field, onFileChange }) => (
    <input
      type="file"
      id={field.name}
      name={field.name}
      required={field.required}
      onChange={(event) => onFileChange(field.name, event.target.files?.[0] || null)}
      className="block w-full text-sm text-gray-600 file:mr-4 file:rounded-md file:border-0 file:bg-indigo-600 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-indigo-700"
    />
  ),
};

function DynamicField({ field, value, onChange, onFileChange }) {
  const Renderer = FIELD_RENDERERS[field.type] || FIELD_RENDERERS.text;
  return (
    <div key={field.name}>
      <label htmlFor={field.name} className="block text-sm font-medium text-gray-700">
        {field.label}
        {field.required && <span className="ml-1 text-red-500">*</span>}
      </label>
      <Renderer field={field} value={value} onChange={onChange} onFileChange={onFileChange} />
      {field.helpText && <p className="mt-1 text-xs text-gray-500">{field.helpText}</p>}
    </div>
  );
}

const emptyPhaseState = () => ({
  meta: {},
  attachments: {},
});

export default function NewProposalPage() {
  const router = useRouter();

  const [proposalTypes, setProposalTypes] = useState([]);
  const [instruments, setInstruments] = useState([]);
  const [generalTemplate, setGeneralTemplate] = useState(null);
  const [instrumentTemplates, setInstrumentTemplates] = useState({});

  const [selectedProposalType, setSelectedProposalType] = useState('');
  const [selectedInstruments, setSelectedInstruments] = useState([]);
  const [phaseState, setPhaseState] = useState({ phase1: emptyPhaseState() });
  const [instrumentState, setInstrumentState] = useState({});

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function bootstrap() {
      setError('');
      try {
        const [types, instrumentList, templates] = await Promise.all([
          getProposalTypes(),
          listInstruments(),
          listFormTemplates({ phase: 'phase1' }),
        ]);
        setProposalTypes(types);
        setInstruments(instrumentList);

        const general = templates.find((tpl) => !tpl.instrument);
        if (general) {
          const detail = await getFormTemplate(general.id);
          setGeneralTemplate(detail.definition);
        }
      } catch (err) {
        console.error(err);
        setError(err.info?.message || '初始化失败，请稍后再试。');
      }
    }
    bootstrap();
  }, []);

  useEffect(() => {
    async function ensureInstrumentTemplate(code) {
      if (instrumentTemplates[code]) {
        return;
      }
      try {
        const list = await listFormTemplates({ instrument_code: code, phase: 'phase1' });
        if (!list.length) {
          setInstrumentTemplates((prev) => ({ ...prev, [code]: null }));
          return;
        }
        const detail = await getFormTemplate(list[0].id);
        setInstrumentTemplates((prev) => ({ ...prev, [code]: detail.definition }));
      } catch (err) {
        console.error(err);
        setInstrumentTemplates((prev) => ({ ...prev, [code]: null }));
      }
    }

    selectedInstruments.forEach((code) => {
      ensureInstrumentTemplate(code);
    });
  }, [selectedInstruments, instrumentTemplates]);

  const instrumentOptions = useMemo(
    () =>
      instruments.map((instrument) => ({
        code: instrument.code,
        name: instrument.name,
        description: instrument.description,
      })),
    [instruments],
  );

  const handlePhaseFieldChange = (phaseName, event) => {
    const { name, value, type, checked } = event.target;
    setPhaseState((prev) => {
      const phase = prev[phaseName] || emptyPhaseState();
      return {
        ...prev,
        [phaseName]: {
          ...phase,
          meta: {
            ...phase.meta,
            [name]: type === 'checkbox' ? checked : value,
          },
        },
      };
    });
  };

  const handlePhaseFileChange = (phaseName, fieldName, file) => {
    setPhaseState((prev) => {
      const phase = prev[phaseName] || emptyPhaseState();
      return {
        ...prev,
        [phaseName]: {
          ...phase,
          attachments: {
            ...phase.attachments,
            [fieldName]: file
              ? { name: file.name, size: file.size, type: file.type }
              : null,
          },
        },
      };
    });
  };

  const toggleInstrument = (code) => {
    setSelectedInstruments((prev) =>
      prev.includes(code) ? prev.filter((item) => item !== code) : [...prev, code],
    );
    setInstrumentState((prev) => {
      if (prev[code]) {
        const clone = { ...prev };
        delete clone[code];
        return clone;
      }
      return { ...prev, [code]: { form: {}, attachments: {} } };
    });
  };

  const handleInstrumentFieldChange = (instrumentCode, event) => {
    const { name, value, type, checked } = event.target;
    setInstrumentState((prev) => {
      const entry = prev[instrumentCode] || { form: {}, attachments: {} };
      return {
        ...prev,
        [instrumentCode]: {
          ...entry,
          form: {
            ...entry.form,
            [name]: type === 'checkbox' ? checked : value,
          },
        },
      };
    });
  };

  const handleInstrumentFileChange = (instrumentCode, fieldName, file) => {
    setInstrumentState((prev) => {
      const entry = prev[instrumentCode] || { form: {}, attachments: {} };
      return {
        ...prev,
        [instrumentCode]: {
          ...entry,
          attachments: {
            ...entry.attachments,
            [fieldName]: file ? { name: file.name, size: file.size, type: file.type } : null,
          },
        },
      };
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    if (!selectedProposalType) {
      setError('请选择提案类型。');
      return;
    }
    if (!selectedInstruments.length) {
      setError('请至少选择一个仪器。');
      return;
    }

    const phase1 = phaseState.phase1 || emptyPhaseState();
    const payload = {
      title: phase1.meta.title || '',
      abstract: phase1.meta.abstract || '',
      proposal_type_id: selectedProposalType,
      meta: phase1.meta,
      phase_payload: {
        phase1: {
          status: 'submitted',
          data: phase1.meta,
          attachments: phase1.attachments,
        },
      },
      instruments: selectedInstruments.map((code) => ({
        instrument_code: code,
        status: 'submitted',
        form_data: instrumentState[code]?.form || {},
        attachments: instrumentState[code]?.attachments || {},
      })),
    };

    setLoading(true);
    try {
      const result = await createProposal(payload);
      setSuccess(`提案创建成功（ID: ${result.id}）。系统将通知各仪器进行排程。`);
      setTimeout(() => router.push('/dashboard'), 2000);
    } catch (err) {
      console.error(err);
      setError(err.info?.message || '提案提交失败，请检查填写内容。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl py-10">
      <h1 className="text-3xl font-bold text-gray-900">提交 CSST Phase-1 提案</h1>
      <p className="mt-2 text-sm text-gray-500">
        Phase-1 聚焦科学与观测需求。选择仪器并填写各自表单，提交后系统会将提案分发给仪器团队排程。
      </p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-10">
        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-800">1. 基本信息</h2>
          <div className="mt-4 grid gap-6 md:grid-cols-2">
            <div>
              <label htmlFor="proposal_type" className="block text-sm font-medium text-gray-700">
                提案类型
              </label>
              <select
                id="proposal_type"
                required
                value={selectedProposalType}
                onChange={(event) => setSelectedProposalType(event.target.value)}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
              >
                <option value="">请选择提案类型</option>
                {proposalTypes.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                提案标题
              </label>
              <input
                id="title"
                name="title"
                required
                value={phaseState.phase1?.meta?.title || ''}
                onChange={(event) => handlePhaseFieldChange('phase1', event)}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
              />
            </div>
          </div>
          <div className="mt-4">
            <label htmlFor="abstract" className="block text-sm font-medium text-gray-700">
              摘要
            </label>
            <textarea
              id="abstract"
              name="abstract"
              rows={4}
              value={phaseState.phase1?.meta?.abstract || ''}
              onChange={(event) => handlePhaseFieldChange('phase1', event)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
            />
          </div>

          {generalTemplate && (
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {generalTemplate.fields
                .filter((field) => !['title', 'abstract'].includes(field.name))
                .map((field) => (
                  <DynamicField
                    key={field.name}
                    field={field}
                    value={phaseState.phase1?.meta?.[field.name]}
                    onChange={(event) => handlePhaseFieldChange('phase1', event)}
                    onFileChange={(fieldName, file) => handlePhaseFileChange('phase1', fieldName, file)}
                  />
                ))}
            </div>
          )}
        </section>

        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-800">2. 选择仪器并填写观测需求</h2>
          <p className="mt-2 text-sm text-gray-500">
            支持多仪器联合提案。每个仪器使用自定义表单定义观测参数。附件目前以元数据形式保存，后续版本将对接文件上传服务。
          </p>

          <div className="mt-4 flex flex-wrap gap-3">
            {instrumentOptions.map((instrument) => {
              const selected = selectedInstruments.includes(instrument.code);
              return (
                <button
                  key={instrument.code}
                  type="button"
                  onClick={() => toggleInstrument(instrument.code)}
                  className={`rounded-md border px-3 py-2 text-left shadow-sm transition ${
                    selected
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                      : 'border-gray-300 hover:border-indigo-300'
                  }`}
                >
                  <span className="font-medium">{instrument.name}</span>
                  <span className="ml-2 text-xs text-gray-500">{instrument.code}</span>
                  {instrument.description && (
                    <span className="mt-1 block text-xs text-gray-400">{instrument.description}</span>
                  )}
                </button>
              );
            })}
          </div>

          <div className="mt-6 space-y-6">
            {selectedInstruments.map((code) => {
              const template = instrumentTemplates[code];
              const instrument = instrumentOptions.find((item) => item.code === code);
              const entry = instrumentState[code] || { form: {}, attachments: {} };
              return (
                <div key={code} className="rounded-md border border-gray-200 p-5 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-800">
                    {instrument?.name || code} — Phase-1 表单
                  </h3>
                  {template ? (
                    <div className="mt-4 space-y-4">
                      {template.fields.map((field) => (
                        <DynamicField
                          key={field.name}
                          field={field}
                          value={entry.form[field.name]}
                          onChange={(event) => handleInstrumentFieldChange(code, event)}
                          onFileChange={(fieldName, file) => handleInstrumentFileChange(code, fieldName, file)}
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="mt-4 text-sm text-gray-500">
                      暂无该仪器的模板定义。请联系管理员在工作流配置中添加表单。
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {error && <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
        {success && (
          <div className="rounded-md border border-green-200 bg-green-50 p-4 text-sm text-green-700">{success}</div>
        )}

        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-indigo-600 px-6 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:bg-indigo-300"
          >
            {loading ? '提交中…' : '提交 Phase-1'}
          </button>
        </div>
      </form>
    </div>
  );
}
