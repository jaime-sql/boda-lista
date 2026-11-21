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
      <Dialog.Trigger className="button button-secondary">{trigger}</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content">
          <Dialog.Title className="heading">{title}</Dialog.Title>
          <Dialog.Description asChild>
            <div className="stack">{children}</div>
          </Dialog.Description>
          <Dialog.Close className="button">Cerrar</Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
