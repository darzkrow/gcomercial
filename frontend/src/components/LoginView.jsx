import React, { useState } from 'react';
import { User, Lock, ShieldCheck, ArrowRight, Loader2, AlertCircle, Building2 } from 'lucide-react';

export default function LoginView({ onLoginSuccess, showToast }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setErrorMsg('Por favor ingrese su usuario y contraseña.');
      return;
    }

    setLoading(true);
    setErrorMsg('');

    try {
      const response = await fetch('/api/v1/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username.trim(),
          password: password.trim(),
          remember_me: rememberMe,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Credenciales inválidas o acceso no autorizado.');
      }

      showToast(`¡Bienvenido/a, ${data.data.user.full_name || data.data.user.username}!`, 'success');
      onLoginSuccess(data.data);
    } catch (err) {
      setErrorMsg(err.message || 'Error al conectar con el servidor.');
      showToast(err.message || 'Error en inicio de sesión', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-wrapper" id="login-screen-wrapper">
      <div className="login-card" id="login-card-container">
        {/* Encabezado del Login */}
        <div className="login-header" id="login-header-section">
          <div className="login-logo-glow" id="login-logo-glow">
            <Building2 size={28} color="#ffffff" />
          </div>
          <h2 className="login-title" id="login-main-title">Portal Corporativo</h2>
          <p className="login-subtitle" id="login-subtitle-desc">
            Acceso seguro a aplicativos de Gestión Comercial
          </p>

          <div className="ad-notice-pill" id="ad-notice-indicator">
            <ShieldCheck size={14} />
            <span>Autenticación Active Directory (AD / LDAP) o Local</span>
          </div>
        </div>

        {/* Mensaje de Error */}
        {errorMsg && (
          <div 
            id="login-error-alert"
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              borderRadius: 'var(--radius-md)',
              padding: '0.75rem 1rem',
              marginBottom: '1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
              color: '#fca5a5',
              fontSize: '0.84rem',
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Formulario de Login */}
        <form onSubmit={handleSubmit} id="login-form">
          <div className="form-group" id="group-input-username">
            <label className="form-label" htmlFor="input-username">
              Usuario de Dominio o Local
            </label>
            <div className="input-glass-container">
              <span className="input-icon-left">
                <User size={18} />
              </span>
              <input
                id="input-username"
                type="text"
                className="input-glass"
                placeholder="ej. carlos.perez o usuario"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group" id="group-input-password">
            <label className="form-label" htmlFor="input-password">
              Contraseña
            </label>
            <div className="input-glass-container">
              <span className="input-icon-left">
                <Lock size={18} />
              </span>
              <input
                id="input-password"
                type="password"
                className="input-glass"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-checkbox-row" id="group-remember-me">
            <label className="checkbox-label" htmlFor="input-remember-me">
              <input
                id="input-remember-me"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={loading}
              />
              <span>Mantener sesión iniciada</span>
            </label>
          </div>

          <button
            id="btn-submit-login"
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.85rem' }}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 size={18} className="spinner-icon" />
                <span>Verificando credenciales...</span>
              </>
            ) : (
              <>
                <span>Ingresar al Portal</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.75rem', fontSize: '0.75rem', color: 'var(--white-50)' }}>
          Protegido con Tokens Criptográficos JWT y Políticas de Grupo (GPO)
        </div>
      </div>
    </div>
  );
}
