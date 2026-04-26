function shellTemplate(pageTitle, pageKey, content) {
    const user = Auth.getUser() || {};
    const links = [
        ["dashboard.html", "dashboard", "Dashboard"],
        ["assets.html", "assets", "Assets"],
        ["add_asset.html", "add_asset", "Add Asset", ["Admin", "IT Manager"]],
        ["transactions.html", "transactions", "Transactions"],
        ["assign.html", "assign", "Assign Asset", ["Admin", "IT Manager"]],
        ["transfer.html", "transfer", "Transfer Asset", ["Admin", "IT Manager"]],
        ["maintenance.html", "maintenance", "Maintenance"],
        ["users.html", "users", "Users", ["Admin"]],
        ["qr_print.html", "qr_print", "QR Print", ["Admin", "IT Manager"]]
    ];

    document.body.className = "ws-body";
    document.body.innerHTML = `
        <div class="ws-layout">
            <aside class="ws-sidebar">
                <div class="ws-brand mb-4">WorkSphere</div>
                <div class="small text-muted-custom mb-3">Asset Management System</div>
                <nav>
                    ${links
                        .filter(([, , , roles]) => !roles || roles.includes(user.role))
                        .map(([href, key, label]) => `
                            <a class="ws-nav-link ${pageKey === key ? "active" : ""}" href="${href}">${label}</a>
                        `)
                        .join("")}
                </nav>
            </aside>
            <main class="ws-main">
                <div class="ws-topbar">
                    <div>
                        <div class="ws-title">${pageTitle}</div>
                        <div class="ws-subtitle">Track, assign, transfer, and maintain assets with confidence.</div>
                    </div>
                    <div class="d-flex align-items-center gap-3">
                        <div class="text-end">
                            <div data-user-name>${user.user_name || "User"}</div>
                            <div class="text-muted-custom small" data-user-role>${user.role || ""}</div>
                        </div>
                        <button class="btn btn-outline-light btn-sm" data-logout>Logout</button>
                    </div>
                </div>
                ${content}
            </main>
        </div>
    `;
    Auth.initProtectedPage();
}

function statusBadge(status) {
    const map = {
        Available: "bg-success-subtle text-success",
        Assigned: "bg-primary-subtle text-primary",
        "In Repair": "bg-warning-subtle text-warning",
        Retired: "bg-secondary-subtle text-secondary",
        Lost: "bg-danger-subtle text-danger",
        Open: "bg-danger-subtle text-danger",
        "In Progress": "bg-warning-subtle text-warning",
        Closed: "bg-success-subtle text-success"
    };
    return `<span class="badge ws-badge ${map[status] || "bg-secondary-subtle text-secondary"}">${status}</span>`;
}

function renderTable(elementId, columns, rows) {
    const container = document.getElementById(elementId);
    if (!container) {
        return;
    }
    if (!rows.length) {
        container.innerHTML = `<div class="ws-empty">No records found.</div>`;
        return;
    }
    container.innerHTML = `
        <div class="table-responsive">
            <table class="table ws-table align-middle">
                <thead>
                    <tr>${columns.map((column) => `<th>${column.label}</th>`).join("")}</tr>
                </thead>
                <tbody>
                    ${rows
                        .map((row) => `
                            <tr>
                                ${columns.map((column) => `<td>${column.render ? column.render(row) : row[column.key] ?? "-"}</td>`).join("")}
                            </tr>
                        `)
                        .join("")}
                </tbody>
            </table>
        </div>
    `;
}

async function initDashboardPage() {
    shellTemplate("Dashboard", "dashboard", `
        <div class="ws-section-grid mb-4" id="dashboard-stats"></div>
        <div class="row g-4">
            <div class="col-lg-6">
                <div class="ws-table-card">
                    <h5 class="mb-3">Warranty Alerts</h5>
                    <div id="warranty-table"></div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="ws-table-card mb-4">
                    <h5 class="mb-3">Recent Transactions</h5>
                    <div id="transactions-table"></div>
                </div>
                <div class="ws-table-card">
                    <h5 class="mb-3">Recent Maintenance</h5>
                    <div id="maintenance-table"></div>
                </div>
            </div>
        </div>
    `);

    const data = await API.get("/dashboard");
    const stats = [
        ["Total Assets", data.counts.total_assets],
        ["Available", data.counts.available],
        ["Assigned", data.counts.assigned],
        ["In Repair", data.counts.in_repair],
        ["Retired", data.counts.retired]
    ];
    document.getElementById("dashboard-stats").innerHTML = stats
        .map(([label, value]) => `
            <div class="ws-card">
                <div class="ws-stat-value">${value}</div>
                <div class="ws-stat-label">${label}</div>
            </div>
        `)
        .join("");

    renderTable("warranty-table", [
        { key: "asset_name", label: "Asset" },
        { key: "serial_number", label: "Serial No" },
        { key: "warranty_end_date", label: "Warranty Ends" }
    ], data.warranty_alerts);

    renderTable("transactions-table", [
        { key: "asset_name", label: "Asset" },
        { key: "transaction_type", label: "Type" },
        { key: "to_assignee_name", label: "To" }
    ], data.recent_transactions);

    renderTable("maintenance-table", [
        { key: "asset_name", label: "Asset" },
        { key: "issue_type", label: "Issue" },
        { key: "maintenance_status", label: "Status", render: (row) => statusBadge(row.maintenance_status) }
    ], data.recent_maintenance);
}

