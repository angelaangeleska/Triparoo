import { Component, type ErrorInfo, type ReactNode } from 'react'
import i18n from '../../i18n'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('UI error:', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-[50vh] flex items-center justify-center px-4">
          <div className="max-w-lg w-full rounded-2xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 p-6 text-center">
            <h2 className="font-display text-xl font-semibold text-red-800 dark:text-red-300 mb-2">
              {i18n.t('common.error')}
            </h2>
            <p className="text-sm text-red-700 dark:text-red-300/80 mb-4">{this.state.error.message}</p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-xl bg-red-600 text-white text-sm font-medium hover:bg-red-700"
            >
              {i18n.t('common.reload')}
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
