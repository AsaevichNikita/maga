(function () {
  const STORAGE = {
    accessToken: 'access_token',
    accessTokenLegacy: 'token',
    refreshToken: 'refresh_token',
    idToken: 'id_token',
    authUser: 'auth_user',
    pkceVerifier: 'pkce_verifier',
    authState: 'auth_state',
    postLoginPath: 'post_login_path'
  };

  function b64UrlEncode(arrayBuffer) {
    const bytes = new Uint8Array(arrayBuffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i += 1) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  }

  function randomString(length = 64) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
    let result = '';
    const random = crypto.getRandomValues(new Uint8Array(length));
    for (let i = 0; i < length; i += 1) {
      result += chars[random[i] % chars.length];
    }
    return result;
  }

  async function sha256(value) {
    const encoder = new TextEncoder();
    const data = encoder.encode(value);
    return crypto.subtle.digest('SHA-256', data);
  }

  function parseJwt(token) {
    try {
      const payload = token.split('.')[1];
      const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
      const json = atob(normalized);
      return JSON.parse(json);
    } catch {
      return null;
    }
  }

  function getStoredToken() {
    return localStorage.getItem(STORAGE.accessToken) || localStorage.getItem(STORAGE.accessTokenLegacy);
  }

  function getStoredUser() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE.authUser) || 'null');
    } catch {
      return null;
    }
  }

  function syncAuthGlobals() {
    const user = getStoredUser();
    window.currentUserRoles = Array.isArray(user?.roles) ? user.roles : [];
  }

  function saveTokens(tokenData) {
    if (tokenData.access_token) {
      localStorage.setItem(STORAGE.accessToken, tokenData.access_token);
      localStorage.setItem(STORAGE.accessTokenLegacy, tokenData.access_token);
    }
    if (tokenData.refresh_token) localStorage.setItem(STORAGE.refreshToken, tokenData.refresh_token);
    if (tokenData.id_token) localStorage.setItem(STORAGE.idToken, tokenData.id_token);
  }

  function saveUser(user) {
    localStorage.setItem(STORAGE.authUser, JSON.stringify(user));
    syncAuthGlobals();
  }

  function clearTokens() {
    localStorage.removeItem(STORAGE.accessToken);
    localStorage.removeItem(STORAGE.accessTokenLegacy);
    localStorage.removeItem(STORAGE.refreshToken);
    localStorage.removeItem(STORAGE.idToken);
    localStorage.removeItem(STORAGE.authUser);
    localStorage.removeItem(STORAGE.pkceVerifier);
    localStorage.removeItem(STORAGE.authState);
    localStorage.removeItem(STORAGE.postLoginPath);
    syncAuthGlobals();
  }

  function renderAuthState() {
    const loginBtn = document.getElementById('auth-login-btn');
    const logoutBtn = document.getElementById('auth-logout-btn');
    const userBox = document.getElementById('auth-user-box');

    if (!loginBtn || !logoutBtn || !userBox) return;

    const token = getStoredToken();
    const user = getStoredUser();

    if (token && user) {
      loginBtn.style.display = 'none';
      logoutBtn.style.display = 'inline-flex';

      const roles = user.roles || [];
      userBox.innerHTML = `
        <div><strong>${user.preferred_username || 'user'}</strong></div>
        <div style="font-size:12px; opacity:.8;">${user.email || 'без email'}</div>
        <div style="font-size:12px; opacity:.8;">${roles.join(', ') || 'без ролей'}</div>
      `;
    } else {
      loginBtn.style.display = 'inline-flex';
      logoutBtn.style.display = 'none';
      userBox.innerHTML = `<div style="font-size:13px; opacity:.8;">Не авторизован</div>`;
    }
  }

  async function loadBackendAuthConfig() {
    const response = await fetch('/api/auth/config', {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) {
      const text = await response.text().catch(() => '');
      throw new Error(`/api/auth/config -> ${response.status} ${text}`);
    }

    return response.json();
  }

  async function startLogin() {
    try {
      const cfg = await loadBackendAuthConfig();

      const verifier = randomString(96);
      const challenge = b64UrlEncode(await sha256(verifier));
      const state = randomString(24);

      localStorage.setItem(STORAGE.pkceVerifier, verifier);
      localStorage.setItem(STORAGE.authState, state);
      localStorage.setItem(
        STORAGE.postLoginPath,
        window.location.pathname + window.location.search + window.location.hash
      );

      const params = new URLSearchParams({
        client_id: cfg.client_id,
        redirect_uri: cfg.redirect_uri,
        response_type: 'code',
        scope: 'openid profile email',
        code_challenge: challenge,
        code_challenge_method: 'S256',
        state
      });

      window.location.href = `${cfg.authorize_url}?${params.toString()}`;
    } catch (error) {
      console.error('startLogin error:', error);
      alert(`Ошибка запуска авторизации: ${error.message}`);
    }
  }

  async function finishLoginIfNeeded() {
    const url = new URL(window.location.href);
    const code = url.searchParams.get('code');
    const returnedState = url.searchParams.get('state');

    if (!code) return false;

    const expectedState = localStorage.getItem(STORAGE.authState);
    if (expectedState && returnedState && expectedState !== returnedState) {
      alert('Не удалось завершить вход: state не совпал');
      return false;
    }

    const cfg = await loadBackendAuthConfig();
    const codeVerifier = localStorage.getItem(STORAGE.pkceVerifier);

    const response = await fetch('/api/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code,
        redirect_uri: cfg.redirect_uri,
        code_verifier: codeVerifier
      })
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok || !data.access_token) {
      console.error('Token exchange failed', data);
      alert('Не удалось завершить вход');
      return false;
    }

    saveTokens(data);

    const jwt = parseJwt(data.access_token) || {};
    const roles = (jwt.realm_access && jwt.realm_access.roles) || [];

    saveUser({
      preferred_username: jwt.preferred_username,
      email: jwt.email,
      sub: jwt.sub,
      roles
    });

    localStorage.removeItem(STORAGE.pkceVerifier);
    localStorage.removeItem(STORAGE.authState);

    const restorePath = localStorage.getItem(STORAGE.postLoginPath) || url.pathname + url.hash;
    localStorage.removeItem(STORAGE.postLoginPath);

    url.searchParams.delete('code');
    url.searchParams.delete('state');
    url.searchParams.delete('session_state');

    window.history.replaceState({}, document.title, restorePath || url.pathname + url.hash);

    renderAuthState();
    return true;
  }

  async function logout() {
    const idToken = localStorage.getItem(STORAGE.idToken);
    const postLogoutRedirectUri = `${window.location.origin}/index.html`;

    clearTokens();
    renderAuthState();

    try {
      if (window.applyRoleVisibility) window.applyRoleVisibility();
    } catch (e) {
      console.error('applyRoleVisibility error after logout:', e);
    }

    try {
      const response = await fetch('/api/auth/logout-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          post_logout_redirect_uri: postLogoutRedirectUri,
          id_token_hint: idToken
        })
      });

      const data = await response.json();
      if (data.logout_url) {
        window.location.href = data.logout_url;
        return;
      }
    } catch (e) {
      console.error('logout error:', e);
    }

    window.location.href = postLogoutRedirectUri;
  }

  function bindAuthButtons() {
    const loginBtn = document.getElementById('auth-login-btn');
    const logoutBtn = document.getElementById('auth-logout-btn');

    if (loginBtn && !loginBtn.dataset.authBound) {
      loginBtn.addEventListener('click', startLogin);
      loginBtn.dataset.authBound = '1';
    }

    if (logoutBtn && !logoutBtn.dataset.authBound) {
      logoutBtn.addEventListener('click', logout);
      logoutBtn.dataset.authBound = '1';
    }
  }

  async function initAuth() {
    bindAuthButtons();
    syncAuthGlobals();

    try {
      await finishLoginIfNeeded();
    } catch (e) {
      console.error('finishLoginIfNeeded error:', e);
    }

    try {
      renderAuthState();
    } catch (e) {
      console.error('renderAuthState error:', e);
    }

    try {
      if (window.applyRoleVisibility) window.applyRoleVisibility();
    } catch (e) {
      console.error('applyRoleVisibility error:', e);
    }
  }

  window.getAccessToken = getStoredToken;
  window.getCurrentAuthUser = getStoredUser;
  window.authInit = initAuth;
  window.authLogout = logout;
})();