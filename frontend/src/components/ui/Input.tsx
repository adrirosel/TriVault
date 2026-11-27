import type { InputHTMLAttributes } from 'react'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export function Input({ label, error, hint, className = '', ...props }: Props) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide">
          {label}
        </label>
      )}
      <input
        {...props}
        className={[
          'w-full rounded-lg border bg-[var(--color-surface)] px-3 py-2 text-[1rem] md:text-sm',
          'text-[var(--color-text)] placeholder-[var(--color-text-muted)]',
          'transition-all duration-150 ease-out outline-none',
          error
            ? 'border-[var(--color-danger)] focus:border-[var(--color-danger)]'
            : 'border-[var(--color-border)] focus:border-[var(--color-accent)]',
          className,
        ].join(' ')}
      />
      {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
      {hint && !error && <p className="text-xs text-[var(--color-text-muted)]">{hint}</p>}
    </div>
  )
}
