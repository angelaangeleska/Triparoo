import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-brand-950',
  {
    variants: {
      variant: {
        default:
          'bg-gradient-to-r from-brand-500 to-brand-600 text-white shadow-soft hover:from-brand-600 hover:to-brand-700 hover:shadow-card',
        secondary:
          'bg-sand-100 text-brand-800 hover:bg-sand-200 dark:bg-brand-800 dark:text-brand-50 dark:hover:bg-brand-700',
        outline:
          'border border-brand-200 text-brand-700 hover:bg-brand-50 dark:border-brand-700 dark:text-brand-100 dark:hover:bg-brand-800',
        ghost: 'text-brand-600 hover:bg-brand-50 dark:text-brand-200 dark:hover:bg-brand-800',
        destructive: 'bg-red-600 text-white hover:bg-red-700',
        accent:
          'bg-gradient-to-r from-sunset-500 to-sunset-600 text-white shadow-soft hover:from-sunset-600 hover:to-sunset-700',
        link: 'text-brand-700 underline-offset-4 hover:underline dark:text-brand-200',
      },
      size: {
        default: 'h-11 px-5 py-2.5',
        sm: 'h-9 px-3.5 text-sm',
        lg: 'h-14 px-8 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  }
)
Button.displayName = 'Button'

export { Button }
