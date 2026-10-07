import React, { useState, useEffect } from 'react';
import { BarChart3, Users, Server, Shield, CheckCircle, Database, RefreshCw } from 'lucide-react';
import { auth_fetch } from '../services/authFetch';

export default function AnalyticsView({ showToast }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await auth_fetch('/api/v1/dashboard/stats/');
      setStats(res.data);
    } catch (err) {
      showToast(err.message || 'Error al obtener métricas del sistema.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading && !stats) {
    return (
      <div style={{ textAlign: 'center', padding: '5rem', color: 'var(--white-70)' }}>
        <RefreshCw size={32} className="spinner-icon" style={{ margin: '0 auto 1rem' }} />
        <p>Cargando analíticas del servidor...</p>
      </div>
    );
  }

  const users = stats?.users || {};
  const depts = stats?.departments || [];
  const system = stats?.system || {};

  return (
    <div className="analytics-container" id="analytics-view-container">
      {/* Encabezado */}
      <div className="dashboard-header">
        <div>
          <h2 style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--white)', letterSpacing: '-0.02em' }}>
            Métricas del Sistema y Directorio
          </h2>
          <p style={{ color: 'var(--white-70)', fontSize: '0.92rem' }}>
            Monitoreo en tiempo real de usuarios, departamentos y estado del backend.
          </p>
        </div>
        <button id="btn-refresh-stats" className="btn btn-glass btn-sm" onClick={fetchStats} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spinner-icon' : ''} />
          <span>Actualizar Datos</span>
        </button>
      </div>

      {/* Tarjetas de Usuarios */}
      <div className="stats-grid">
        <div className="stat-card-glass">
          <div className="stat-icon-box stat-icon-blue">
            <Users size={24} />
          </div>
          <div>
            <div className="stat-value">{users.total || 0}</div>
            <div className="stat-title">Total Usuarios Registrados</div>
          </div>
        </div>

        <div className="stat-card-glass">
          <div className="stat-icon-box stat-icon-green">
            <CheckCircle size={24} />
          </div>
          <div>
            <div className="stat-value">{users.active || 0}</div>
            <div className="stat-title">Cuentas Activas</div>
          </div>
        </div>

        <div className="stat-card-glass">
          <div className="stat-icon-box stat-icon-cyan">
            <Shield size={24} />
          </div>
          <div>
            <div className="stat-value">{users.staff || 0}</div>
            <div className="stat-title">Operadores Staff</div>
          </div>
        </div>

        <div className="stat-card-glass">
          <div className="stat-icon-box stat-icon-purple">
            <Server size={24} />
          </div>
          <div>
            <div className="stat-value">{users.superusers || 0}</div>
            <div className="stat-title">Superadministradores</div>
          </div>
        </div>
      </div>

      {/* Grid de 2 columnas: Distribución de Departamentos y Estado del Sistema */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem', marginTop: '1rem' }}>
        {/* Distribución por Departamento */}
        <div className="app-card-glass" style={{ padding: '1.75rem' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <BarChart3 size={18} color="var(--corporate-cyan-light)" />
            <span>Usuarios por Departamento AD</span>
          </h3>

          {depts.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {depts.map((d, idx) => {
                const percentage = users.total ? Math.round((d.count / users.total) * 100) : 0;
                return (
                  <div key={idx}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
                      <span style={{ fontWeight: 600 }}>{d.name}</span>
                      <span style={{ color: 'var(--corporate-cyan-light)' }}>{d.count} ({percentage}%)</span>
                    </div>
                    <div style={{ height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div 
                        style={{ 
                          height: '100%', 
                          width: `${percentage}%`, 
                          background: 'linear-gradient(90deg, var(--corporate-blue-600), var(--corporate-cyan))',
                          borderRadius: '4px',
                          transition: 'width 0.8s ease'
                        }} 
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p style={{ color: 'var(--white-50)', fontSize: '0.88rem' }}>No hay registros de departamentos sincronizados.</p>
          )}
        </div>

        {/* Estado del Entorno de Ejecución */}
        <div className="app-card-glass" style={{ padding: '1.75rem' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Database size={18} color="var(--corporate-cyan-light)" />
            <span>Entorno y Seguridad del Backend</span>
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem', fontSize: '0.88rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.6rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ color: 'var(--white-70)' }}>Entorno Activo:</span>
              <span className="badge-pill badge-active" style={{ textTransform: 'uppercase' }}>{system.environment || 'development'}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.6rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ color: 'var(--white-70)' }}>Motor de Base de Datos:</span>
              <span style={{ fontWeight: 600, color: 'var(--white)' }}>{system.database_engine || 'sqlite3'}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.6rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ color: 'var(--white-70)' }}>Active Directory / LDAP:</span>
              <span className={`badge-pill ${system.ldap_enabled ? 'badge-active' : 'badge-ad-group'}`}>
                {system.ldap_enabled ? 'Habilitado' : 'Modo Local'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--white-70)' }}>Versión de la API REST:</span>
              <span style={{ fontWeight: 600, color: 'var(--corporate-cyan-light)' }}>{system.api_version || 'api/v1'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
