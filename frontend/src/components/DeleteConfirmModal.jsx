import React from 'react';
import { AlertTriangle, Trash2, X, Loader2 } from 'lucide-react';

export default function DeleteConfirmModal({ isOpen, onClose, onConfirm, app, isDeleting }) {
  if (!isOpen || !app) return null;

  return (
    <div className="modal-overlay-glass" id="modal-delete-overlay" onClick={onClose}>
      <div 
        className="modal-content-glass" 
        id="modal-delete-content"
        style={{ maxWidth: '440px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header-glass">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: '#fca5a5' }}>
            <AlertTriangle size={20} />
            <h3 className="modal-title" id="modal-delete-title">Eliminar Aplicativo</h3>
          </div>
          <button 
            id="btn-close-delete-modal"
            className="btn btn-glass btn-icon-only" 
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <p style={{ color: 'var(--white-85)', fontSize: '0.92rem', lineHeight: 1.5 }}>
            ¿Está seguro de que desea eliminar el aplicativo{' '}
            <strong style={{ color: 'var(--white)' }}>"{app.nombre}"</strong>?
          </p>
          <p style={{ color: 'var(--white-50)', fontSize: '0.8rem', marginTop: '0.6rem' }}>
            Esta acción removerá el acceso directo para todos los usuarios y grupos de Active Directory asignados.
          </p>
        </div>

        <div className="modal-footer">
          <button
            id="btn-cancel-delete"
            className="btn btn-glass"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancelar
          </button>
          <button
            id="btn-confirm-delete"
            className="btn btn-danger-glass"
            onClick={() => onConfirm(app.id)}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <Loader2 size={16} className="spinner-icon" />
                <span>Eliminando...</span>
              </>
            ) : (
              <>
                <Trash2 size={16} />
                <span>Confirmar Eliminación</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
