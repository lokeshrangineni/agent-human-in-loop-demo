import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FileText,
  Search,
  Trash2,
  Loader2,
  Upload,
  X,
  ChevronUp,
} from 'lucide-react';
import { api } from '../services/api';
import type { InvoiceListItem } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { formatDate } from '../lib/utils';
import { useCurrentUser } from '../hooks/useCurrentUser';

export function InvoiceListPage() {
  const navigate = useNavigate();
  const { currentUser } = useCurrentUser();
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  // Upload panel state
  const [uploadOpen, setUploadOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const isAdmin = currentUser.role === 'admin';

  useEffect(() => {
    api.listInvoices()
      .then(setInvoices)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await api.deleteInvoice(id);
      setInvoices((prev) => prev.filter((inv) => inv.id !== id));
    } catch (err) {
      console.error(err);
    } finally {
      setDeletingId(null);
      setConfirmDeleteId(null);
    }
  };

  // Upload handlers
  const handleFile = useCallback((f: File) => {
    const allowed = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'];
    const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
    if (!allowed.includes(ext)) {
      setUploadError(`File type '${ext}' not supported. Use: ${allowed.join(', ')}`);
      return;
    }
    if (f.size > 30 * 1024 * 1024) {
      setUploadError('File too large. Maximum size is 30MB.');
      return;
    }
    setUploadError(null);
    setFile(f);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    },
    [handleFile]
  );

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const invoice = await api.uploadInvoice(file);
      navigate(`/invoices/${invoice.id}`);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
      setUploading(false);
    }
  };

  const closeUpload = () => {
    setUploadOpen(false);
    setFile(null);
    setUploadError(null);
    setDragActive(false);
  };

  const filtered = invoices.filter((inv) => {
    const q = search.toLowerCase();
    return (
      inv.file_name.toLowerCase().includes(q) ||
      (inv.vendor_name || '').toLowerCase().includes(q) ||
      (inv.invoice_number || '').toLowerCase().includes(q) ||
      inv.status.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
          <p className="mt-1 text-sm text-gray-500">
            All processed invoices and their current status.
          </p>
        </div>
        <button
          onClick={() => (uploadOpen ? closeUpload() : setUploadOpen(true))}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 transition-colors"
        >
          {uploadOpen ? (
            <>
              <ChevronUp className="h-4 w-4" />
              Cancel Upload
            </>
          ) : (
            <>
              <Upload className="h-4 w-4" />
              Upload Invoice
            </>
          )}
        </button>
      </div>

      {/* Inline upload panel */}
      {uploadOpen && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-6 space-y-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className={`relative rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
              dragActive
                ? 'border-blue-400 bg-blue-100'
                : file
                ? 'border-green-300 bg-green-50'
                : 'border-blue-300 bg-white hover:border-blue-400'
            }`}
          >
            {file ? (
              <div className="flex flex-col items-center gap-3">
                <FileText className="h-10 w-10 text-green-500" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={() => { setFile(null); setUploadError(null); }}
                  className="inline-flex items-center gap-1 text-sm text-red-600 hover:text-red-800"
                >
                  <X className="h-4 w-4" /> Remove
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <Upload className="h-10 w-10 text-blue-400" />
                <div>
                  <p className="text-sm font-medium text-gray-700">
                    Drag and drop your invoice here, or{' '}
                    <label className="cursor-pointer text-blue-600 hover:text-blue-800">
                      browse
                      <input
                        type="file"
                        className="hidden"
                        accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
                        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                      />
                    </label>
                  </p>
                  <p className="mt-1 text-xs text-gray-500">
                    PDF, PNG, JPG, TIFF, BMP — up to 30MB
                  </p>
                </div>
              </div>
            )}
          </div>

          {uploadError && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {uploadError}
            </div>
          )}

          <div className="flex justify-end gap-3">
            <button
              onClick={closeUpload}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Upload & Process
                </>
              )}
            </button>
          </div>
        </div>
      )}

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search by vendor, invoice number, file name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-gray-300 bg-white py-2.5 pl-10 pr-4 text-sm placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <FileText className="mb-2 h-8 w-8" />
            <p>{search ? 'No invoices match your search.' : 'No invoices yet.'}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100 text-left text-xs font-medium uppercase text-gray-500">
                  <th className="px-6 py-3">File</th>
                  <th className="px-6 py-3">Vendor</th>
                  <th className="px-6 py-3">Invoice #</th>
                  <th className="px-6 py-3">Amount</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Confidence</th>
                  <th className="px-6 py-3">Uploaded</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((inv) => (
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
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {inv.total_amount != null
                        ? `$${inv.total_amount.toLocaleString()}`
                        : '—'}
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
                    <td className="px-6 py-4">
                      {(isAdmin || inv.uploaded_by === currentUser.id) && (
                        confirmDeleteId === inv.id ? (
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">Delete?</span>
                            <button
                              onClick={() => handleDelete(inv.id)}
                              disabled={deletingId === inv.id}
                              className="rounded px-2 py-1 text-xs font-medium bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                            >
                              {deletingId === inv.id
                                ? <Loader2 className="h-3 w-3 animate-spin" />
                                : 'Yes'}
                            </button>
                            <button
                              onClick={() => setConfirmDeleteId(null)}
                              className="rounded px-2 py-1 text-xs font-medium border border-gray-300 text-gray-600 hover:bg-gray-50"
                            >
                              No
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={(e) => { e.preventDefault(); setConfirmDeleteId(inv.id); }}
                            className="rounded p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                            title="Delete invoice"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )
                      )}
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
