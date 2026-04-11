(function () {
  function getCurrentUser() {
    try {
      return JSON.parse(localStorage.getItem('auth_user') || 'null');
    } catch {
      return null;
    }
  }

  function getCurrentRoles() {
    const user = getCurrentUser();
    return Array.isArray(user?.roles) ? user.roles : [];
  }

  function hasAnyRole(requiredRoles = [], userRoles = []) {
    if (!requiredRoles.length) return true;
    return requiredRoles.some((role) => userRoles.includes(role));
  }

  function syncRoleCache() {
    window.currentUserRoles = getCurrentRoles();
    return window.currentUserRoles;
  }

  function applyRoleVisibility() {
    const userRoles = syncRoleCache();

    document.querySelectorAll('[data-roles]').forEach((node) => {
      const raw = node.getAttribute('data-roles') || '';
      const requiredRoles = raw
        .split(',')
        .map((x) => x.trim())
        .filter(Boolean);

      const visible = hasAnyRole(requiredRoles, userRoles);

      if (visible) {
        node.style.display = '';
        node.classList.remove('hidden-by-role');
      } else {
        node.style.display = 'none';
        node.classList.add('hidden-by-role');
      }
    });

    document.querySelectorAll('[data-role-note]').forEach((node) => {
      const raw = node.getAttribute('data-role-note') || '';
      const requiredRoles = raw
        .split(',')
        .map((x) => x.trim())
        .filter(Boolean);

      const visible = hasAnyRole(requiredRoles, userRoles);
      node.style.display = visible ? '' : 'none';
    });
  }

  syncRoleCache();

  window.getCurrentUser = getCurrentUser;
  window.getCurrentRoles = getCurrentRoles;
  window.applyRoleVisibility = applyRoleVisibility;
})();
