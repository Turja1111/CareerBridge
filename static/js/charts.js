/**
 * CareerBridge - Market Intelligence Analytics Chart Rendering
 * Powered by ApexCharts and Django DRF APIs
 */

document.addEventListener("DOMContentLoaded", function() {
    // Shared Chart Options Helpers
    const themeMode = 'dark';
    const textColor = '#9ca3af';
    const gridColor = 'rgba(255, 255, 255, 0.05)';
    const chartFont = 'Plus Jakarta Sans, sans-serif';

    // 1. Top Skills Chart
    const skillsEl = document.querySelector("#topSkillsChart");
    if (skillsEl) {
        fetch("/api/analytics/top-skills/?limit=10")
            .then(res => res.json())
            .then(data => {
                if (data.length === 0) {
                    skillsEl.innerHTML = '<div class="no-data">No data available</div>';
                    return;
                }
                const options = {
                    chart: { type: 'bar', height: 320, foreColor: textColor, background: 'transparent', toolbar: { show: false } },
                    series: [{ name: 'Job Openings', data: data.map(d => d.job_count) }],
                    plotOptions: { bar: { horizontal: true, borderRadius: 6, barHeight: '65%', distributed: true } },
                    colors: ['#6366f1', '#8b5cf6', '#a78bfa', '#c084fc', '#d8b4fe', '#f472b6', '#fb7185', '#fda4af', '#f43f5e', '#ec4899'],
                    xaxis: { categories: data.map(d => d.name), labels: { style: { fontFamily: chartFont } } },
                    grid: { borderColor: gridColor },
                    legend: { show: false },
                    theme: { mode: themeMode },
                    tooltip: { theme: 'dark' }
                };
                new ApexCharts(skillsEl, options).render();
            });
    }

    // 2. Jobs Over Time Chart
    const jobsTimeEl = document.querySelector("#jobsOverTimeChart");
    if (jobsTimeEl) {
        fetch("/api/analytics/jobs-over-time/?days=30")
            .then(res => res.json())
            .then(data => {
                if (data.length === 0) {
                    jobsTimeEl.innerHTML = '<div class="no-data">No data available</div>';
                    return;
                }
                // Format dates to human readable
                const categories = data.map(d => {
                    const date = new Date(d.date);
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                });
                const options = {
                    chart: { type: 'area', height: 320, foreColor: textColor, background: 'transparent', toolbar: { show: false } },
                    series: [{ name: 'Jobs Scraped', data: data.map(d => d.count) }],
                    stroke: { curve: 'smooth', width: 3 },
                    colors: ['#10b981'],
                    fill: {
                        type: 'gradient',
                        gradient: { shadeIntensity: 1, opacityFrom: 0.45, opacityTo: 0.05, stops: [0, 90, 100] }
                    },
                    xaxis: { categories: categories, labels: { style: { fontFamily: chartFont } } },
                    grid: { borderColor: gridColor },
                    theme: { mode: themeMode },
                    tooltip: { theme: 'dark', x: { show: true } }
                };
                new ApexCharts(jobsTimeEl, options).render();
            });
    }

    // 3. Work Type Distribution Chart
    const workTypeEl = document.querySelector("#workTypeDistributionChart");
    if (workTypeEl) {
        fetch("/api/analytics/work-type-distribution/")
            .then(res => res.json())
            .then(data => {
                if (data.length === 0) {
                    workTypeEl.innerHTML = '<div class="no-data">No data available</div>';
                    return;
                }
                const options = {
                    chart: { type: 'donut', height: 320, foreColor: textColor, background: 'transparent' },
                    series: data.map(d => d.count),
                    labels: data.map(d => d.work_type),
                    colors: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'],
                    stroke: { show: true, colors: ['#111827'], width: 2 },
                    legend: { position: 'bottom', labels: { colors: '#f3f4f6' }, fontFamily: chartFont },
                    dataLabels: { enabled: false },
                    theme: { mode: themeMode }
                };
                new ApexCharts(workTypeEl, options).render();
            });
    }

    // 4. Salary Ranges Chart (Floating Bar/Range Bar Chart)
    const salaryEl = document.querySelector("#salaryRangesChart");
    if (salaryEl) {
        fetch("/api/analytics/salary-ranges/?limit=8")
            .then(res => res.json())
            .then(data => {
                if (data.length === 0) {
                    salaryEl.innerHTML = '<div class="no-data">No salary data found. Ensure salary fields are seeded.</div>';
                    return;
                }
                // Construct range bar series data
                const chartData = data.map(d => {
                    return {
                        x: d.title,
                        y: [Math.round(d.avg_min), Math.round(d.avg_max)]
                    };
                });
                const options = {
                    chart: { type: 'bar', height: 320, foreColor: textColor, background: 'transparent', toolbar: { show: false } },
                    plotOptions: { bar: { horizontal: true, barHeight: '50%', borderRadius: 4 } },
                    series: [{ data: chartData }],
                    colors: ['#f59e0b'],
                    xaxis: { labels: { formatter: val => `$${val.toLocaleString()}` } },
                    grid: { borderColor: gridColor },
                    theme: { mode: themeMode },
                    tooltip: {
                        theme: 'dark',
                        custom: function({ series, seriesIndex, dataPointIndex, w }) {
                            const item = data[dataPointIndex];
                            return `<div style="padding: 12px; background: #1f2937; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;">
                                <strong style="display:block; margin-bottom: 4px;">${item.title}</strong>
                                <span>Avg Min: $${Math.round(item.avg_min).toLocaleString()}</span><br/>
                                <span>Avg Max: $${Math.round(item.avg_max).toLocaleString()}</span><br/>
                                <span>Record Count: ${item.count} postings</span>
                            </div>`;
                        }
                    }
                };
                new ApexCharts(salaryEl, options).render();
            });
    }

    // 5. Top Companies Chart
    const companiesEl = document.querySelector("#topCompaniesChart");
    if (companiesEl) {
        fetch("/api/analytics/top-companies/?limit=8")
            .then(res => res.json())
            .then(data => {
                if (data.length === 0) {
                    companiesEl.innerHTML = '<div class="no-data">No data available</div>';
                    return;
                }
                const options = {
                    chart: { type: 'bar', height: 320, foreColor: textColor, background: 'transparent', toolbar: { show: false } },
                    series: [{ name: 'Jobs Posted', data: data.map(d => d.job_count) }],
                    plotOptions: { bar: { horizontal: true, borderRadius: 5, barHeight: '60%' } },
                    colors: ['#3b82f6'],
                    xaxis: { categories: data.map(d => d.name) },
                    grid: { borderColor: gridColor },
                    theme: { mode: themeMode }
                };
                new ApexCharts(companiesEl, options).render();
            });
    }

    // 6. Top Locations Chart
    const locationsEl = document.querySelector("#topLocationsChart");
    if (locationsEl) {
        fetch("/api/analytics/top-locations/?limit=8")
            .then(res => res.json())
            .then(data => {
                if (data.length === 0) {
                    locationsEl.innerHTML = '<div class="no-data">No data available</div>';
                    return;
                }
                const options = {
                    chart: { type: 'bar', height: 320, foreColor: textColor, background: 'transparent', toolbar: { show: false } },
                    series: [{ name: 'Job Openings', data: data.map(d => d.count) }],
                    plotOptions: { bar: { horizontal: false, columnWidth: '50%', borderRadius: 6 } },
                    colors: ['#a855f7'],
                    xaxis: { categories: data.map(d => d.location.split(',')[0]) },
                    grid: { borderColor: gridColor },
                    theme: { mode: themeMode }
                };
                new ApexCharts(locationsEl, options).render();
            });
    }

    // 7. Skills by Experience Level Chart
    const skillsExpEl = document.querySelector("#skillsByExperienceChart");
    if (skillsExpEl) {
        fetch("/api/analytics/skills-by-experience/")
            .then(res => res.json())
            .then(data => {
                // Group skills across categories to construct multibar series.
                // We'll extract a unique set of skills that appear in top lists.
                const allSkillNames = new Set();
                ['Entry', 'Mid', 'Senior'].forEach(lvl => {
                    if (data[lvl]) {
                        data[lvl].forEach(s => allSkillNames.add(s.name));
                    }
                });
                
                // Let's filter to top 8 overall skills to keep chart readable
                const topSkillsList = Array.from(allSkillNames).slice(0, 10);
                
                if (topSkillsList.length === 0) {
                    skillsExpEl.innerHTML = '<div class="no-data">No data available</div>';
                    return;
                }

                const series = ['Entry', 'Mid', 'Senior'].map(lvl => {
                    const counts = topSkillsList.map(skillName => {
                        const match = data[lvl] ? data[lvl].find(s => s.name === skillName) : null;
                        return match ? match.job_count : 0;
                    });
                    return { name: `${lvl} Level`, data: counts };
                });

                const options = {
                    chart: { type: 'bar', height: 340, foreColor: textColor, background: 'transparent', toolbar: { show: false } },
                    series: series,
                    plotOptions: { bar: { horizontal: false, columnWidth: '55%', borderRadius: 4 } },
                    stroke: { show: true, width: 2, colors: ['transparent'] },
                    xaxis: { categories: topSkillsList },
                    colors: ['#10b981', '#3b82f6', '#f59e0b'],
                    grid: { borderColor: gridColor },
                    theme: { mode: themeMode },
                    legend: { labels: { colors: '#f3f4f6' } }
                };
                new ApexCharts(skillsExpEl, options).render();
            });
    }
});
