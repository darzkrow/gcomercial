import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import LoginView from './components/LoginView';
import StatsOverview from './components/StatsOverview';
import AplicativoCard from './components/AplicativoCard';
import AplicativoModal from './components/AplicativoModal';
import DeleteConfirmModal from './components/DeleteConfirmModal';
import AnalyticsView from './components/AnalyticsView';
import DirectoryView from './components/DirectoryView';
import ToastContainer from './components/Toast';
import { aplicativosService } from './services/aplicativosService';
import { authService } from './services/authService';
import { subscribeAuth, isAuthenticated, getCurrentUser } from './services/authFetch';
import { Plus, Search, RefreshCw, Layers, ShieldAlert, Sparkles, Filter } from 'lucide-react';

export default function App() {
  const [authed, setAuthed] = useState(isAuthenticated());
  const [currentUser, setCurrentUser] = useState(getCurrentUser());
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Navegación del Dashboard
  const [activeTab, setActiveTab] = useState('launchpad'); // 'launchpad' | 'analytics' | 'directory'
  const [activeFilter, setActiveFilter] = useState('all'); // 'all' | 'dept' | 'active'
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Modales
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingApp, setEditingApp] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [appToDelete, setAppToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Notificaciones Toast
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const dismissToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Suscribirse a cambios de estado de autenticación (ej. cuando expira el token o hace logout)
  useEffect(() => {
    const unsubscribe = subscribeAuth(({ isAuthenticated: newAuth, user: newUser }) => {
      setAuthed(newAuth);
      setCurrentUser(newUser);
      if (!newAuth) {
        setApps([]);
      }
    });
    return unsubscribe;
  }, []);

  // Cargar lista de aplicativos usando SIEMPRE auth_fetch
  const fetchApps = useCallback(async () => {
    if (!authed) return;
    setLoading(true);
    try {
      const data = await aplicativosService.getAplicativos({ search: searchQuery });
      setApps(data.aplicativos || []);
    } catch (err) {
      console.error('Error al cargar aplicativos:', err);
      showToast(err.message || 'Error al obtener los aplicativos.', 'error');
    } finally {
      setLoading(false);
    }
  }, [authed, searchQuery, showToast]);

  useEffect(() => {
    if (authed) {
      fetchApps();
    }
  }, [authed, fetchApps]);

  // Manejo de inicio de sesión exitoso
  const handleLoginSuccess = (loginData) => {
    setAuthed(true);
    setCurrentUser(loginData.user);
    setActiveTab('launchpad');
  };

  // Manejo de cierre de sesión
  const handleLogout = async () => {
    try {
      await authService.logout();
      showToast('Sesión cerrada correctamente.', 'info');
    } catch (e) {
      console.error(e);
    }
  };

  // Guardar (Crear o Actualizar) Aplicativo
  const handleSaveApp = async (payload) => {
    setIsSaving(true);
    try {
      if (editingApp) {
        await aplicativosService.updateAplicativo(editingApp.id, payload);
        showToast(`Aplicativo '${editingApp.nombre}' actualizado con éxito.`, 'success');
      } else {
        const created = await aplicativosService.createAplicativo(payload);
        showToast(`Aplicativo '${created.nombre}' creado exitosamente.`, 'success');
      }
      setIsModalOpen(false);
      setEditingApp(null);
      await fetchApps();
    } catch (err) {
      showToast(err.message || 'No fue posible guardar el aplicativo.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  // Confirmar y Ejecutar Eliminación
  const handleConfirmDelete = async (appId) => {
    setIsDeleting(true);
    try {
      await aplicativosService.deleteAplicativo(appId);
      showToast('Aplicativo eliminado correctamente.', 'success');
      setAppToDelete(null);
      await fetchApps();
    } catch (err) {
      showToast(err.message || 'No fue posible eliminar el aplicativo.', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  // Filtrado en el cliente para el filtro rápido de departamento y estado
  const userDept = (currentUser?.profile?.department || '').toLowerCase().trim();
  const displayedApps = apps.filter((app) => {
    if (activeFilter === 'dept' && userDept) {
      const appDepts = (app.departamentos_ad || []).map((d) => d.toLowerCase().trim());
      if (!appDepts.includes(userDept)) return false;
    }
    if (activeFilter === 'active') {
      if (!app.activo) return false;
    }
    return true;
  });

  return (
    <div className="app-container" id="app-root-container">
      {/* Fondo con resplandores orbes ambientales */}
      <div className="ambient-glow" id="ambient-glow-background">
        <div className="ambient-orb-1" />
        <div className="ambient-orb-2" />
      </div>

      {/* Contenido Principal: Login o Dashboard con Sidebar */}
      {!authed ? (
        <>
          <Navbar user={null} onLogout={handleLogout} />
          <LoginView onLoginSuccess={handleLoginSuccess} showToast={showToast} />
        </>
      ) : (
        <div className="dashboard-layout" id="dashboard-layout-root">
          {/* Barra Lateral Dashboard */}
          <Sidebar
            user={currentUser}
            apps={apps}
            activeTab={activeTab}
            onSelectTab={setActiveTab}
            activeFilter={activeFilter}
            onSelectFilter={setActiveFilter}
            onLogout={handleLogout}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
          />

          {/* Área Principal con Encabezado y Vistas */}
          <div className="dashboard-main-wrapper" id="dashboard-main-wrapper">
            <Navbar 
              user={currentUser} 
              onLogout={handleLogout} 
              activeTab={activeTab}
              onSelectTab={setActiveTab}
            />

            <main className="main-content" id="dashboard-main-content">
              {/* VISTA 1: LAUNCHPAD DE APLICATIVOS */}
              {activeTab === 'launchpad' && (
                <>
                  {/* Bienvenida y Encabezado */}
                  <div className="dashboard-header" id="dashboard-header-container">
                    <div className="welcome-section" id="welcome-text-section">
                      <h2 style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--white)', letterSpacing: '-0.02em' }}>
                        Launchpad de Aplicativos
                      </h2>
                      <p>
                        Accesos directos protegidos con tokens JWT y permisos corporativos de Active Directory.
                      </p>
                    </div>

                    <button
                      id="btn-open-create-modal"
                      className="btn btn-primary"
                      onClick={() => {
                        setEditingApp(null);
                        setIsModalOpen(true);
                      }}
                    >
                      <Plus size={18} />
                      <span>Nuevo Aplicativo</span>
                    </button>
                  </div>

                  {/* Resumen de Estadísticas Glass */}
                  <StatsOverview apps={apps} user={currentUser} />

                  {/* Barra de Herramientas y Búsqueda */}
                  <div className="filter-toolbar-glass" id="filter-toolbar-section">
                    <div className="search-input-wrapper" id="search-input-wrapper">
                      <span className="input-icon-left" style={{ left: '0.9rem' }}>
                        <Search size={16} color="var(--white-50)" />
                      </span>
                      <input
                        id="input-search-apps"
                        type="text"
                        className="input-glass"
                        placeholder="Buscar por nombre, descripción o grupo AD..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        style={{ paddingLeft: '2.5rem' }}
                      />
                    </div>

                    <div className="filter-actions" id="filter-actions-group">
                      {currentUser?.profile?.department && (
                        <button
                          id="btn-filter-my-dept"
                          className={`btn btn-sm ${activeFilter === 'dept' ? 'btn-primary' : 'btn-glass'}`}
                          onClick={() => setActiveFilter((prev) => (prev === 'dept' ? 'all' : 'dept'))}
                        >
                          <Sparkles size={14} />
                          <span>Mi Depto ({currentUser.profile.department})</span>
                        </button>
                      )}

                      <button
                        id="btn-refresh-apps"
                        className="btn btn-glass btn-sm"
                        onClick={fetchApps}
                        disabled={loading}
                        title="Actualizar listado"
                      >
                        <RefreshCw size={14} className={loading ? 'spinner-icon' : ''} />
                        <span>Actualizar</span>
                      </button>
                    </div>
                  </div>

                  {/* Grilla de Aplicativos */}
                  {loading && apps.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--white-70)' }}>
                      <RefreshCw size={28} className="spinner-icon" style={{ margin: '0 auto 1rem' }} />
                      <p>Consultando aplicativos autorizados...</p>
                    </div>
                  ) : displayedApps.length > 0 ? (
                    <div className="apps-grid" id="apps-cards-grid">
                      {displayedApps.map((app) => (
                        <AplicativoCard
                          key={app.id}
                          app={app}
                          onEdit={(item) => {
                            setEditingApp(item);
                            setIsModalOpen(true);
                          }}
                          onDelete={(item) => setAppToDelete(item)}
                          canManage={true}
                        />
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state-glass" id="empty-state-container">
                      <div className="empty-icon-circle">
                        <Layers size={36} />
                      </div>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                        No se encontraron aplicativos
                      </h3>
                      <p style={{ color: 'var(--white-70)', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
                        {searchQuery || activeFilter !== 'all'
                          ? 'No hay aplicativos que coincidan con los filtros de búsqueda o categoría aplicados.'
                          : 'Aún no tiene aplicativos vinculados para sus permisos o grupos de Active Directory.'}
                      </p>
                      {(searchQuery || activeFilter !== 'all') && (
                        <button
                          id="btn-clear-filters"
                          className="btn btn-glass btn-sm"
                          onClick={() => {
                            setSearchQuery('');
                            setActiveFilter('all');
                          }}
                        >
                          Limpiar Filtros
                        </button>
                      )}
                    </div>
                  )}
                </>
              )}

              {/* VISTA 2: MÉTRICAS Y ANALÍTICAS */}
              {activeTab === 'analytics' && (
                <AnalyticsView showToast={showToast} />
              )}

              {/* VISTA 3: DIRECTORIO ACTIVE DIRECTORY */}
              {activeTab === 'directory' && (
                <DirectoryView user={currentUser} />
              )}
            </main>
          </div>
        </div>
      )}

      {/* Modal de Creación / Edición */}
      <AplicativoModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingApp(null);
        }}
        onSave={handleSaveApp}
        app={editingApp}
        isSaving={isSaving}
      />

      {/* Modal de Confirmación de Borrado */}
      <DeleteConfirmModal
        isOpen={!!appToDelete}
        onClose={() => setAppToDelete(null)}
        onConfirm={handleConfirmDelete}
        app={appToDelete}
        isDeleting={isDeleting}
      />

      {/* Contenedor Global de Toasts */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
