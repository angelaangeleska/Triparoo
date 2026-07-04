import { forwardRef, type LabelHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn(
        'text-sm font-medium text-brand-700 dark:text-brand-200 mb-1.5 block',
        className
      )}
      {...props}
    />
  )
)
Label.displayName = 'Label'

export { Label }
