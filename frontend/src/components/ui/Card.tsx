import type { ElementType, ReactNode } from 'react'

interface Props {
  children: ReactNode
  className?: string
  as?: ElementType
}

export function Card({ children, className = '', as: Tag = 'div' }: Props) {
  return (
    <Tag
      className={[
        'rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5',
        className,
      ].join(' ')}
    >
      {children}
    </Tag>
  )
}
