/* Shared URL and bearer-auth handling for every browser request to the API. */
(function (root) {
  function buildApiUrl(path) {
    const base = String(root.CAREERTRACK_API_BASE_URL || '').trim().replace(/\/+$/, '');
    const route = String(path || '');
    const normalizedRoute = route.startsWith('/') ? route : `/${route}`;
    return `${base}${normalizedRoute}`;
  }

  function apiFetch(path, options = {}, accessToken = null, fetchImpl = root.fetch.bind(root)) {
    const headers = new Headers(options.headers || {});
    if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
    return fetchImpl(buildApiUrl(path), {...options, headers});
  }

  const client = {buildApiUrl, apiFetch};
  root.CareerTrackApi = client;
  if (typeof module !== 'undefined' && module.exports) module.exports = client;
})(typeof window !== 'undefined' ? window : globalThis);
