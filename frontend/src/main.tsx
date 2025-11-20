import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Set favicon to Nxzen.jpg from src assets
try {
  const favicon = document.getElementById('favicon') as HTMLLinkElement | null;
  if (favicon) {
    const nxzenUrl = new URL('./images/Nxzen.jpg', import.meta.url).href;
    favicon.href = nxzenUrl;
    favicon.type = 'image/jpeg';
  }
} catch {}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

