import React from 'react';
import { 
  LayoutGrid, 
  BarChart3, 
  Users, 
  Building, 
  CheckCircle2, 
  Layers, 
  ExternalLink, 
  LogOut, 
  ChevronLeft, 
  ChevronRight, 
  ShieldCheck,
  Sparkles
} from 'lucide-react';
import { sanitizeSafeUrl } from '../services/authFetch';

export default function Sidebar({
  user,
  apps = [],
  activeTab = 'launchpad',
  onSelectTab,
  activeFilter = 'all',
  onSelectFilter,
  onLogout,
  isCollapsed = false,
  onToggleCollapse,
}) {
  const department = user?.profile?.department || 'Comercial';
  const activeCount = apps.filter((a) => a.activo).length;
  const deptCount = apps.filter((a) => {
    const depts = (a.departamentos_ad || []).map((d) => d.toLowerCase().trim());
    return depts.includes(department.toLowerCase().trim());
  }).length;

  // Primeros 3 aplicativos para accesos rápidos en la barra lateral
  const quickApps = apps.slice(0, 3);

  return (
    <aside 
      className={`dashboard-sidebar ${isCollapsed ? 'sidebar-collapsed' : ''}`}
      id="dashboard-main-sidebar"
    >
      {/* Cabecera del Sidebar con Marca y Botón de Colapso */}
      <div className="sidebar-header" id="sidebar-header-section">
        <div className="sidebar-brand-wrapper" id="sidebar-brand-wrapper">
          <div className="sidebar-brand-icon" id="sidebar-brand-icon">
            <Layers size={22} color="#ffffff" />
          </div>
          {!isCollapsed && (
            <div className="sidebar-brand-text">
              <span className="sidebar-brand-title">Gestión Comercial</span>
              <span className="sidebar-brand-badge">Launchpad AD</span>
            </div>
          )}
        </div>

        <button
          id="btn-toggle-sidebar"
          className="btn-sidebar-toggle"
          onClick={onToggleCollapse}
          title={isCollapsed ? 'Expandir barra lateral' : 'Contraer barra lateral'}
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Contenido desplazable del Sidebar */}
      <div className="sidebar-nav-container">
        {/* Sección: Vistas del Sistema */}
        <div className="sidebar-nav-group">
          {!isCollapsed && <span className="sidebar-group-title">Navegación</span>}
          
          <button
            id="nav-tab-launchpad"
            className={`sidebar-nav-item ${activeTab === 'launchpad' ? 'active' : ''}`}
            onClick={() => onSelectTab('launchpad')}
            title="Launchpad de Aplicativos"
          >
            <LayoutGrid size={18} className="sidebar-item-icon" />
            {!isCollapsed && (
              <>
                <span className="sidebar-item-label">Aplicativos</span>
                <span className="sidebar-item-count">{apps.length}</span>
              </>
            )}
          </button>

          <button
            id="nav-tab-analytics"
            className={`sidebar-nav-item ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => onSelectTab('analytics')}
            title="Métricas y Analíticas"
          >
            <BarChart3 size={18} className="sidebar-item-icon" />
            {!isCollapsed && (
              <span className="sidebar-item-label">Métricas Globales</span>
            )}
          </button>

          <button
            id="nav-tab-directory"
            className={`sidebar-nav-item ${activeTab === 'directory' ? 'active' : ''}`}
            onClick={() => onSelectTab('directory')}
            title="Directorio Active Directory"
          >
            <Users size={18} className="sidebar-item-icon" />
            {!isCollapsed && (
              <span className="sidebar-item-label">Directorio AD</span>
            )}
          </button>
        </div>

        {/* Sección: Filtros Rápidos (solo visible en pestaña launchpad) */}
        {activeTab === 'launchpad' && (
          <div className="sidebar-nav-group">
            {!isCollapsed && <span className="sidebar-group-title">Filtros Rápidos</span>}

            <button
              id="filter-sidebar-all"
              className={`sidebar-nav-item ${activeFilter === 'all' ? 'active-filter' : ''}`}
              onClick={() => onSelectFilter('all')}
              title="Todos los aplicativos"
            >
              <Sparkles size={16} className="sidebar-item-icon" />
              {!isCollapsed && (
                <>
                  <span className="sidebar-item-label">Todos</span>
                  <span className="sidebar-item-pill">{apps.length}</span>
                </>
              )}
            </button>

            {department && (
              <button
                id="filter-sidebar-dept"
                className={`sidebar-nav-item ${activeFilter === 'dept' ? 'active-filter' : ''}`}
                onClick={() => onSelectFilter('dept')}
                title={`Aplicativos de ${department}`}
              >
                <Building size={16} className="sidebar-item-icon" />
                {!isCollapsed && (
                  <>
                    <span className="sidebar-item-label">Mi Departamento</span>
                    <span className="sidebar-item-pill">{deptCount}</span>
                  </>
                )}
              </button>
            )}

            <button
              id="filter-sidebar-active"
              className={`sidebar-nav-item ${activeFilter === 'active' ? 'active-filter' : ''}`}
              onClick={() => onSelectFilter('active')}
              title="Aplicativos activos"
            >
              <CheckCircle2 size={16} className="sidebar-item-icon" />
              {!isCollapsed && (
                <>
                  <span className="sidebar-item-label">Activos</span>
                  <span className="sidebar-item-pill">{activeCount}</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Sección: Accesos Directos (Top Aplicativos) */}
        {!isCollapsed && quickApps.length > 0 && (
          <div className="sidebar-nav-group">
            <span className="sidebar-group-title">Accesos Directos</span>
            <div className="sidebar-quick-apps">
              {quickApps.map((item) => (
                <a
                  key={item.id}
                  id={`quick-app-link-${item.id}`}
                  href={sanitizeSafeUrl(item.url)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="sidebar-quick-app-item"
                  title={`Abrir ${item.nombre}`}
                >
                  <div className="quick-app-logo">
                    {item.logo ? (
                      <img src={item.logo} alt={item.nombre} />
                    ) : (
                      <span>{item.nombre.slice(0, 2).toUpperCase()}</span>
                    )}
                  </div>
                  <span className="quick-app-name">{item.nombre}</span>
                  <ExternalLink size={12} className="quick-app-ext" />
                </a>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Pie del Sidebar: Usuario y Logout */}
      <div className="sidebar-footer" id="sidebar-user-footer">
        <div className="sidebar-user-card" id="sidebar-user-card">
          <div className="user-avatar-circle" id="sidebar-user-avatar">
            {user?.first_name ? user.first_name[0].toUpperCase() : (user?.username?.[0]?.toUpperCase() || 'U')}
          </div>
          {!isCollapsed && (
            <div className="sidebar-user-info">
              <span className="sidebar-user-name" id="sidebar-user-name">
                {user?.full_name || user?.username}
              </span>
              <span className="sidebar-user-dept" id="sidebar-user-dept">
                {department}
              </span>
            </div>
          )}
          <button
            id="btn-sidebar-logout"
            className="btn-sidebar-logout"
            onClick={onLogout}
            title="Cerrar Sesión"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
