import React from 'react';
import { Shield, Building, Mail, Phone, Key, CheckCircle, ShieldCheck } from 'lucide-react';

export default function DirectoryView({ user }) {
  const profile = user?.profile || {};
  const adGroups = profile.ad_groups || [];

  return (
    <div className="directory-container" id="directory-view-container">
      <div className="dashboard-header">
        <div>
          <h2 style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--white)', letterSpacing: '-0.02em' }}>
            Directorio y Perfil Active Directory
          </h2>
          <p style={{ color: 'var(--white-70)', fontSize: '0.92rem' }}>
            Atributos y grupos de seguridad sincronizados desde el Controlador de Dominio.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {/* Tarjeta de Datos del Usuario */}
        <div className="app-card-glass" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="user-avatar-circle" style={{ width: '56px', height: '56px', fontSize: '1.4rem' }}>
              {user?.first_name ? user.first_name[0].toUpperCase() : (user?.username?.[0]?.toUpperCase() || 'U')}
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{user?.full_name || user?.username}</h3>
              <span className="badge-pill badge-ad-dept">{profile.department || 'Sin Departamento'}</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.88rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Mail size={16} color="var(--corporate-cyan-light)" />
              <span style={{ color: 'var(--white-70)' }}>Email:</span>
              <span style={{ fontWeight: 600, color: 'var(--white)' }}>{user?.email || 'No registrado'}</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Building size={16} color="var(--corporate-cyan-light)" />
              <span style={{ color: 'var(--white-70)' }}>Cargo / Título:</span>
              <span style={{ fontWeight: 600, color: 'var(--white)' }}>{profile.job_title || 'Empleado'}</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Phone size={16} color="var(--corporate-cyan-light)" />
              <span style={{ color: 'var(--white-70)' }}>Teléfono:</span>
              <span style={{ fontWeight: 600, color: 'var(--white)' }}>{profile.phone || 'No registrado'}</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Key size={16} color="var(--corporate-cyan-light)" />
              <span style={{ color: 'var(--white-70)' }}>Tipo de Cuenta:</span>
              <span className="badge-pill badge-active">
                {user?.is_superuser ? 'Superusuario' : (user?.is_staff ? 'Staff' : 'Usuario Estándar')}
              </span>
            </div>
          </div>
        </div>

        {/* Tarjeta de Grupos de Seguridad de Active Directory */}
        <div className="app-card-glass" style={{ padding: '1.75rem' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <ShieldCheck size={20} color="var(--corporate-cyan-light)" />
            <span>Grupos de Seguridad AD Asignados ({adGroups.length})</span>
          </h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--white-70)', marginBottom: '1.25rem' }}>
            Estos grupos determinan de forma automática a qué aplicativos de la plataforma tiene autorización de acceso:
          </p>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem' }}>
            {adGroups.length > 0 ? (
              adGroups.map((group, idx) => (
                <div 
                  key={idx} 
                  className="badge-pill badge-ad-group"
                  style={{ padding: '0.5rem 0.85rem', fontSize: '0.8rem' }}
                >
                  <Shield size={13} />
                  <span>{group}</span>
                </div>
              ))
            ) : (
              <p style={{ color: 'var(--white-50)', fontSize: '0.85rem' }}>
                No tiene grupos de Active Directory sincronizados.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
