import * as Toast from '@radix-ui/react-toast';
import { createContext, useContext, useState, type ReactNode } from 'react';

export type ToastMessage = {
  title: string;
  description?: string;
};

type ToastRecord = ToastMessage & { id: string };

const ToastContext = createContext<((toast: ToastMessage) => void) | null>(null);

export function useToast(): (toast: ToastMessage) => void {
  const publish = useContext(ToastContext);
  if (!publish) throw new Error('ToastProvider missing');
  return publish;
}

type ToastProviderProps = {
  children: ReactNode;
};

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);

  function publish(toast: ToastMessage) {
    const id = crypto.randomUUID();
    setToasts((current) => [...current, { ...toast, id }]);
  }

  function dismiss(id: string) {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }

  return (
    <ToastContext.Provider value={publish}>
      <Toast.Provider duration={8000} label="Avisos">
        {children}
        {toasts.map((toast) => (
          <Toast.Root key={toast.id} className="toast" onOpenChange={(open) => !open && dismiss(toast.id)}>
            <Toast.Title className="heading">{toast.title}</Toast.Title>
            {toast.description ? <Toast.Description>{toast.description}</Toast.Description> : null}
            <Toast.Close className="button button-secondary">Cerrar</Toast.Close>
          </Toast.Root>
        ))}
        <Toast.Viewport className="toast-viewport" />
      </Toast.Provider>
    </ToastContext.Provider>
  );
}
