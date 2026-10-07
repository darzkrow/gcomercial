import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

export default function ToastContainer({ toasts, onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="toast-container" id="global-toast-container">
      {toasts.map((toast) => {
        let Icon = CheckCircle2;
        let iconColor = '#10b981';
        let typeClass = 'toast-success';

        if (toast.type === 'error') {
          Icon = AlertCircle;
          iconColor = '#ef4444';
          typeClass = 'toast-error';
        } else if (toast.type === 'warning') {
          Icon = AlertTriangle;
          iconColor = '#f59e0b';
          typeClass = 'toast-warning';
        } else if (toast.type === 'info') {
          Icon = Info;
          iconColor = '#38bdf8';
          typeClass = 'toast-info';
        }

        return (
          <div 
            key={toast.id} 
            className={`toast-glass ${typeClass}`} 
            id={`toast-${toast.id}`}
          >
            <Icon size={20} color={iconColor} style={{ flexShrink: 0 }} />
            <div style={{ flex: 1, fontSize: '0.86rem', lineHeight: 1.35 }}>
              {toast.message}
            </div>
            <button
              id={`btn-dismiss-toast-${toast.id}`}
              className="btn btn-glass btn-icon-only"
              style={{ width: '24px', height: '24px', border: 'none', background: 'transparent' }}
              onClick={() => onDismiss(toast.id)}
            >
              <X size={14} color="#94a3b8" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
