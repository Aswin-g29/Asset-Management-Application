const Auth = {
    tokenKey: "ws_token",
    userKey: "ws_user",

    setSession(payload) {
        localStorage.setItem(this.tokenKey, payload.access_token);
        localStorage.setItem(this.userKey, JSON.stringify(payload.user));
    },

    getToken() {
        return localStorage.getItem(this.tokenKey);
    },

    getUser() {
        const raw = localStorage.getItem(this.userKey);
        return raw ? JSON.parse(raw) : null;
    },

    getCurrentUser() {
        return this.getUser();
    },

    isLoggedIn() {
        return Boolean(this.getToken());
    },

    requireAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = "login.html";
        }
    },

    // Alias for backward compatibility
    requireLogin() {
        return this.requireAuth();
    },

    logout() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
        window.location.href = "login.html";
    },

    hasRole(roles) {
        const user = this.getUser();
        return user ? roles.includes(user.role) : false;
    },

    roleHomePage() {
        const role = this.getUser()?.role;
        if (role === "Viewer") {
            return "assets.html";
        }
        return "dashboard.html";
    },

    canAccessPage(pageKey) {
        const user = this.getUser();
        if (!user) return false;
        const access = {
            dashboard: ["Admin", "IT Manager"],
            assets: ["Admin", "IT Manager", "Viewer"],
            add_asset: ["Admin", "IT Manager"],
            asset_detail: ["Admin", "IT Manager", "Viewer"],
            transactions: ["Admin", "IT Manager"],
            assign: ["Admin", "IT Manager"],
            transfer: ["Admin", "IT Manager"],
            maintenance: ["Admin", "IT Manager"],
            users: ["Admin"],
            qr_print: ["Admin", "IT Manager"],
        };
        const allowedRoles = access[pageKey] || [];
        return allowedRoles.includes(user.role);
    },

    initProtectedPage() {
        this.requireAuth();
        const user = this.getUser();
        document.querySelectorAll("[data-user-name]").forEach((el) => {
            el.textContent = user?.user_name || "User";
        });
        document.querySelectorAll("[data-user-role]").forEach((el) => {
            el.textContent = user?.role || "";
        });
        document.querySelectorAll("[data-role]").forEach((el) => {
            const roles = el.dataset.role.split("|");
            if (!this.hasRole(roles)) {
                el.classList.add("ws-hidden");
            }
        });
        document.querySelectorAll("[data-logout]").forEach((el) => {
            el.addEventListener("click", () => this.logout());
        });
    }
};
