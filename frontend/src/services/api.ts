import type {
  UserInfo,
  Invoice,
  InvoiceListItem,
  ApprovalRequest,
  FeedbackItem,
  PromptSummary,
  PromptDetail,
  PromptVersion,
} from '../types';

const BASE_URL = '/api';

function getUserId(): string {
  return localStorage.getItem('currentUserId') || 'user-john';
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': getUserId(),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Auth
  getUsers: () => request<UserInfo[]>('/auth/users'),

  // Invoices
  listInvoices: () => request<InvoiceListItem[]>('/invoices'),

  getInvoice: (id: string) => request<Invoice>(`/invoices/${id}`),

  uploadInvoice: async (file: File): Promise<Invoice> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/invoices`, {
      method: 'POST',
      headers: { 'X-User-Id': getUserId() },
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || 'Upload failed');
    }
    return res.json();
  },

  processInvoice: (id: string) =>
    request<Record<string, unknown>>(`/invoices/${id}/process`, { method: 'POST' }),

  updateInvoiceFields: (
    id: string,
    updates: {
      header_fields?: Record<string, unknown>;
      summary_fields?: Record<string, unknown>;
      line_items?: Record<string, unknown>[];
    }
  ) =>
    request<Invoice>(`/invoices/${id}/fields`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }),

  invoiceAction: (id: string, action: string) =>
    request<Record<string, unknown>>(`/invoices/${id}/action`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    }),

  deleteInvoice: async (id: string): Promise<void> => {
    const res = await fetch(`${BASE_URL}/invoices/${id}`, {
      method: 'DELETE',
      headers: { 'X-User-Id': getUserId() },
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || 'Delete failed');
    }
  },

  getInvoiceDocumentUrl: (id: string) => `${BASE_URL}/invoices/${id}/document`,

  // Approvals
  listApprovals: (status?: string) =>
    request<ApprovalRequest[]>(`/approvals${status ? `?status=${status}` : ''}`),

  createApproval: (invoiceId: string, proposedChanges: Record<string, unknown>) =>
    request<ApprovalRequest>('/approvals', {
      method: 'POST',
      body: JSON.stringify({ invoice_id: invoiceId, proposed_changes: proposedChanges }),
    }),

  reviewApproval: (id: string, status: string, adminNotes?: string) =>
    request<ApprovalRequest>(`/approvals/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({ status, admin_notes: adminNotes }),
    }),

  // Feedback
  listFeedback: (status?: string) =>
    request<FeedbackItem[]>(`/feedback${status ? `?status=${status}` : ''}`),

  listFeedbackForInvoice: (invoiceId: string) =>
    request<FeedbackItem[]>(`/feedback?invoice_id=${encodeURIComponent(invoiceId)}`),

  submitFeedback: (data: {
    invoice_id: string;
    vendor_name?: string;
    field_name?: string;
    original_value?: string;
    corrected_value?: string;
    feedback_text: string;
  }) =>
    request<FeedbackItem>('/feedback', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  reviewFeedback: (id: string, status: string) =>
    request<FeedbackItem>(`/feedback/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({ status }),
    }),

  // Prompts
  listPrompts: () => request<PromptSummary[]>('/prompts'),

  getPrompt: (key: string) => request<PromptDetail>(`/prompts/${key}`),

  updatePrompt: (key: string, content: string, changeSummary: string) =>
    request<PromptVersion>(`/prompts/${key}`, {
      method: 'POST',
      body: JSON.stringify({ content, change_summary: changeSummary }),
    }),

  activatePromptVersion: (key: string, versionId: string) =>
    request<PromptVersion>(`/prompts/${key}/activate`, {
      method: 'POST',
      body: JSON.stringify({ version_id: versionId }),
    }),
};
