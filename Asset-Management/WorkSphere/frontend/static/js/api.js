const API = {
    baseUrl: "http://127.0.0.1:8000",

    async request(path, options = {}) {
        const headers = {
            "Content-Type": "application/json",
            ...(options.headers || {})
        };
        const token = Auth.getToken();
        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }

        const response = await fetch(`${this.baseUrl}${path}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            Auth.logout();
            return null;
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "Request failed" }));
            throw new Error(error.detail || "Request failed");
        }

        if (response.status === 204) {
            return null;
        }

        return response.json();
    },

    get(path) {
        return this.request(path);
    },

    post(path, body) {
        return this.request(path, { method: "POST", body: JSON.stringify(body) });
    },

    put(path, body) {
        return this.request(path, { method: "PUT", body: JSON.stringify(body) });
    },

    patch(path, body = {}) {
        return this.request(path, { method: "PATCH", body: JSON.stringify(body) });
    }
};
