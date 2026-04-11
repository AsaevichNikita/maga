(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const apiUrl = document.getElementById('api-url');
    if (apiUrl) apiUrl.textContent = window.API_BASE;
  });
})();