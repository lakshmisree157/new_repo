const API_BASE_URL =
    window.__API_BASE_URL ||
    document.documentElement?.dataset?.apiBaseUrl ||
    '';

async function apiFetch(endpoint, method = 'GET', data = null, token = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    if (token) {
        options.headers['Authorization'] = 'Bearer ' + token;
    }
    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(API_BASE_URL + endpoint, options);
        const json = await response.json();
        if (!response.ok) {
            throw new Error(json.error || 'API error');
        }
        return json;
    } catch (error) {
        console.error('API fetch error:', error);
        throw error;
    }
}

// Adoption Admin API
async function getPendingCenters(token) {
    return apiFetch('/adoptions/admin/pending-centers', 'GET', null, token);
}

async function verifyCenter(centerId, token) {
    return apiFetch(`/adoptions/admin/verify-center/${centerId}`, 'POST', null, token);
}

// Profile APIs

async function getProfile(token) {
    return apiFetch('/api/auth/profile', 'GET', null, token);
}

async function updateProfile(data, token) {
    return apiFetch('/api/auth/profile', 'PATCH', data, token);
}

async function login(email, password) {
    const response = await fetch(API_BASE_URL + '/api/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password})
    });
    const data = await response.json();
    if (response.ok) {
        if (data.access_token) {
            localStorage.setItem('access_token', data.access_token);
        }
        return data;
    } else {
        throw new Error(data.error || 'Login failed');
    }
}

export { 
    apiFetch,
    getPendingCenters, 
    verifyCenter, 
    getProfile, 
    updateProfile, 
    login };

