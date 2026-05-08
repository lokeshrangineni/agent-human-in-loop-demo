import { cn, statusColor, formatLabel } from '../lib/utils';

interface Props {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: Props) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        statusColor(status),
        className
      )}
    >
      {formatLabel(status)}
    </span>
  );
}
