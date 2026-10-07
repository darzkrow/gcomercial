import React from 'react';
import { Layers, ShieldCheck, LogOut, LayoutGrid, BarChart3, Users, ChevronRight } from 'lucide-react';

export default function Navbar({ user, onLogout, activeTab = 'launchpad', onSelectTab }) {
  const adGroups = user?.profile?.ad_groups || [];
  const department = user?.profile?.department || 'General';

  const tabLabels = {
    launchpad: { label: 'Launchpad de Aplicativos', icon: <LayoutGrid size={15} /> },
    analytics: { label: 'Métricas y Analíticas Globales', icon: <BarChart3 size={15} /> },
    directory: { label: 'Directorio Active Directory', icon: <Users size={15} /> }
  };

  const currentTabInfo = tabLabels[activeTab] || tabLabels.launchpad;

  return (
    <header className="glass-navbar" id="app-main-navbar">
      {/* Indicador de Ubicación / Breadcrumb Corporativo */}
      <div className="nav-brand" id="brand-container">
        {!user ? (
          <>
            <div className="brand-icon-wrapper" id="brand-logo-icon">
              <Layers size={22} color="#ffffff" />
            </div>
            <div>
              <h1 className="brand-title" id="brand-heading">Gestión Comercial</h1>
              <span className="brand-subtitle" id="brand-subheading">Portal de Aplicativos Corporativos</span>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div className="brand-icon-wrapper" style={{ width: '36px', height: '36px' }}>
              <Layers size={18} color="#ffffff" />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.88rem' }}>
              <span style={{ fontWeight: 700, color: 'var(--white)' }}>Dashboard</span>
              <ChevronRight size={14} color="var(--white-50)" />
              <div 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.4rem', 
                  color: 'var(--corporate-cyan-light)', 
                  fontWeight: 600,
                  background: 'rgba(14, 165, 233, 0.12)',
                  padding: '0.25rem 0.65rem',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid rgba(56, 189, 248, 0.25)'
                }}
              >
                {currentTabInfo.icon}
                <span>{currentTabInfo.label}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Panel de Usuario y Seguridad */}
      {user && (
        <div className="nav-user-panel" id="nav-user-panel">
          {/* Indicador de Seguridad JWT */}
          <div 
            className="user-badge-glass" 
            id="jwt-security-indicator"
            title="Conexión asegurada con JSON Web Tokens (RS256/HS256) y renovación automática"
          >
            <ShieldCheck size={16} color="#38bdf8" />
            <span style={{ fontSize: '0.74rem', color: '#93c5fd', fontWeight: 600 }}>JWT Seguro</span>
          </div>

          {/* Información del Perfil (Active Directory) */}
          <div className="user-badge-glass" id="user-profile-badge">
            <div className="user-avatar-circle" id="user-avatar">
              {user.first_name ? user.first_name[0].toUpperCase() : user.username[0].toUpperCase()}
            </div>
            <div className="user-info-text">
              <span className="user-name" id="user-display-name">
                {user.full_name || user.username}
              </span>
              <span className="user-role-pill" id="user-dept-pill">
                {department} {adGroups.length > 0 && `• ${adGroups.length} Grupos AD`}
              </span>
            </div>
          </div>

          {/* Botón de Cierre de Sesión */}
          <button
            id="btn-nav-logout"
            className="btn btn-glass btn-sm"
            onClick={onLogout}
            title="Cerrar Sesión Segura"
          >
            <LogOut size={16} />
            <span>Salir</span>
          </button>
        </div>
      )}
    </header>
  );
}
