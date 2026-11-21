import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { initFirebase } from './firebase/client';
import './styles/tokens.css';
import './styles/components.css';
import './styles/guest.css';
import './styles/app.css';

initFirebase();

const root = document.getElementById('root');
if (!root) throw new Error('root missing');

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
