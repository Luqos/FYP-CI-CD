/**
 * Smart Parking AWS Academy Dashboard Client Application
 */

(function () {
  // Read API Base URL from generated config.js
  const config = window.SMART_PARKING_CONFIG || {};
  const API_BASE_URL = config.API_BASE_URL || "";

  // DOM Elements
  const totalSlotsEl = document.getElementById("totalSlots");
  const availableSlotsEl = document.getElementById("availableSlots");
  const occupiedSlotsEl = document.getElementById("occupiedSlots");
  const offlineErrorSlotsEl = document.getElementById("offlineErrorSlots");
  const slotsGridEl = document.getElementById("slotsGrid");
  
  const adminSectionsWrapper = document.getElementById("adminSectionsWrapper");
  const adminToggle = document.getElementById("adminToggle");
  
  const eventsTableBodyEl = document.getElementById("eventsTableBody");
  const lastUpdatedEl = document.getElementById("lastUpdated");
  const refreshBtn = document.getElementById("refreshBtn");
  const triggerReportBtn = document.getElementById("triggerReportBtn");
  const ingestTestForm = document.getElementById("ingestTestForm");
  const adminNotification = document.getElementById("adminNotification");

  // Pagination Elements
  const prevPageBtn = document.getElementById("prevPageBtn");
  const nextPageBtn = document.getElementById("nextPageBtn");
  const pageIndicator = document.getElementById("pageIndicator");

  // Maintenance Override Buttons
  const setMaintA01Btn = document.getElementById("setMaintA01");
  const clearMaintA01Btn = document.getElementById("clearMaintA01");
  const setMaintA02Btn = document.getElementById("setMaintA02");
  const clearMaintA02Btn = document.getElementById("clearMaintA02");

  // Global State
  let isAdmin = false;
  let allEvents = [];
  let currentPage = 1;
  const eventsPerPage = 10;
  let chartInstance = null;

  // Initialize
  document.addEventListener("DOMContentLoaded", () => {
    if (!API_BASE_URL) {
      showNotification("Warning: API_BASE_URL is missing in config.js. Run deploy script first.", true);
    }
    
    // Set up Admin Toggle listener
    adminToggle.addEventListener("change", (e) => {
      isAdmin = e.target.checked;
      if (isAdmin) {
        adminSectionsWrapper.classList.remove("hidden");
        // Re-render components that might need updating upon revealing
        renderEventsPagination();
        renderAnalyticsChart();
      } else {
        adminSectionsWrapper.classList.add("hidden");
      }
    });

    fetchDashboardData();
    // Auto-refresh every 10 seconds
    setInterval(fetchDashboardData, 10000);

    refreshBtn.addEventListener("click", fetchDashboardData);
    triggerReportBtn.addEventListener("click", generateDailyReport);
    ingestTestForm.addEventListener("submit", handleIngestTestSubmit);

    // Pagination Listeners
    prevPageBtn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        renderEventsPagination();
      }
    });

    nextPageBtn.addEventListener("click", () => {
      const maxPage = Math.ceil(allEvents.length / eventsPerPage) || 1;
      if (currentPage < maxPage) {
        currentPage++;
        renderEventsPagination();
      }
    });

    setMaintA01Btn.addEventListener("click", () => setMaintenance("A01", true));
    clearMaintA01Btn.addEventListener("click", () => setMaintenance("A01", false));
    setMaintA02Btn.addEventListener("click", () => setMaintenance("A02", true));
    clearMaintA02Btn.addEventListener("click", () => setMaintenance("A02", false));
  });

  async function fetchDashboardData() {
    if (!API_BASE_URL) return;

    try {
      refreshBtn.textContent = "Loading...";
      const [slotsRes, eventsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/slots`),
        fetch(`${API_BASE_URL}/events?limit=100`) // Fetch up to 100 for analytics/pagination
      ]);

      if (slotsRes.ok) {
        const slotsData = await slotsRes.json();
        renderSlots(slotsData.slots || [], slotsData.summary || {});
      }

      if (eventsRes.ok) {
        const eventsData = await eventsRes.json();
        allEvents = eventsData.events || [];
        
        // Reset to page 1 if we have new data and the user isn't actively paging? 
        // For simplicity, we just leave currentPage as is, but ensure bounds:
        const maxPage = Math.ceil(allEvents.length / eventsPerPage) || 1;
        if (currentPage > maxPage) currentPage = maxPage;

        if (isAdmin) {
          renderEventsPagination();
          renderAnalyticsChart();
        }
      }

      lastUpdatedEl.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      if (isAdmin) showNotification("Network error connecting to API Gateway.", true);
    } finally {
      refreshBtn.textContent = "↻ Refresh";
    }
  }

  function renderSlots(slots, summary) {
    totalSlotsEl.textContent = summary.total !== undefined ? summary.total : slots.length;
    availableSlotsEl.textContent = summary.available || 0;
    occupiedSlotsEl.textContent = summary.occupied || 0;
    offlineErrorSlotsEl.textContent = (summary.offline || 0) + (summary.sensorError || 0);

    if (slots.length === 0) {
      slotsGridEl.innerHTML = `
        <div class="card slot-card">
          <p class="text-muted text-center">No parking slots registered in DynamoDB yet.</p>
        </div>
      `;
      return;
    }

    slotsGridEl.innerHTML = slots.map(slot => {
      const statusClass = getStatusBadgeClass(slot.status);
      const isStaleText = slot.isStale ? '<span class="text-amber">(Stale > 60s)</span>' : '';
      const distDisplay = slot.distanceCm !== undefined && slot.distanceCm !== null && slot.distanceCm >= 0
        ? `${slot.distanceCm} cm`
        : 'N/A';
      const confDisplay = slot.confidence !== undefined && slot.confidence !== null
        ? `${Math.round(slot.confidence * 100)}%`
        : 'N/A';
      const lastSeenText = slot.lastSeenIso ? new Date(slot.lastSeenIso).toLocaleTimeString() : 'Never';

      return `
        <div class="card slot-card">
          <div class="slot-header">
            <span class="slot-id">Slot ${escapeHtml(slot.slotId)}</span>
            <span class="badge ${statusClass}">${escapeHtml(slot.status)}</span>
          </div>

          <div class="slot-details">
            <div class="detail-row">
              <span class="detail-label">Distance:</span>
              <span class="detail-value">${distDisplay}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Confidence:</span>
              <span class="detail-value">${confDisplay}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Sensor Health:</span>
              <span class="detail-value">${escapeHtml(slot.sensorHealth || 'ONLINE')} ${isStaleText}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Last Telemetry:</span>
              <span class="detail-value">${lastSeenText}</span>
            </div>
          </div>
        </div>
      `;
    }).join("");
  }

  function renderEventsPagination() {
    const totalEvents = allEvents.length;
    const maxPage = Math.ceil(totalEvents / eventsPerPage) || 1;
    
    // Safety check
    if (currentPage > maxPage) currentPage = maxPage;
    if (currentPage < 1) currentPage = 1;

    // Update Pagination UI
    pageIndicator.textContent = `Page ${currentPage} of ${maxPage}`;
    prevPageBtn.disabled = currentPage === 1;
    nextPageBtn.disabled = currentPage === maxPage;

    // Slice the array for the current page
    const startIndex = (currentPage - 1) * eventsPerPage;
    const endIndex = startIndex + eventsPerPage;
    const paginatedEvents = allEvents.slice(startIndex, endIndex);

    renderEventsTable(paginatedEvents);
  }

  function renderEventsTable(events) {
    if (events.length === 0) {
      eventsTableBodyEl.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-muted">No recent events logged.</td>
        </tr>
      `;
      return;
    }

    eventsTableBodyEl.innerHTML = events.map(ev => {
      const formattedTime = ev.eventTime ? new Date(ev.eventTime).toLocaleTimeString() : '--';
      const dist = ev.distanceCm !== undefined && ev.distanceCm !== null && ev.distanceCm >= 0 ? `${ev.distanceCm} cm` : '-';
      const billing = ev.billingAmountRM !== undefined && ev.billingAmountRM !== null ? `RM ${ev.billingAmountRM.toFixed(2)}` : '-';
      const transition = ev.previousStatus ? `${ev.previousStatus} → ${ev.newStatus}` : ev.newStatus;

      return `
        <tr>
          <td>${formattedTime}</td>
          <td><strong>${escapeHtml(ev.slotId || '')}</strong></td>
          <td><span class="badge badge-outline">${escapeHtml(ev.eventType || 'STATUS')}</span></td>
          <td>${escapeHtml(transition)}</td>
          <td>${dist}</td>
          <td><strong>${billing}</strong></td>
        </tr>
      `;
    }).join("");
  }

  function renderAnalyticsChart() {
    const ctx = document.getElementById('utilizationChart');
    if (!ctx) return;

    // Aggregate Data: Count parking events (OCCUPIED transitions) per slot
    const slotCounts = {};
    let totalRevenue = 0;

    allEvents.forEach(ev => {
      if (!slotCounts[ev.slotId]) {
        slotCounts[ev.slotId] = 0;
      }
      
      // Count if it's a parking event or transition to OCCUPIED
      if (ev.newStatus === "OCCUPIED" || ev.eventType === "PARKING") {
        slotCounts[ev.slotId]++;
      }
      
      // Accumulate billing
      if (ev.billingAmountRM) {
        totalRevenue += ev.billingAmountRM;
      }
    });

    const labels = Object.keys(slotCounts).length > 0 ? Object.keys(slotCounts) : ["A01", "A02"];
    const dataPoints = Object.keys(slotCounts).length > 0 ? Object.values(slotCounts) : [0, 0];

    // Destroy existing chart to prevent canvas overlay glitche
    if (chartInstance) {
      chartInstance.destroy();
    }

    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";

    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Total Parking Sessions (Occupied)',
          data: dataPoints,
          backgroundColor: 'rgba(59, 130, 246, 0.7)',
          borderColor: '#3b82f6',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true },
          title: {
            display: true,
            text: `Est. Revenue in Period: RM ${totalRevenue.toFixed(2)}`,
            color: '#10b981',
            font: { size: 14 }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1 },
            grid: { color: 'rgba(51, 65, 85, 0.5)' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  async function handleIngestTestSubmit(e) {
    e.preventDefault();
    const slotId = document.getElementById("testSlotId").value;
    const distanceCm = parseFloat(document.getElementById("testDistance").value);

    try {
      showNotification(`Sending reading for ${slotId}...`);
      const res = await fetch(`${API_BASE_URL}/ingest-test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slotId, distanceCm, deviceId: "dashboard-test" })
      });

      if (res.ok) {
        const data = await res.json();
        showNotification(`Success: Ingested telemetry for ${slotId} (Status: ${data.status})`);
        fetchDashboardData();
      } else {
        const errData = await res.json();
        showNotification(`Ingest error: ${errData.error || 'Failed'}`, true);
      }
    } catch (err) {
      showNotification(`Ingest error: ${err.message}`, true);
    }
  }

  async function setMaintenance(slotId, enable) {
    const action = enable ? "maintenance" : "available";
    try {
      showNotification(`Updating slot ${slotId} mode to ${action}...`);
      const res = await fetch(`${API_BASE_URL}/admin/slot/${slotId}/${action}`, {
        method: "POST"
      });
      if (res.ok) {
        showNotification(`Updated slot ${slotId} to ${enable ? 'MAINTENANCE' : 'AVAILABLE'}`);
        fetchDashboardData();
      } else {
        showNotification(`Admin override failed`, true);
      }
    } catch (err) {
      showNotification(`Error: ${err.message}`, true);
    }
  }

  async function generateDailyReport() {
    try {
      showNotification("Triggering daily report generation...");
      const res = await fetch(`${API_BASE_URL}/reports/daily`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      if (res.ok) {
        const data = await res.json();
        showNotification(`Report generated: ${data.recordCount} events → s3://${data.bucket}/${data.key}`);
      } else {
        const errData = await res.json();
        showNotification(`Report error: ${errData.error || 'Failed'}`, true);
      }
    } catch (err) {
      showNotification(`Report error: ${err.message}`, true);
    }
  }

  function getStatusBadgeClass(status) {
    switch (status) {
      case "AVAILABLE": return "badge-available";
      case "OCCUPIED": return "badge-occupied";
      case "SENSOR_ERROR": return "badge-sensor_error";
      case "OFFLINE": return "badge-offline";
      case "MAINTENANCE": return "badge-maintenance";
      default: return "badge-outline";
    }
  }

  function showNotification(msg, isError = false) {
    adminNotification.textContent = msg;
    adminNotification.className = `notification ${isError ? 'text-red' : ''}`;
    adminNotification.classList.remove("hidden");
    setTimeout(() => adminNotification.classList.add("hidden"), 6000);
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
