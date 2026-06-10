import { Loader2 } from 'lucide-react'

interface Props {
  message?: string
  fullScreen?: boolean
}

export default function LoadingSpinner({ message = 'Loading...', fullScreen }: Props) {
  const content = (
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="w-10 h-10 text-brand-500 animate-spin" />
      <p className="text-sm text-brand-600 font-medium">{message}</p>
    </div>
  )

  if (fullScreen) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">{content}</div>
    )
  }

  return <div className="py-16 flex items-center justify-center">{content}</div>
}