async function initAssetsPage() {
    shellTemplate("Assets", "assets", `
        <div class="ws-table-card">
            <div class="row g-3 mb-3">
                <div class="col-md-4"><input class="form-control" id="asset-search" placeholder="Search by asset, serial, brand"></div>
                <div class="col-md-3">
                    <select class="form-select" id="status-filter">
                        <option value="">All Statuses</option>
                        <option>Available</option>
                        <option>Assigned</option>
                        <option>In Repair</option>
                        <option>Retired</option>
                        <option>Lost</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <select class="form-select" id="type-filter">
                        <option value="">All Types</option>
                        <option>Laptop</option>
                        <option>Desktop</option>
                        <option>Server</option>
                        <option>Furniture</option>
                        <option>Printer</option>
                        <option>Phone</option>
                        <option>Monitor</option>
                        <option>UPS</option>
                        <option>Other</option>
                    </select>
                </div>
                <div class="col-md-2"><button class="btn btn-primary w-100" id="filter-btn">Filter</button></div>
            </div>
            <div id="assets-table"></div>
        </div>
    `);

    async function loadAssets() {
        const params = new URLSearchParams();
        const search = document.getElementById("asset-search").value.trim();
        const status = document.getElementById("status-filter").value;
        const type = document.getElementById("type-filter").value;
        if (search) params.set("search", search);
        if (status) params.set("status_filter", status);
        if (type) params.set("type_filter", type);
        const data = await API.get(`/assets?${params.toString()}`);
        renderTable("assets-table", [
            { key: "asset_name", label: "Asset" },
            { key: "asset_type", label: "Type" },
            { key: "serial_number", label: "Serial No" },
            { key: "department", label: "Department" },
            { key: "asset_status", label: "Status", render: (row) => statusBadge(row.asset_status) },
            { key: "asset_id", label: "Action", render: (row) => `<a class="btn btn-sm btn-outline-light" href="asset_detail.html?id=${row.asset_id}">View</a>` }
        ], data.items);
    }

    document.getElementById("filter-btn").addEventListener("click", loadAssets);
    loadAssets();
}

async function initAddAssetPage() {
    shellTemplate("Add Asset", "add_asset", `
        <div class="ws-card">
            <form id="asset-form" class="row g-3">
                <div class="col-md-6"><input required name="asset_name" class="form-control" placeholder="Asset Name"></div>
                <div class="col-md-3">
                    <select required name="asset_type" class="form-select">
                        <option value="">Asset Type</option>
                        <option>Laptop</option><option>Desktop</option><option>Server</option><option>Furniture</option>
                        <option>Printer</option><option>Phone</option><option>Monitor</option><option>UPS</option><option>Other</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <select required name="category" class="form-select">
                        <option value="">Category</option>
                        <option>IT</option>
                        <option>Non-IT</option>
                    </select>
                </div>
                <div class="col-md-6"><input required name="serial_number" class="form-control" placeholder="Serial Number"></div>
                <div class="col-md-3"><input name="brand" class="form-control" placeholder="Brand"></div>
                <div class="col-md-3"><input name="model" class="form-control" placeholder="Model"></div>
                <div class="col-md-4"><input name="department" class="form-control" placeholder="Department"></div>
                <div class="col-md-4"><input name="location" class="form-control" placeholder="Location"></div>
                <div class="col-md-4">
                    <select name="condition_status" class="form-select">
                        <option>New</option><option>Good</option><option>Damaged</option>
                    </select>
                </div>
                <div class="col-md-4"><input name="purchase_date" type="date" class="form-control"></div>
                <div class="col-md-4"><input name="purchase_cost" type="number" step="0.01" class="form-control" placeholder="Purchase Cost"></div>
                <div class="col-md-4"><input name="vendor_name" class="form-control" placeholder="Vendor"></div>
                <div class="col-md-6"><textarea name="specifications" class="form-control" rows="3" placeholder="Specifications"></textarea></div>
                <div class="col-md-3"><input name="warranty_start_date" type="date" class="form-control"></div>
                <div class="col-md-3"><input name="warranty_expiry" type="number" class="form-control" placeholder="Warranty (years)"></div>
                <div class="col-12 d-flex justify-content-end"><button class="btn btn-primary">Create Asset</button></div>
            </form>
            <div id="asset-form-message" class="mt-3 text-muted-custom"></div>
        </div>
    `);

    document.getElementById("asset-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const payload = Object.fromEntries(formData.entries());
        Object.keys(payload).forEach((key) => {
            if (payload[key] === "") {
                delete payload[key];
            }
        });
        if (payload.purchase_cost) payload.purchase_cost = Number(payload.purchase_cost);
        if (payload.warranty_expiry) payload.warranty_expiry = Number(payload.warranty_expiry);
        const result = await API.post("/assets", payload);
        document.getElementById("asset-form-message").textContent = `${result.message}. Asset ID: ${result.asset_id}`;
        event.target.reset();
    });
}

