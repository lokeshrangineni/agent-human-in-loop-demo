import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { XCircle, MessageSquare, ScrollText, Eye, ExternalLink } from 'lucide-react';
import { api } from '../services/api';
import type { FeedbackItem, UserInfo } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { formatDate, formatLabel } from '../lib/utils';

interface Props {
  currentUser: UserInfo;
}

const PROMPT_LABELS: Record<string, string> = {
  extraction_system: 'Extraction Agent',
  validation_system: 'Validation Agent',
};

function FeedbackCard({
  fb,
  isAdmin,
  onReview,
}: {
  fb: FeedbackItem;
  isAdmin: boolean;
  onReview: (id: string, status: string) => void;
}) {
  const promptKey = fb.field_name;
  const promptLabel = promptKey ? PROMPT_LABELS[promptKey] ?? formatLabel(promptKey) : null;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={fb.status} />
            {promptLabel && (
              <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
                <ScrollText className="h-3 w-3" />
                {promptLabel}
              </span>
            )}
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
                  View Invoice
                </Link>
              </>
            )}
            {' · '}{formatDate(fb.created_at)}
          </p>
        </div>

        {isAdmin && (
          <div className="shrink-0 flex flex-col gap-2 items-end">
            {promptKey && (
              <Link
                to={`/prompts?key=${promptKey}`}
                className="inline-flex items-center gap-1 rounded-lg border border-purple-300 bg-purple-50 px-3 py-1.5 text-xs font-medium text-purple-700 hover:bg-purple-100"
              >
                <ScrollText className="h-3.5 w-3.5" />
                Edit Prompt
              </Link>
            )}
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
        )}
      </div>
    </div>
  );
}

export function FeedbackPage({ currentUser }: Props) {
  const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('');

  const isAdmin = currentUser.role === 'admin';

  const load = () => {
    setLoading(true);
    api.listFeedback(filter || undefined)
      .then(setFeedback)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(load, [filter]);

  const handleReview = async (id: string, status: string) => {
    try {
      await api.reviewFeedback(id, status);
      load();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Prompt Feedback</h1>
        <p className="mt-1 text-sm text-gray-500">
          {isAdmin
            ? 'User suggestions for improving agent prompts. Review and action them from the Prompts editor.'
            : 'Your submitted prompt improvement suggestions and their review status.'}
        </p>
      </div>

      <div className="flex gap-1 rounded-lg border border-gray-200 bg-white p-1 w-fit">
        {(['', 'pending', 'reviewed', 'rejected'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              filter === f ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {f === '' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          </div>
        ) : feedback.length === 0 ? (
          <div className="rounded-lg border border-gray-200 bg-white py-12 text-center text-gray-500">
            <MessageSquare className="mx-auto mb-2 h-8 w-8" />
            <p>No feedback found.</p>
          </div>
        ) : (
          feedback.map((fb) => (
            <FeedbackCard
              key={fb.id}
              fb={fb}
              isAdmin={isAdmin}
              onReview={handleReview}
            />
          ))
        )}
      </div>
    </div>
  );
}
