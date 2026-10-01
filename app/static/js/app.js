// CareVault AI - Main Frontend Application Logic
// Single-Page Application with Multi-Role Switching and Comprehensive Feature Integration

let currentUser = null;
let currentRole = "PATIENT";
let currentPatientProfile = null;
let currentTab = "dashboard";
let recordsList = [];
let timelineMode = false;
let leafletMap = null;
let mapMarkers = [];
let doctorTimerInterval = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", async () => {
    lucide.createIcons();
    await checkAuth();
});

// ==========================================
// AUTHENTICATION & DEMO ROLE SWITCHER
// ==========================================

async function checkAuth() {
    try {
        const res = await fetch("/api/auth/me");
        if (res.ok) {
            const data = await res.json();
            currentUser = data;
            currentRole = data.role;
            updateUserUI();
            loadRolePortal(currentRole);
        } else {
            // Default auto-login as Demo Patient for hackathon evaluation
            await switchRole("PATIENT");
        }
    } catch (e) {
        console.error("Auth check failed, defaulting to Demo Patient", e);
        await switchRole("PATIENT");
    }
}

async function switchRole(role) {
    try {
        const res = await fetch("/api/auth/demo-switch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ role: role })
        });
        if (res.ok) {
            const data = await res.json();
            currentUser = {
                id: 1,
                email: data.email,
                role: data.role,
                full_name: data.full_name,
                profile: data
            };
            currentRole = data.role;
            updateUserUI();
            loadRolePortal(currentRole);
            showToast(`Switched to ${role} Portal (${data.full_name})`, "info");
        }
    } catch (e) {
        console.error("Role switch failed", e);
    }
}

function updateUserUI() {
    if (!currentUser) return;
    document.getElementById("user-name-display").textContent = currentUser.full_name;
    document.getElementById("user-role-badge").textContent = currentUser.role;

    // Highlight active role pill
    ["PATIENT", "DOCTOR", "LAB", "ADMIN"].forEach(r => {
        const btn = document.getElementById(`btn-role-${r.toLowerCase()}`);
        if (btn) {
            if (r === currentRole) {
                btn.className = "px-3 py-1.5 rounded-full text-xs font-semibold bg-sky-600 text-white shadow-sm flex items-center space-x-1.5 transition";
            } else {
                btn.className = "px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 flex items-center space-x-1.5 transition";
            }
        }
    });

    lucide.createIcons();
}

function loadRolePortal(role) {
    // Hide all role containers
    document.getElementById("portal-patient").classList.add("hidden");
    document.getElementById("portal-doctor").classList.add("hidden");
    document.getElementById("portal-lab").classList.add("hidden");
    document.getElementById("portal-admin").classList.add("hidden");

    if (role === "PATIENT") {
        document.getElementById("portal-patient").classList.remove("hidden");
        loadPatientDashboard();
    } else if (role === "DOCTOR") {
        document.getElementById("portal-doctor").classList.remove("hidden");
        loadDoctorPortal();
    } else if (role === "LAB") {
        document.getElementById("portal-lab").classList.remove("hidden");
        loadLabPortal();
    } else if (role === "ADMIN") {
        document.getElementById("portal-admin").classList.remove("hidden");
        loadAdminPortal();
    }
    lucide.createIcons();
}

// ==========================================
// PATIENT PORTAL CONTROLLER
// ==========================================