async function initAssetDetailPage() {
    shellTemplate("Asset Detail", "assets", `
        <div class="row g-4">
            <div class="col-lg-7">
                <div class="ws-card" id="asset-detail"></div>
            </div>
            <div class="col-lg-5">
                <div class="ws-table-card mb-4">
                    <h5 class="mb-3">Transaction History</h5>
                    <div id="asset-transactions"></div>
                </div>
                <div class="ws-table-card">
                    <h5 class="mb-3">Maintenance History</h5>
                    <div id="asset-maintenance"></div>
                </div>
            </div>
        </div>
    `);
    const params = new URLSearchParams(window.location.search);
    const assetId = params.get("id");
    if (!assetId) {
        document.getElementById("asset-detail").innerHTML = `<div class="ws-empty">Missing asset id.</div>`;
        return;
    }
    const data = await API.get(`/assets/${assetId}`);
    const asset = data.asset;
    document.getElementById("asset-detail").innerHTML = `
        <div class="d-flex justify-content-between align-items-start mb-3">
            <div>
                <h4>${asset.asset_name}</h4>
                <div class="text-muted-custom">${asset.brand || "-"} ${asset.model || ""}</div>
            </div>
            ${statusBadge(asset.asset_status)}
        </div>
        <div class="row g-3">
            <div class="col-md-6"><strong>Type:</strong> ${asset.asset_type}</div>
            <div class="col-md-6"><strong>Serial:</strong> ${asset.serial_number}</div>
            <div class="col-md-6"><strong>Department:</strong> ${asset.department || "-"}</div>
            <div class="col-md-6"><strong>Location:</strong> ${asset.location || "-"}</div>
            <div class="col-md-6"><strong>Condition:</strong> ${asset.condition_status}</div>
            <div class="col-md-6"><strong>QR:</strong> ${asset.qr_code_value || "-"}</div>
            <div class="col-12"><strong>Specifications:</strong><br>${asset.specifications || "-"}</div>
            <div class="col-12 d-flex gap-2" data-role="Admin|IT Manager">
                <button class="btn btn-primary" id="generate-qr-btn">Generate QR</button>
                ${Auth.hasRole(["Admin"]) ? `<button class="btn btn-outline-danger" id="retire-btn">Retire Asset</button>` : ""}
            </div>
            <div class="col-12" id="asset-detail-message"></div>
        </div>
    `;

    document.getElementById("generate-qr-btn")?.addEventListener("click", async () => {
        const result = await API.post(`/assets/${assetId}/qr`, {});
        document.getElementById("asset-detail-message").innerHTML = `<a class="btn btn-sm btn-outline-light" href="${API.baseUrl}${result.qr_code_image_url}" target="_blank">Open QR Image</a>`;
    });

    document.getElementById("retire-btn")?.addEventListener("click", async () => {
        await API.patch(`/assets/${assetId}/retire`);
        window.location.reload();
    });

    renderTable("asset-transactions", [
        { key: "transaction_type", label: "Type" },
        { key: "from_employee_name", label: "From" },
        { key: "to_assignee_name", label: "To" }
    ], data.transactions);

    renderTable("asset-maintenance", [
        { key: "issue_type", label: "Issue" },
        { key: "maintenance_status", label: "Status", render: (row) => statusBadge(row.maintenance_status) },
        { key: "vendor", label: "Vendor" }
    ], data.maintenance);
}

