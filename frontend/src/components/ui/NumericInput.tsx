import { useState, type FocusEvent, type InputHTMLAttributes } from 'react'

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange' | 'type'> & {
  value: number
  onChange: (value: number) => void
  integer?: boolean
  min?: number
  max?: number
}

function stripLeadingZeros(raw: string): string {
  if (raw === '' || raw === '0' || raw.startsWith('0.')) return raw
  const stripped = raw.replace(/^0+/, '')
  return stripped === '' ? '0' : stripped
}

export default function NumericInput({
  value,
  onChange,
  integer = false,
  min,
  max,
  className,
  onFocus,
  onBlur,
  ...rest
}: Props) {
  const [draft, setDraft] = useState<string | null>(null)

  const display = draft !== null ? draft : String(value)

  const clamp = (n: number) => {
    let next = n
    if (min !== undefined) next = Math.max(min, next)
    if (max !== undefined) next = Math.min(max, next)
    return next
  }

  const commit = (raw: string) => {
    if (raw === '' || raw === '.') {
      onChange(clamp(min ?? value))
      return
    }
    const parsed = integer ? parseInt(raw, 10) : parseFloat(raw)
    if (!Number.isNaN(parsed)) {
      onChange(clamp(parsed))
    }
  }

  const handleFocus = (e: FocusEvent<HTMLInputElement>) => {
    setDraft(String(value))
    requestAnimationFrame(() => e.target.select())
    onFocus?.(e)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let next = e.target.value
    if (integer) {
      next = next.replace(/\D/g, '')
    } else {
      next = next.replace(/[^\d.]/g, '')
      const dot = next.indexOf('.')
      if (dot !== -1) {
        next = next.slice(0, dot + 1) + next.slice(dot + 1).replace(/\./g, '')
      }
    }
    setDraft(stripLeadingZeros(next))
  }

  const handleBlur = (e: FocusEvent<HTMLInputElement>) => {
    if (draft !== null) commit(draft)
    setDraft(null)
    onBlur?.(e)
  }

  return (
    <input
      type="text"
      inputMode={integer ? 'numeric' : 'decimal'}
      value={display}
      onFocus={handleFocus}
      onChange={handleChange}
      onBlur={handleBlur}
      className={className}
      {...rest}
    />
  )
}