function switchPatientTab(tabName) {
    currentTab = tabName;
    const tabIds = [
        "dashboard", "records", "ai-assistant", "ai-explainer",
        "ai-prescription", "ai-duplicates", "ai-awareness",
        "doctor-questions", "consent-share", "hospital-finder",
        "emergency", "access-history"
    ];

    tabIds.forEach(t => {
        const el = document.getElementById(`tab-${t}`);
        if (el) el.classList.add("hidden");
        const btn = document.getElementById(`nav-${t}`);
        if (btn) {
            btn.classList.remove("bg-sky-50", "text-sky-700", "font-semibold");
            btn.classList.add("text-slate-600");
        }
    });

    const activeEl = document.getElementById(`tab-${tabName}`);
    if (activeEl) activeEl.classList.remove("hidden");

    const activeBtn = document.getElementById(`nav-${tabName}`);
    if (activeBtn) {
        activeBtn.classList.add("bg-sky-50", "text-sky-700", "font-semibold");
        activeBtn.classList.remove("text-slate-600");
    }

    // Lazy load specific tab contents
    if (tabName === "records") loadPatientRecords();
    if (tabName === "doctor-questions") loadDoctorQuestions();
    if (tabName === "consent-share") loadConsentSharing();
    if (tabName === "hospital-finder") {
        loadHospitals();
        setTimeout(initLeafletMap, 200);
    }
    if (tabName === "emergency") loadEmergencyScreen();
    if (tabName === "access-history") loadAccessHistory();
    if (tabName === "ai-awareness") loadConditionsList();

    lucide.createIcons();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function loadPatientDashboard() {
    try {
        const res = await fetch("/api/patients/overview");
        if (!res.ok) return;
        const data = await res.json();
        currentPatientProfile = data;

        // Populate health overview card
        document.getElementById("p-welcome-name").textContent = data.patient_name;
        document.getElementById("p-blood-group").textContent = data.blood_group;
        document.getElementById("p-allergies").textContent = data.allergies || "None reported";
        document.getElementById("p-conditions").textContent = data.existing_conditions || "None reported";
        document.getElementById("p-medications").textContent = data.current_medications || "None active";

        // Statistics
        document.getElementById("stat-total-records").textContent = data.statistics.total_records;
        document.getElementById("stat-recent-records").textContent = data.statistics.recent_records;
        document.getElementById("stat-active-consents").textContent = data.statistics.active_consents;
        document.getElementById("stat-expired-consents").textContent = data.statistics.expired_consents;

        // Recent Reports table
        const tbody = document.getElementById("recent-reports-table");
        if (tbody) {
            tbody.innerHTML = "";
            if (data.recent_reports && data.recent_reports.length > 0) {
                data.recent_reports.forEach(r => {
                    const tr = document.createElement("tr");
                    tr.className = "border-b border-slate-100 hover:bg-slate-50/80 transition";
                    tr.innerHTML = `
                        <td class="py-3 px-4 text-xs text-slate-500 font-mono">${r.record_date}</td>
                        <td class="py-3 px-4 font-medium text-slate-800">${r.title}</td>
                        <td class="py-3 px-4"><span class="badge-category bg-sky-100 text-sky-800">${r.record_type}</span></td>
                        <td class="py-3 px-4 text-slate-600 text-sm">${r.hospital_name}</td>
                        <td class="py-3 px-4 text-right">
                            <button onclick="openExplainModal('${r.record_id}')" class="px-2.5 py-1 text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-md font-medium transition mr-1.5">
                                Explain AI
                            </button>
                            <button onclick="openDocumentView('${r.record_id}')" class="px-2.5 py-1 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-medium transition">
                                View
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-400">No medical records uploaded yet.</td></tr>`;
            }
        }

        loadNotifications();
    } catch (e) {
        console.error("Dashboard overview error", e);
    }
}

async function loadNotifications() {
    try {
        const res = await fetch("/api/patients/notifications");
        if (!res.ok) return;
        const notifs = await res.json();
        const container = document.getElementById("notif-list-container");
        const countBadge = document.getElementById("notif-count-badge");

        const unread = notifs.filter(n => !n.is_read).length;
        if (countBadge) {
            countBadge.textContent = unread;
            countBadge.style.display = unread > 0 ? "inline-flex" : "none";
        }

        if (container) {
            container.innerHTML = "";
            if (notifs.length === 0) {
                container.innerHTML = `<div class="p-4 text-center text-xs text-slate-400">No notifications.</div>`;
                return;
            }
            notifs.slice(0, 5).forEach(n => {
                const item = document.createElement("div");
                item.className = `p-3.5 border-b border-slate-100 flex items-start space-x-3 text-left ${n.is_read ? 'opacity-70 bg-white' : 'bg-sky-50/50'}`;
                item.innerHTML = `
                    <div class="mt-0.5"><i data-lucide="bell" class="w-4 h-4 text-sky-600"></i></div>
                    <div class="flex-1">
                        <div class="text-xs font-semibold text-slate-800">${n.title}</div>
                        <div class="text-xs text-slate-600 mt-0.5">${n.message}</div>
                        <div class="text-[10px] text-slate-400 mt-1">${new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                `;
                container.appendChild(item);
            });
            lucide.createIcons();
        }
    } catch (e) {
        console.error("Notifs error", e);
    }
}

// ==========================================
// DIGITAL HEALTH WALLET & TIMELINE
// ==========================================

async function loadPatientRecords() {
    const q = document.getElementById("record-search-input") ? document.getElementById("record-search-input").value : "";
    const cat = document.getElementById("record-category-filter") ? document.getElementById("record-category-filter").value : "All";
    const sort = document.getElementById("record-sort-select") ? document.getElementById("record-sort-select").value : "desc";

    let url = `/api/records?sort=${sort}`;
    if (q) url += `&q=${encodeURIComponent(q)}`;
    if (cat && cat !== "All") url += `&category=${encodeURIComponent(cat)}`;

    try {
        const res = await fetch(url);
        if (!res.ok) return;
        recordsList = await res.json();

        if (timelineMode) {
            renderTimelineView();
        } else {
            renderRecordsGrid();
        }
    } catch (e) {
        console.error("Load records error", e);
    }
}

function toggleTimelineMode(isTimeline) {
    timelineMode = isTimeline;
    const gridBtn = document.getElementById("btn-view-grid");
    const timelineBtn = document.getElementById("btn-view-timeline");
    if (gridBtn && timelineBtn) {
        if (isTimeline) {
            timelineBtn.className = "px-3 py-1.5 rounded-lg bg-sky-600 text-white font-medium text-xs flex items-center space-x-1";
            gridBtn.className = "px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 font-medium text-xs flex items-center space-x-1";
            document.getElementById("records-grid-container").classList.add("hidden");
            document.getElementById("records-timeline-container").classList.remove("hidden");
            renderTimelineView();
        } else {
            gridBtn.className = "px-3 py-1.5 rounded-lg bg-sky-600 text-white font-medium text-xs flex items-center space-x-1";
            timelineBtn.className = "px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 font-medium text-xs flex items-center space-x-1";
            document.getElementById("records-grid-container").classList.remove("hidden");
            document.getElementById("records-timeline-container").classList.add("hidden");
            renderRecordsGrid();
        }
        lucide.createIcons();
    }
}

function renderRecordsGrid() {
    const container = document.getElementById("records-grid-container");
    if (!container) return;
    container.innerHTML = "";

    if (recordsList.length === 0) {
        container.innerHTML = `
            <div class="col-span-full py-16 text-center text-slate-400">
                <i data-lucide="file-question" class="w-12 h-12 mx-auto mb-3 opacity-40 text-slate-500"></i>
                <div class="font-medium text-slate-700">No medical records match your criteria.</div>
                <div class="text-xs text-slate-500 mt-1">Try clearing your search filters or upload a new record.</div>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    recordsList.forEach(r => {
        const card = document.createElement("div");
        card.className = "glass-panel p-5 rounded-2xl shadow-sm hover:shadow-md transition border border-slate-200/80 flex flex-col justify-between";
        
        let sourceBadge = `<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Verified Transfer</span>`;
        if (r.source === "PATIENT_UPLOAD") {
            sourceBadge = `<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">Patient Upload</span>`;
        }

        card.innerHTML = `
            <div>
                <div class="flex items-center justify-between gap-2 mb-2">
                    <span class="badge-category bg-sky-100 text-sky-800">${r.record_type}</span>
                    ${sourceBadge}
                </div>
                <h4 class="font-bold text-slate-900 text-base leading-snug line-clamp-2">${r.title}</h4>
                <div class="text-xs text-slate-500 mt-1 font-mono">${r.record_date} | ${r.hospital_name}</div>
                <div class="text-xs text-slate-600 mt-2 line-clamp-2">${r.description || 'No additional clinical remarks recorded.'}</div>
                
                <div class="flex flex-wrap gap-1.5 mt-3">
                    ${(r.tags || []).map(t => `<span class="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">#${t}</span>`).join('')}
                </div>
            </div>

            <div class="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                <button onclick="openExplainModal('${r.record_id}')" class="flex-1 py-1.5 px-3 text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg font-semibold transition flex items-center justify-center space-x-1">
                    <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
                    <span>Explain AI</span>
                </button>
                <button onclick="openDocumentView('${r.record_id}')" class="flex-1 py-1.5 px-3 text-xs bg-slate-800 hover:bg-slate-900 text-white rounded-lg font-semibold transition flex items-center justify-center space-x-1">
                    <i data-lucide="file-text" class="w-3.5 h-3.5"></i>
                    <span>View Record</span>
                </button>
            </div>
        `;
        container.appendChild(card);
    });
    lucide.createIcons();
}

async function renderTimelineView() {
    const container = document.getElementById("records-timeline-container");
    if (!container) return;
    container.innerHTML = "";

    try {
        const res = await fetch("/api/records/timeline");
        if (!res.ok) return;
        const timelineData = await res.json();

        if (timelineData.length === 0) {
            container.innerHTML = `<div class="py-12 text-center text-slate-400 text-sm">No timeline events found.</div>`;
            return;
        }

        timelineData.forEach(yr => {
            const yearBox = document.createElement("div");
            yearBox.className = "mb-8";
            yearBox.innerHTML = `
                <div class="flex items-center space-x-3 mb-4">
                    <span class="px-3.5 py-1 bg-slate-900 text-white font-bold text-sm rounded-lg shadow-sm">${yr.year}</span>
                    <div class="flex-1 h-px bg-slate-200"></div>
                </div>
            `;

            const monthsWrap = document.createElement("div");
            monthsWrap.className = "relative pl-6 space-y-6";

            yr.months.forEach(m => {
                const monthBlock = document.createElement("div");
                monthBlock.className = "relative";
                monthBlock.innerHTML = `
                    <div class="absolute -left-[30px] top-1.5 w-3 h-3 rounded-full bg-sky-500 border-2 border-white ring-2 ring-sky-200"></div>
                    <div class="font-bold text-xs uppercase tracking-wider text-slate-500 mb-2">${m.month}</div>
                `;

                const recGrid = document.createElement("div");
                recGrid.className = "grid grid-cols-1 md:grid-cols-2 gap-3";

                m.records.forEach(r => {
                    const node = document.createElement("div");
                    node.className = "p-3.5 bg-white border border-slate-200 rounded-xl hover:border-sky-300 transition shadow-sm flex items-center justify-between";
                    node.innerHTML = `
                        <div>
                            <div class="font-semibold text-slate-900 text-sm">${r.title}</div>
                            <div class="text-xs text-slate-500">${r.record_date} &bull; ${r.hospital_name}</div>
                            <span class="badge-category bg-sky-50 text-sky-700 text-[10px] mt-1">${r.record_type}</span>
                        </div>
                        <div class="flex items-center space-x-1.5">
                            <button onclick="openExplainModal('${r.record_id}')" class="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-md" title="Explain with AI">
                                <i data-lucide="sparkles" class="w-4 h-4"></i>
                            </button>
                            <button onclick="openDocumentView('${r.record_id}')" class="p-1.5 text-slate-700 hover:bg-slate-100 rounded-md" title="View Document">
                                <i data-lucide="eye" class="w-4 h-4"></i>
                            </button>
                        </div>
                    `;
                    recGrid.appendChild(node);
                });

                monthBlock.appendChild(recGrid);
                monthsWrap.appendChild(monthBlock);
            });

            yearBox.appendChild(monthsWrap);
            container.appendChild(yearBox);
        });

        lucide.createIcons();
    } catch (e) {
        console.error("Timeline error", e);
    }
}

// ==========================================
// VIEW-ONLY WATERMARKED DOCUMENT MODAL
// ==========================================

async function openDocumentView(recordId) {
    try {
        const res = await fetch(`/api/records/${recordId}`);
        if (!res.ok) {
            const err = await res.json();
            showToast(err.detail || "Unable to access record", "error");
            return;
        }
        const data = await res.json();
        
        document.getElementById("modal-view-title").textContent = data.title;
        document.getElementById("modal-view-meta").textContent = `${data.record_type} | ${data.hospital_name} | Date: ${data.record_date} | Attending: ${data.doctor_name || 'Staff'}`;
        
        const imgEl = document.getElementById("modal-view-img");
        // Request signed watermarked stream
        imgEl.src = `/api/records/${recordId}/view?token=${data.view_token}`;

        document.getElementById("document-view-modal").classList.remove("hidden");
        lucide.createIcons();
    } catch (e) {
        console.error("Document view error", e);
    }
}

function closeDocumentViewModal() {
    document.getElementById("document-view-modal").classList.add("hidden");
    document.getElementById("modal-view-img").src = "";
}

// ==========================================
// AI REPORT EXPLAINER & MULTI-LANGUAGE
// ==========================================

let activeExplainingRecordId = null;

async function openExplainModal(recordId) {
    activeExplainingRecordId = recordId;
    switchPatientTab("ai-explainer");
    loadRecordExplanation(recordId, "en");
}

async function loadRecordExplanation(recordId, langCode) {
    const container = document.getElementById("ai-explanation-content");
    container.innerHTML = `
        <div class="py-16 text-center text-slate-500">
            <i data-lucide="loader" class="w-8 h-8 animate-spin mx-auto text-sky-600 mb-2"></i>
            <div class="text-sm font-medium">Analyzing diagnostic markers & synthesizing patient-friendly insights...</div>
            <div class="text-xs text-slate-400 mt-1">Applying strict non-diagnostic healthcare safety guardrails</div>
        </div>
    `;
    lucide.createIcons();

    try {
        const res = await fetch(`/api/ai/explain-report/${recordId}?lang=${langCode}`, { method: "POST" });
        if (!res.ok) {
            container.innerHTML = `<div class="p-6 text-center text-rose-600 font-medium">Could not generate explanation.</div>`;
            return;
        }
        const exp = await res.json();
        renderExplanationView(exp);
    } catch (e) {
        console.error("Explain error", e);
        container.innerHTML = `<div class="p-6 text-center text-rose-600 font-medium">Network or server error.</div>`;
    }
}

function renderExplanationView(exp) {
    const container = document.getElementById("ai-explanation-content");
    if (!container) return;

    const termsHtml = (exp.important_terms || []).map(t => `
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
            <div class="font-bold text-slate-900 text-xs">${t.term}</div>
            <div class="text-xs text-slate-600 mt-0.5">${t.meaning}</div>
        </div>
    `).join('');

    const questionsHtml = (exp.questions_to_ask_doctor || []).map(q => `
        <li class="flex items-start space-x-2 text-xs text-slate-700">
            <span class="text-sky-500 font-bold text-sm leading-none">&bull;</span>
            <span>${q}</span>
        </li>
    `).join('');

    container.innerHTML = `
        <!-- Report Header -->
        <div class="border-b border-slate-100 pb-4">
            <div class="flex items-center space-x-2">
                <span class="badge-category bg-sky-100 text-sky-800">${exp.type}</span>
                <span class="text-xs text-slate-400 font-mono">${exp.target_language ? exp.target_language : 'English'}</span>
            </div>
            <h3 class="text-xl font-bold text-slate-900 mt-1">${exp.title}</h3>
        </div>

        <!-- Safety Disclaimer Banner -->
        <div class="bg-amber-50/80 border border-amber-200/80 rounded-xl p-3.5 flex items-start space-x-2.5">
            <i data-lucide="shield-alert" class="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0"></i>
            <div class="text-xs text-amber-900 leading-relaxed">${exp.disclaimer}</div>
        </div>

        <!-- 1. What this report is -->
        <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5 flex items-center space-x-1.5">
                <i data-lucide="info" class="w-3.5 h-3.5 text-sky-600"></i>
                <span>1. What This Report Is</span>
            </h4>
            <p class="text-sm text-slate-800 leading-relaxed">${exp.what_it_is}</p>
        </div>

        <!-- 2. Simple Explanation -->
        <div class="bg-sky-50/60 border border-sky-100 rounded-xl p-4">
            <h4 class="text-xs font-bold uppercase tracking-wider text-sky-800 mb-1.5 flex items-center space-x-1.5">
                <i data-lucide="sparkles" class="w-3.5 h-3.5 text-sky-600"></i>
                <span>2. Simple Explanation</span>
            </h4>
            <p class="text-sm text-slate-800 leading-relaxed font-medium">
                ${exp.simple_explanation_translated || exp.simple_explanation}
            </p>
        </div>

        <!-- 3. Important Terms -->
        <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center space-x-1.5">
                <i data-lucide="book-open" class="w-3.5 h-3.5 text-slate-600"></i>
                <span>3. Key Terms Explained</span>
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                ${termsHtml}
            </div>
        </div>

        <!-- 4. What it measures -->
        <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">4. What This Test Generally Measures</h4>
            <p class="text-sm text-slate-700">${exp.what_it_measures}</p>
        </div>

        <!-- 5. Questions to discuss with doctor -->
        <div class="bg-indigo-50/60 border border-indigo-100 rounded-xl p-4">
            <h4 class="text-xs font-bold uppercase tracking-wider text-indigo-900 mb-2 flex items-center space-x-1.5">
                <i data-lucide="help-circle" class="w-3.5 h-3.5 text-indigo-600"></i>
                <span>5. Questions to Discuss with Your Doctor</span>
            </h4>
            <ul class="space-y-2">
                ${questionsHtml}
            </ul>
        </div>

        <!-- 6. Warning Signs -->
        <div class="bg-rose-50 border border-rose-200/80 rounded-xl p-3.5 flex items-start space-x-2.5">
            <i data-lucide="alert-triangle" class="w-4 h-4 text-rose-600 mt-0.5 flex-shrink-0"></i>
            <div>
                <div class="text-xs font-bold text-rose-900">Important Warning Signs</div>
                <div class="text-xs text-rose-800 mt-0.5">${exp.warning_signs}</div>
            </div>
        </div>
    `;
    lucide.createIcons();
}

function changeExplanationLanguage(langCode) {
    if (!activeExplainingRecordId) {
        if (recordsList.length > 0) activeExplainingRecordId = recordsList[0].record_id;
        else return;
    }
    loadRecordExplanation(activeExplainingRecordId, langCode);
}

// ==========================================
// AI HANDWRITTEN PRESCRIPTION READER
// ==========================================

async function runPrescriptionReader(presetKey = "clear_diabetes_bp") {
    const resBox = document.getElementById("prescription-result-container");
    const previewImg = document.getElementById("rx-preview-img");
    
    // Update preview sample image
    previewImg.src = `/api/ai/prescription-sample-image/${presetKey}`;

    resBox.innerHTML = `
        <div class="py-12 text-center text-slate-500">
            <i data-lucide="loader" class="w-8 h-8 animate-spin mx-auto text-sky-600 mb-2"></i>
            <div class="text-sm font-semibold">Running Handwriting OCR & Stroke Analysis Pipeline...</div>
            <div class="text-xs text-slate-400 mt-1">Cross-referencing pharmacological formulary & confidence thresholds</div>
        </div>
    `;
    lucide.createIcons();

    try {
        const formData = new FormData();
        formData.append("preset_key", presetKey);

        const res = await fetch("/api/ai/read-prescription", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            resBox.innerHTML = `<div class="p-6 text-center text-rose-600">Prescription analysis failed.</div>`;
            return;
        }

        const data = await res.json();
        renderPrescriptionAnalysis(data);
    } catch (e) {
        console.error("Rx read error", e);
    }
}

function renderPrescriptionAnalysis(data) {
    const container = document.getElementById("prescription-result-container");

    const pipelineHtml = (data.pipeline_steps || []).map(s => `
        <div class="flex items-center space-x-2 text-xs py-1">
            <i data-lucide="check-circle" class="w-4 h-4 text-emerald-600 flex-shrink-0"></i>
            <span class="font-semibold text-slate-800">${s.step}:</span>
            <span class="text-slate-600">${s.detail}</span>
        </div>
    `).join('');

    const medsHtml = (data.extracted_medicines || []).map(m => {
        if (!m.is_confident) {
            // Low confidence guardrail display
            return `
                <div class="p-4 bg-rose-50 border border-rose-200 rounded-xl">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-rose-900 text-sm">${m.medicine_name}</span>
                        <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-200 text-rose-800">${m.confidence_label}</span>
                    </div>
                    <div class="mt-2 text-xs text-rose-800 font-semibold flex items-start space-x-1.5">
                        <i data-lucide="shield-alert" class="w-4 h-4 text-rose-600 flex-shrink-0"></i>
                        <span>${m.safety_alert}</span>
                    </div>
                </div>
            `;
        }

        return `
            <div class="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                <div class="flex items-center justify-between">
                    <div>
                        <span class="font-bold text-slate-900 text-base">${m.medicine_name}</span>
                        <span class="text-xs text-slate-500 font-mono ml-2">(${m.strength})</span>
                    </div>
                    <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800">${m.confidence_label}</span>
                </div>
                <div class="text-xs font-semibold text-sky-800 mt-1">Doctor's Instruction: <span class="font-normal text-slate-700">${m.instruction}</span></div>
                <div class="text-xs text-slate-600 mt-1.5 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span class="font-semibold text-slate-700">What it is commonly for:</span> ${m.simple_explanation}
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = `
        <div class="space-y-4">
            <!-- Confidence & Doctor Info -->
            <div class="flex flex-wrap items-center justify-between gap-2 p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                <div>
                    <div class="font-bold text-slate-800 text-sm">${data.doctor_name}</div>
                    <div class="text-xs text-slate-500">${data.clinic_name} | Rx Date: ${data.prescription_date}</div>
                </div>
                <div class="text-right">
                    <div class="text-xs text-slate-500 font-medium">Model Confidence</div>
                    <div class="font-black text-lg ${data.overall_confidence > 0.8 ? 'text-emerald-600' : 'text-amber-600'}">
                        ${Math.round(data.overall_confidence * 100)}%
                    </div>
                </div>
            </div>

            <!-- Pipeline Status Accordion -->
            <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
                <div class="text-xs font-bold text-slate-700 mb-1">OCR & Pharmacological Pipeline Execution</div>
                ${pipelineHtml}
            </div>

            <!-- Unclear Handwriting Alert Banner if triggered -->
            ${data.has_unclear_handwriting ? `
                <div class="p-3.5 bg-amber-50 border border-amber-300 rounded-xl flex items-start space-x-2">
                    <i data-lucide="alert-triangle" class="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0"></i>
                    <div class="text-xs text-amber-900 leading-relaxed font-semibold">
                        SAFEGUARD ACTIVATED: Some medicine names could not be identified with clinical confidence (>=85%). CareVault AI strictly refuses to guess unclear handwriting to safeguard patient health.
                    </div>
                </div>
            ` : ''}

            <!-- Extracted Medicines List -->
            <div class="space-y-2.5">
                <div class="text-xs font-bold uppercase tracking-wider text-slate-500">Identified Medications (${data.extracted_medicines.length})</div>
                ${medsHtml}
            </div>

            <!-- Mandatory Safety Warning -->
            <div class="p-3 bg-sky-50 border border-sky-200 rounded-xl text-xs text-sky-900 leading-relaxed flex items-start space-x-2">
                <i data-lucide="info" class="w-4 h-4 text-sky-600 mt-0.5 flex-shrink-0"></i>
                <span>${data.safety_notice}</span>
            </div>
        </div>
    `;
    lucide.createIcons();
}

// ==========================================
// AI PREVIOUS / DUPLICATE TEST DETECTION
// ==========================================

async function runDuplicateCheck() {
    const testName = document.getElementById("duplicate-test-input").value;
    if (!testName.trim()) {
        showToast("Please enter a test or investigation name.", "warning");
        return;
    }

    const resBox = document.getElementById("duplicate-result-container");
    resBox.innerHTML = `
        <div class="py-8 text-center text-slate-400">
            <i data-lucide="loader" class="w-6 h-6 animate-spin mx-auto text-sky-600 mb-2"></i>
            <div class="text-xs font-semibold">Scanning health timeline for similar investigations...</div>
        </div>
    `;
    lucide.createIcons();

    try {
        const res = await fetch("/api/ai/duplicate-check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ test_name: testName })
        });
        if (!res.ok) return;
        const data = await res.json();

        if (data.has_duplicate) {
            resBox.innerHTML = `
                <div class="p-5 bg-amber-50 border-2 border-amber-300 rounded-2xl shadow-sm space-y-3">
                    <div class="flex items-center space-x-2">
                        <i data-lucide="alert-triangle" class="w-5 h-5 text-amber-600 flex-shrink-0"></i>
                        <h4 class="font-bold text-amber-950 text-base">${data.alert_header}</h4>
                    </div>

                    <p class="text-sm font-semibold text-slate-800">${data.summary}</p>

                    <div class="p-3.5 bg-white border border-amber-200 rounded-xl text-xs text-slate-800 leading-relaxed font-medium">
                        "${data.guidance}"
                    </div>

                    <div class="space-y-1.5 pt-2">
                        <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Matching Prior Records:</div>
                        ${data.matched_records.map(m => `
                            <div class="p-2.5 bg-white border border-slate-200 rounded-lg text-xs flex items-center justify-between">
                                <div>
                                    <div class="font-bold text-slate-800">${m.title}</div>
                                    <div class="text-[11px] text-slate-500">${m.previous_date} &bull; ${m.hospital}</div>
                                </div>
                                <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800">${m.days_ago} days ago</span>
                            </div>
                        `).join('')}
                    </div>

                    <div class="text-[11px] text-amber-800/90 italic pt-1">
                        ${data.safety_note}
                    </div>
                </div>
            `;
        } else {
            resBox.innerHTML = `
                <div class="p-5 bg-emerald-50 border border-emerald-200 rounded-2xl text-left space-y-2">
                    <div class="flex items-center space-x-2 text-emerald-800 font-bold text-sm">
                        <i data-lucide="check-circle" class="w-4 h-4 text-emerald-600"></i>
                        <span>No Recent Duplicate Detected</span>
                    </div>
                    <p class="text-xs text-slate-700">${data.summary}</p>
                    <p class="text-xs text-slate-500 italic">${data.guidance}</p>
                </div>
            `;
        }
        lucide.createIcons();
    } catch (e) {
        console.error("Duplicate check error", e);
    }
}

// ==========================================
// CONVERSATIONAL AI HEALTH ASSISTANT
// ==========================================

async function sendChatMessage(queryOverride = null) {
    const input = document.getElementById("chat-query-input");
    const query = queryOverride || input.value;
    if (!query.trim()) return;

    if (!queryOverride) input.value = "";

    const chatWindow = document.getElementById("chat-messages-container");

    // Append user message
    const userMsg = document.createElement("div");
    userMsg.className = "flex justify-end mb-3";
    userMsg.innerHTML = `
        <div class="bg-sky-600 text-white rounded-2xl rounded-tr-none px-4 py-2.5 max-w-[80%] text-sm shadow-sm">
            ${query}
        </div>
    `;
    chatWindow.appendChild(userMsg);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Loading placeholder
    const typingMsg = document.createElement("div");
    typingMsg.id = "typing-placeholder";
    typingMsg.className = "flex justify-start mb-3";
    typingMsg.innerHTML = `
        <div class="bg-slate-100 text-slate-600 rounded-2xl rounded-tl-none px-4 py-2.5 text-xs flex items-center space-x-2">
            <i data-lucide="loader" class="w-3.5 h-3.5 animate-spin text-sky-600"></i>
            <span>Consulting authorized records & safety guidelines...</span>
        </div>
    `;
    chatWindow.appendChild(typingMsg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    lucide.createIcons();

    try {
        const res = await fetch("/api/ai/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: query })
        });
        const typingEl = document.getElementById("typing-placeholder");
        if (typingEl) typingEl.remove();

        if (!res.ok) return;
        const data = await res.json();

        const botMsg = document.createElement("div");
        botMsg.className = "flex justify-start mb-3";
        botMsg.innerHTML = `
            <div class="bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-none p-4 max-w-[85%] text-sm shadow-sm space-y-2">
                <div class="flex items-center space-x-1.5 text-xs font-bold text-sky-700 pb-1 border-b border-slate-100">
                    <i data-lucide="shield-check" class="w-3.5 h-3.5 text-sky-600"></i>
                    <span>CareVault AI Assistant</span>
                </div>
                <div class="leading-relaxed whitespace-pre-wrap">${data.response}</div>
                <div class="text-[10px] text-slate-400 pt-1 border-t border-slate-100 italic">
                    CareVault AI is an informational decision-support tool, not a diagnostic system.
                </div>
            </div>
        `;
        chatWindow.appendChild(botMsg);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        lucide.createIcons();
    } catch (e) {
        console.error("Chat error", e);
    }
}

async function loadHistorySummary() {
    switchPatientTab("ai-assistant");
    sendChatMessage("Summarize my medical history");
}

// ==========================================
// "UNDERSTAND YOUR HEALTH" CONDITION AWARENESS
// ==========================================

async function loadConditionsList() {
    try {
        const res = await fetch("/api/ai/conditions-list");
        if (!res.ok) return;
        const list = await res.json();
        const select = document.getElementById("condition-select");
        if (select) {
            select.innerHTML = list.map(c => `<option value="${c.name}">${c.name} (${c.category})</option>`).join('');
            if (list.length > 0) fetchConditionDetails(list[0].name);
        }
    } catch (e) {
        console.error("Conditions list error", e);
    }
}

async function fetchConditionDetails(condName = null) {
    const select = document.getElementById("condition-select");
    const name = condName || (select ? select.value : "Type 2 Diabetes Mellitus");
    const container = document.getElementById("condition-detail-card");

    try {
        const res = await fetch(`/api/ai/understand-health?condition=${encodeURIComponent(name)}`);
        if (!res.ok) return;
        const c = await res.json();

        container.innerHTML = `
            <div class="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-5">
                <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                        <span class="badge-category bg-sky-100 text-sky-800">Educational Health Guide</span>
                        <h3 class="text-xl font-bold text-slate-900 mt-1">${c.name}</h3>
                    </div>
                </div>

                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 leading-relaxed flex items-start space-x-2">
                    <i data-lucide="shield-alert" class="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0"></i>
                    <span>${c.safety_note}</span>
                </div>

                <div>
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">What is it?</h4>
                    <p class="text-sm text-slate-800 leading-relaxed">${c.what_is_it}</p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="p-4 bg-slate-50 rounded-xl border border-slate-100">
                        <h4 class="text-xs font-bold text-slate-800 mb-2">Common Signs / Symptoms</h4>
                        <ul class="text-xs text-slate-600 space-y-1">
                            ${c.common_symptoms.map(s => `<li>&bull; ${s}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="p-4 bg-slate-50 rounded-xl border border-slate-100">
                        <h4 class="text-xs font-bold text-slate-800 mb-2">Common Risk Factors</h4>
                        <ul class="text-xs text-slate-600 space-y-1">
                            ${c.risk_factors.map(r => `<li>&bull; ${r}</li>`).join('')}
                        </ul>
                    </div>
                </div>

                <div>
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">What Tests are Used for Monitoring</h4>
                    <div class="flex flex-wrap gap-2">
                        ${c.tests_used_for_monitoring.map(t => `<span class="badge-category bg-sky-50 text-sky-700 text-xs">${t}</span>`).join('')}
                    </div>
                </div>

                <div>
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">General Management Topics to Discuss</h4>
                    <p class="text-xs text-slate-700 leading-relaxed">${c.general_management_topics}</p>
                </div>

                <div class="p-4 bg-rose-50 border border-rose-200 rounded-xl">
                    <h4 class="text-xs font-bold text-rose-900 mb-1">When Urgent Attention May Be Needed</h4>
                    <p class="text-xs text-rose-800">${c.when_urgent_attention_needed}</p>
                </div>
            </div>
        `;
        lucide.createIcons();
    } catch (e) {
        console.error("Condition fetch error", e);
    }
}

// ==========================================
// DOCTOR VISIT QUESTION GENERATOR & CHECKLIST
// ==========================================

async function loadDoctorQuestions() {
    try {
        const res = await fetch("/api/ai/doctor-questions");
        if (!res.ok) return;
        const questions = await res.json();
        renderDoctorQuestions(questions);
    } catch (e) {
        console.error("Doctor questions error", e);
    }
}

function renderDoctorQuestions(questions) {
    const listEl = document.getElementById("doctor-questions-list");
    if (!listEl) return;
    listEl.innerHTML = "";

    questions.forEach(q => {
        const item = document.createElement("div");
        item.className = `p-3.5 bg-white border ${q.is_checked ? 'border-emerald-200 bg-emerald-50/30' : 'border-slate-200'} rounded-xl shadow-sm flex items-start justify-between gap-3 transition`;
        item.innerHTML = `
            <div class="flex items-start space-x-3 flex-1">
                <input type="checkbox" ${q.is_checked ? 'checked' : ''} onchange="toggleDoctorQuestion(${q.id})" class="mt-1 w-4 h-4 text-sky-600 rounded border-slate-300 focus:ring-sky-500 cursor-pointer">
                <div>
                    <div class="text-sm text-slate-800 ${q.is_checked ? 'line-through opacity-60' : 'font-medium'}">${q.question_text}</div>
                    <span class="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mt-0.5 inline-block">${q.category}</span>
                </div>
            </div>
            <button onclick="deleteDoctorQuestion(${q.id})" class="text-slate-400 hover:text-rose-500 p-1 transition" title="Delete Question">
                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            </button>
        `;
        listEl.appendChild(item);
    });
    lucide.createIcons();
}

async function addCustomDoctorQuestion() {
    const input = document.getElementById("new-question-input");
    const txt = input.value.trim();
    if (!txt) return;

    try {
        const res = await fetch("/api/ai/doctor-questions/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question_text: txt, category: "Custom Patient Note" })
        });
        if (res.ok) {
            input.value = "";
            loadDoctorQuestions();
            showToast("Question added to your visit checklist", "success");
        }
    } catch (e) {
        console.error("Add question error", e);
    }
}

async function toggleDoctorQuestion(qId) {
    try {
        await fetch(`/api/ai/doctor-questions/${qId}/toggle`, { method: "POST" });
        loadDoctorQuestions();
    } catch (e) {
        console.error("Toggle error", e);
    }
}

async function deleteDoctorQuestion(qId) {
    try {
        await fetch(`/api/ai/doctor-questions/${qId}`, { method: "DELETE" });
        loadDoctorQuestions();
    } catch (e) {
        console.error("Delete error", e);
    }
}

function printDoctorChecklist() {
    window.print();
}

// ==========================================
// PATIENT CONSENT & QR SHARING
// ==========================================

async function loadConsentSharing() {
    try {
        const res = await fetch("/api/consents");
        if (!res.ok) return;
        const consents = await res.json();

        const pendingContainer = document.getElementById("pending-consents-container");
        const activeContainer = document.getElementById("active-consents-container");

        pendingContainer.innerHTML = "";
        activeContainer.innerHTML = "";

        const pending = consents.filter(c => c.status === "REQUESTED");
        const active = consents.filter(c => c.status === "GRANTED");

        if (pending.length === 0) {
            pendingContainer.innerHTML = `<div class="p-4 text-center text-xs text-slate-400">No pending access requests.</div>`;
        } else {
            pending.forEach(c => {
                const card = document.createElement("div");
                card.className = "p-4 bg-white border-2 border-sky-300 rounded-2xl shadow-sm space-y-3";
                card.innerHTML = `
                    <div class="flex items-start justify-between">
                        <div>
                            <span class="badge-category bg-sky-100 text-sky-800">Access Requested</span>
                            <h4 class="font-bold text-slate-900 text-base mt-1">${c.provider_name}</h4>
                            <div class="text-xs text-slate-500">${c.provider_hospital}</div>
                        </div>
                        <span class="text-xs font-mono font-bold text-slate-500">${c.duration_minutes} mins</span>
                    </div>

                    <div class="text-xs text-slate-700 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                        <div><span class="font-semibold">Clinical Purpose:</span> ${c.purpose}</div>
                        <div class="mt-1"><span class="font-semibold">Requested Scopes:</span> ${(c.requested_records || []).join(', ')}</div>
                    </div>

                    <div class="flex items-center space-x-2 pt-1">
                        <button onclick="respondConsent('${c.consent_id}', 'GRANTED')" class="flex-1 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm transition">
                            ALLOW ACCESS
                        </button>
                        <button onclick="respondConsent('${c.consent_id}', 'REJECTED')" class="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition">
                            REJECT
                        </button>
                    </div>
                `;
                pendingContainer.appendChild(card);
            });
        }

        if (active.length === 0) {
            activeContainer.innerHTML = `<div class="p-4 text-center text-xs text-slate-400">No active provider sharing sessions.</div>`;
        } else {
            active.forEach(c => {
                const card = document.createElement("div");
                card.className = "p-4 bg-white border border-emerald-200 rounded-2xl shadow-sm space-y-2";
                card.innerHTML = `
                    <div class="flex items-start justify-between">
                        <div>
                            <div class="flex items-center space-x-2">
                                <span class="badge-category bg-emerald-100 text-emerald-800">Active Session</span>
                                <span class="text-[11px] text-slate-400 font-mono">${c.consent_id}</span>
                            </div>
                            <h4 class="font-bold text-slate-900 text-sm mt-1">${c.provider_name}</h4>
                        </div>
                        <button onclick="respondConsent('${c.consent_id}', 'REVOKED')" class="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-bold transition">
                            REVOKE
                        </button>
                    </div>
                    <div class="text-xs text-slate-600">
                        Scopes: ${(c.requested_records || []).join(', ')}
                    </div>
                    <div class="text-[11px] text-slate-400 font-mono">
                        Expires at: ${new Date(c.expires_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                `;
                activeContainer.appendChild(card);
            });
        }

        lucide.createIcons();
    } catch (e) {
        console.error("Consent load error", e);
    }
}

async function respondConsent(consentId, status) {
    try {
        const res = await fetch(`/api/consents/${consentId}/status`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: status })
        });
        if (res.ok) {
            showToast(`Access permission ${status.toLowerCase()} successfully`, "success");
            loadConsentSharing();
            loadPatientDashboard();
        }
    } catch (e) {
        console.error("Respond consent error", e);
    }
}

async function generateShareQR() {
    const duration = parseInt(document.getElementById("qr-duration-select").value);
    const scopes = [];
    if (document.getElementById("qr-scope-labs").checked) scopes.push("Lab Reports");
    if (document.getElementById("qr-scope-rx").checked) scopes.push("Prescriptions");
    if (document.getElementById("qr-scope-scans").checked) scopes.push("CT/MRI", "X-rays");

    if (scopes.length === 0) {
        showToast("Select at least one record scope.", "warning");
        return;
    }

    try {
        const res = await fetch("/api/consents/qr/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ allowed_scopes: scopes, duration_minutes: duration })
        });
        if (!res.ok) return;
        const data = await res.json();

        const qrModal = document.getElementById("qr-modal");
        const qrImg = document.getElementById("qr-modal-image");
        const qrScopes = document.getElementById("qr-modal-scopes");
        const qrExpires = document.getElementById("qr-modal-expires");

        qrImg.src = `/api/consents/qr/image?token=${encodeURIComponent(data.qr_token)}`;
        qrScopes.textContent = data.allowed_scopes.join(', ');
        qrExpires.textContent = `${data.expires_in_minutes} minutes from now`;

        qrModal.classList.remove("hidden");
        lucide.createIcons();
    } catch (e) {
        console.error("QR generate error", e);
    }
}

function closeQRModal() {
    document.getElementById("qr-modal").classList.add("hidden");
}

// ==========================================
// SMART HOSPITAL FINDER & MATCHING ENGINE
// ==========================================

async function loadHospitals() {
    const query = document.getElementById("hospital-query-input").value;
    const specialty = document.getElementById("hospital-spec-filter").value;
    const cost = document.getElementById("hospital-cost-filter").value;
    const insurance = document.getElementById("hospital-ins-filter").value;
    const emergencyOnly = document.getElementById("hospital-emergency-filter").checked;

    // Weight sliders
    const wSpec = parseFloat(document.getElementById("weight-spec").value) / 100.0;
    const wDist = parseFloat(document.getElementById("weight-dist").value) / 100.0;
    const wCost = parseFloat(document.getElementById("weight-cost").value) / 100.0;
    const wIns = parseFloat(document.getElementById("weight-ins").value) / 100.0;
    const wVer = parseFloat(document.getElementById("weight-ver").value) / 100.0;

    const payload = {
        query: query || null,
        specialty: specialty !== "All" ? specialty : null,
        cost: cost !== "All" ? cost : null,
        insurance: insurance !== "All" ? insurance : null,
        emergency_only: emergencyOnly,
        weights: {
            specialty_match: wSpec,
            distance: wDist,
            cost_fit: wCost,
            insurance_match: wIns,
            facility_verification: wVer
        }
    };

    try {
        const res = await fetch("/api/hospitals/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!res.ok) return;
        const data = await res.json();
        renderHospitalResults(data.results);
        updateMapMarkers(data.results);
    } catch (e) {
        console.error("Hospitals load error", e);
    }
}

function renderHospitalResults(facilities) {
    const container = document.getElementById("hospital-results-list");
    if (!container) return;
    container.innerHTML = "";

    if (facilities.length === 0) {
        container.innerHTML = `<div class="py-12 text-center text-slate-400">No facilities found matching your criteria.</div>`;
        return;
    }

    facilities.forEach(f => {
        const card = document.createElement("div");
        card.className = "p-5 bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md transition space-y-3";
        card.innerHTML = `
            <div class="flex items-start justify-between gap-3">
                <div>
                    <div class="flex items-center space-x-2">
                        <span class="badge-category bg-emerald-100 text-emerald-800 font-bold">${f.match_percentage}% Match</span>
                        ${f.emergency ? '<span class="badge-category bg-rose-100 text-rose-800">24/7 ER</span>' : ''}
                        <span class="text-xs font-bold text-slate-500 font-mono">${f.cost_range}</span>
                    </div>
                    <h4 class="font-bold text-slate-900 text-lg mt-1">${f.name}</h4>
                    <div class="text-xs text-slate-500">${f.address}</div>
                </div>
                <div class="text-right flex-shrink-0">
                    <span class="text-sm font-bold text-sky-700">${f.distance_km} km</span>
                    <div class="text-[11px] text-slate-400">from your location</div>
                </div>
            </div>

            <!-- Why this facility appears -->
            <div class="p-3 bg-sky-50/50 rounded-xl border border-sky-100/80 space-y-1">
                <div class="text-[11px] font-bold uppercase tracking-wider text-sky-900">Why this facility matches your criteria:</div>
                ${f.match_reasons.map(r => `<div class="text-xs text-slate-700 font-medium">${r}</div>`).join('')}
            </div>

            <div class="flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100">
                <div>Phone: <span class="font-bold text-slate-700 font-mono">${f.contact_phone}</span></div>
                <button onclick="panMapTo(${f.latitude}, ${f.longitude}, '${f.name.replace(/'/g, "\\'")}')" class="text-sky-600 font-bold hover:underline flex items-center space-x-1">
                    <i data-lucide="map-pin" class="w-3.5 h-3.5"></i>
                    <span>Show on Map</span>
                </button>
            </div>
        `;
        container.appendChild(card);
    });
    lucide.createIcons();
}

function initLeafletMap() {
    if (leafletMap) return;
    const mapEl = document.getElementById("leaflet-map");
    if (!mapEl) return;

    leafletMap = L.map('leaflet-map').setView([17.4300, 78.4100], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(leafletMap);
}

function updateMapMarkers(facilities) {
    if (!leafletMap) return;
    mapMarkers.forEach(m => leafletMap.removeLayer(m));
    mapMarkers = [];

    facilities.forEach(f => {
        const marker = L.marker([f.latitude, f.longitude]).addTo(leafletMap);
        marker.bindPopup(`
            <div style="font-size:12px; font-family:sans-serif;">
                <b>${f.name}</b><br>
                <span>${f.address}</span><br>
                <b style="color:#0284c7;">${f.match_percentage}% Match</b> &bull; ${f.distance_km} km<br>
                <span>Call: ${f.contact_phone}</span>
            </div>
        `);
        mapMarkers.push(marker);
    });
}

function panMapTo(lat, lng, name) {
    if (!leafletMap) return;
    leafletMap.setView([lat, lng], 15);
    window.scrollTo({ top: document.getElementById("leaflet-map").offsetTop - 100, behavior: 'smooth' });
}

// ==========================================
// 🚨 EMERGENCY MODE SCREEN
// ==========================================

async function loadEmergencyScreen() {
    try {
        const res = await fetch("/api/hospitals/emergency");
        if (!res.ok) return;
        const data = await res.json();

        const container = document.getElementById("emergency-facilities-container");
        if (container) {
            container.innerHTML = data.nearest_facilities.map(f => `
                <div class="p-5 bg-white border-2 border-rose-300 rounded-2xl shadow-md space-y-3 text-left">
                    <div class="flex items-start justify-between">
                        <div>
                            <span class="badge-category bg-rose-600 text-white font-bold">${f.trauma_level} Trauma</span>
                            <h4 class="font-black text-slate-900 text-lg mt-1">${f.name}</h4>
                            <div class="text-xs text-slate-500">${f.address}</div>
                        </div>
                        <div class="text-right">
                            <span class="text-sm font-black text-rose-600">${f.distance_km} km</span>
                            <div class="text-[10px] text-slate-400">away</div>
                        </div>
                    </div>

                    <div class="flex items-center space-x-3 pt-2">
                        <a href="tel:${f.helpline}" class="flex-1 py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-black text-xs rounded-xl flex items-center justify-center space-x-1.5 shadow-sm transition">
                            <i data-lucide="phone-call" class="w-4 h-4"></i>
                            <span>Call ER (${f.helpline})</span>
                        </a>
                        <a href="tel:${f.ambulance_phone}" class="flex-1 py-2.5 bg-slate-900 hover:bg-black text-white font-bold text-xs rounded-xl flex items-center justify-center space-x-1.5 transition">
                            <i data-lucide="truck" class="w-4 h-4"></i>
                            <span>Ambulance</span>
                        </a>
                    </div>
                </div>
            `).join('');
            lucide.createIcons();
        }
    } catch (e) {
        console.error("Emergency load error", e);
    }
}

async function showEmergencyMedicalID() {
    try {
        const res = await fetch("/api/patients/emergency-card");
        if (!res.ok) return;
        const card = await res.json();

        const modal = document.getElementById("emergency-id-modal");
        document.getElementById("em-name").textContent = card.full_name;
        document.getElementById("em-pid").textContent = card.patient_id;
        document.getElementById("em-blood").textContent = card.blood_group;
        document.getElementById("em-dob").textContent = card.dob;
        document.getElementById("em-allergies").textContent = card.allergies || "None reported";
        document.getElementById("em-conditions").textContent = card.existing_conditions || "None reported";
        document.getElementById("em-meds").textContent = card.current_medications || "None active";
        document.getElementById("em-contact").textContent = `${card.emergency_contact.name} (${card.emergency_contact.relation}) - ${card.emergency_contact.phone}`;

        modal.classList.remove("hidden");
        lucide.createIcons();
    } catch (e) {
        console.error("Emergency ID error", e);
    }
}

function closeEmergencyIDModal() {
    document.getElementById("emergency-id-modal").classList.add("hidden");
}

// ==========================================
// ACCESS HISTORY / AUDIT LOG
// ==========================================

async function loadAccessHistory() {
    try {
        const res = await fetch("/api/audit/my-history");
        if (!res.ok) return;
        const logs = await res.json();

        const tbody = document.getElementById("audit-history-table");
        if (!tbody) return;
        tbody.innerHTML = "";

        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-slate-400">No access history recorded yet.</td></tr>`;
            return;
        }

        logs.forEach(l => {
            const tr = document.createElement("tr");
            tr.className = "border-b border-slate-100 hover:bg-slate-50 transition text-xs";
            
            let statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">SUCCESS</span>`;
            if (l.status === "DENIED" || l.status === "REVOKED") statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">${l.status}</span>`;
            if (l.status === "EXPIRED") statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600">EXPIRED</span>`;

            tr.innerHTML = `
                <td class="py-3 px-4 font-mono text-slate-500">${l.timestamp.replace('T', ' ').substring(0, 16)}</td>
                <td class="py-3 px-4 font-bold text-slate-800">${l.actor_name} <span class="text-[10px] text-slate-400">(${l.actor_role})</span></td>
                <td class="py-3 px-4 text-slate-700">${l.record_title || 'N/A'}</td>
                <td class="py-3 px-4 font-mono text-sky-700">${l.action}</td>
                <td class="py-3 px-4">${statusBadge}</td>
                <td class="py-3 px-4 text-slate-500">${l.details}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Audit load error", e);
    }
}

// ==========================================
// DOCTOR PORTAL CONTROLLER
// ==========================================

async function loadDoctorPortal() {
    clearInterval(doctorTimerInterval);
    try {
        const res = await fetch("/api/doctor/my-consents");
        if (!res.ok) return;
        const sessions = await res.json();

        const container = document.getElementById("doctor-sessions-container");
        if (!container) return;
        container.innerHTML = "";

        if (sessions.length === 0) {
            container.innerHTML = `<div class="p-8 text-center text-slate-400">No active patient sessions. Request access below.</div>`;
            return;
        }

        sessions.forEach(s => {
            const card = document.createElement("div");
            card.className = "p-5 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-3";
            card.innerHTML = `
                <div class="flex items-start justify-between">
                    <div>
                        <div class="flex items-center space-x-2">
                            <span class="badge-category ${s.is_live ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}">
                                ${s.is_live ? 'LIVE CONSENT' : s.status}
                            </span>
                            <span class="text-xs font-mono text-slate-400">${s.patient_id}</span>
                        </div>
                        <h4 class="font-bold text-slate-900 text-lg mt-1">${s.patient_name}</h4>
                        <div class="text-xs text-slate-500">Blood: ${s.blood_group} | Allergies: ${s.allergies || 'None'}</div>
                    </div>
                    <div class="text-right">
                        ${s.is_live ? `
                            <div class="text-[10px] uppercase font-bold text-slate-400">Access Expiry Timer</div>
                            <div id="timer-${s.consent_id}" class="text-sm font-mono font-black text-rose-600">Calculating...</div>
                        ` : `
                            <div class="text-xs font-mono text-slate-400">${s.status}</div>
                        `}
                    </div>
                </div>

                <div class="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                    <div><b>Purpose:</b> ${s.purpose}</div>
                    <div class="mt-0.5"><b>Scopes:</b> ${(s.requested_records || []).join(', ')}</div>
                </div>

                ${s.is_live ? `
                    <div class="flex items-center space-x-2 pt-2">
                        <button onclick="viewDoctorPatientRecords('${s.patient_id}')" class="flex-1 py-2 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-xl shadow-sm transition flex items-center justify-center space-x-1">
                            <i data-lucide="folder" class="w-3.5 h-3.5"></i>
                            <span>View Consented Records</span>
                        </button>
                        <button onclick="openDoctorAddNoteModal('${s.patient_id}', '${s.patient_name}')" class="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition flex items-center justify-center space-x-1">
                            <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i>
                            <span>Add Clinical Note / Rx</span>
                        </button>
                    </div>
                ` : ''}
            `;
            container.appendChild(card);

            if (s.is_live) {
                startDoctorCountdown(s.consent_id, s.remaining_seconds);
            }
        });

        lucide.createIcons();
    } catch (e) {
        console.error("Doctor portal load error", e);
    }
}

function startDoctorCountdown(consentId, remainingSeconds) {
    let secs = remainingSeconds;
    const updateEl = () => {
        const el = document.getElementById(`timer-${consentId}`);
        if (!el) return;
        if (secs <= 0) {
            el.textContent = "EXPIRED";
            el.className = "text-xs font-mono font-bold text-slate-400";
            return;
        }
        const m = Math.floor(secs / 60);
        const s = secs % 60;
        el.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')} remaining`;
        secs--;
    };
    updateEl();
    doctorTimerInterval = setInterval(updateEl, 1000);
}

async function requestDoctorAccess() {
    const pid = document.getElementById("doc-req-pid").value.trim();
    const purpose = document.getElementById("doc-req-purpose").value.trim();
    const duration = parseInt(document.getElementById("doc-req-duration").value);

    const scopes = [];
    if (document.getElementById("doc-scope-labs").checked) scopes.push("Lab Reports");
    if (document.getElementById("doc-scope-rx").checked) scopes.push("Prescriptions");
    if (document.getElementById("doc-scope-scans").checked) scopes.push("CT/MRI", "X-rays");
    if (document.getElementById("doc-scope-all").checked) scopes.push("All Records");

    if (!pid || !purpose) {
        showToast("Enter Patient ID and clinical purpose.", "warning");
        return;
    }

    try {
        const res = await fetch("/api/consents/request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                patient_id: pid,
                requested_records: scopes.length ? scopes : ["All Records"],
                purpose: purpose,
                duration_minutes: duration
            })
        });

        if (res.ok) {
            showToast("Access request submitted to patient.", "success");
            loadDoctorPortal();
        } else {
            const err = await res.json();
            showToast(err.detail || "Request failed", "error");
        }
    } catch (e) {
        console.error("Doctor req error", e);
    }
}

async function viewDoctorPatientRecords(patientId) {
    try {
        const res = await fetch(`/api/doctor/patient-records/${patientId}`);
        if (!res.ok) {
            const err = await res.json();
            showToast(err.detail || "Access Denied", "error");
            return;
        }
        const data = await res.json();

        const modal = document.getElementById("doctor-records-modal");
        document.getElementById("doc-modal-pname").textContent = `${data.patient.name} (${data.patient.patient_id})`;
        document.getElementById("doc-modal-meta").textContent = `Purpose: ${data.purpose} | Scope: ${data.permitted_scopes.join(', ')}`;
        
        const grid = document.getElementById("doc-modal-records-grid");
        grid.innerHTML = data.records.map(r => `
            <div class="p-4 bg-white border border-slate-200 rounded-xl shadow-sm flex items-center justify-between">
                <div>
                    <span class="badge-category bg-sky-100 text-sky-800 text-[10px]">${r.record_type}</span>
                    <h5 class="font-bold text-slate-900 text-sm mt-1">${r.title}</h5>
                    <div class="text-xs text-slate-500">${r.record_date} &bull; ${r.hospital_name}</div>
                </div>
                <button onclick="openDocumentView('${r.record_id}')" class="px-3 py-1.5 bg-slate-900 hover:bg-black text-white rounded-lg text-xs font-bold transition flex items-center space-x-1">
                    <i data-lucide="eye" class="w-3.5 h-3.5"></i>
                    <span>View Watermarked</span>
                </button>
            </div>
        `).join('');

        modal.classList.remove("hidden");
        lucide.createIcons();
    } catch (e) {
        console.error("Doctor patient records error", e);
    }
}

function closeDoctorRecordsModal() {
    document.getElementById("doctor-records-modal").classList.add("hidden");
}

function openDoctorAddNoteModal(patientId, patientName) {
    document.getElementById("doc-note-pid").value = patientId;
    document.getElementById("doc-note-pname").textContent = `${patientName} (${patientId})`;
    document.getElementById("doctor-add-note-modal").classList.remove("hidden");
}

function closeDoctorAddNoteModal() {
    document.getElementById("doctor-add-note-modal").classList.add("hidden");
}

async function submitDoctorConsultation() {
    const pid = document.getElementById("doc-note-pid").value;
    const title = document.getElementById("doc-note-title").value.trim();
    const notes = document.getElementById("doc-note-text").value.trim();

    if (!title || !notes) {
        showToast("Enter title and consultation notes.", "warning");
        return;
    }

    try {
        const res = await fetch("/api/doctor/add-consultation", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                patient_id: pid,
                title: title,
                clinical_notes: notes
            })
        });

        if (res.ok) {
            showToast("Consultation record added directly to patient's wallet!", "success");
            closeDoctorAddNoteModal();
            loadDoctorPortal();
        } else {
            const err = await res.json();
            showToast(err.detail || "Failed to add record", "error");
        }
    } catch (e) {
        console.error("Doctor add note error", e);
    }
}