async function initTransactionsPage() {
    shellTemplate("Transactions", "transactions", `<div class="ws-table-card"><div id="transactions-list"></div></div>`);
    const rows = await API.get("/transactions");
    renderTable("transactions-list", [
        { key: "asset_name", label: "Asset" },
        { key: "transaction_type", label: "Type" },
        { key: "from_employee_name", label: "From" },
        { key: "to_assignee_name", label: "To" },
        { key: "action_date", label: "Date" }
    ], rows);
}

async function loadUsersForSelect(selectId) {
    const rows = await API.get("/users/assignable");
    const select = document.getElementById(selectId);
    if (!select) return;
    select.innerHTML = `<option value="">Select User</option>` + rows
        .filter((row) => row.is_active)
        .map((row) => `<option value="${row.user_id}">${row.user_name} (${row.role})</option>`)
        .join("");
}

async function loadAssetsForSelect(selectId, status) {
    const rows = await API.get(`/assets?status_filter=${encodeURIComponent(status)}&page_size=100`);
    const select = document.getElementById(selectId);
    if (!select) return;
    select.innerHTML = `<option value="">Select Asset</option>` + rows.items
        .map((row) => `<option value="${row.asset_id}">${row.asset_name} - ${row.serial_number}</option>`)
        .join("");
}

async function initAssignPage() {
    shellTemplate("Assign Asset", "assign", `
        <div class="ws-card">
            <form id="assign-form" class="row g-3">
                <div class="col-md-6"><select id="assign-asset" class="form-select" required></select></div>
                <div class="col-md-6"><select id="assign-user" class="form-select" required></select></div>
                <div class="col-12"><textarea id="assign-remarks" class="form-control" rows="3" placeholder="Remarks"></textarea></div>
                <div class="col-12 d-flex justify-content-end"><button class="btn btn-primary">Assign</button></div>
            </form>
            <div id="assign-message" class="mt-3 text-muted-custom"></div>
        </div>
    `);
    await loadAssetsForSelect("assign-asset", "Available");
    await loadUsersForSelect("assign-user");
    document.getElementById("assign-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const result = await API.post("/transactions/assign", {
            asset_id: Number(document.getElementById("assign-asset").value),
            to_assignee: Number(document.getElementById("assign-user").value),
            remarks: document.getElementById("assign-remarks").value
        });
        document.getElementById("assign-message").textContent = result.message;
    });
}

async function initTransferPage() {
    shellTemplate("Transfer Asset", "transfer", `
        <div class="ws-card">
            <form id="transfer-form" class="row g-3">
                <div class="col-md-6"><select id="transfer-asset" class="form-select" required></select></div>
                <div class="col-md-6"><select id="transfer-user" class="form-select" required></select></div>
                <div class="col-12"><textarea id="transfer-remarks" class="form-control" rows="3" placeholder="Remarks"></textarea></div>
                <div class="col-12 d-flex justify-content-end"><button class="btn btn-primary">Transfer</button></div>
            </form>
            <div id="transfer-message" class="mt-3 text-muted-custom"></div>
        </div>
    `);
    await loadAssetsForSelect("transfer-asset", "Assigned");
    await loadUsersForSelect("transfer-user");
    document.getElementById("transfer-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const result = await API.post("/transactions/transfer", {
            asset_id: Number(document.getElementById("transfer-asset").value),
            to_assignee: Number(document.getElementById("transfer-user").value),
            remarks: document.getElementById("transfer-remarks").value
        });
        document.getElementById("transfer-message").textContent = result.message;
    });
}

