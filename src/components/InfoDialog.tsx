import * as Dialog from '@radix-ui/react-dialog';
import type { ReactNode } from 'react';

type InfoDialogProps = {
  trigger: string;
  title: string;
  children: ReactNode;
};

export function InfoDialog({ trigger, title, children }: InfoDialogProps) {
  return (
    <Dialog.Root>
      <Dialog.Trigger className="btn btn-secondary">{trigger}</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content">
          <Dialog.Title className="section-title">{title}</Dialog.Title>
          <Dialog.Description asChild>
            <div className="stack">{children}</div>
          </Dialog.Description>
          <Dialog.Close className="btn btn-primary">Cerrar</Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
