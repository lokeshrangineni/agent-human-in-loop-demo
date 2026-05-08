import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Upload, FileText, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import type { InvoiceListItem } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { formatDate } from '../lib/utils';

export function DashboardPage() {
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listInvoices()
      .then(setInvoices)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const counts = {
    total: invoices.length,
    pending: invoices.filter((i) => ['pending_review', 'uploaded', 'processing'].includes(i.status)).length,
    approved: invoices.filter((i) => i.status === 'approved').length,
    rejected: invoices.filter((i) => i.status === 'rejected').length,
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Invoice processing overview
          </p>
        </div>
        <Link
          to="/invoices"
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 transition-colors"
        >
          <Upload className="h-4 w-4" />
          Upload Invoice
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={FileText} label="Total Invoices" value={counts.total} color="blue" />
        <StatCard icon={Clock} label="Pending Review" value={counts.pending} color="amber" />
        <StatCard icon={CheckCircle} label="Approved" value={counts.approved} color="green" />
        <StatCard icon={XCircle} label="Rejected" value={counts.rejected} color="red" />
      </div>

      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Invoices</h2>
        </div>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          </div>
        ) : invoices.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <AlertTriangle className="mb-2 h-8 w-8" />
            <p>No invoices yet. Upload one to get started.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100 text-left text-xs font-medium uppercase text-gray-500">
                  <th className="px-6 py-3">File</th>
                  <th className="px-6 py-3">Vendor</th>
                  <th className="px-6 py-3">Invoice #</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Confidence</th>
                  <th className="px-6 py-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {invoices.slice(0, 10).map((inv) => (
                  <tr key={inv.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <Link
                        to={`/invoices/${inv.id}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        {inv.file_name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {inv.vendor_name || '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {inv.invoice_number || '—'}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={inv.status} />
                    </td>
                    <td className="px-6 py-4">
                      {inv.overall_confidence != null ? (
                        <ConfidenceBadge confidence={inv.overall_confidence} />
                      ) : (
                        <span className="text-sm text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatDate(inv.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  color: string;
}) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    amber: 'bg-amber-50 text-amber-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <div className={`rounded-lg p-2 ${colors[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}
