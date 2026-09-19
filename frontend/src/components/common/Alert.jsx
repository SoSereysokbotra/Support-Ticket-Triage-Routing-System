import React from 'react';
import clsx from 'clsx';
import { CheckCircle2, AlertTriangle, AlertCircle, Info } from 'lucide-react';

// Alerts are a plain white panel with a coloured 2px left rule — the
// colour sits on the rule and the icon, not behind the text.
const STYLES = {
  success: { rule: 'border-l-ok', icon: 'text-ok' },
  warning: { rule: 'border-l-warn', icon: 'text-warn' },
  error: { rule: 'border-l-bad', icon: 'text-bad' },
  info: { rule: 'border-l-ink', icon: 'text-ink' },
};

const ICONS = {
  success: CheckCircle2,
  warning: AlertTriangle,
  error: AlertCircle,
  info: Info,
};

export const Alert = ({ variant = 'info', title, children, className = '' }) => {
  const Icon = ICONS[variant];
  const style = STYLES[variant];
  return (
    <div
      role="status"
      className={clsx(
        'flex items-start gap-3 border border-rule border-l-2 bg-surface px-4 py-3 text-sm text-ink',
        style.rule,
        className
      )}
    >
      <Icon className={clsx('mt-0.5 h-4 w-4 shrink-0', style.icon)} strokeWidth={1.75} />
      <div className="min-w-0">
        {title && <div className="font-medium">{title}</div>}
        {children && (
          <div className={clsx(title && 'mt-0.5', 'text-[13px] leading-relaxed text-ink-2')}>{children}</div>
        )}
      </div>
    </div>
  );
};
