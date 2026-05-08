import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Save,
  RotateCcw,
  CheckCircle,
  ScrollText,
  Clock,
  Loader2,
  X,
  MessageSquarePlus,
  Eye,
  XCircle,
  ExternalLink,
} from 'lucide-react';
import { api } from '../services/api';
import type { PromptDetail, PromptVersion, FeedbackItem, UserInfo } from '../types';
import { formatDate } from '../lib/utils';

interface Props {
  currentUser: UserInfo;
}

const PROMPT_KEYS = ['extraction_system', 'validation_system'] as const;

const PROMPT_LABELS: Record<string, string> = {
  extraction_system: 'Extraction Agent',
  validation_system: 'Validation Agent',
};

const PROMPT_DESCRIPTIONS: Record<string, string> = {
  extraction_system:
    'Controls how the extraction agent reads invoices and produces structured data with confidence scores.',
  validation_system:
    'Controls how the validation agent checks extracted data against business rules.',
};

export function PromptsPage({ currentUser }: Props) {
  const [searchParams] = useSearchParams();
  const initialKey = PROMPT_KEYS.includes(searchParams.get('key') as typeof PROMPT_KEYS[number])
    ? searchParams.get('key')!
    : 'extraction_system';
  const [selectedKey, setSelectedKey] = useState<string>(initialKey);
  const [detail, setDetail] = useState<PromptDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const [editContent, setEditContent] = useState('');
  const [changeSummary, setChangeSummary] = useState('');
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [previewVersion, setPreviewVersion] = useState<PromptVersion | null>(null);

  const [feedbackList, setFeedbackList] = useState<FeedbackItem[]>([]);

  const loadPrompt = (key: string) => {
    setLoading(true);
    setError(null);
    setPreviewVersion(null);
    api.getPrompt(key)
      .then((d) => {
        setDetail(d);
        setEditContent(d.active_content);
        setDirty(false);
        setChangeSummary('');
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const loadFeedback = () => {
    api.listFeedback()
      .then((items) => {
        setFeedbackList(
          items.filter(
            (f) => f.field_name === selectedKey && f.status === 'pending'
          )
        );
      })
      .catch(console.error);
  };

  useEffect(() => {
    loadPrompt(selectedKey);
    loadFeedback();
  }, [selectedKey]);

  const handleContentChange = (value: string) => {
    setEditContent(value);
    setDirty(value !== detail?.active_content);
  };

  const handleSave = async () => {
    if (!changeSummary.trim()) {
      setError('Please describe what you changed and why.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.updatePrompt(selectedKey, editContent, changeSummary);
      loadPrompt(selectedKey);
      setSuccess('Prompt saved as new active version.');
      setTimeout(() => setSuccess(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleActivate = async (version: PromptVersion) => {
    setError(null);
    try {
      await api.activatePromptVersion(selectedKey, version.id);
      loadPrompt(selectedKey);
      setSuccess(`Activated v${version.version} as the new active version.`);
      setTimeout(() => setSuccess(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Activation failed');
    }
  };

  const handleDiscard = () => {
    if (detail) {
      setEditContent(detail.active_content);
      setDirty(false);
      setChangeSummary('');
    }
  };

  const handleReviewFeedback = async (fbId: string, status: string) => {
    try {
      await api.reviewFeedback(fbId, status);
      loadFeedback();
    } catch (err) {
      console.error(err);
    }
  };

  if (currentUser.role !== 'admin') {
    return (
      <div className="text-center py-24 text-gray-500">
        Only admins can access prompt management.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Agent Prompts</h1>
        <p className="mt-1 text-sm text-gray-500">
          Edit the system prompts used by the extraction and validation agents.
          Each edit creates a new version. You can activate any previous version at any time.
        </p>
      </div>

      {/* Prompt selector tabs */}
      <div className="flex gap-2">
        {Object.entries(PROMPT_LABELS).map(([key, label]) => (
          <button
            key={key}
            onClick={() => {
              if (dirty && !confirm('You have unsaved changes. Switch anyway?')) return;
              setSelectedKey(key);
            }}
            className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
              selectedKey === key
                ? 'bg-purple-100 text-purple-800 border border-purple-300'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            <ScrollText className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-purple-600 border-t-transparent" />
        </div>
      ) : detail ? (
        <>
          {/* Main grid: editor + version history */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* ── Left: Editor (2/3 width) ── */}
            <div className="lg:col-span-2 space-y-4">
              {/* Info bar */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {PROMPT_LABELS[selectedKey]}
                  </h2>
                  <p className="text-xs text-gray-500">
                    {PROMPT_DESCRIPTIONS[selectedKey]}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-purple-100 px-3 py-1 text-xs font-semibold text-purple-800">
                    Active: v{detail.active_version?.version}
                  </span>
                  <span className="text-xs text-gray-400">
                    {detail.versions.length} version{detail.versions.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {/* Success / error */}
              {success && (
                <div className="flex items-center gap-2 rounded-lg bg-green-50 border border-green-200 px-4 py-2.5 text-sm text-green-700">
                  <CheckCircle className="h-4 w-4 shrink-0" /> {success}
                </div>
              )}
              {error && (
                <div className="flex items-center justify-between rounded-lg bg-red-50 border border-red-200 px-4 py-2.5 text-sm text-red-700">
                  <span>{error}</span>
                  <button onClick={() => setError(null)}><X className="h-4 w-4" /></button>
                </div>
              )}

              {/* Editor textarea */}
              <div className="space-y-3">
                <div className="relative">
                  <textarea
                    value={editContent}
                    onChange={(e) => handleContentChange(e.target.value)}
                    rows={28}
                    spellCheck={false}
                    className="w-full rounded-lg border border-gray-300 bg-white p-4 font-mono text-sm leading-relaxed text-gray-800 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200 resize-y min-h-[400px]"
                  />
                  {dirty && (
                    <span className="absolute right-3 top-3 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700">
                      Unsaved changes
                    </span>
                  )}
                </div>

                {/* Save controls */}
                <div className="flex items-end gap-3">
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Change summary (required)
                    </label>
                    <input
                      type="text"
                      value={changeSummary}
                      onChange={(e) => setChangeSummary(e.target.value)}
                      placeholder="What did you change and why?"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm placeholder-gray-400 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                  </div>
                  <button
                    onClick={handleDiscard}
                    disabled={!dirty}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-30"
                  >
                    Discard
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving || !dirty || !changeSummary.trim()}
                    className="inline-flex items-center gap-2 rounded-lg bg-purple-600 px-5 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                    {saving ? 'Saving...' : 'Save New Version'}
                  </button>
                </div>
              </div>
            </div>

            {/* ── Right: Version history (1/3 width) ── */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                <Clock className="h-4 w-4 text-gray-500" />
                Version History
              </h3>

              <div className="space-y-2 max-h-[700px] overflow-y-auto pr-1">
                {detail.versions.map((v) => {
                  const isActive = !!v.is_active;
                  const isPreviewing = previewVersion?.id === v.id;

                  return (
                    <div
                      key={v.id}
                      className={`rounded-lg border p-3 transition-colors cursor-pointer ${
                        isActive
                          ? 'border-purple-300 bg-purple-50'
                          : isPreviewing
                          ? 'border-blue-300 bg-blue-50'
                          : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        if (!isActive) {
                          setPreviewVersion(isPreviewing ? null : v);
                        }
                      }}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-gray-800">v{v.version}</span>
                          {isActive && (
                            <span className="rounded-full bg-purple-200 px-2 py-0.5 text-[10px] font-semibold text-purple-800">
                              Active
                            </span>
                          )}
                        </div>
                        {!isActive && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (confirm(`Activate v${v.version} as the new active version?`)) {
                                handleActivate(v);
                              }
                            }}
                            className="inline-flex items-center gap-1 rounded-md bg-purple-600 px-2.5 py-1 text-[11px] font-medium text-white hover:bg-purple-700"
                          >
                            <RotateCcw className="h-3 w-3" />
                            Activate
                          </button>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-2">{v.change_summary}</p>
                      <p className="mt-1 text-[10px] text-gray-400">
                        {v.created_by} &middot; {formatDate(v.created_at)}
                      </p>
                    </div>
                  );
                })}
              </div>

              {/* Preview panel for non-active version */}
              {previewVersion && (
                <div className="rounded-lg border border-blue-200 bg-white p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-blue-800">
                      Preview: v{previewVersion.version}
                    </span>
                    <button
                      onClick={() => setPreviewVersion(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-md bg-gray-50 p-3 font-mono text-[11px] leading-relaxed text-gray-700">
                    {previewVersion.content}
                  </pre>
                  <button
                    onClick={() => {
                      if (confirm(`Activate v${previewVersion.version} as the new active version?`)) {
                        handleActivate(previewVersion);
                      }
                    }}
                    className="inline-flex w-full items-center justify-center gap-1 rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Activate v{previewVersion.version}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* ── Pending User Suggestions (full width, below editor) ── */}
          {feedbackList.length > 0 && (
            <section className="rounded-lg border border-purple-200 bg-white shadow-sm">
              <div className="border-b border-purple-100 px-6 py-4 flex items-center gap-2">
                <MessageSquarePlus className="h-5 w-5 text-purple-600" />
                <h2 className="text-base font-semibold text-gray-900">
                  Pending User Suggestions for {PROMPT_LABELS[selectedKey]}
                </h2>
                <span className="ml-auto rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700">
                  {feedbackList.length} pending
                </span>
              </div>
              <div className="divide-y divide-gray-100">
                {feedbackList.map((fb) => (
                  <div key={fb.id} className="px-6 py-4 flex gap-4 items-start">
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-medium text-gray-700">
                          {fb.submitted_by}
                        </span>
                        <span className="text-xs text-gray-400">
                          {formatDate(fb.created_at)}
                        </span>
                        {fb.invoice_id && (
                          <Link
                            to={`/invoices/${fb.invoice_id}`}
                            className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                          >
                            <ExternalLink className="h-3 w-3" />
                            View Invoice
                          </Link>
                        )}
                      </div>
                      <p className="text-sm text-gray-800 whitespace-pre-wrap">
                        {fb.feedback_text}
                      </p>
                    </div>
                    <div className="shrink-0 flex gap-1.5">
                      <button
                        onClick={() => handleReviewFeedback(fb.id, 'reviewed')}
                        className="inline-flex items-center gap-1 rounded-md border border-blue-300 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50"
                        title="Mark as reviewed"
                      >
                        <Eye className="h-3 w-3" />
                        Reviewed
                      </button>
                      <button
                        onClick={() => handleReviewFeedback(fb.id, 'rejected')}
                        className="inline-flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-500 hover:bg-gray-50"
                        title="Dismiss suggestion"
                      >
                        <XCircle className="h-3 w-3" />
                        Dismiss
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      ) : null}
    </div>
  );
}
