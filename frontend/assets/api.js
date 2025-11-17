/**
 * API Helper: apiFetch()
 * Utility for making authenticated API calls to the Flask backend.
 * Uses JWT token stored in localStorage (key: 'authToken').
 * 
 * Us *   apiFetch('/api/pets', 'GET').then(r => console.log(r.data))
 *   apiFetch('/api/auth/register', 'POST', { username: 'john', email: 'john@example.com', password: 'pass123', role: 'adopter' })
 */

const API_BASE = 'http://localhost:4000';

/**
 * Make an authenticated API call with JWT token in Authorization header.
 * @param {string} endpoint - API endpoint path (e.g., '/api/pets')
 * @param {string} method - HTTP method (GET, POST, PATCH, DELETE, PUT)
 * @param {object} data - Request body (optional, for POST/PATCH/PUT)
 * @returns {Promise<{status: number, data: object}>} - { status, data }
 */
async function apiFetch(endpoint, method = 'GET', data = null) {
    const token = localStorage.getItem('authToken');

    const headers = { 'Content-Type': 'application/json' };
    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
        console.log('[apiFetch] Token found, using Authorization header');
    } else {
        console.log('[apiFetch] No token, request is unauthenticated');
    }

    const options = { method, headers };
    if (data && (method === 'POST' || method === 'PATCH' || method === 'PUT')) {
        options.body = JSON.stringify(data);
        console.log('[apiFetch]', method, endpoint, 'body:', data);
    } else {
        console.log('[apiFetch]', method, endpoint);
    }

    try {
        const response = await fetch(API_BASE + endpoint, options);
        const contentType = response.headers.get('content-type') || '';
        
        let body;
        if (contentType.includes('application/json')) {
            body = await response.json();
        } else {
            body = { text: await response.text() };
        }

        console.log('[apiFetch] response:', response.status, body);

        // Return status and data for caller to decide how to handle errors
        return { status: response.status, data: body };
    } catch (err) {
        console.error('[apiFetch] ERROR:', err);
        throw err;
    }
}

/**
 * Register a new user and return result.
 * @param {string} username 
 * @param {string} email 
 * @param {string} password 
 * @param {string} role - 'adopter', 'center', or 'admin'
 * @param {object} roleData - role-specific fields (center_name, full_name, etc.)
 * @returns {Promise<object>} - backend response
 */
async function register(username, email, password, role, roleData = {}) {
    const payload = {
        username,
        email,
        password,
        role,
        ...roleData
    };
    const resp = await apiFetch('/api/auth/register', 'POST', payload);
    return resp.data;
}

/**
 * Login user: authenticate and store token + user info.
 * @param {string} email 
 * @param {string} password 
 * @returns {Promise<object>} - backend response
 */
async function login(email, password) {
    const resp = await apiFetch('/api/auth/login', 'POST', { email, password });
    const { status, data } = resp;

    // Backend returns: { message, access_token, user: { user_id, username, email, role } }
    if (status === 200 && data && data.access_token) {
        localStorage.setItem('authToken', data.access_token);
        if (data.user) {
            localStorage.setItem('userId', data.user.user_id || '');
            localStorage.setItem('username', data.user.username || '');
            localStorage.setItem('userRole', data.user.role || '');
        }
        console.log('[login] Success. Token and user stored.');
    } else {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userId');
        localStorage.removeItem('username');
        localStorage.removeItem('userRole');
        console.log('[login] Failed. Cleared token.');
    }

    return data;
}

/**
 * Logout: clear localStorage.
 */
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    localStorage.removeItem('userRole');
    console.log('[logout] Cleared localStorage');
}

/**
 * Check if user is authenticated (has token).
 * @returns {boolean}
 */
function isAuthenticated() {
    return !!localStorage.getItem('authToken');
}

/**
 * Get current user from localStorage.
 * @returns {object} - { userId, username, role }
 */
function getCurrentUser() {
    return {
        userId: localStorage.getItem('userId'),
        username: localStorage.getItem('username'),
        role: localStorage.getItem('userRole')
    };
}

/**
 * Get current auth token.
 * @returns {string|null}
 */
function getAuthToken() {
    return localStorage.getItem('authToken');
}
