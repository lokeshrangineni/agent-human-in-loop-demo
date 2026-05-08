import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle, XCircle, Clock, ScrollText, Eye, ExternalLink } from 'lucide-react';
import { api } from '../services/api';
import type { ApprovalRequest, FeedbackItem } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { formatDate, formatLabel } from '../lib/utils';

const PROMPT_KEYS = new Set(['extraction_system', 'validation_system']);

function ApprovalCard({
  req,
  onReview,
}: {
  req: ApprovalRequest;
  onReview: (id: string, status: string) => void;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <StatusBadge status={req.status} />
            <span className="text-sm text-gray-500">Data Correction</span>
          </div>
          <p className="mt-1 text-sm text-gray-700">
            Invoice: <span className="font-mono text-xs">{req.invoice_id}</span>
          </p>
          <p className="text-sm text-gray-500">
            Requested by {req.requested_by} on {formatDate(req.created_at)}
          </p>
        </div>
        {req.status === 'pending' && (
          <div className="flex gap-2">
            <button
              onClick={() => onReview(req.id, 'approved')}
              className="inline-flex items-center gap-1 rounded-lg bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700"
            >
              <CheckCircle className="h-4 w-4" /> Approve
            </button>
            <button
              onClick={() => onReview(req.id, 'rejected')}
              className="inline-flex items-center gap-1 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
            >
              <XCircle className="h-4 w-4" /> Reject
            </button>
          </div>
        )}
      </div>
      <div className="mt-4 rounded-md bg-gray-50 p-3">
        <p className="text-xs font-medium text-gray-500 mb-1">Proposed Changes</p>
        <pre className="text-xs text-gray-700 whitespace-pre-wrap">
          {JSON.stringify(req.proposed_changes, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function PromptFeedbackCard({
  fb,
  onReview,
}: {
  fb: FeedbackItem;
  onReview: (id: string, status: string) => void;
}) {
  const promptKey = fb.field_name!;

  return (
    <div className="rounded-lg border border-purple-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0 space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={fb.status} />
            <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
              <ScrollText className="h-3 w-3" />
              {formatLabel(promptKey)} Prompt
            </span>
          </div>
          <p className="text-sm text-gray-900">{fb.feedback_text}</p>
          <p className="text-xs text-gray-400">
            By {fb.submitted_by}
            {fb.invoice_id && (
              <>
                {' · '}
                <Link
                  to={`/invoices/${fb.invoice_id}`}
                  className="inline-flex items-center gap-0.5 text-blue-600 hover:text-blue-800"
                >
                  <ExternalLink className="h-3 w-3" />
                  invoice
                </Link>
              </>
            )}
            {' · '}{formatDate(fb.created_at)}
          </p>
        </div>

        <div className="shrink-0 flex flex-col gap-2 items-end">
          <Link
            to={`/prompts?key=${promptKey}`}
            className="inline-flex items-center gap-1 rounded-lg border border-purple-300 bg-purple-50 px-3 py-1.5 text-xs font-medium text-purple-700 hover:bg-purple-100"
          >
            <ScrollText className="h-3.5 w-3.5" />
            Edit Prompt
          </Link>
          {fb.status === 'pending' && (
            <div className="flex gap-2">
              <button
                onClick={() => onReview(fb.id, 'reviewed')}
                className="inline-flex items-center gap-1 rounded-lg border border-blue-300 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50"
              >
                <Eye className="h-3.5 w-3.5" /> Reviewed
              </button>
              <button
                onClick={() => onReview(fb.id, 'rejected')}
                className="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-500 hover:bg-gray-50"
              >
                <XCircle className="h-3.5 w-3.5" /> Dismiss
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [promptFeedback, setPromptFeedback] = useState<FeedbackItem[]>([]);
  const [loadingApprovals, setLoadingApprovals] = useState(true);
  const [loadingFeedback, setLoadingFeedback] = useState(true);
  const [filter, setFilter] = useState<string>('pending');

  const loadApprovals = () => {
    setLoadingApprovals(true);
    api.listApprovals(filter || undefined)
      .then(setApprovals)
      .catch(console.error)
      .finally(() => setLoadingApprovals(false));
  };

  const loadFeedback = () => {
    setLoadingFeedback(true);
    api.listFeedback(filter || undefined)
      .then((all) => setPromptFeedback(all.filter((fb) => fb.field_name != null && PROMPT_KEYS.has(fb.field_name))))
      .catch(console.error)
      .finally(() => setLoadingFeedback(false));
  };

  useEffect(() => {
    loadApprovals();
    loadFeedback();
  }, [filter]);

  const handleApprovalReview = async (id: string, status: string) => {
    try {
      await api.reviewApproval(id, status);
      loadApprovals();
    } catch (err) {
      console.error(err);
    }
  };

  const handleFeedbackReview = async (id: string, status: string) => {
    try {
      await api.reviewFeedback(id, status);
      loadFeedback();
    } catch (err) {
      console.error(err);
    }
  };

  const loading = loadingApprovals || loadingFeedback;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Approval Queue</h1>
        <p className="mt-1 text-sm text-gray-500">
          Review data correction requests and prompt feedback from users.
        </p>
      </div>

      <div className="flex gap-2">
        {['pending', 'approved', 'rejected', ''].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              filter === f ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {f || 'All'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : (
        <div className="space-y-8">
          <div className="space-y-4">
            <h2 className="text-base font-semibold text-gray-700">
              Data Corrections
              {approvals.length > 0 && (
                <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                  {approvals.length}
                </span>
              )}
            </h2>
            {approvals.length === 0 ? (
              <div className="rounded-lg border border-gray-200 bg-white py-8 text-center text-gray-500">
                <Clock className="mx-auto mb-2 h-7 w-7" />
                <p className="text-sm">No {filter} data correction requests.</p>
              </div>
            ) : (
              approvals.map((req) => (
                <ApprovalCard key={req.id} req={req} onReview={handleApprovalReview} />
              ))
            )}
          </div>

          <div className="space-y-4">
            <h2 className="text-base font-semibold text-gray-700">
              Prompt Feedback
              {promptFeedback.length > 0 && (
                <span className="ml-2 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
                  {promptFeedback.length}
                </span>
              )}
            </h2>
            {promptFeedback.length === 0 ? (
              <div className="rounded-lg border border-gray-200 bg-white py-8 text-center text-gray-500">
                <ScrollText className="mx-auto mb-2 h-7 w-7" />
                <p className="text-sm">No {filter} prompt feedback.</p>
              </div>
            ) : (
              promptFeedback.map((fb) => (
                <PromptFeedbackCard key={fb.id} fb={fb} onReview={handleFeedbackReview} />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
