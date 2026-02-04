import { Component, type ErrorInfo, type ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="fixed inset-0 flex items-center justify-center bg-black/90 z-[9999]">
          <div className="text-center max-w-sm px-6">
            <h1 className="text-xl font-semibold text-white mb-3">Something went wrong</h1>
            <p className="text-white/60 text-sm mb-6">
              An unexpected error occurred. Click below to try again.
            </p>
            <button
              onClick={this.handleRetry}
              className="px-5 py-2 rounded-lg bg-white/10 text-white text-sm hover:bg-white/20 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
