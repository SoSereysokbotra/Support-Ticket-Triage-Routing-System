import React from 'react';
import clsx from 'clsx';

// A badge is a square mono tag with a small colour swatch — the colour is
// carried by the swatch, never by a tinted background.
const SWATCHES = {
  neutral: 'bg-rule-strong',
  ink: 'bg-ink',
  blue: 'bg-cat-software',
  green: 'bg-ok',
  amber: 'bg-warn',
  red: 'bg-bad',
  purple: 'bg-cat-network',
  accent: 'bg-accent',
};

// Domain values map onto the swatch tones above so callers can pass
// a category / priority string straight through as `variant`.
const ALIASES = {
  Hardware: 'amber',
  Software: 'blue',
  Network: 'purple',
  'Access & Security': 'red',
  'Billing & Admin': 'green',
  Other: 'neutral',
  Low: 'neutral',
  Medium: 'ink',
  High: 'amber',
  Critical: 'red',
  VIP: 'accent',
};

// Values that render as a solid inverted tag instead of swatch + text.
const SOLID = {
  Critical: 'border-bad bg-bad text-white',
  VIP: 'border-accent bg-accent text-white',
};

const SIZES = {
  sm: 'h-[22px] px-1.5 text-xs',
  md: 'h-6 px-2 text-[13px]',
  lg: 'h-7 px-2.5 text-sm',
};

export const Badge = ({ label, variant = 'neutral', size = 'md', className = '' }) => {
  const tone = SWATCHES[variant] ? variant : ALIASES[variant] || 'neutral';
  const solid = SOLID[variant];

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 whitespace-nowrap border font-medium',
        solid || 'border-rule bg-surface text-ink',
        SIZES[size],
        className
      )}
    >
      {!solid && <span className={clsx('h-2 w-2 shrink-0', SWATCHES[tone])} aria-hidden="true" />}
      {label}
    </span>
  );
};
