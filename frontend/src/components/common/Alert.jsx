import React from 'react';
import clsx from 'clsx';
import { CheckCircle2, AlertTriangle, AlertCircle, Info } from 'lucide-react';

const STYLES = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  error: 'border-red-200 bg-red-50 text-red-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800',
};

const ICONS = {
  success: CheckCircle2,
  warning: AlertTriangle,
  error: AlertCircle,
  info: Info,
};

export const Alert = ({ variant = 'info', title, children, className = '' }) => {
  const Icon = ICONS[variant];
  return (
    <div
      role="status"
      className={clsx('flex items-start gap-3 rounded-lg border px-4 py-3 text-sm', STYLES[variant], className)}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="min-w-0">
        {title && <div className="font-medium">{title}</div>}
        {children && (
          <div className={clsx(title && 'mt-0.5', 'text-[13px] leading-relaxed opacity-90')}>{children}</div>
        )}
      </div>
    </div>
  );
};
