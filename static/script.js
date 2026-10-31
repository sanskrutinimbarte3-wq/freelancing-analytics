// Format a number as Indian Rupees, e.g. 45000 -> ₹45,000
function rupees(n) {
  return "₹" + Math.round(n).toLocaleString("en-IN");
}

const INDIGO = "#4f46e5";
const GREEN = "#16a34a";
const NAVY = "#14213d";

// ---------------------------------------------------------------
// DASHBOARD: draw the 4 charts using data from /api/chart-data
// ---------------------------------------------------------------
async function drawCharts() {
  if (!document.getElementById("demandChart")) return;   // not on the dashboard page
  const data = await (await fetch("/api/chart-data")).json();
  Chart.defaults.font.family = "'Segoe UI', system-ui, sans-serif";
  Chart.defaults.color = NAVY;

  // Chart 1: Skill demand (horizontal bars so skill names are readable)
  new Chart(document.getElementById("demandChart"), {
    type: "bar",
    data: { labels: data.demand.labels, datasets: [{ label: "Freelancers", data: data.demand.values, backgroundColor: INDIGO, borderRadius: 4 }] },
    options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false } },
               scales: { x: { title: { display: true, text: "Number of freelancers" }, grid: { display: false } } } }
  });

  // Chart 2: Average income by skill
  new Chart(document.getElementById("incomeChart"), {
    type: "bar",
    data: { labels: data.income.labels, datasets: [{ label: "Avg monthly income", data: data.income.values, backgroundColor: GREEN, borderRadius: 4 }] },
    options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false },
               tooltip: { callbacks: { label: (c) => rupees(c.parsed.x) } } },
               scales: { x: { title: { display: true, text: "Average monthly income (₹)" }, grid: { display: false },
                             ticks: { callback: (v) => rupees(v) } } } }
  });

  // Chart 3: Experience vs income
  new Chart(document.getElementById("experienceChart"), {
    type: "bar",
    data: { labels: data.experience.labels, datasets: [{ label: "Avg monthly income", data: data.experience.values, backgroundColor: [ "#a5b4fc", "#6366f1", INDIGO ], borderRadius: 6 }] },
    options: { maintainAspectRatio: false, plugins: { legend: { display: false },
               tooltip: { callbacks: { label: (c) => rupees(c.parsed.y) } } },
               scales: { y: { beginAtZero: true, title: { display: true, text: "Average monthly income (₹)" }, ticks: { callback: (v) => rupees(v) } },
                         x: { grid: { display: false } } } }
  });

  // Chart 4: Hourly rate vs client rating (scatter)
  new Chart(document.getElementById("scatterChart"), {
    type: "scatter",
    data: { datasets: [{ label: "Freelancer", data: data.scatter, backgroundColor: "rgba(79,70,229,0.55)", pointRadius: 4 }] },
    options: { maintainAspectRatio: false, plugins: { legend: { display: false } },
               scales: { x: { title: { display: true, text: "Hourly rate (₹)" } },
                         y: { min: 3, max: 5, title: { display: true, text: "Client rating" } } } }
  });
  document.getElementById("scatterNote").textContent =
    "Do higher-rated freelancers charge more? Correlation between rate and rating: " + data.correlation;
}

// ---------------------------------------------------------------
// DASHBOARD: income predictor
// ---------------------------------------------------------------
function setupPredictor() {
  const form = document.getElementById("predictForm");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      experience: document.getElementById("experience").value,
      hourly_rate: document.getElementById("hourly_rate").value,
      hours_per_week: document.getElementById("hours_per_week").value,
      projects: document.getElementById("projects").value,
      rating: document.getElementById("rating").value
    };
    const res = await fetch("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const result = await res.json();
    const value = document.getElementById("predictValue");
    const msg = document.getElementById("predictMsg");
    if (!res.ok) {
      value.textContent = "—";
      msg.textContent = result.error;
      return;
    }
    value.textContent = result.formatted + " / month";
    msg.textContent = "Based on the selected experience, hourly rate, workload and project history.";
  });
}

// ---------------------------------------------------------------
// SKILL EXPLORER: searchable and filterable table
// ---------------------------------------------------------------
let allRecords = [];

function showRecords() {
  const text = document.getElementById("search").value.toLowerCase();
  const skill = document.getElementById("fSkill").value;
  const category = document.getElementById("fCategory").value;
  const experience = document.getElementById("fExperience").value;
  const demand = document.getElementById("fDemand").value;

  // Keep only the records that match every filter and the search text
  const rows = allRecords.filter((r) => {
    if (skill && r.Skill !== skill) return false;
    if (category && r.Category !== category) return false;
    if (experience && r.Experience_Level !== experience) return false;
    if (demand && r.Job_Demand !== demand) return false;
    const searchable = (r.Skill + " " + r.Category + " " + r.Experience_Level + " " + r.Job_Demand).toLowerCase();
    return searchable.includes(text);
  });

  const body = document.getElementById("recordsBody");
  if (rows.length === 0) {
    body.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No records match. Clear a filter or change the search.</td></tr>';
  } else {
    body.innerHTML = rows.map((r) =>
      `<tr><td class="fw-semibold">${r.Skill}</td><td>${r.Category}</td><td>${r.Experience_Level}</td>` +
      `<td class="text-end">${rupees(r.Hourly_Rate)}</td><td class="text-end">${r.Projects_Completed}</td>` +
      `<td class="text-end">${r.Client_Rating.toFixed(1)}</td><td class="text-end text-green fw-semibold">${rupees(r.Monthly_Income)}</td>` +
      `<td><span class="badge badge-${r.Job_Demand.toLowerCase()}">${r.Job_Demand}</span></td></tr>`
    ).join("");
  }
  document.getElementById("rowCount").textContent = "Showing " + rows.length + " of " + allRecords.length + " records";
}

async function setupExplorer() {
  if (!document.getElementById("recordsBody")) return;
  allRecords = await (await fetch("/api/records")).json();
  ["search", "fSkill", "fCategory", "fExperience", "fDemand"].forEach((id) => {
    document.getElementById(id).addEventListener("input", showRecords);   // filter live as the user types or selects
  });
  showRecords();
}

// ---------------------------------------------------------------
// SKILL EXPLORER: compare two skills
// ---------------------------------------------------------------
function setupCompare() {
  const button = document.getElementById("compareBtn");
  if (!button) return;
  const second = document.getElementById("skill2");
  if (second.options.length > 1) second.selectedIndex = 1;   // start with two different skills

  button.addEventListener("click", async () => {
    const s1 = document.getElementById("skill1").value;
    const s2 = second.value;
    const error = document.getElementById("compareError");
    const box = document.getElementById("compareResult");
    const res = await fetch("/api/compare?skill1=" + encodeURIComponent(s1) + "&skill2=" + encodeURIComponent(s2));
    const result = await res.json();
    if (!res.ok) {
      error.textContent = result.error;
      box.style.display = "none";
      return;
    }
    error.textContent = "";
    document.getElementById("thSkill1").textContent = result.skill1;
    document.getElementById("thSkill2").textContent = result.skill2;
    document.getElementById("compareBody").innerHTML = result.rows.map((r) =>
      `<tr><td class="fw-semibold">${r.metric}</td><td class="text-end">${r.a}</td><td class="text-end">${r.b}</td></tr>`).join("");
    document.getElementById("compareConclusion").textContent = result.conclusion;
    box.style.display = "block";
  });
}

drawCharts();
setupPredictor();
setupExplorer();
setupCompare();
