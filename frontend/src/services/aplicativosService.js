import { auth_fetch } from './authFetch';

export const aplicativosService = {
  /**
   * Obtiene la lista de aplicativos autorizados para el usuario actual.
   * Utiliza SIEMPRE auth_fetch con cabeceras Bearer JWT.
   */
  async getAplicativos({ activo, search, orderBy } = {}) {
    const params = new URLSearchParams();
    if (activo !== undefined && activo !== null && activo !== '') {
      params.append('activo', activo);
    }
    if (search && search.trim()) {
      params.append('search', search.trim());
    }
    if (orderBy) {
      params.append('order_by', orderBy);
    }

    const query = params.toString() ? `?${params.toString()}` : '';
    const res = await auth_fetch(`/api/v1/aplicativos/${query}`);
    return res.data;
  },

  /**
   * Obtiene el detalle de un aplicativo por ID.
   */
  async getAplicativoById(id) {
    const res = await auth_fetch(`/api/v1/aplicativos/${id}/`);
    return res.data;
  },

  /**
   * Crea un nuevo aplicativo.
   * Soporta tanto JSON como FormData (para subida de archivo de logo).
   */
  async createAplicativo(payload) {
    let body;
    let headers = {};

    if (payload instanceof FormData) {
      body = payload;
      // El navegador asigna el Content-Type multipart automáticamente con su boundary
    } else {
      body = JSON.stringify(payload);
      headers['Content-Type'] = 'application/json';
    }

    const res = await auth_fetch('/api/v1/aplicativos/', {
      method: 'POST',
      headers,
      body,
    });
    return res.data;
  },

  /**
   * Actualiza un aplicativo existente (PATCH).
   */
  async updateAplicativo(id, payload) {
    let body;
    let headers = {};

    if (payload instanceof FormData) {
      body = payload;
    } else {
      body = JSON.stringify(payload);
      headers['Content-Type'] = 'application/json';
    }

    const res = await auth_fetch(`/api/v1/aplicativos/${id}/`, {
      method: 'PATCH',
      headers,
      body,
    });
    return res.data;
  },

  /**
   * Elimina un aplicativo por ID.
   */
  async deleteAplicativo(id) {
    const res = await auth_fetch(`/api/v1/aplicativos/${id}/`, {
      method: 'DELETE',
    });
    return res.data;
  },
};
