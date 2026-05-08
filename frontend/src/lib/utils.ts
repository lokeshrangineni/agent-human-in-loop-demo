import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function confidenceColor(confidence: number): string {
  if (confidence >= 0.85) return 'text-green-600 bg-green-50 border-green-200';
  if (confidence >= 0.6) return 'text-amber-600 bg-amber-50 border-amber-200';
  return 'text-red-600 bg-red-50 border-red-200';
}

export function confidenceBadgeColor(confidence: number): string {
  if (confidence >= 0.85) return 'bg-green-100 text-green-800';
  if (confidence >= 0.6) return 'bg-amber-100 text-amber-800';
  return 'bg-red-100 text-red-800';
}

export function statusColor(status: string): string {
  switch (status) {
    case 'approved': return 'bg-green-100 text-green-800';
    case 'rejected': return 'bg-red-100 text-red-800';
    case 'processing': return 'bg-blue-100 text-blue-800';
    case 'validated':
    case 'extracted': return 'bg-indigo-100 text-indigo-800';
    case 'pending_approval': return 'bg-purple-100 text-purple-800';
    case 'pending_review':
    case 'pending': return 'bg-amber-100 text-amber-800';
    case 'uploaded': return 'bg-gray-100 text-gray-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