async function initMaintenancePage() {
    shellTemplate("Maintenance", "maintenance", `
        <div class="row g-4">
            <div class="col-lg-5" data-role="Admin|IT Manager">
                <div class="ws-card">
                    <form id="maintenance-form" class="row g-3">
                        <div class="col-12"><select id="maintenance-asset" class="form-select" required></select></div>
                        <div class="col-md-6">
                            <select id="issue-type" class="form-select" required>
                                <option value="">Issue Type</option>
                                <option>Repair</option><option>Physical Damage</option><option>Theft</option><option>Software Issue</option>
                            </select>
                        </div>
                        <div class="col-md-6"><input id="maintenance-vendor" class="form-control" placeholder="Vendor"></div>
                        <div class="col-12"><textarea id="issue-description" class="form-control" rows="3" placeholder="Issue Description"></textarea></div>
                        <div class="col-12"><textarea id="resolution-notes" class="form-control" rows="3" placeholder="Resolution Notes"></textarea></div>
                        <div class="col-12 form-check">
                            <input class="form-check-input" type="checkbox" id="warranty-applicable">
                            <label class="form-check-label" for="warranty-applicable">Warranty Applicable</label>
                        </div>
                        <div class="col-12 d-flex justify-content-end"><button class="btn btn-primary">Log Issue</button></div>
                    </form>
                </div>
            </div>
            <div class="col-lg-7">
                <div class="ws-table-card">
                    <h5 class="mb-3">Maintenance Records</h5>
                    <div id="maintenance-list"></div>
                </div>
            </div>
        </div>
    `);
    await loadAssetsForSelect("maintenance-asset", "Assigned");
    const rows = await API.get("/maintenance");
    renderTable("maintenance-list", [
        { key: "asset_name", label: "Asset" },
        { key: "issue_type", label: "Issue" },
        { key: "vendor", label: "Vendor" },
        { key: "maintenance_status", label: "Status", render: (row) => statusBadge(row.maintenance_status) }
    ], rows);

    document.getElementById("maintenance-form")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        await API.post("/maintenance", {
            asset_id: Number(document.getElementById("maintenance-asset").value),
            issue_description: document.getElementById("issue-description").value,
            issue_type: document.getElementById("issue-type").value,
            vendor: document.getElementById("maintenance-vendor").value,
            resolution_notes: document.getElementById("resolution-notes").value,
            warranty_applicable: document.getElementById("warranty-applicable").checked
        });
        window.location.reload();
    });
}

async function initUsersPage() {
    shellTemplate("Users", "users", `
        <div class="row g-4">
            <div class="col-lg-4">
                <div class="ws-card">
                    <form id="user-form" class="row g-3">
                        <div class="col-12"><input name="user_name" class="form-control" placeholder="Full Name" required></div>
                        <div class="col-12"><input name="username" class="form-control" placeholder="Username" required></div>
                        <div class="col-12"><input name="email" type="email" class="form-control" placeholder="Email" required></div>
                        <div class="col-12"><input name="password" type="password" class="form-control" placeholder="Password" required></div>
                        <div class="col-12">
                            <select name="role" class="form-select" required>
                                <option value="">Role</option>
                                <option>Admin</option><option>IT Manager</option><option>Viewer</option>
                            </select>
                        </div>
                        <div class="col-12 d-flex justify-content-end"><button class="btn btn-primary">Create User</button></div>
                    </form>
                </div>
            </div>
            <div class="col-lg-8">
                <div class="ws-table-card">
                    <div id="users-list"></div>
                </div>
            </div>
        </div>
    `);
    const rows = await API.get("/users");
    renderTable("users-list", [
        { key: "user_name", label: "Name" },
        { key: "username", label: "Username" },
        { key: "role", label: "Role" },
        { key: "is_active", label: "Status", render: (row) => row.is_active ? "Active" : "Inactive" }
    ], rows);

    document.getElementById("user-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(event.target).entries());
        await API.post("/users", payload);
        window.location.reload();
    });
}

async function initQrPage() {
    shellTemplate("QR Print", "qr_print", `
        <div class="ws-card">
            <form id="qr-form" class="row g-3">
                <div class="col-md-9"><input class="form-control" id="qr-asset-id" placeholder="Enter asset id" required></div>
                <div class="col-md-3"><button class="btn btn-primary w-100">Generate</button></div>
            </form>
            <div id="qr-result" class="mt-4"></div>
        </div>
    `);
    document.getElementById("qr-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const assetId = document.getElementById("qr-asset-id").value;
        const result = await API.post(`/assets/${assetId}/qr`, {});
        document.getElementById("qr-result").innerHTML = `
            <div class="text-center">
                <img class="img-fluid mb-3" src="${API.baseUrl}${result.qr_code_image_url}" alt="QR Code">
                <div class="mb-3">${result.qr_code_value}</div>
                <button class="btn btn-outline-light" onclick="window.print()">Print QR</button>
            </div>
        `;
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    const page = document.body.dataset.page;
    try {
        switch (page) {
            case "dashboard":
                await initDashboardPage();
                break;
            case "assets":
                await initAssetsPage();
                break;
            case "add_asset":
                await initAddAssetPage();
                break;
            case "asset_detail":
                await initAssetDetailPage();
                break;
            case "transactions":
                await initTransactionsPage();
                break;
            case "assign":
                await initAssignPage();
                break;
            case "transfer":
                await initTransferPage();
                break;
            case "maintenance":
                await initMaintenancePage();
                break;
            case "users":
                await initUsersPage();
                break;
            case "qr_print":
                await initQrPage();
                break;
            default:
                break;
        }
    } catch (error) {
        document.body.insertAdjacentHTML("beforeend", `<div class="position-fixed bottom-0 end-0 m-3 alert alert-danger">${error.message}</div>`);
    }
});
