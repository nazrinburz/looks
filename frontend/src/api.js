/**
 * api.js – Centralised fetch wrapper for the Profile Review backend.
 *
 * Usage:
 *   import api from './api';
 *   const { data, error } = await api.get('/profiles');
 *   const { data, error } = await api.post('/auth/login', { email, password });
 */

const BASE_URL =
  import.meta.env.VITE_API_URL ||
  `${window.location.protocol}//${window.location.hostname}:5000/api`;

/**
 * Internal fetch helper – attaches Auth header when a token is stored.
 */
async function request(method, path, body) {
  const token = localStorage.getItem('token');
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const init = { method, headers };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(body);
  }

  let resp;
  try {
    resp = await fetch(`${BASE_URL}${path}`, init);
  } catch {
    return { data: null, error: 'Unable to connect to the server. Please try again.', status: 0 };
  }

  const json = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    // Normalise server errors into a single `message` string
    const message =
      json.error ||
      (json.errors && Object.values(json.errors).join('; ')) ||
      `HTTP ${resp.status}`;
    return { data: null, error: message, status: resp.status };
  }

  return { data: json, error: null, status: resp.status };
}

const api = {
  get:    (path)         => request('GET',    path),
  post:   (path, body)   => request('POST',   path, body),
  patch:  (path, body)   => request('PATCH',  path, body),
  delete: (path)         => request('DELETE', path),
};

export default api;
