/**
 * CareerBridge — Scraper engine controls and real-time status polling
 */

document.addEventListener("DOMContentLoaded", function() {
    const triggerBtn = document.querySelector("#trigger-scrape-btn");
    const triggerIcon = document.querySelector("#trigger-btn-icon");
    const triggerText = document.querySelector("#trigger-btn-text");
    const statusMsg = document.querySelector("#trigger-status-msg");
    
    const engineStateText = document.querySelector("#engine-state-text");
    const lastSuccessTime = document.querySelector("#last-success-time");
    const lastSuccessJobs = document.querySelector("#last-success-jobs");
    const logsTableBody = document.querySelector("#logs-table-body");
    const prefsForm = document.querySelector("#preferences-form");

    let pollingInterval = null;

    // Helper to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // 1. Polling function to monitor active scraping
    function pollScraperStatus() {
        fetch("/api/scraper/status/")
            .then(res => res.json())
            .then(data => {
                if (data.is_running) {
                    // Update monitor state to running
                    engineStateText.innerHTML = '<span class="status-indicator running"></span> Running Scrape';
                    
                    // Disable button
                    if (triggerBtn) {
                        triggerBtn.disabled = true;
                        triggerText.innerText = "Scraper Running...";
                        triggerIcon.className = "spin";
                        triggerIcon.setAttribute("data-lucide", "loader-2");
                        if (window.lucide) window.lucide.createIcons();
                    }

                    let foundText = data.current_run?.jobs_found !== undefined ? ` (${data.current_run.jobs_found} found so far)` : "";
                    let progressText = data.current_run?.progress_message ? ` ${data.current_run.progress_message}` : "";
                    statusMsg.innerText = `Background task active${foundText}.${progressText} Polling for completion...`;
                    
                    // Keep polling
                    if (!pollingInterval) {
                        pollingInterval = setInterval(pollScraperStatus, 3000);
                    }
                } else {
                    // Scraper is IDLE
                    engineStateText.innerHTML = '<span class="status-indicator idle" style="background-color: var(--text-secondary);"></span> Idle';
                    
                    // Enable button
                    if (triggerBtn) {
                        triggerBtn.disabled = false;
                        triggerText.innerText = "Trigger Scraper Now";
                        triggerIcon.className = "";
                        triggerIcon.setAttribute("data-lucide", "play");
                        if (window.lucide) window.lucide.createIcons();
                    }

                    // Update success counters from last run info
                    if (data.last_success) {
                        const date = new Date(data.last_success.started_at);
                        lastSuccessTime.innerText = date.toLocaleDateString('en-US', {
                            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                        });
                        lastSuccessJobs.innerText = `${data.last_success.jobs_new} new / ${data.last_success.jobs_found} total`;
                    }

                    // Clear polling if running
                    if (pollingInterval) {
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                        statusMsg.innerText = "Scrape task finished! Log table refreshed.";
                        // Refresh log table
                        refreshLogsTable();
                    }
                }
            })
            .catch(err => console.error("Error polling scraper status:", err));
    }

    // Initialize polling check on page load
    pollScraperStatus();

    // 2. Trigger scraper manually
    if (triggerBtn) {
        triggerBtn.addEventListener("click", function() {
            triggerBtn.disabled = true;
            triggerText.innerText = "Triggering task...";
            statusMsg.innerText = "Connecting to Celery task queue...";

            fetch("/api/scraper/trigger/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken
                }
            })
            .then(res => {
                if (res.status === 409) {
                    throw new Error("A scrape task is already running.");
                }
                if (!res.ok) {
                    throw new Error("Failed to trigger scraper task.");
                }
                return res.json();
            })
            .then(data => {
                statusMsg.innerText = "Scraper triggered! Polling engine status...";
                // Start polling immediately
                pollScraperStatus();
            })
            .catch(err => {
                triggerBtn.disabled = false;
                triggerText.innerText = "Trigger Scraper Now";
                statusMsg.innerText = err.message;
                alert(err.message);
            });
        });
    }

    // 3. Refresh log table dynamically
    function refreshLogsTable() {
        if (!logsTableBody) return;

        fetch("/api/scraper/logs/")
            .then(res => res.json())
            .then(data => {
                if (data.length === 0) {
                    logsTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--text-muted);">No execution logs available.</td></tr>';
                    return;
                }

                logsTableBody.innerHTML = data.map(log => {
                    const date = new Date(log.started_at);
                    const formattedDate = date.toLocaleDateString('en-US', {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
                    });
                    const durationStr = log.duration ? `${log.duration}s` : '—';
                    const errorMsg = log.error_message ? log.error_message : 'Success';
                    const badgeClass = log.status === 'success' ? 'new' : (log.status === 'running' ? 'applied' : 'ignored');
                    const errorColorStyle = log.status === 'failed' ? 'color: var(--color-ignored);' : 'color: var(--text-secondary);';

                    return `
                        <tr style="border-bottom: 1px solid var(--border-color);">
                            <td style="padding: 12px 8px; font-weight: 500;">${formattedDate}</td>
                            <td style="padding: 12px 8px; text-transform: capitalize;">${log.triggered_by}</td>
                            <td style="padding: 12px 8px;">
                                <span class="badge badge-${badgeClass}">
                                    ${log.status.toUpperCase()}
                                </span>
                            </td>
                            <td style="padding: 12px 8px;">${log.jobs_found} / ${log.jobs_new}</td>
                            <td style="padding: 12px 8px;">${durationStr}</td>
                            <td style="padding: 12px 8px; ${errorColorStyle} max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${errorMsg}">
                                ${errorMsg}
                            </td>
                        </tr>
                    `;
                }).join("");
            })
            .catch(err => console.error("Error refreshing logs table:", err));
    }

    // 4. Save preferences form
    if (prefsForm) {
        prefsForm.addEventListener("submit", function(e) {
            e.preventDefault();

            // Convert comma-separated string inputs to arrays
            const keywordsInput = document.querySelector("#pref-keywords").value;
            const locationsInput = document.querySelector("#pref-locations").value;

            const keywords = keywordsInput.split(",").map(k => k.trim()).filter(k => k.length > 0);
            const locations = locationsInput.split(",").map(l => l.trim()).filter(l => l.length > 0);

            // Get selected checkboxes
            const workTypes = [];
            document.querySelectorAll("input[name='work_types']:checked").forEach(cb => {
                workTypes.push(cb.value);
            });

            const experienceLevel = [];
            document.querySelectorAll("input[name='experience_level']:checked").forEach(cb => {
                experienceLevel.push(cb.value);
            });

            const submitBtn = prefsForm.querySelector("button[type='submit']");
            const originalBtnHtml = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="spin" data-lucide="loader-2"></i> Saving...';
            if (window.lucide) window.lucide.createIcons();

            fetch("/api/scraper/preferences/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken
                },
                body: JSON.stringify({
                    keywords: keywords,
                    locations: locations,
                    work_types: workTypes,
                    experience_level: experienceLevel
                })
            })
            .then(res => {
                if (!res.ok) {
                    throw new Error("Failed to save preferences");
                }
                return res.json();
            })
            .then(data => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnHtml;
                if (window.lucide) window.lucide.createIcons();
                alert("Preferences saved successfully!");
            })
            .catch(err => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnHtml;
                if (window.lucide) window.lucide.createIcons();
                console.error(err);
                alert("Error saving preferences. Please check inputs.");
            });
        });
    }
});
