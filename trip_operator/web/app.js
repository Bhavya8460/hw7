const jsonBox = document.getElementById("jsonBox");
const traceBox = document.getElementById("traceBox");
const tripList = document.getElementById("tripList");
const tripCount = document.getElementById("tripCount");
const statusBadge = document.getElementById("statusBadge");
const statusTripId = document.getElementById("statusTripId");
const expenseTripId = document.getElementById("expenseTripId");
const downloadExcelButton = document.getElementById("downloadExcel");
const summaryHeadline = document.getElementById("summaryHeadline");
const summaryLead = document.getElementById("summaryLead");
const summaryTags = document.getElementById("summaryTags");
const metricGrid = document.getElementById("metricGrid");
const overviewBox = document.getElementById("overviewBox");
const travelBox = document.getElementById("travelBox");
const budgetBox = document.getElementById("budgetBox");
const calendarBox = document.getElementById("calendarBox");
const expenseTable = document.getElementById("expenseTable");
const reminderTable = document.getElementById("reminderTable");
const expenseCount = document.getElementById("expenseCount");
const reminderCount = document.getElementById("reminderCount");

let currentTripId = "";

function setStatus(label, type = "") {
  statusBadge.textContent = label;
  statusBadge.className = "status-badge";
  if (type) {
    statusBadge.classList.add(type);
  }
}

function setExportTripId(tripId) {
  currentTripId = tripId || "";
  downloadExcelButton.disabled = !currentTripId;
}

