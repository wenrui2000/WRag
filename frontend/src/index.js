import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Set the page title
document.title = "Example RAG UI";

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
