import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, X, Loader2 } from 'lucide-react';
import { api } from '../services/api';

export function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback((f: File) => {
    const allowed = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'];
    const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
    if (!allowed.includes(ext)) {
      setError(`File type '${ext}' not supported. Use: ${allowed.join(', ')}`);
      return;
    }
    if (f.size > 30 * 1024 * 1024) {
      setError('File too large. Maximum size is 30MB.');
      return;
    }
    setError(null);
    setFile(f);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const invoice = await api.uploadInvoice(file);
      navigate(`/invoices/${invoice.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload Invoice</h1>
        <p className="mt-1 text-sm text-gray-500">
          Upload a PDF or image to start the extraction workflow.
        </p>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`relative rounded-lg border-2 border-dashed p-12 text-center transition-colors ${
          dragActive
            ? 'border-blue-400 bg-blue-50'
            : file
            ? 'border-green-300 bg-green-50'
            : 'border-gray-300 bg-white hover:border-gray-400'
        }`}
      >
        {file ? (
          <div className="flex flex-col items-center gap-3">
            <FileText className="h-12 w-12 text-green-500" />
            <div>
              <p className="text-sm font-medium text-gray-900">{file.name}</p>
              <p className="text-xs text-gray-500">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <button
              onClick={() => { setFile(null); setError(null); }}
              className="inline-flex items-center gap-1 text-sm text-red-600 hover:text-red-800"
            >
              <X className="h-4 w-4" /> Remove
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="h-12 w-12 text-gray-400" />
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

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex justify-end gap-3">
        <button
          onClick={() => navigate('/')}
          className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
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
  );
}
