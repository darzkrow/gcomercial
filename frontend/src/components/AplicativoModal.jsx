import React, { useState, useEffect } from 'react';
import { X, Save, Upload, Link, Shield, Building, Loader2 } from 'lucide-react';

export default function AplicativoModal({ isOpen, onClose, onSave, app = null, isSaving }) {
  const [nombre, setNombre] = useState('');
  const [url, setUrl] = useState('');
  const [logo, setLogo] = useState('');
  const [logoFile, setLogoFile] = useState(null);
  const [descripcion, setDescripcion] = useState('');
  const [gruposAd, setGruposAd] = useState('');
  const [departamentosAd, setDepartamentosAd] = useState('');
  const [orden, setOrden] = useState(0);
  const [activo, setActivo] = useState(true);
  const [validationError, setValidationError] = useState('');

  useEffect(() => {
    if (app) {
      setNombre(app.nombre || '');
      setUrl(app.url || '');
      setLogo(app.logo_url || app.logo || '');
      setLogoFile(null);
      setDescripcion(app.descripcion || '');
      setGruposAd(Array.isArray(app.grupos_ad) ? app.grupos_ad.join(', ') : (app.grupos_ad || ''));
      setDepartamentosAd(Array.isArray(app.departamentos_ad) ? app.departamentos_ad.join(', ') : (app.departamentos_ad || ''));
      setOrden(app.orden || 0);
      setActivo(app.activo !== undefined ? app.activo : true);
    } else {
      setNombre('');
      setUrl('');
      setLogo('');
      setLogoFile(null);
      setDescripcion('');
      setGruposAd('');
      setDepartamentosAd('');
      setOrden(0);
      setActivo(true);
    }
    setValidationError('');
  }, [app, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!nombre.trim()) {
      setValidationError('El nombre del aplicativo es obligatorio.');
      return;
    }
    if (!url.trim()) {
      setValidationError('La URL de acceso es obligatoria.');
      return;
    }

    // Validar sintaxis básica de URL
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      setValidationError('La URL debe iniciar con https:// o http://');
      return;
    }

    setValidationError('');

    // Si se subió archivo de logo, usamos FormData
    if (logoFile) {
      const formData = new FormData();
      formData.append('nombre', nombre.trim());
      formData.append('url', url.trim());
      formData.append('logo', logo.trim());
      formData.append('logo_archivo', logoFile);
      formData.append('descripcion', descripcion.trim());
      formData.append('grupos_ad', gruposAd.trim());
      formData.append('departamentos_ad', departamentosAd.trim());
      formData.append('orden', orden);
      formData.append('activo', activo);
      onSave(formData);
    } else {
      const jsonPayload = {
        nombre: nombre.trim(),
        url: url.trim(),
        logo: logo.trim(),
        descripcion: descripcion.trim(),
        grupos_ad: gruposAd.trim(),
        departamentos_ad: departamentosAd.trim(),
        orden: Number(orden),
        activo,
      };
      onSave(jsonPayload);
    }
  };

  return (
    <div className="modal-overlay-glass" id="modal-app-overlay" onClick={onClose}>
      <div 
        className="modal-content-glass" 
        id="modal-app-content"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera del Modal */}
        <div className="modal-header-glass">
          <h3 className="modal-title" id="modal-app-heading">
            {app ? 'Editar Aplicativo' : 'Registrar Nuevo Aplicativo'}
          </h3>
          <button 
            id="btn-close-modal"
            className="btn btn-glass btn-icon-only" 
            onClick={onClose}
            type="button"
          >
            <X size={18} />
          </button>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} id="modal-app-form">
          <div className="modal-body">
            {validationError && (
              <div 
                id="modal-validation-error"
                style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.65rem 1rem',
                  marginBottom: '1.25rem',
                  color: '#fca5a5',
                  fontSize: '0.82rem',
                }}
              >
                {validationError}
              </div>
            )}

            <div className="form-group">
              <label className="form-label" htmlFor="modal-input-name">Nombre del Aplicativo *</label>
              <div className="input-glass-container">
                <input
                  id="modal-input-name"
                  type="text"
                  className="input-glass"
                  placeholder="ej. ERP Corporativo SAP"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  style={{ paddingLeft: '1rem' }}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="modal-input-url">URL de Destino *</label>
              <div className="input-glass-container">
                <span className="input-icon-left"><Link size={16} /></span>
                <input
                  id="modal-input-url"
                  type="url"
                  className="input-glass"
                  placeholder="https://sistema.empresa.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="modal-input-desc">Descripción</label>
              <textarea
                id="modal-input-desc"
                className="input-glass"
                rows="2"
                placeholder="Breve resumen de la funcionalidad del aplicativo..."
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                style={{ paddingLeft: '1rem', resize: 'vertical' }}
              />
            </div>

            {/* Configuración de Logo */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="modal-input-logo-url">URL del Logo (Opcional)</label>
                <input
                  id="modal-input-logo-url"
                  type="text"
                  className="input-glass"
                  placeholder="https://.../logo.png"
                  value={logo}
                  onChange={(e) => setLogo(e.target.value)}
                  style={{ paddingLeft: '1rem' }}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="modal-input-logo-file">Subir Archivo Logo</label>
                <div className="input-glass-container">
                  <input
                    id="modal-input-logo-file"
                    type="file"
                    accept="image/*,.svg"
                    className="input-glass"
                    onChange={(e) => setLogoFile(e.target.files[0] || null)}
                    style={{ paddingLeft: '1rem', fontSize: '0.8rem' }}
                  />
                </div>
              </div>
            </div>

            {/* Control de Acceso Active Directory */}
            <div 
              style={{
                background: 'rgba(14, 165, 233, 0.08)',
                border: '1px solid rgba(14, 165, 233, 0.22)',
                borderRadius: 'var(--radius-md)',
                padding: '1rem',
                margin: '1.25rem 0',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.75rem', color: 'var(--corporate-cyan-light)', fontWeight: 600, fontSize: '0.85rem' }}>
                <Shield size={16} />
                <span>Restricciones de Active Directory (AD / LDAP)</span>
              </div>

              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <label className="form-label" htmlFor="modal-input-ad-groups" style={{ fontSize: '0.76rem' }}>
                  Grupos de AD autorizados (separados por coma)
                </label>
                <input
                  id="modal-input-ad-groups"
                  type="text"
                  className="input-glass"
                  placeholder="ej. Ventas_Chile, GPO_ERP, Finanzas_Staff"
                  value={gruposAd}
                  onChange={(e) => setGruposAd(e.target.value)}
                  style={{ paddingLeft: '1rem', fontSize: '0.85rem' }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" htmlFor="modal-input-ad-dept" style={{ fontSize: '0.76rem' }}>
                  Departamentos de AD autorizados (separados por coma)
                </label>
                <input
                  id="modal-input-ad-dept"
                  type="text"
                  className="input-glass"
                  placeholder="ej. Comercial, Ventas, Finanzas"
                  value={departamentosAd}
                  onChange={(e) => setDepartamentosAd(e.target.value)}
                  style={{ paddingLeft: '1rem', fontSize: '0.85rem' }}
                />
              </div>
            </div>

            {/* Orden y Estado */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', alignItems: 'center' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" htmlFor="modal-input-orden">Orden de Prioridad</label>
                <input
                  id="modal-input-orden"
                  type="number"
                  className="input-glass"
                  value={orden}
                  onChange={(e) => setOrden(e.target.value)}
                  style={{ paddingLeft: '1rem' }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0, paddingTop: '1.25rem' }}>
                <label className="checkbox-label" htmlFor="modal-input-activo">
                  <input
                    id="modal-input-activo"
                    type="checkbox"
                    checked={activo}
                    onChange={(e) => setActivo(e.target.checked)}
                  />
                  <span>Aplicativo Habilitado</span>
                </label>
              </div>
            </div>
          </div>

          {/* Botones de Acción */}
          <div className="modal-footer">
            <button
              id="btn-cancel-modal"
              type="button"
              className="btn btn-glass"
              onClick={onClose}
              disabled={isSaving}
            >
              Cancelar
            </button>
            <button
              id="btn-save-modal"
              type="submit"
              className="btn btn-primary"
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <Loader2 size={16} className="spinner-icon" />
                  <span>Guardando...</span>
                </>
              ) : (
                <>
                  <Save size={16} />
                  <span>{app ? 'Actualizar' : 'Crear Aplicativo'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
