import React, { useState } from 'react';
import { ExternalLink, Edit2, Trash2, Shield, Building, Globe } from 'lucide-react';
import { sanitizeSafeUrl } from '../services/authFetch';

export default function AplicativoCard({ app, onEdit, onDelete, canManage }) {
  const [imgError, setImgError] = useState(false);
  const safeUrl = sanitizeSafeUrl(app.url);
  const adGroups = app.grupos_ad || [];
  const adDepts = app.departamentos_ad || [];

  // Letra inicial para el monograma si no hay logo
  const initials = app.nombre ? app.nombre.slice(0, 2).toUpperCase() : 'AP';

  return (
    <div className="app-card-glass" id={`app-card-${app.id}`}>
      <div>
        <div className="app-card-top">
          {/* Caja de Logo */}
          <div className="app-logo-box" id={`app-logo-box-${app.id}`}>
            {app.logo && !imgError ? (
              <img
                src={app.logo}
                alt={`Logo de ${app.nombre}`}
                className="app-logo-img"
                id={`app-logo-img-${app.id}`}
                onError={() => setImgError(true)}
              />
            ) : (
              <span className="app-logo-fallback" id={`app-logo-fallback-${app.id}`}>
                {initials}
              </span>
            )}
          </div>

          {/* Información Principal */}
          <div className="app-details">
            <h3 className="app-title" id={`app-title-${app.id}`}>{app.nombre}</h3>
            <span className={`badge-pill ${app.activo ? 'badge-active' : 'badge-inactive'}`}>
              {app.activo ? 'Disponible' : 'Inactivo'}
            </span>
          </div>
        </div>

        {/* Descripción */}
        <p className="app-description" id={`app-desc-${app.id}`} title={app.descripcion}>
          {app.descripcion || 'Sin descripción disponible.'}
        </p>

        {/* Etiquetas de Control de Acceso (AD / LDAP) */}
        <div className="app-meta-tags" id={`app-tags-${app.id}`}>
          {adDepts.map((dept, idx) => (
            <span key={idx} className="badge-pill badge-ad-dept" title={`Departamento AD: ${dept}`}>
              <Building size={11} />
              <span>{dept}</span>
            </span>
          ))}

          {adGroups.slice(0, 2).map((group, idx) => (
            <span key={idx} className="badge-pill badge-ad-group" title={`Grupo AD: ${group}`}>
              <Shield size={11} />
              <span>{group}</span>
            </span>
          ))}

          {adGroups.length > 2 && (
            <span className="badge-pill badge-ad-group" title={adGroups.join(', ')}>
              +{adGroups.length - 2} grupos
            </span>
          )}

          {adGroups.length === 0 && adDepts.length === 0 && (
            <span className="badge-pill" style={{ background: 'rgba(255,255,255,0.08)', color: '#e2e8f0' }}>
              <Globe size={11} />
              <span>General</span>
            </span>
          )}
        </div>
      </div>

      {/* Pie de Tarjeta y Acciones */}
      <div className="app-card-footer" id={`app-footer-${app.id}`}>
        <a
          id={`btn-open-app-${app.id}`}
          href={safeUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-primary btn-sm"
          style={{ flex: 1 }}
        >
          <span>Acceder</span>
          <ExternalLink size={14} />
        </a>

        {canManage && (
          <div className="app-admin-actions" id={`admin-actions-${app.id}`}>
            <button
              id={`btn-edit-app-${app.id}`}
              className="btn btn-glass btn-icon-only"
              onClick={() => onEdit(app)}
              title="Editar aplicativo"
            >
              <Edit2 size={14} color="#93c5fd" />
            </button>
            <button
              id={`btn-delete-app-${app.id}`}
              className="btn btn-danger-glass btn-icon-only"
              onClick={() => onDelete(app)}
              title="Eliminar aplicativo"
            >
              <Trash2 size={14} color="#fca5a5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
