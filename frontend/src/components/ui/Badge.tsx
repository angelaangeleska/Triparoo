import { type HTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-brand-500/10 text-brand-700 dark:bg-brand-400/20 dark:text-brand-200',
        accent: 'bg-sunset-500/10 text-sunset-600 dark:bg-sunset-400/20 dark:text-sunset-300',
        outline: 'border border-brand-200 text-brand-700 dark:border-brand-700 dark:text-brand-200',
        success: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/20 dark:text-emerald-300',
        muted: 'bg-sand-100 text-brand-600 dark:bg-brand-800 dark:text-brand-300',
      },
    },
    defaultVariants: { variant: 'default' },
  }
)

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />
}

export { Badge, badgeVariants }
