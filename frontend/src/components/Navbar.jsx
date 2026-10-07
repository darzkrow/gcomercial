import React from 'react';
import { Layers, ShieldCheck, LogOut, User, Building, Users } from 'lucide-react';

export default function Navbar({ user, onLogout }) {
  const adGroups = user?.profile?.ad_groups || [];
  const department = user?.profile?.department || 'General';

  return (
    <header className="glass-navbar" id="app-main-navbar">
      {/* Marca Corporativa */}
      <div className="nav-brand" id="brand-container">
        <div className="brand-icon-wrapper" id="brand-logo-icon">
          <Layers size={22} color="#ffffff" />
        </div>
        <div>
          <h1 className="brand-title" id="brand-heading">Gestión Comercial</h1>
          <span className="brand-subtitle" id="brand-subheading">Portal de Aplicativos Corporativos</span>
        </div>
      </div>

      {/* Panel de Usuario y Seguridad */}
      {user && (
        <div className="nav-user-panel" id="nav-user-panel">
          {/* Indicador de Seguridad JWT */}
          <div 
            className="user-badge-glass" 
            id="jwt-security-indicator"
            title="Conexión asegurada con JSON Web Tokens y cifrado corporativo"
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