// ==========================================
// LAB PORTAL CONTROLLER
// ==========================================

function loadLabPortal() {
    // Reset lab form
    document.getElementById("lab-verified-patient-box").classList.add("hidden");
}

async function verifyPatientForLab() {
    const pid = document.getElementById("lab-patient-search-id").value.trim();
    if (!pid) return;

    try {
        const res = await fetch(`/api/lab/search-patient?patient_id=${encodeURIComponent(pid)}`);
        const box = document.getElementById("lab-verified-patient-box");
        
        if (res.ok) {
            const p = await res.json();
            document.getElementById("lab-confirmed-name").textContent = p.full_name;
            document.getElementById("lab-confirmed-dob").textContent = p.dob;
            document.getElementById("lab-confirmed-blood").textContent = p.blood_group;
            document.getElementById("lab-target-pid").value = p.patient_id;
            box.classList.remove("hidden");
            showToast(`Patient ${p.patient_id} verified. Ready for record transfer.`, "success");
        } else {
            box.classList.add("hidden");
            showToast("Patient ID not found.", "error");
        }
    } catch (e) {
        console.error("Lab verify error", e);
    }
}

async function submitLabRecordTransfer() {
    const pid = document.getElementById("lab-target-pid").value;
    const title = document.getElementById("lab-rec-title").value.trim();
    const type = document.getElementById("lab-rec-type").value;
    const doctor = document.getElementById("lab-rec-doctor").value.trim();
    const date = document.getElementById("lab-rec-date").value;
    const params = document.getElementById("lab-rec-params").value.trim();

    if (!pid || !title || !date) {
        showToast("Please fill in the required fields.", "warning");
        return;
    }

    const formData = new FormData();
    formData.append("patient_id", pid);
    formData.append("title", title);
    formData.append("record_type", type);
    formData.append("doctor_name", doctor || "Consulting Pathologist");
    formData.append("record_date", date);
    formData.append("description", `Diagnostic transfer delivered directly to patient wallet.`);
    formData.append("parameters", params);

    try {
        const res = await fetch("/api/lab/transfer-record", {
            method: "POST",
            body: formData
        });

        if (res.ok) {
            showToast(`Test record successfully transferred directly into patient's wallet!`, "success");
            // Clear inputs
            document.getElementById("lab-rec-title").value = "";
            document.getElementById("lab-rec-params").value = "";
            document.getElementById("lab-verified-patient-box").classList.add("hidden");
        } else {
            const err = await res.json();
            showToast(err.detail || "Transfer failed", "error");
        }
    } catch (e) {
        console.error("Lab transfer error", e);
    }
}

