/**
 * CareerBridge — Job interactions (Asynchronous status updates)
 */

document.addEventListener("DOMContentLoaded", function() {
    // CSRF Token fetcher helper
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

    // Attach click listeners to status update buttons
    document.querySelectorAll(".status-update-btn").forEach(btn => {
        btn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();

            const jobId = this.getAttribute("data-job-id");
            const targetStatus = this.getAttribute("data-status");
            const btnGroup = this.parentElement;
            
            // Check if this button is already active (we are clicking to toggle off/reset to new)
            const isAlreadyActive = this.classList.contains("active");
            const statusToSubmit = isAlreadyActive ? "new" : targetStatus;

            // Visual feedback - disable button group temporarily
            btnGroup.style.opacity = "0.5";
            btnGroup.style.pointerEvents = "none";

            fetch(`/api/jobs/${jobId}/status/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ status: statusToSubmit })
            })
            .then(res => {
                if (!res.ok) {
                    throw new Error("Failed to update status");
                }
                return res.json();
            })
            .then(data => {
                // Restore button group opacity
                btnGroup.style.opacity = "1";
                btnGroup.style.pointerEvents = "auto";

                // Update active state of buttons in this group
                btnGroup.querySelectorAll(".status-update-btn").forEach(b => {
                    const statusVal = b.getAttribute("data-status");
                    if (statusVal === data.status) {
                        b.classList.add("active");
                        // Set style properties based on active class
                        setButtonStyle(b, statusVal, true);
                    } else {
                        b.classList.remove("active");
                        setButtonStyle(b, statusVal, false);
                    }
                });

                // Update status badge on job card if present
                const statusBadge = document.querySelector(`#status-badge-${jobId}`);
                if (statusBadge) {
                    statusBadge.innerText = data.status.toUpperCase();
                    // Reset status class
                    statusBadge.className = "badge badge-status";
                    statusBadge.classList.add(`badge-${data.status}`);
                }

                // If we are on the Job List page, update the sidebar badge counts
                updateSidebarCounts(targetStatus, isAlreadyActive);
            })
            .catch(err => {
                btnGroup.style.opacity = "1";
                btnGroup.style.pointerEvents = "auto";
                console.error(err);
                alert("Error updating status. Please try again.");
            });
        });
    });

    // Helper to style active/inactive buttons programmatically
    function setButtonStyle(button, statusType, isActive) {
        if (isActive) {
            if (statusType === 'saved') {
                button.style.borderColor = 'var(--color-saved)';
                button.style.color = 'var(--color-saved)';
                button.style.background = 'var(--bg-saved-light)';
            } else if (statusType === 'applied') {
                button.style.borderColor = 'var(--color-applied)';
                button.style.color = 'var(--color-applied)';
                button.style.background = 'var(--bg-applied-light)';
            } else if (statusType === 'ignored') {
                button.style.borderColor = 'var(--color-ignored)';
                button.style.color = 'var(--color-ignored)';
                button.style.background = 'var(--bg-ignored-light)';
            }
        } else {
            button.style.borderColor = '';
            button.style.color = '';
            button.style.background = '';
        }
    }

    // Helper to adjust the numbers in the sidebar filters dynamically
    function updateSidebarCounts(clickedStatus, toggledOff) {
        const savedBadge = document.querySelector("#saved-count-badge");
        const appliedBadge = document.querySelector("#applied-count-badge");
        const ignoredBadge = document.querySelector("#ignored-count-badge");
        
        if (!savedBadge || !appliedBadge || !ignoredBadge) return;

        // Since we are moving a job from its old status to a new status (or reset to new),
        // we can trigger a soft page refresh or adjust counts directly.
        // Let's reload the page if we want exact counts, or just do a simple reload to update query filtering!
        // Actually, if we are filtering by status (e.g. only viewing "saved" jobs) and we mark as "ignored",
        // the job card should disappear and counts update. A page reload is simpler if we've filtered the view.
        const urlParams = new URLSearchParams(window.location.search);
        const currentStatusFilter = urlParams.get('status');

        if (currentStatusFilter) {
            // If viewing a filtered list, reload so the job card disappears
            window.location.reload();
        } else {
            // Otherwise, we just fetch the summary API to get fresh counts for the sidebar!
            // This is super elegant.
            fetch('/api/analytics/summary/')
                .then(res => res.json())
                .then(data => {
                    // Update stats counters
                    savedBadge.innerText = data.total_jobs_by_status?.saved || 0;
                    appliedBadge.innerText = data.total_jobs_by_status?.applied || 0;
                    ignoredBadge.innerText = data.total_jobs_by_status?.ignored || 0;
                })
                .catch(() => {
                    // Fallback to reload if endpoint fails
                    window.location.reload();
                });
        }
    }
});
