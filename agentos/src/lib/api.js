import axios from 'axios'

// ─── Base Axios Instance ──────────────────────────────────────────────
const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30_000,
})

// ─── Request Interceptor ──────────────────────────────────────────────
api.interceptors.request.use(
    (config) => config,
    (error) => Promise.reject(error)
)

// ─── Response Interceptor ─────────────────────────────────────────────
api.interceptors.response.use(
    (response) => response.data,
    (error) => {
        const message =
            error.response?.data?.detail ||
            error.response?.data?.message ||
            error.message ||
            'An unexpected error occurred'
        return Promise.reject(new Error(message))
    }
)

// ─── Task Endpoints ───────────────────────────────────────────────────
export const tasksApi = {
    /** Submit a new task — POST /api/task */
    create: (payload) => api.post('/api/task', payload),

    /** Get all tasks — GET /api/task */
    getAll: () => api.get('/api/task'),

    /** Get task status + agent logs — GET /api/task/:id/status */
    getById: (id) => api.get(`/api/task/${id}/status`),

    /** Approve or reject at human-review checkpoint */
    approve: (id, action = 'approve', feedback = '') =>
        api.post(`/api/task/${id}/approve`, { action, feedback }),

    /** Reject shorthand */
    reject: (id, feedback = '') =>
        api.post(`/api/task/${id}/approve`, { action: 'reject', feedback }),
}

// ─── Memory Endpoints ─────────────────────────────────────────────────
export const memoryApi = {
    /** Semantic search — GET /api/memory/search?q= */
    search: (query) => api.get('/api/memory/search', { params: { q: query } }),

    /** Get all memory */
    getAll: () => api.get('/api/memory/search', { params: { q: '', limit: 50 } }),

    /** Memory entry count */
    count: () => api.get('/api/memory/count'),
}

export default api
