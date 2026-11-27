import type { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'ghost' | 'danger'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  loading?: boolean
}

const styles: Record<Variant, string> = {
  primary:
    'bg-[var(--color-accent)] text-[var(--color-on-accent)] border border-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] hover:border-[var(--color-accent-hover)]',
  ghost:
    'bg-transparent text-[var(--color-text)] border border-[var(--color-border)] hover:border-[var(--color-text-muted)]',
  danger:
    'bg-transparent text-[var(--color-danger)] border border-[var(--color-border)] hover:border-[var(--color-danger)]',
}

export function Button({ variant = 'primary', loading, children, className = '', disabled, ...props }: Props) {
  return (
    <button
      {...props}
      disabled={disabled ?? loading}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium',
        'transition-all duration-150 ease-out',
        'active:scale-[0.98]',
        'disabled:cursor-not-allowed disabled:opacity-40',
        styles[variant],
        className,
      ].join(' ')}
    >
      {loading ? <span className="num animate-pulse">···</span> : children}
    </button>
  )
}
