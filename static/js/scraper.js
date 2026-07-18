/**
 * CareerBridge — Scraper engine controls, real-time status polling, and Force Stop.
 */

document.addEventListener("DOMContentLoaded", function () {

    // ── DOM refs ────────────────────────────────────────────────────────────────
    const triggerBtn      = document.querySelector("#trigger-scrape-btn");
    const triggerIcon     = document.querySelector("#trigger-btn-icon");
    const triggerText     = document.querySelector("#trigger-btn-text");
    const statusMsg       = document.querySelector("#trigger-status-msg");
    const forceStopBtn    = document.querySelector("#force-stop-btn");
    const forceStopText   = document.querySelector("#force-stop-text");
    const stuckBanner     = document.querySelector("#stuck-warning-banner");
    const stuckWarningText= document.querySelector("#stuck-warning-text");

    const engineStateText = document.querySelector("#engine-state-text");
    const lastSuccessTime = document.querySelector("#last-success-time");
    const lastSuccessJobs = document.querySelector("#last-success-jobs");
    const logsTableBody   = document.querySelector("#logs-table-body");
    const prefsForm       = document.querySelector("#preferences-form");

    let pollingInterval   = null;
    let healthInterval    = null;

    // ── Helpers ─────────────────────────────────────────────────────────────────
    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)"));
        return match ? decodeURIComponent(match[2]) : null;
    }
    const csrftoken = getCookie("csrftoken");

    function setEngineRunning(msg) {
        if (engineStateText)
            engineStateText.innerHTML = '<span class="status-indicator running"></span> Running Scrape';
        if (triggerBtn) {
            triggerBtn.disabled = true;
            if (triggerText) triggerText.innerText = "Scraper Running...";
            if (triggerIcon) {
                triggerIcon.className = "spin";
                triggerIcon.setAttribute("data-lucide", "loader-2");
                if (window.lucide) window.lucide.createIcons();
            }
        }
        if (forceStopBtn) forceStopBtn.style.display = "flex";
        if (statusMsg && msg) statusMsg.innerText = msg;
    }

    function setEngineIdle() {
        if (engineStateText)
            engineStateText.innerHTML = '<span class="status-indicator idle" style="background-color: var(--text-secondary);"></span> Idle';
        if (triggerBtn) {
            triggerBtn.disabled = false;
            if (triggerText) triggerText.innerText = "Trigger Scraper Now";
            if (triggerIcon) {
                triggerIcon.className = "";
                triggerIcon.setAttribute("data-lucide", "play");
                if (window.lucide) window.lucide.createIcons();
            }
        }
        if (forceStopBtn) forceStopBtn.style.display = "none";
        if (stuckBanner)  stuckBanner.style.display  = "none";
        if (forceStopBtn) {
            forceStopBtn.disabled = false;
            if (forceStopText) forceStopText.innerText = "Force Stop";
        }
    }

    // ── 1. Status Polling ───────────────────────────────────────────────────────
    function pollScraperStatus() {
        fetch("/api/scraper/status/")
            .then(res => res.json())
            .then(data => {
                if (data.is_running) {
                    const found    = data.current_run?.jobs_found ?? 0;
                    const progress = data.current_run?.progress_message ?? "";
                    setEngineRunning(
                        `Background task active (${found} found so far). ${progress} Polling for completion...`
                    );
                    if (!pollingInterval)
                        pollingInterval = setInterval(pollScraperStatus, 3000);
                } else {
                    setEngineIdle();

                    if (data.last_success) {
                        const d = new Date(data.last_success.started_at);
                        if (lastSuccessTime)
                            lastSuccessTime.innerText = d.toLocaleDateString("en-US", {
                                month: "short", day: "numeric",
                                hour: "2-digit", minute: "2-digit"
                            });
                        if (lastSuccessJobs)
                            lastSuccessJobs.innerText =
                                `${data.last_success.jobs_new} new / ${data.last_success.jobs_found} total`;
                    }

                    if (pollingInterval) {
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                        if (statusMsg) statusMsg.innerText = "Scrape task finished! Log refreshed.";
                        refreshLogsTable();
                    }
                    if (healthInterval) {
                        clearInterval(healthInterval);
                        healthInterval = null;
                    }
                }
            })
            .catch(err => console.error("Polling error:", err));
    }

    // ── 2. Stuck-run Health Check ───────────────────────────────────────────────
    function checkHealth() {
        fetch("/api/scraper/health/")
            .then(res => res.json())
            .then(data => {
                if (data.is_stuck && stuckBanner) {
                    const run     = data.stuck_runs[0];
                    const minutes = run?.running_minutes ?? data.threshold_minutes;
                    stuckBanner.style.display = "flex";
                    if (stuckWarningText)
                        stuckWarningText.innerText =
                            `⚠ Scraper has been running for ${minutes} min and may be stuck. ` +
                            `Use "Force Stop" to reset it and start fresh.`;
                } else if (stuckBanner) {
                    stuckBanner.style.display = "none";
                }
            })
            .catch(() => {});
    }

    // ── 3. Trigger scraper ──────────────────────────────────────────────────────
    if (triggerBtn) {
        triggerBtn.addEventListener("click", function () {
            triggerBtn.disabled = true;
            if (triggerText) triggerText.innerText = "Triggering task...";
            if (statusMsg)   statusMsg.innerText    = "Connecting to Celery task queue...";

            fetch("/api/scraper/trigger/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken }
            })
            .then(res => {
                if (res.status === 409) throw new Error("A scrape task is already running.");
                if (!res.ok)            throw new Error("Failed to trigger scraper task.");
                return res.json();
            })
            .then(() => {
                // Immediately show running state — the Celery task will start soon
                setEngineRunning("Scraper triggered! Waiting for background task to start...");

                // Start polling for real status after a short delay (give Celery time to create ScrapeLog)
                setTimeout(() => {
                    pollScraperStatus();
                    if (!pollingInterval)
                        pollingInterval = setInterval(pollScraperStatus, 3000);
                }, 2000);

                // Start health checks every 2 min once triggered
                if (!healthInterval)
                    healthInterval = setInterval(checkHealth, 120_000);
            })
            .catch(err => {
                triggerBtn.disabled = false;
                if (triggerText) triggerText.innerText = "Trigger Scraper Now";
                if (statusMsg)   statusMsg.innerText   = err.message;
            });
        });
    }

    // ── 4. Force Stop ───────────────────────────────────────────────────────────
    if (forceStopBtn) {
        forceStopBtn.addEventListener("click", function () {
            const confirmed = window.confirm(
                "⛔ Force Stop Scraper?\n\n" +
                "This will immediately mark all running scrape sessions as FAILED " +
                "so you can start a fresh scrape.\n\n" +
                "The Celery/browser process in the background may take a moment to " +
                "fully terminate. Click OK to proceed."
            );
            if (!confirmed) return;

            forceStopBtn.disabled = true;
            if (forceStopText) forceStopText.innerText = "Stopping...";
            if (statusMsg)     statusMsg.innerText      = "Sending stop signal...";

            fetch("/api/scraper/stop/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
                body: JSON.stringify({})
            })
            .then(res => res.json())
            .then(data => {
                // Clear all polling
                if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null; }
                if (healthInterval)  { clearInterval(healthInterval);  healthInterval  = null; }

                setEngineIdle();

                if (statusMsg)
                    statusMsg.innerText = data.message || "Scraper stopped. You can now start a fresh scrape.";

                // Flash the status message green briefly
                if (statusMsg) {
                    statusMsg.style.color = "var(--color-new, #4ade80)";
                    setTimeout(() => { if (statusMsg) statusMsg.style.color = ""; }, 3000);
                }

                refreshLogsTable();
            })
            .catch(err => {
                forceStopBtn.disabled = false;
                if (forceStopText) forceStopText.innerText = "Force Stop";
                if (statusMsg)     statusMsg.innerText = "Stop failed: " + err.message;
                console.error("Force stop error:", err);
            });
        });
    }

    // ── 5. Refresh log table ────────────────────────────────────────────────────
    function refreshLogsTable() {
        if (!logsTableBody) return;

        fetch("/api/scraper/logs/")
            .then(res => res.json())
            .then(data => {
                if (data.length === 0) {
                    logsTableBody.innerHTML =
                        '<tr><td colspan="6" style="text-align:center;padding:30px;' +
                        'color:var(--text-muted);">No execution logs available.</td></tr>';
                    return;
                }

                logsTableBody.innerHTML = data.map(log => {
                    const date   = new Date(log.started_at);
                    const fmtDate = date.toLocaleDateString("en-US", {
                        month: "short", day: "numeric",
                        hour: "2-digit", minute: "2-digit", second: "2-digit"
                    });
                    const duration  = log.duration ? `${log.duration}s` : "-";
                    const infoMsg   = log.status === "running"
                        ? (log.progress_message || "Running...")
                        : (log.error_message    || "Success");
                    const badgeCls  = log.status === "success" ? "new"
                                    : log.status === "running"  ? "applied"
                                    : "ignored";
                    const infoColor = log.status === "failed"
                        ? "color:var(--color-ignored);"
                        : "color:var(--text-secondary);";

                    return `
                        <tr style="border-bottom:1px solid var(--border-color);">
                            <td style="padding:12px 8px;font-weight:500;">${fmtDate}</td>
                            <td style="padding:12px 8px;text-transform:capitalize;">${log.triggered_by}</td>
                            <td style="padding:12px 8px;">
                                <span class="badge badge-${badgeCls}">${log.status.toUpperCase()}</span>
                            </td>
                            <td style="padding:12px 8px;">${log.jobs_found} / ${log.jobs_new}</td>
                            <td style="padding:12px 8px;">${duration}</td>
                            <td style="padding:12px 8px;${infoColor}max-width:200px;overflow:hidden;
                                text-overflow:ellipsis;white-space:nowrap;" title="${infoMsg}">
                                ${infoMsg}
                            </td>
                        </tr>
                    `;
                }).join("");
            })
            .catch(err => console.error("Log refresh error:", err));
    }

    // ── 6. Save preferences ─────────────────────────────────────────────────────
    if (prefsForm) {
        prefsForm.addEventListener("submit", function (e) {
            e.preventDefault();

            const keywords = document.querySelector("#pref-keywords").value
                .split(",").map(k => k.trim()).filter(k => k.length > 0);
            const locations = document.querySelector("#pref-locations").value
                .split(",").map(l => l.trim()).filter(l => l.length > 0);

            const workTypes = [...document.querySelectorAll("input[name='work_types']:checked")]
                .map(cb => cb.value);
            const expLevels = [...document.querySelectorAll("input[name='experience_level']:checked")]
                .map(cb => cb.value);

            const submitBtn = prefsForm.querySelector("button[type='submit']");
            const origHtml  = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="spin" data-lucide="loader-2"></i> Saving...';
            if (window.lucide) window.lucide.createIcons();

            fetch("/api/scraper/preferences/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
                body: JSON.stringify({
                    keywords, locations, work_types: workTypes, experience_level: expLevels
                })
            })
            .then(res => {
                if (!res.ok) throw new Error("Failed to save preferences");
                return res.json();
            })
            .then(() => {
                submitBtn.disabled  = false;
                submitBtn.innerHTML = origHtml;
                if (window.lucide) window.lucide.createIcons();
                if (statusMsg) {
                    statusMsg.innerText = "✓ Preferences saved!";
                    statusMsg.style.color = "var(--color-new, #4ade80)";
                    setTimeout(() => {
                        if (statusMsg) { statusMsg.innerText = ""; statusMsg.style.color = ""; }
                    }, 3000);
                }
            })
            .catch(err => {
                submitBtn.disabled  = false;
                submitBtn.innerHTML = origHtml;
                if (window.lucide) window.lucide.createIcons();
                console.error(err);
                if (statusMsg) statusMsg.innerText = "Error saving preferences.";
            });
        });
    }

    // ── Init ────────────────────────────────────────────────────────────────────
    // Poll immediately and check health on page load
    pollScraperStatus();
    checkHealth();

    // If already running on load, set up ongoing health checks
    // (will auto-cancel when engine goes idle)
    fetch("/api/scraper/status/")
        .then(r => r.json())
        .then(data => {
            if (data.is_running && !healthInterval)
                healthInterval = setInterval(checkHealth, 120_000);
        })
        .catch(() => {});
});
