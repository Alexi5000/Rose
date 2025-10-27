import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { SmoothScrollWrapper } from './components/Layout/SmoothScrollWrapper.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SmoothScrollWrapper enabled={false}>
      <App />
    </SmoothScrollWrapper>
  </React.StrictMode>,
)
