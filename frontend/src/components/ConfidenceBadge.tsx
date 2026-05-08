import { cn, confidenceBadgeColor } from '../lib/utils';

interface Props {
  confidence: number;
  className?: string;
}

export function ConfidenceBadge({ confidence, className }: Props) {
  const pct = Math.round(confidence * 100);
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        confidenceBadgeColor(confidence),
        className
      )}
    >
      {pct}%
    </span>
  );
}
