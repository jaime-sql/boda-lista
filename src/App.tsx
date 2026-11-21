import { Component, type ReactNode } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { ErrorState } from './components/ScreenState';
import { ToastProvider } from './components/ToastProvider';
import { AdminPage } from './pages/AdminPage';
import { GuestPage } from './pages/GuestPage';

type BoundaryProps = { children: ReactNode };
type BoundaryState = { failed: boolean };

class ScreenBoundary extends Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { failed: false };

  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return (
        <ErrorState
          title="Algo salió mal"
          detail="Recarga la página e inténtalo de nuevo."
          onRetry={() => window.location.reload()}
        />
      );
    }
    return this.props.children;
  }
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AppShell>
          <ScreenBoundary>
            <Routes>
              <Route path="/" element={<GuestPage />} />
              <Route path="/admin" element={<AdminPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ScreenBoundary>
        </AppShell>
      </ToastProvider>
    </BrowserRouter>
  );
}
