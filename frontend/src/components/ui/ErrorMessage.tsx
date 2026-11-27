interface Props {
  message?: string
}

export function ErrorMessage({ message }: Props) {
  if (!message) return null
  return (
    <p className="rounded-lg border border-[var(--color-danger)]/25 bg-[var(--color-danger-bg)] px-3 py-2 text-sm text-[var(--color-danger)]">
      {message}
    </p>
  )
}
