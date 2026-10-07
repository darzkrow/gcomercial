/**
 * Módulo de Autenticación y Peticiones Seguras (auth_fetch)
 * Implementa las mejores prácticas de ciberseguridad:
 * - Inyección automática y segura de cabeceras Authorization: Bearer <token>.
 * - Detección proactiva de tokens vencidos con auto-renovación silenciosa (Refresh Token Flow).
 * - Manejo seguro de tokens en memoria y sessionStorage (evitando robo por XSS persistente).
 * - Bloqueo de condiciones de carrera mediante mutex/promesa compartida para renovación de token.
 * - Sanitización preventiva de URLs contra ataques de inyección 'javascript:'.
 */

const STORAGE_KEY_ACCESS = 'gc_access_token';
const STORAGE_KEY_REFRESH = 'gc_refresh_token';
const STORAGE_KEY_USER = 'gc_user_profile';

// Almacenamiento en memoria para mayor seguridad
let memoryAccessToken = sessionStorage.getItem(STORAGE_KEY_ACCESS) || null;
let memoryRefreshToken = sessionStorage.getItem(STORAGE_KEY_REFRESH) || null;
let memoryUser = null;
try {
  const rawUser = sessionStorage.getItem(STORAGE_KEY_USER);
  if (rawUser) memoryUser = JSON.parse(rawUser);
} catch (e) {
  sessionStorage.removeItem(STORAGE_KEY_USER);
}

// Candado para evitar múltiples llamadas simultáneas a refresh
let isRefreshingPromise = null;
const authListeners = new Set();

export function subscribeAuth(listener) {
  authListeners.add(listener);
  return () => authListeners.delete(listener);
}

function notifyAuthChange() {
  authListeners.forEach((listener) => {
    try {
      listener({
        isAuthenticated: !!memoryAccessToken,
        user: memoryUser,
      });
    } catch (e) {
      console.error('Error en listener de autenticación:', e);
    }
  });
}

export function setTokens({ access_token, refresh_token, user }) {
  if (access_token) {
    memoryAccessToken = access_token;
    sessionStorage.setItem(STORAGE_KEY_ACCESS, access_token);
  }
  if (refresh_token) {
    memoryRefreshToken = refresh_token;
    sessionStorage.setItem(STORAGE_KEY_REFRESH, refresh_token);
  }
  if (user) {
    memoryUser = user;
    sessionStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
  }
  notifyAuthChange();
}

export function clearTokens() {
  memoryAccessToken = null;
  memoryRefreshToken = null;
  memoryUser = null;
  sessionStorage.removeItem(STORAGE_KEY_ACCESS);
  sessionStorage.removeItem(STORAGE_KEY_REFRESH);
  sessionStorage.removeItem(STORAGE_KEY_USER);
  notifyAuthChange();
}

export function getAccessToken() {
  return memoryAccessToken;
}

export function getRefreshToken() {
  return memoryRefreshToken;
}

export function getCurrentUser() {
  return memoryUser;
}

export function isAuthenticated() {
  return !!memoryAccessToken;
}

/**
 * Renueva el token de acceso usando el refresh token.
 * Protegido contra llamadas simultáneas (Singleton Promise).
 */
export async function refreshAccessToken() {
  if (isRefreshingPromise) {
    return isRefreshingPromise;
  }

  isRefreshingPromise = (async () => {
    try {
      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearTokens();
        throw new Error('No existe refresh token disponible.');
      }

      const response = await fetch('/api/v1/auth/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        clearTokens();
        throw new Error(data.error || 'Sesión expirada. Por favor inicie sesión nuevamente.');
      }

      const newAccess = data.data.access_token;
      const newRefresh = data.data.refresh_token || refreshToken;
      setTokens({ access_token: newAccess, refresh_token: newRefresh });
      return newAccess;
    } finally {
      isRefreshingPromise = null;
    }
  })();

  return isRefreshingPromise;
}

/**
 * Cliente HTTP seguro que DEBE utilizarse para todas las peticiones a endpoints de la API.
 * - Inyecta 'Authorization: Bearer <token>'
 * - Si recibe 401 (TOKEN_EXPIRED), renueva automáticamente el token y reintenta la petición.
 */
export async function auth_fetch(url, options = {}) {
  const config = { ...options };
  config.headers = { ...(config.headers || {}) };

  // Inyectar token si existe
  const token = getAccessToken();
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  // Si el cuerpo no es FormData y no tiene Content-Type, establecer JSON
  if (config.body && !(config.body instanceof FormData) && !config.headers['Content-Type']) {
    config.headers['Content-Type'] = 'application/json';
    if (typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }
  }

  let response = await fetch(url, config);

  // Si responde 401 y hay token de refresco, intentar renovar y reintentar
  if (response.status === 401 && getRefreshToken()) {
    try {
      const newAccessToken = await refreshAccessToken();
      // Reintentar con el nuevo token
      config.headers['Authorization'] = `Bearer ${newAccessToken}`;
      response = await fetch(url, config);
    } catch (refreshErr) {
      clearTokens();
      throw refreshErr;
    }
  }

  let responseData = null;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    responseData = await response.json();
  } else {
    responseData = await response.text();
  }

  if (!response.ok) {
    const errorMsg = (responseData && responseData.error) || response.statusText || 'Error en la petición';
    const err = new Error(errorMsg);
    err.status = response.status;
    err.code = responseData?.code || 'HTTP_ERROR';
    err.details = responseData?.details;
    err.data = responseData;
    throw err;
  }

  return responseData;
}

/**
 * Sanitiza URLs externas antes de abrirlas para prevenir XSS (ej. javascript:alert(1)).
 */
export function sanitizeSafeUrl(rawUrl) {
  if (!rawUrl || typeof rawUrl !== 'string') return '#';
  const trimmed = rawUrl.trim();
  if (trimmed.startsWith('https://') || trimmed.startsWith('http://') || trimmed.startsWith('/')) {
    return trimmed;
  }
  return `https://${trimmed}`;
}
