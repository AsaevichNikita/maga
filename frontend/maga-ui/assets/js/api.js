(function () {
  function getToken() {
    if (typeof window.getAccessToken === 'function') {
      return window.getAccessToken();
    }
    return localStorage.getItem('access_token') || localStorage.getItem('token');
  }

  async function makeRequest(method, endpoint, data = null) {
    const startTime = Date.now();
    const safeEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = safeEndpoint.startsWith('http')
      ? safeEndpoint
      : `${window.API_BASE}${safeEndpoint}`;

    const headers = { 'Content-Type': 'application/json' };

    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    const options = { method, headers };
    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const responseTime = Date.now() - startTime;

      const rawText = await response.text();

      let responseData = rawText;
      if (rawText) {
        try {
          responseData = JSON.parse(rawText);
        } catch {
          responseData = rawText;
        }
      }

      if (window.displayResponse) {
        window.displayResponse(safeEndpoint, method, response.status, responseData, responseTime);
      }

      return {
        ok: response.ok,
        status: response.status,
        data: responseData,
        responseTime,
      };
    } catch (error) {
      const responseTime = Date.now() - startTime;

      if (window.displayResponse) {
        window.displayResponse(safeEndpoint, method, 0, { error: error.message }, responseTime);
      }

      return {
        ok: false,
        status: 0,
        data: { error: error.message },
        responseTime,
      };
    }
  }

  function toQuery(params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query.append(key, String(value));
      }
    });
    const qs = query.toString();
    return qs ? `?${qs}` : '';
  }

  async function apiGet(endpoint, params = {}) {
    return makeRequest('GET', `${endpoint}${toQuery(params)}`);
  }

  async function apiPost(endpoint, data = {}) {
    return makeRequest('POST', endpoint, data);
  }

  async function apiPut(endpoint, data = {}) {
    return makeRequest('PUT', endpoint, data);
  }

  async function apiDelete(endpoint) {
    return makeRequest('DELETE', endpoint);
  }

  window.makeRequest = makeRequest;
  window.apiGet = apiGet;
  window.apiPost = apiPost;
  window.apiPut = apiPut;
  window.apiDelete = apiDelete;
})();
