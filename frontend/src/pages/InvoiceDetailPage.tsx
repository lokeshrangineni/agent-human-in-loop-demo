import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  Play,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  XOctagon,
  Trash2,
  ThumbsUp,
  Clock,
  Pencil,
  Check,
  X,
  ScrollText,
  MessageSquarePlus,
  Send,
  Eye,
  XCircle,
} from 'lucide-react';
import { api } from '../services/api';
import type { Invoice, UserInfo, FeedbackItem } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { formatLabel, confidenceColor, formatDate } from '../lib/utils';

interface Props {
  currentUser: UserInfo;
}

interface EditingCell {
  section: 'header' | 'summary' | 'line';
  key: string;
  rowIdx?: number;
}

// Statuses where users may edit extracted fields
const EDITABLE_STATUSES = new Set(['validated', 'pending_review']);

export function InvoiceDetailPage({ currentUser }: Props) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Inline editing
  const [editingCell, setEditingCell] = useState<EditingCell | null>(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Prompt feedback state
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackPromptKey, setFeedbackPromptKey] = useState<'extraction_system' | 'validation_system'>('extraction_system');
  const [feedbackText, setFeedbackText] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState(false);

  // Existing prompt suggestions for this invoice
  const [promptFeedbackList, setPromptFeedbackList] = useState<FeedbackItem[]>([]);

  const isAdmin = currentUser.role === 'admin';
  const isOwner = invoice?.uploaded_by === currentUser.id;
  const canEdit = !!invoice && EDITABLE_STATUSES.has(invoice.status) && (isAdmin || isOwner);

  const loadInvoice = () => {
    if (!id) return;
    setLoading(true);
    api.getInvoice(id)
      .then(setInvoice)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const loadFeedback = () => {
    if (!id) return;
    api.listFeedbackForInvoice(id)
      .then((items) => {
        const promptKeys = new Set(['extraction_system', 'validation_system']);
        setPromptFeedbackList(items.filter((f) => f.field_name && promptKeys.has(f.field_name)));
      })
      .catch(console.error);
  };

  useEffect(loadInvoice, [id]);
  useEffect(loadFeedback, [id]);

  // Focus input when editing starts
  useEffect(() => {
    if (editingCell) inputRef.current?.focus();
  }, [editingCell]);

  const startEdit = (cell: EditingCell, currentValue: string) => {
    setEditingCell(cell);
    setEditValue(currentValue);
  };

  const cancelEdit = () => {
    setEditingCell(null);
    setEditValue('');
  };

  const commitEdit = async () => {
    if (!editingCell || !id || !invoice?.extraction_result) return;
    setSaving(true);
    try {
      let updates: Parameters<typeof api.updateInvoiceFields>[1] = {};

      if (editingCell.section === 'header') {
        updates = { header_fields: { [editingCell.key]: editValue } };
      } else if (editingCell.section === 'summary') {
        updates = { summary_fields: { [editingCell.key]: editValue } };
      } else if (editingCell.section === 'line' && editingCell.rowIdx !== undefined) {
        // Build full line items list with one cell changed
        const items = invoice.extraction_result.line_items.map((row, i) => {
          const plain: Record<string, unknown> = {};
          for (const [col, field] of Object.entries(row)) {
            plain[col] = i === editingCell.rowIdx && col === editingCell.key
              ? editValue
              : field.value;
          }
          return plain;
        });
        updates = { line_items: items };
      }

      const updated = await api.updateInvoiceFields(id, updates);
      setInvoice(updated);
      setEditingCell(null);
      setEditValue('');
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') commitEdit();
    if (e.key === 'Escape') cancelEdit();
  };

  const handleProcess = async () => {
    if (!id) return;
    setProcessing(true);
    try {
      await api.processInvoice(id);
      loadInvoice();
    } catch (err) {
      console.error(err);
    } finally {
      setProcessing(false);
    }
  };

  const handleAction = async (action: string) => {
    if (!id) return;
    setActionLoading(action);
    try {
      await api.invoiceAction(id, action);
      loadInvoice();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    setDeleting(true);
    try {
      await api.deleteInvoice(id);
      navigate('/invoices');
    } catch (err) {
      console.error(err);
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!feedbackText.trim() || !id) return;
    setSubmittingFeedback(true);
    try {
      await api.submitFeedback({
        invoice_id: id,
        field_name: feedbackPromptKey,
        feedback_text: feedbackText,
      });
      setFeedbackText('');
      setShowFeedbackForm(false);
      setFeedbackSent(true);
      loadFeedback();
      setTimeout(() => setFeedbackSent(false), 5000);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!invoice) {
    return <div className="text-center py-24 text-gray-500">Invoice not found.</div>;
  }

  const ext = invoice.extraction_result;
  const val = invoice.validation_result;

  // ── Inline edit cell renderer ──────────────────────────────────────────────
  const renderEditableValue = (
    cell: EditingCell,
    value: unknown,
    confidence: number,
    isBold = false
  ) => {
    const isEditing =
      editingCell?.section === cell.section &&
      editingCell?.key === cell.key &&
      editingCell?.rowIdx === cell.rowIdx;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const isUserEdited = (invoice.extraction_result as any)
      ?.[(cell.section === 'line' ? 'line_items' : `${cell.section}_fields`)]
      ?.[cell.rowIdx ?? cell.key]
      ?.[cell.section === 'line' ? cell.key : undefined]
      ?.user_edited;

    if (isEditing) {
      return (
        <div className="flex flex-1 items-center gap-1">
          <input
            ref={inputRef}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 rounded border border-blue-400 px-2 py-0.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={commitEdit}
            disabled={saving}
            className="rounded p-1 text-green-600 hover:bg-green-50 disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
          </button>
          <button onClick={cancelEdit} className="rounded p-1 text-gray-400 hover:bg-gray-100">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      );
    }

    return (
      <div className="flex flex-1 items-center gap-2 group">
        <span className={`text-sm ${isBold ? 'font-semibold' : ''} ${isUserEdited ? 'text-blue-700' : 'text-gray-900'}`}>
          {String(value ?? '—')}
        </span>
        {isUserEdited && (
          <span className="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700">
            edited
          </span>
        )}
        {canEdit && (
          <button
            onClick={() => startEdit(cell, String(value ?? ''))}
            className="ml-auto rounded p-1 text-gray-300 opacity-0 group-hover:opacity-100 hover:bg-gray-100 hover:text-gray-600 transition-opacity"
            title="Edit field"
          >
            <Pencil className="h-3.5 w-3.5" />
          </button>
        )}
        <ConfidenceBadge confidence={confidence} />
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* ── Page header ── */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="rounded-lg p-2 hover:bg-gray-100">
          <ArrowLeft className="h-5 w-5 text-gray-600" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{invoice.file_name}</h1>
          <p className="mt-1 text-sm text-gray-500">Uploaded {formatDate(invoice.created_at)}</p>
        </div>
        <StatusBadge status={invoice.status} />
        {invoice.overall_confidence != null && (
          <ConfidenceBadge confidence={invoice.overall_confidence} className="text-sm px-3 py-1" />
        )}
        {(isAdmin || isOwner) && (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="rounded-lg p-2 text-red-500 hover:bg-red-50 hover:text-red-700 transition-colors"
            title="Delete invoice"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* ── Edit hint banner ── */}
      {canEdit && (
        <div className="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm text-blue-700">
          <Pencil className="h-4 w-4 shrink-0" />
          <span>
            You can edit any extracted field — hover over a value and click the pencil icon.
            Changes are saved immediately.
          </span>
        </div>
      )}

      {/* ── Delete confirmation modal ── */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100">
                <Trash2 className="h-5 w-5 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Delete Invoice?</h3>
            </div>
            <p className="text-sm text-gray-500 mb-6">
              This will permanently delete{' '}
              <span className="font-medium text-gray-900">{invoice.file_name}</span> along with
              all extraction results, approvals, and feedback. This cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleting}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Process prompt ── */}
      {invoice.status === 'uploaded' && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-blue-700">
              This invoice has not been processed yet. Click "Process" to run extraction and
              validation.
            </p>
            <button
              onClick={handleProcess}
              disabled={processing}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {processing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              {processing ? 'Processing...' : 'Process'}
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* ── Left: extraction data ── */}
        <div className="lg:col-span-2 space-y-6">
          {ext && (
            <>
              {/* Header fields */}
              <section className="rounded-lg border border-gray-200 bg-white shadow-sm">
                <div className="border-b border-gray-200 px-6 py-4">
                  <h2 className="text-lg font-semibold text-gray-900">Header Fields</h2>
                </div>
                <div className="divide-y divide-gray-100">
                  {Object.entries(ext.header_fields).map(([key, field]) => (
                    <div
                      key={key}
                      className={`flex items-center px-6 py-3 ${confidenceColor(field.confidence)} bg-opacity-20`}
                    >
                      <span className="w-40 shrink-0 text-sm font-medium text-gray-600">
                        {formatLabel(key)}
                      </span>
                      {renderEditableValue(
                        { section: 'header', key },
                        field.value,
                        field.confidence
                      )}
                    </div>
                  ))}
                  {Object.keys(ext.header_fields).length === 0 && (
                    <p className="px-6 py-4 text-sm text-gray-500">No header fields extracted.</p>
                  )}
                </div>
              </section>

              {/* Line items */}
              {ext.line_items.length > 0 && (
                <section className="rounded-lg border border-gray-200 bg-white shadow-sm">
                  <div className="border-b border-gray-200 px-6 py-4">
                    <h2 className="text-lg font-semibold text-gray-900">
                      Line Items ({ext.line_items.length})
                    </h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-100 text-left text-xs font-medium uppercase text-gray-500">
                          {ext.line_items[0] &&
                            Object.keys(ext.line_items[0]).map((col) => (
                              <th key={col} className="px-4 py-3">
                                {formatLabel(col)}
                              </th>
                            ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {ext.line_items.map((row, rowIdx) => (
                          <tr key={rowIdx} className="hover:bg-gray-50">
                            {Object.entries(row).map(([col, field]) => {
                              const cell: EditingCell = { section: 'line', key: col, rowIdx };
                              const isEditing =
                                editingCell?.section === 'line' &&
                                editingCell?.key === col &&
                                editingCell?.rowIdx === rowIdx;

                              return (
                                <td key={col} className="px-4 py-3">
                                  {isEditing ? (
                                    <div className="flex items-center gap-1">
                                      <input
                                        ref={inputRef}
                                        value={editValue}
                                        onChange={(e) => setEditValue(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        className="w-28 rounded border border-blue-400 px-2 py-0.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                      />
                                      <button
                                        onClick={commitEdit}
                                        disabled={saving}
                                        className="rounded p-1 text-green-600 hover:bg-green-50 disabled:opacity-50"
                                      >
                                        {saving ? (
                                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                        ) : (
                                          <Check className="h-3.5 w-3.5" />
                                        )}
                                      </button>
                                      <button
                                        onClick={cancelEdit}
                                        className="rounded p-1 text-gray-400 hover:bg-gray-100"
                                      >
                                        <X className="h-3.5 w-3.5" />
                                      </button>
                                    </div>
                                  ) : (
                                    <div className="flex items-center gap-2 group">
                                      <span
                                        className={`text-sm ${
                                          (field as { user_edited?: boolean }).user_edited
                                            ? 'text-blue-700'
                                            : ''
                                        }`}
                                      >
                                        {String(field.value ?? '—')}
                                      </span>
                                      {canEdit && (
                                        <button
                                          onClick={() => startEdit(cell, String(field.value ?? ''))}
                                          className="rounded p-0.5 text-gray-300 opacity-0 group-hover:opacity-100 hover:bg-gray-100 hover:text-gray-600 transition-opacity"
                                        >
                                          <Pencil className="h-3 w-3" />
                                        </button>
                                      )}
                                      <ConfidenceBadge confidence={field.confidence} />
                                    </div>
                                  )}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              {/* Summary fields */}
              {Object.keys(ext.summary_fields).length > 0 && (
                <section className="rounded-lg border border-gray-200 bg-white shadow-sm">
                  <div className="border-b border-gray-200 px-6 py-4">
                    <h2 className="text-lg font-semibold text-gray-900">Summary</h2>
                  </div>
                  <div className="divide-y divide-gray-100">
                    {Object.entries(ext.summary_fields).map(([key, field]) => (
                      <div key={key} className="flex items-center px-6 py-3">
                        <span className="w-40 shrink-0 text-sm font-medium text-gray-600">
                          {formatLabel(key)}
                        </span>
                        {renderEditableValue(
                          { section: 'summary', key },
                          field.value,
                          field.confidence,
                          true
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Extraction notes */}
              {ext.extraction_notes.length > 0 && (
                <section className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                  <h3 className="text-sm font-semibold text-amber-800 mb-2">Extraction Notes</h3>
                  <ul className="list-disc list-inside text-sm text-amber-700 space-y-1">
                    {ext.extraction_notes.map((note, i) => (
                      <li key={i}>{note}</li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}
        </div>

        {/* ── Right: validation + actions ── */}
        <div className="space-y-6">
          {val && (
            <section className="rounded-lg border border-gray-200 bg-white shadow-sm">
              <div className="border-b border-gray-200 px-6 py-4">
                <h2 className="text-lg font-semibold text-gray-900">Validation</h2>
              </div>
              <div className="p-6 space-y-4">
                <div className="text-center">
                  <p className="text-sm text-gray-500">Recommendation</p>
                  <p className="mt-1 text-lg font-bold capitalize">
                    {val.overall_recommendation}
                  </p>
                </div>
                <div className="space-y-2">
                  {val.rules.map((rule, i) => (
                    <div
                      key={i}
                      className={`flex items-start gap-2 rounded-md p-2 text-sm ${
                        rule.passed
                          ? 'text-green-700'
                          : rule.severity === 'error'
                          ? 'bg-red-50 text-red-700'
                          : 'bg-amber-50 text-amber-700'
                      }`}
                    >
                      {rule.passed ? (
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                      ) : rule.severity === 'error' ? (
                        <XOctagon className="mt-0.5 h-4 w-4 shrink-0" />
                      ) : (
                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                      )}
                      <span>{rule.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* ═══════════════ ACTION 1: Invoice Review & Submit ═══════════════ */}
          {(invoice.status === 'validated' || invoice.status === 'pending_review') && (
            <section className="rounded-lg border-2 border-blue-200 bg-white shadow-sm p-5">
              <div className="flex items-center gap-2 mb-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">1</span>
                <h2 className="text-base font-semibold text-gray-900">Review & Submit Invoice</h2>
              </div>
              <p className="text-xs text-gray-500 mb-4">
                Check the extracted data on the left. Edit any fields that need correction,
                then submit for admin approval.
              </p>
              <button
                onClick={() => handleAction('submit')}
                disabled={!!actionLoading}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {actionLoading === 'submit' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ThumbsUp className="h-4 w-4" />
                )}
                Looks Good — Submit for Approval
              </button>
            </section>
          )}

          {/* ═══════════════ ACTION 2: Prompt Feedback ═══════════════ */}
          {(invoice.status === 'validated' || invoice.status === 'pending_review') &&
            (invoice.extraction_prompt_version != null || invoice.validation_prompt_version != null) && (
            <section className="rounded-lg border-2 border-purple-200 bg-white shadow-sm p-5">
              <div className="flex items-center gap-2 mb-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-purple-600 text-xs font-bold text-white">2</span>
                <h2 className="text-base font-semibold text-gray-900">Prompt Feedback</h2>
              </div>

              {/* Prompt versions used */}
              <div className="rounded-md bg-purple-50 p-3 mb-3">
                <p className="text-xs font-medium text-purple-800 mb-1.5">Prompt versions used for this invoice:</p>
                <dl className="space-y-1 text-xs">
                  {invoice.extraction_prompt_version != null && (
                    <div className="flex justify-between">
                      <dt className="text-purple-600">Extraction Agent</dt>
                      <dd>
                        <Link
                          to={`/prompts?key=extraction_system`}
                          className="font-semibold text-purple-900 underline decoration-purple-300 hover:text-purple-700"
                        >
                          v{invoice.extraction_prompt_version}
                        </Link>
                      </dd>
                    </div>
                  )}
                  {invoice.validation_prompt_version != null && (
                    <div className="flex justify-between">
                      <dt className="text-purple-600">Validation Agent</dt>
                      <dd>
                        <Link
                          to={`/prompts?key=validation_system`}
                          className="font-semibold text-purple-900 underline decoration-purple-300 hover:text-purple-700"
                        >
                          v{invoice.validation_prompt_version}
                        </Link>
                      </dd>
                    </div>
                  )}
                </dl>
              </div>

              <p className="text-xs text-gray-500 mb-3">
                Did the agent miss something or produce incorrect results?
                Suggest how the prompt could be improved — an admin will review it.
              </p>

              {feedbackSent && (
                <div className="flex items-center gap-2 rounded-md bg-green-50 px-3 py-2 text-xs text-green-700 mb-3">
                  <CheckCircle className="h-3 w-3" />
                  Feedback submitted — an admin will review it.
                </div>
              )}

              {showFeedbackForm ? (
                <div className="space-y-2">
                  <select
                    value={feedbackPromptKey}
                    onChange={(e) => setFeedbackPromptKey(e.target.value as 'extraction_system' | 'validation_system')}
                    className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-xs focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="extraction_system">Extraction Agent Prompt</option>
                    <option value="validation_system">Validation Agent Prompt</option>
                  </select>
                  <textarea
                    value={feedbackText}
                    onChange={(e) => setFeedbackText(e.target.value)}
                    rows={3}
                    placeholder="e.g. The extraction agent missed the PO number on this invoice…"
                    className="w-full rounded-md border border-gray-300 p-2 text-xs placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => { setShowFeedbackForm(false); setFeedbackText(''); }}
                      className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSubmitFeedback}
                      disabled={submittingFeedback || !feedbackText.trim()}
                      className="inline-flex items-center gap-1 rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700 disabled:opacity-50"
                    >
                      <Send className="h-3 w-3" />
                      {submittingFeedback ? 'Submitting…' : 'Submit Suggestion'}
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowFeedbackForm(true)}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-purple-300 px-4 py-2 text-sm font-medium text-purple-700 hover:bg-purple-50"
                >
                  <MessageSquarePlus className="h-4 w-4" />
                  Suggest Prompt Improvement
                </button>
              )}
            </section>
          )}

          {/* ═══════════════ Status: Waiting for admin (user view) ═══════════════ */}
          {invoice.status === 'pending_approval' && !isAdmin && (
            <section className="rounded-lg border border-purple-200 bg-purple-50 p-6">
              <div className="flex items-start gap-3">
                <Clock className="mt-0.5 h-5 w-5 shrink-0 text-purple-600" />
                <div>
                  <p className="text-sm font-semibold text-purple-900">Awaiting Admin Approval</p>
                  <p className="mt-1 text-xs text-purple-700">
                    You have submitted this invoice. An admin will review and approve or delete it.
                  </p>
                </div>
              </div>
            </section>
          )}

          {/* ═══════════════ Admin: Approve / Delete ═══════════════ */}
          {invoice.status === 'pending_approval' && isAdmin && (
            <section className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-1">Final Approval</h2>
              <p className="text-xs text-gray-500 mb-4">
                The user has reviewed and signed off. Approve the invoice or delete it.
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => handleAction('approve')}
                  disabled={!!actionLoading}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                >
                  {actionLoading === 'approve' ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <CheckCircle className="h-4 w-4" />
                  )}
                  Approve
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="flex w-full items-center justify-center gap-2 rounded-lg border border-red-300 px-4 py-2.5 text-sm font-medium text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Invoice
                </button>
              </div>
            </section>
          )}

          {/* ═══════════════ Final state: Approved ═══════════════ */}
          {invoice.status === 'approved' && (
            <section className="rounded-lg border border-green-200 bg-green-50 p-6">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <p className="text-sm font-semibold text-green-900">Invoice Approved</p>
              </div>
            </section>
          )}

          {/* ═══════════════ Prompts Used (always visible once processed) ═══════════════ */}
          {(invoice.extraction_prompt_version != null || invoice.validation_prompt_version != null) &&
            invoice.status !== 'validated' && invoice.status !== 'pending_review' && (
            <section className="rounded-lg border border-gray-200 bg-white shadow-sm p-4">
              <div className="flex items-center gap-2 mb-2">
                <ScrollText className="h-4 w-4 text-purple-600" />
                <h2 className="text-sm font-semibold text-gray-900">Prompts Used</h2>
              </div>
              <dl className="space-y-1.5 text-xs">
                {invoice.extraction_prompt_version != null && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Extraction Agent</dt>
                    <dd>
                      <Link
                        to={`/prompts?key=extraction_system`}
                        className="font-semibold text-purple-700 underline decoration-purple-300 hover:text-purple-900"
                      >
                        v{invoice.extraction_prompt_version}
                      </Link>
                    </dd>
                  </div>
                )}
                {invoice.validation_prompt_version != null && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Validation Agent</dt>
                    <dd>
                      <Link
                        to={`/prompts?key=validation_system`}
                        className="font-semibold text-purple-700 underline decoration-purple-300 hover:text-purple-900"
                      >
                        v{invoice.validation_prompt_version}
                      </Link>
                    </dd>
                  </div>
                )}
              </dl>
            </section>
          )}

          {/* Document info */}
          <section className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Document Info</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">File</dt>
                <dd className="text-gray-900">{invoice.file_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Pages</dt>
                <dd className="text-gray-900">{invoice.page_count || '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Uploaded by</dt>
                <dd className="text-gray-900">{invoice.uploaded_by}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Last updated</dt>
                <dd className="text-gray-900">{formatDate(invoice.updated_at)}</dd>
              </div>
            </dl>
            <a
              href={api.getInvoiceDocumentUrl(invoice.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 block text-center rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              View Original Document
            </a>
          </section>
        </div>
      </div>

      {/* ── Prompt Suggestions (full width, bottom of page) ── */}
      {promptFeedbackList.length > 0 && (
        <section className="rounded-lg border border-purple-200 bg-white shadow-sm">
          <div className="border-b border-purple-100 px-6 py-4 flex items-center gap-2">
            <MessageSquarePlus className="h-5 w-5 text-purple-600" />
            <h2 className="text-lg font-semibold text-gray-900">
              Prompt Suggestions
            </h2>
            <span className="ml-auto rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-semibold text-purple-800">
              {promptFeedbackList.length}
            </span>
          </div>
          <div className="divide-y divide-gray-100">
            {promptFeedbackList.map((fb) => {
              const promptLabel =
                fb.field_name === 'extraction_system'
                  ? 'Extraction Agent'
                  : fb.field_name === 'validation_system'
                  ? 'Validation Agent'
                  : fb.field_name ?? 'Unknown';

              const statusStyle =
                fb.status === 'pending'
                  ? 'bg-amber-100 text-amber-700'
                  : fb.status === 'reviewed'
                  ? 'bg-blue-100 text-blue-700'
                  : fb.status === 'approved'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-600';

              const handleReviewAction = async (status: string) => {
                try {
                  await api.reviewFeedback(fb.id, status);
                  loadFeedback();
                } catch (err) {
                  console.error(err);
                }
              };

              return (
                <div key={fb.id} className="px-6 py-4 flex gap-4">
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
                        {promptLabel}
                      </span>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusStyle}`}>
                        {fb.status}
                      </span>
                      <span className="text-xs text-gray-400">
                        by {fb.submitted_by} &middot; {formatDate(fb.created_at)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {fb.feedback_text}
                    </p>
                  </div>
                  {isAdmin && (
                    <div className="shrink-0 self-center flex flex-col gap-1.5">
                      {fb.field_name && (
                        <Link
                          to={`/prompts?key=${fb.field_name}`}
                          className="inline-flex items-center gap-1 rounded-md border border-purple-300 px-3 py-1.5 text-xs font-medium text-purple-700 hover:bg-purple-50"
                        >
                          <ScrollText className="h-3 w-3" />
                          Edit Prompt
                        </Link>
                      )}
                      {fb.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleReviewAction('reviewed')}
                            className="inline-flex items-center gap-1 rounded-md border border-blue-300 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50"
                          >
                            <Eye className="h-3 w-3" />
                            Mark Reviewed
                          </button>
                          <button
                            onClick={() => handleReviewAction('rejected')}
                            className="inline-flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-500 hover:bg-gray-50"
                          >
                            <XCircle className="h-3 w-3" />
                            Dismiss
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