// ==========================================
// ADMIN DASHBOARD CONTROLLER
// ==========================================

async function loadAdminPortal() {
    try {
        const res = await fetch("/api/admin/metrics");
        if (!res.ok) return;
        const m = await res.json();

        document.getElementById("admin-total-patients").textContent = m.total_patients;
        document.getElementById("admin-total-doctors").textContent = m.total_doctors;
        document.getElementById("admin-total-facilities").textContent = m.total_facilities;
        document.getElementById("admin-total-records").textContent = m.total_records;
        document.getElementById("admin-active-consents").textContent = m.active_sharing_sessions;
        document.getElementById("admin-total-audits").textContent = m.total_audit_events;

        loadAdminFacilities();
    } catch (e) {
        console.error("Admin load error", e);
    }
}

async function loadAdminFacilities() {
    try {
        const res = await fetch("/api/admin/facilities");
        if (!res.ok) return;
        const facs = await res.json();

        const tbody = document.getElementById("admin-facilities-table");
        if (!tbody) return;
        tbody.innerHTML = "";

        facs.forEach(f => {
            const tr = document.createElement("tr");
            tr.className = "border-b border-slate-100 hover:bg-slate-50 transition text-xs";
            tr.innerHTML = `
                <td class="py-3 px-4 font-mono font-bold text-slate-800">${f.hospital_id}</td>
                <td class="py-3 px-4 font-medium text-slate-900">${f.name}</td>
                <td class="py-3 px-4 text-slate-600">${(f.specialties || []).slice(0, 3).join(', ')}</td>
                <td class="py-3 px-4 text-slate-600 font-mono">${f.cost_range}</td>
                <td class="py-3 px-4">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${f.verification_status === 'VERIFIED_SYNTHETIC' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                        ${f.verification_status}
                    </span>
                </td>
                <td class="py-3 px-4 text-right">
                    <button onclick="toggleFacilityVerification('${f.hospital_id}')" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold">
                        Toggle Status
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Admin facs error", e);
    }
}

async function toggleFacilityVerification(hid) {
    try {
        const res = await fetch(`/api/admin/facilities/${hid}/toggle-verification`, { method: "POST" });
        if (res.ok) {
            showToast("Facility verification status updated", "info");
            loadAdminFacilities();
        }
    } catch (e) {
        console.error("Toggle ver error", e);
    }
}

// ==========================================
// TOAST NOTIFICATION UTILITY
// ==========================================

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    let bg = "bg-slate-900 text-white";
    if (type === "success") bg = "bg-emerald-600 text-white";
    if (type === "error") bg = "bg-rose-600 text-white";
    if (type === "warning") bg = "bg-amber-600 text-white";

    toast.className = `fixed bottom-5 right-5 z-50 px-4 py-3 rounded-2xl shadow-xl font-medium text-xs flex items-center space-x-2 transition-all transform duration-300 ${bg}`;
    toast.innerHTML = `<span>${message}</span>`;

    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}
