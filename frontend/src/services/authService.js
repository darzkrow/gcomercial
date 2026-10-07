import { auth_fetch, setTokens, clearTokens, getCurrentUser, isAuthenticated } from './authFetch';

export const authService = {
  /**
   * Inicia sesión con usuario y contraseña (validación AD/LDAP o local)
   * y guarda de forma segura los tokens JWT.
   */
  async login(username, password, rememberMe = false) {
    const response = await fetch('/api/v1/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username.trim(),
        password: password.trim(),
        remember_me: rememberMe,
      }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      const err = new Error(data.error || 'Credenciales inválidas');
      err.code = data.code || 'LOGIN_FAILED';
      throw err;
    }

    const { user, tokens } = data.data;
    setTokens({
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
      user,
    });

    return { user, tokens };
  },

  /**
   * Cierra la sesión activa en el servidor y limpia tokens locales.
   */
  async logout() {
    try {
      await auth_fetch('/api/v1/auth/logout/', { method: 'POST' });
    } catch (e) {
      console.warn('Error al notificar cierre de sesión al servidor:', e);
    } finally {
      clearTokens();
    }
  },

  /**
   * Obtiene la información del usuario autenticado en la sesión actual.
   */
  async getMe() {
    const data = await auth_fetch('/api/v1/auth/me/');
    return data.data;
  },

  getCurrentUser,
  isAuthenticated,
};
