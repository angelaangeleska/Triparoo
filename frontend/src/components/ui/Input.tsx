import { forwardRef, type InputHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
}

const Input = forwardRef<HTMLInputElement, InputProps>(({ className, error, ...props }, ref) => {
  return (
    <input
      ref={ref}
      className={cn(
        'flex h-11 w-full rounded-xl border bg-white/80 px-4 py-2.5 text-sm text-brand-900 shadow-sm transition-colors placeholder:text-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:cursor-not-allowed disabled:opacity-50',
        'dark:bg-brand-900/60 dark:text-brand-50 dark:placeholder:text-brand-500',
        error
          ? 'border-red-400 focus:ring-red-400'
          : 'border-brand-200 dark:border-brand-700',
        className
      )}
      {...props}
    />
  )
})
Input.displayName = 'Input'

export { Input }