function pluralize(count, singular, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function toPrettyJson(value) {
  return JSON.stringify(value, null, 2);
}

function setRawJson(value) {
  jsonBox.textContent = toPrettyJson(value);
}

function formatCurrency(value, currencyCode = "USD") {
  if (value === null || value === undefined || value === "" || Number.isNaN(Number(value))) {
    return "n/a";
  }
  const amount = Number(value).toFixed(2);
  return currencyCode && currencyCode !== "USD" ? `${amount} ${currencyCode}` : `$${amount}`;
}

function formatValue(value, fallback = "n/a") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

function renderTrace(trace) {
  if (!trace || !trace.length) {
    traceBox.innerHTML = "<p class='caption'>No MCP calls yet.</p>";
    return;
  }
  traceBox.innerHTML = trace.map((entry, index) => {
    const payload = typeof entry.payload === "string" ? entry.payload : toPrettyJson(entry.payload || {});
    const phase = entry.phase ? `<span class="trace-phase">${escapeHtml(entry.phase)}</span>` : "";
    return `
      <article class="trace-entry">
        <header>
          <div class="trace-meta">
            <span class="direction">${index + 1}. ${escapeHtml(entry.direction || "event")}</span>
            ${phase}
          </div>
          <span>${escapeHtml(entry.server || "app")} · ${escapeHtml(entry.tool || "n/a")}</span>
        </header>
        <pre>${escapeHtml(payload)}</pre>
      </article>
    `;
  }).join("");
}

function renderTagRow(tags) {
  const validTags = tags.filter(Boolean);
  if (!validTags.length) {
    return "<span class='tag'>No active trip</span>";
  }
  return validTags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
}

function renderFacts(items) {
  const rows = items.filter(([, value]) => value !== null && value !== undefined && value !== "");
  if (!rows.length) {
    return "<p class='caption'>No details available.</p>";
  }
  return `
    <div class="fact-list">
      ${rows.map(([label, value]) => `
        <div class="fact-row">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function renderTipCloud(tips) {
  if (!tips || !tips.length) {
    return "<p class='caption'>No tips generated yet.</p>";
  }
  return `<div class="tip-cloud">${tips.map((tip) => `<span class="tip-pill">${escapeHtml(tip)}</span>`).join("")}</div>`;
}

function renderBars(items, currencyCode = "USD") {
  const normalized = items.filter((item) => Number(item.value) > 0);
  if (!normalized.length) {
    return "<p class='caption'>No spend categories yet.</p>";
  }
  const maxValue = Math.max(...normalized.map((item) => Number(item.value)));
  return `
    <div class="bar-list">
      ${normalized.map((item) => {
        const width = Math.max(12, Math.round((Number(item.value) / maxValue) * 100));
        return `
          <div class="bar-item">
            <div class="bar-row">
              <span>${escapeHtml(item.label)}</span>
              <strong>${escapeHtml(formatCurrency(item.value, currencyCode))}</strong>
            </div>
            <div class="bar-track">
              <span style="width: ${width}%"></span>
            </div>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function renderTable(headers, rows, emptyMessage) {
  if (!rows.length) {
    return `<p class="caption">${escapeHtml(emptyMessage)}</p>`;
  }
  return `
    <table class="data-table">
      <thead>
        <tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${rows.map((row) => `
          <tr>${row.map((value) => `<td>${escapeHtml(value)}</td>`).join("")}</tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function clearDashboard(message = "Create a trip or load a saved one to see each MCP server rendered separately.") {
  summaryHeadline.textContent = "No request yet.";
  summaryLead.textContent = message;
  summaryTags.innerHTML = renderTagRow([]);
  metricGrid.innerHTML = `
    <article class="metric-card">
      <span class="metric-label">Budget</span>
      <strong class="metric-value">$0.00</strong>
      <span class="metric-meta">Waiting for a request</span>
    </article>
  `;
  overviewBox.innerHTML = "Trip details will appear here.";
  overviewBox.className = "detail-stack empty-state";
  travelBox.innerHTML = "Destination, weather, transport, and travel estimates will appear here.";
  travelBox.className = "detail-stack empty-state";
  budgetBox.innerHTML = "Budget status, spend pacing, and expense categories will appear here.";
  budgetBox.className = "detail-stack empty-state";
  calendarBox.innerHTML = "Reminder counts, schedule highlights, and export path will appear here.";
  calendarBox.className = "detail-stack empty-state";
  expenseTable.innerHTML = "No expenses yet.";
  expenseTable.className = "table-wrap empty-state";
  reminderTable.innerHTML = "No reminders yet.";
  reminderTable.className = "table-wrap empty-state";
  expenseCount.textContent = "0";
  reminderCount.textContent = "0";
  setExportTripId("");
}

function getBudgetSegments(model) {
  if (model.categoryBreakdown.length) {
    return model.categoryBreakdown.map((item) => ({ label: item.category, value: item.total_usd }));
  }
  return [
    { label: "transport", value: model.transportUsd },
    { label: "lodging", value: model.lodgingUsd },
    { label: "food", value: model.foodUsd },
    { label: "local transit", value: model.localTransportUsd },
    { label: "activities", value: model.activitiesUsd }
  ];
}

function buildPlanModel(payload) {
  const { snapshot, trip, calendar } = payload.result;
  return {
    kind: "plan",
    tripId: trip.trip_id,
    destination: snapshot.destination.resolved_name,
    destinationRequested: snapshot.destination.requested,
    homeCity: snapshot.home_city?.display_name || trip.home_city,
    startDate: trip.start_date,
    endDate: trip.end_date,
    days: snapshot.dates.days,
    nights: snapshot.dates.nights,
    travelers: snapshot.budget.travelers,
    budgetUsd: trip.budget_usd,
    estimatedTotalUsd: snapshot.estimated_costs.total_usd,
    spentTotalUsd: 0,
    remainingBudgetUsd: trip.budget_usd,
    budgetGapUsd: snapshot.assessment.budget_gap_usd,
    paceDeltaUsd: null,
    weatherSummary: snapshot.weather.summary,
    weatherHigh: snapshot.weather.average_high_c,
    weatherLow: snapshot.weather.average_low_c,
    weatherRainRisk: snapshot.weather.rain_risk_days,
    transportMode: snapshot.estimated_costs.transport_details.mode,
    transportUsd: snapshot.estimated_costs.transport_usd,
    lodgingUsd: snapshot.estimated_costs.lodging_usd,
    foodUsd: snapshot.estimated_costs.food_usd,
    localTransportUsd: snapshot.estimated_costs.local_transport_usd,
    activitiesUsd: snapshot.estimated_costs.activities_usd,
    localTotal: snapshot.estimated_costs.total_in_destination_currency,
    localCurrencyCode: snapshot.estimated_costs.destination_currency_code,
    costTier: snapshot.cost_profile.tier,
    notes: trip.notes || "",
    tips: snapshot.tips || [],
    sources: snapshot.service_sources || {},
    calendarPath: calendar.calendar_path,
    reminders: calendar.events || [],
    dailyPlan: calendar.daily_plan || [],
    categoryBreakdown: [],
    expenses: [],
    onTrack: snapshot.assessment.within_budget,
    expenseCount: 0
  };
}

function buildStatusModel(payload) {
  const { status, weather, reminders } = payload.result;
  const snapshot = status.trip.metadata || {};
  const tripWeather = weather.weather || {};
  return {
    kind: "status",
    tripId: status.trip.trip_id,
    destination: snapshot.destination?.resolved_name || weather.destination || status.trip.destination,
    destinationRequested: snapshot.destination?.requested || status.trip.destination,
    homeCity: snapshot.home_city?.display_name || status.trip.home_city,
    startDate: status.trip.start_date,
    endDate: status.trip.end_date,
    days: snapshot.dates?.days,
    nights: snapshot.dates?.nights,
    travelers: snapshot.budget?.travelers || status.trip.travelers,
    budgetUsd: status.trip.budget_usd,
    estimatedTotalUsd: status.trip.estimated_total_usd,
    spentTotalUsd: status.spent_total_usd,
    remainingBudgetUsd: status.remaining_budget_usd,
    budgetGapUsd: status.budget_vs_estimate_usd,
    paceDeltaUsd: status.pace_delta_usd,
    weatherSummary: tripWeather.summary || snapshot.weather?.summary || "Weather unavailable.",
    weatherHigh: tripWeather.average_high_c ?? snapshot.weather?.average_high_c,
    weatherLow: tripWeather.average_low_c ?? snapshot.weather?.average_low_c,
    weatherRainRisk: tripWeather.rain_risk_days ?? snapshot.weather?.rain_risk_days,
    transportMode: snapshot.estimated_costs?.transport_details?.mode,
    transportUsd: snapshot.estimated_costs?.transport_usd,
    lodgingUsd: snapshot.estimated_costs?.lodging_usd,
    foodUsd: snapshot.estimated_costs?.food_usd,
    localTransportUsd: snapshot.estimated_costs?.local_transport_usd,
    activitiesUsd: snapshot.estimated_costs?.activities_usd,
    localTotal: snapshot.estimated_costs?.total_in_destination_currency,
    localCurrencyCode: snapshot.estimated_costs?.destination_currency_code || snapshot.cost_profile?.currency_code,
    costTier: snapshot.cost_profile?.tier,
    notes: status.trip.notes || "",
    tips: snapshot.tips || [],
    sources: snapshot.service_sources || {},
    calendarPath: status.trip.calendar_path,
    reminders: reminders.events || [],
    dailyPlan: reminders.daily_plan || [],
    categoryBreakdown: status.category_breakdown || [],
    expenses: status.expenses || [],
    onTrack: status.on_track,
    expenseCount: status.expense_count || 0
  };
}

function buildHeadline(model) {
  if (model.kind === "plan") {
    const amount = formatCurrency(Math.abs(model.budgetGapUsd));
    return model.budgetGapUsd >= 0
      ? `${model.destination} is projected ${amount} under budget.`
      : `${model.destination} is projected ${amount} over budget.`;
  }
  const amount = formatCurrency(Math.abs(model.remainingBudgetUsd));
  return model.remainingBudgetUsd >= 0
    ? `${model.destination} still has ${amount} remaining.`
    : `${model.destination} is ${amount} over budget.`;
}

function renderDashboard(model) {
  setExportTripId(model.tripId);
  summaryHeadline.textContent = buildHeadline(model);
  summaryLead.textContent = [
    `${model.startDate} to ${model.endDate}`,
    pluralize(model.travelers, "traveler"),
    model.weatherSummary
  ].join(" · ");
  summaryTags.innerHTML = renderTagRow([
    model.tripId,
    model.transportMode,
    model.costTier ? `${model.costTier} cost tier` : "",
    `${pluralize(model.reminders.length, "reminder")}`,
    model.dailyPlan.length ? `${pluralize(model.dailyPlan.length, "planned day")}` : ""
  ]);

  const metrics = [
    {
      label: "Budget",
      value: formatCurrency(model.budgetUsd),
      meta: `${pluralize(model.travelers, "traveler")} · ${model.days || "?"} days`,
      tone: "warm"
    },
    {
      label: "Estimated total",
      value: formatCurrency(model.estimatedTotalUsd),
      meta: `Budget gap ${formatCurrency(model.budgetGapUsd)}`,
      tone: model.budgetGapUsd >= 0 ? "success" : "danger"
    },
    {
      label: "Spent so far",
      value: formatCurrency(model.spentTotalUsd),
      meta: pluralize(model.expenseCount, "expense"),
      tone: "neutral"
    },
    {
      label: "Remaining",
      value: formatCurrency(model.remainingBudgetUsd),
      meta: model.onTrack ? "Within budget" : "Needs correction",
      tone: model.remainingBudgetUsd >= 0 ? "success" : "danger"
    },
    {
      label: "Transport",
      value: formatValue(model.transportMode),
      meta: formatCurrency(model.transportUsd),
      tone: "neutral"
    },
    {
      label: "Weather",
      value: model.weatherHigh !== null && model.weatherHigh !== undefined
        ? `${model.weatherHigh}C / ${model.weatherLow}C`
        : "n/a",
      meta: `${formatValue(model.weatherRainRisk, "0")} rain-risk days`,
      tone: "neutral"
    }
  ];

  metricGrid.innerHTML = metrics.map((metric) => `
    <article class="metric-card ${metric.tone}">
      <span class="metric-label">${escapeHtml(metric.label)}</span>
      <strong class="metric-value">${escapeHtml(metric.value)}</strong>
      <span class="metric-meta">${escapeHtml(metric.meta)}</span>
    </article>
  `).join("");

  overviewBox.className = "detail-stack";
  overviewBox.innerHTML = `
    ${renderFacts([
      ["Trip ID", model.tripId],
      ["Destination", model.destination],
      ["Requested by user", model.destinationRequested],
      ["Home city", model.homeCity],
      ["Dates", `${model.startDate} -> ${model.endDate}`],
      ["Length", `${formatValue(model.days, "?")} days / ${formatValue(model.nights, "?")} nights`],
      ["Travelers", pluralize(model.travelers, "traveler")],
      ["Notes", model.notes || "No notes"]
    ])}
    <div class="subsection">
      <p class="tiny-label">Planner tips</p>
      ${renderTipCloud(model.tips)}
    </div>
  `;

  travelBox.className = "detail-stack";
  travelBox.innerHTML = `
    ${renderFacts([
      ["Resolved destination", model.destination],
      ["Weather", model.weatherSummary],
      ["Transport mode", model.transportMode],
      ["Travel estimate", formatCurrency(model.transportUsd)],
      ["Lodging estimate", formatCurrency(model.lodgingUsd)],
      ["Food estimate", formatCurrency(model.foodUsd)],
      ["Local transit", formatCurrency(model.localTransportUsd)],
      ["Activities", formatCurrency(model.activitiesUsd)],
      ["Destination total", formatCurrency(model.localTotal, model.localCurrencyCode)]
    ])}
    <div class="subsection">
      <p class="tiny-label">External service sources</p>
      <div class="tag-row compact">
        ${renderTagRow([
          model.sources.geocoding ? `Geocoder: ${model.sources.geocoding}` : "",
          model.sources.weather ? `Weather: ${model.sources.weather}` : "",
          model.sources.exchange_rate ? `FX: ${model.sources.exchange_rate}` : ""
        ])}
      </div>
    </div>
  `;

  const progressBase = model.kind === "plan" ? model.estimatedTotalUsd : model.spentTotalUsd;
  const progressPercent = model.budgetUsd ? Math.min(100, Math.max(0, Math.round((progressBase / model.budgetUsd) * 100))) : 0;
  budgetBox.className = "detail-stack";
  budgetBox.innerHTML = `
    <div class="budget-progress">
      <div class="progress-header">
        <strong>${escapeHtml(model.kind === "plan" ? "Projected budget usage" : "Current budget usage")}</strong>
        <span>${escapeHtml(`${progressPercent}%`)}</span>
      </div>
      <div class="progress-track"><span style="width: ${progressPercent}%"></span></div>
      <p class="caption">${escapeHtml(formatCurrency(progressBase))} of ${escapeHtml(formatCurrency(model.budgetUsd))}</p>
    </div>
    ${renderFacts([
      ["Estimated total", formatCurrency(model.estimatedTotalUsd)],
      ["Spent so far", formatCurrency(model.spentTotalUsd)],
      ["Remaining", formatCurrency(model.remainingBudgetUsd)],
      ["Pace delta", model.paceDeltaUsd === null ? "n/a" : formatCurrency(model.paceDeltaUsd)],
      ["Status", model.onTrack ? "On track" : "Needs attention"]
    ])}
    <div class="subsection">
      <p class="tiny-label">${model.categoryBreakdown.length ? "Actual spend by category" : "Planned cost mix"}</p>
      ${renderBars(getBudgetSegments(model))}
    </div>
  `;

  const itineraryPreview = model.dailyPlan.slice(0, 4);
  const nextReminders = model.reminders.slice(0, 5);
  calendarBox.className = "detail-stack";
  calendarBox.innerHTML = `
    ${renderFacts([
      ["Calendar file", model.calendarPath],
      ["Reminder count", pluralize(model.reminders.length, "event")],
      ["Planned days", pluralize(model.dailyPlan.length, "day")],
      ["First plan", itineraryPreview[0] ? `${itineraryPreview[0].date}: ${itineraryPreview[0].title}` : "n/a"],
      ["First reminder", nextReminders[0] ? `${nextReminders[0].date}: ${nextReminders[0].title}` : "n/a"],
      ["Trip window", `${model.startDate} -> ${model.endDate}`]
    ])}
    <div class="subsection">
      <p class="tiny-label">Suggested day plan</p>
      <div class="timeline-list">
        ${itineraryPreview.length ? itineraryPreview.map((day) => `
          <div class="timeline-item">
            <span class="timeline-date">${escapeHtml(day.date)}</span>
            <strong>${escapeHtml(day.title)}</strong>
            <span class="caption">${escapeHtml(`Spend cap ${formatCurrency(day.spend_target_usd)}`)}</span>
          </div>
        `).join("") : "<p class='caption'>No daily plan available.</p>"}
      </div>
    </div>
    <div class="subsection">
      <p class="tiny-label">Reminder highlights</p>
      <div class="timeline-list">
        ${nextReminders.length ? nextReminders.map((event) => `
          <div class="timeline-item">
            <span class="timeline-date">${escapeHtml(event.date)}</span>
            <strong>${escapeHtml(event.title)}</strong>
          </div>
        `).join("") : "<p class='caption'>No reminder events available.</p>"}
      </div>
    </div>
  `;

  expenseCount.textContent = String(model.expenses.length);
  expenseTable.className = "table-wrap";
  expenseTable.innerHTML = renderTable(
    ["Date", "Category", "Amount", "Vendor", "Notes"],
    model.expenses.slice(0, 10).map((item) => [
      formatValue(item.expense_date),
      formatValue(item.category),
      formatCurrency(item.amount_usd),
      formatValue(item.vendor, "n/a"),
      formatValue(item.notes, "n/a")
    ]),
    "No expenses recorded yet."
  );

  reminderCount.textContent = String(model.reminders.length);
  reminderTable.className = "table-wrap";
  reminderTable.innerHTML = renderTable(
    ["Date", "Title", "Description"],
    model.reminders.slice(0, 10).map((event) => [
      formatValue(event.date),
      formatValue(event.title),
      formatValue(event.description)
    ]),
    "No reminders generated yet."
  );
}

async function apiGet(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok || !payload.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

async function apiPost(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const payload = await response.json();
  if (!response.ok || !payload.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

async function downloadExcelReport(tripId) {
  const response = await fetch(`/api/export?trip_id=${encodeURIComponent(tripId)}`);
  if (!response.ok) {
    let errorMessage = `Download failed: ${response.status}`;
    try {
      const payload = await response.json();
      errorMessage = payload.error || errorMessage;
    } catch (error) {
      errorMessage = errorMessage;
    }
    throw new Error(errorMessage);
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="([^"]+)"/);
  const fileName = match?.[1] || `${tripId}.xlsx`;
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

async function loadTrips() {
  const payload = await apiGet("/api/trips");
  const trips = payload.result.trips;
  tripCount.textContent = String(trips.length);
  if (!trips.length) {
    tripList.innerHTML = "<p class='caption'>No trips saved yet.</p>";
    return;
  }
  tripList.innerHTML = trips.map((trip) => `
    <article class="trip-item">
      <div class="trip-item-head">
        <strong>${escapeHtml(trip.destination)}</strong>
        <span class="count-pill">${escapeHtml(formatCurrency(trip.budget_usd))}</span>
      </div>
      <div class="trip-meta">${escapeHtml(trip.trip_id)}</div>
      <div class="trip-meta">${escapeHtml(`${trip.start_date} -> ${trip.end_date}`)}</div>
      <div class="trip-meta">Est. ${escapeHtml(formatCurrency(trip.estimated_total_usd))}</div>
      <div class="trip-actions">
        <button type="button" class="ghost-button use-trip" data-trip-id="${escapeHtml(trip.trip_id)}">Use trip</button>
        <button type="button" class="secondary-button load-trip" data-trip-id="${escapeHtml(trip.trip_id)}">Load status</button>
        <button type="button" class="ghost-button download-trip" data-trip-id="${escapeHtml(trip.trip_id)}">Excel</button>
      </div>
    </article>
  `).join("");

  document.querySelectorAll(".use-trip").forEach((button) => {
    button.addEventListener("click", () => {
      statusTripId.value = button.dataset.tripId;
      expenseTripId.value = button.dataset.tripId;
      setExportTripId(button.dataset.tripId);
      setStatus("Trip selected", "success");
    });
  });

  document.querySelectorAll(".load-trip").forEach((button) => {
    button.addEventListener("click", async () => {
      statusTripId.value = button.dataset.tripId;
      expenseTripId.value = button.dataset.tripId;
      setStatus("Loading status...", "");
      try {
        const payload = await apiGet(`/api/status?trip_id=${encodeURIComponent(button.dataset.tripId)}`);
        renderDashboard(buildStatusModel(payload));
        setRawJson(payload);
        renderTrace(payload.trace);
        setStatus("Status loaded", "success");
      } catch (error) {
        clearDashboard(error.message);
        setRawJson({ error: error.message });
        renderTrace([]);
        setStatus("Request failed", "error");
      }
    });
  });

  document.querySelectorAll(".download-trip").forEach((button) => {
    button.addEventListener("click", async () => {
      setStatus("Preparing Excel...", "");
      try {
        await downloadExcelReport(button.dataset.tripId);
        setExportTripId(button.dataset.tripId);
        setStatus("Excel downloaded", "success");
      } catch (error) {
        setStatus("Download failed", "error");
        setRawJson({ error: error.message });
      }
    });
  });
}

document.getElementById("planForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Planning...", "");
  const formData = new FormData(event.target);
  const body = Object.fromEntries(formData.entries());
  body.budget_usd = Number(body.budget_usd);
  body.travelers = Number(body.travelers);
  try {
    const payload = await apiPost("/api/plan", body);
    renderDashboard(buildPlanModel(payload));
    setRawJson(payload);
    renderTrace(payload.trace);
    statusTripId.value = payload.result.trip.trip_id;
    expenseTripId.value = payload.result.trip.trip_id;
    setStatus("Trip planned", "success");
    await loadTrips();
  } catch (error) {
    clearDashboard(error.message);
    setRawJson({ error: error.message });
    renderTrace([]);
    setStatus("Request failed", "error");
  }
});

document.getElementById("statusForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Loading status...", "");
  const tripId = statusTripId.value.trim();
  try {
    const payload = await apiGet(`/api/status?trip_id=${encodeURIComponent(tripId)}`);
    renderDashboard(buildStatusModel(payload));
    setRawJson(payload);
    renderTrace(payload.trace);
    setStatus("Status loaded", "success");
  } catch (error) {
    clearDashboard(error.message);
    setRawJson({ error: error.message });
    renderTrace([]);
    setStatus("Request failed", "error");
  }
});

document.getElementById("expenseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Saving expense...", "");
  const formData = new FormData(event.target);
  const body = Object.fromEntries(formData.entries());
  body.amount_usd = Number(body.amount_usd);
  try {
    const expensePayload = await apiPost("/api/expense", body);
    const statusPayload = await apiGet(`/api/status?trip_id=${encodeURIComponent(body.trip_id)}`);
    const mergedTrace = [
      ...expensePayload.trace.map((entry) => ({ ...entry, phase: "expense save" })),
      ...statusPayload.trace.map((entry) => ({ ...entry, phase: "status refresh" }))
    ];
    renderDashboard(buildStatusModel(statusPayload));
    setRawJson({
      expense_saved: expensePayload.result,
      refreshed_status: statusPayload.result
    });
    renderTrace(mergedTrace);
    setStatus("Expense saved", "success");
    await loadTrips();
  } catch (error) {
    clearDashboard(error.message);
    setRawJson({ error: error.message });
    renderTrace([]);
    setStatus("Request failed", "error");
  }
});

document.getElementById("refreshTrips").addEventListener("click", async () => {
  try {
    await loadTrips();
    setStatus("Trips refreshed", "success");
  } catch (error) {
    clearDashboard(error.message);
    setRawJson({ error: error.message });
    setStatus("Refresh failed", "error");
  }
});

downloadExcelButton.addEventListener("click", async () => {
  const tripId = currentTripId || statusTripId.value.trim() || expenseTripId.value.trim();
  if (!tripId) {
    setStatus("Select a trip first", "error");
    return;
  }
  setStatus("Preparing Excel...", "");
  try {
    await downloadExcelReport(tripId);
    setStatus("Excel downloaded", "success");
  } catch (error) {
    setRawJson({ error: error.message });
    setStatus("Download failed", "error");
  }
});

clearDashboard();
loadTrips().catch((error) => {
  clearDashboard(error.message);
  setRawJson({ error: error.message });
  setStatus("Startup failed", "error");
});
