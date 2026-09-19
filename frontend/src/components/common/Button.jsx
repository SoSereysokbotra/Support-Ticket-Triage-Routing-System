import React from 'react';
import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

const VARIANTS = {
  primary: 'border border-ink bg-ink text-paper hover:border-ink-hover hover:bg-ink-hover',
  // Outlined; inverts to solid ink on hover.
  secondary: 'border border-ink bg-transparent text-ink hover:bg-ink hover:text-paper',
  ghost: 'border border-transparent text-ink-2 hover:border-rule-strong hover:text-ink',
  danger: 'border border-bad bg-bad text-white hover:bg-[#9A1D13]',
};

const SIZES = {
  sm: 'h-8 px-3 text-[13px] gap-1.5',
  md: 'h-9 px-4 text-sm gap-2',
  lg: 'h-11 px-5 text-sm gap-2',
};

export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled = false,
  icon: Icon,
  className = '',
  ...props
}) => (
  <button
    type="button"
    disabled={disabled || isLoading}
    className={clsx(
      'inline-flex items-center justify-center whitespace-nowrap font-medium tracking-[0.01em] transition-colors',
      'disabled:pointer-events-none disabled:opacity-40',
      VARIANTS[variant],
      SIZES[size],
      className
    )}
    {...props}
  >
    {isLoading ? (
      <Loader2 className="h-3.5 w-3.5 animate-spin" />
    ) : Icon ? (
      <Icon className="h-3.5 w-3.5" strokeWidth={1.75} />
    ) : null}
    {children}
  </button>
);
