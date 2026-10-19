// Same origin: FastAPI serves this page and the API together.
const MAX_BYTES = 5 * 1024 * 1024;

const form = document.getElementById("analyze-form");
const formError = document.getElementById("form-error");
const submitBtn = document.getElementById("submit-btn");
const results = document.getElementById("results");

// Everything from the server/user is escaped before going into innerHTML (prevents XSS).
function esc(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function showError(message) {
  formError.textContent = message;
  formError.hidden = false;
}

function showFileInfo(inputId, infoId) {
  document.getElementById(inputId).addEventListener("change", (e) => {
    const file = e.target.files[0];
    document.getElementById(infoId).textContent = file ? `${file.name} (${(file.size / 1024).toFixed(0)} KB)` : "";
  });
}
showFileInfo("resume", "resume-info");
showFileInfo("job_file", "job-info");

function checkFile(file, label) {
  if (!/\.(pdf|txt)$/i.test(file.name)) return `${label} must be a PDF or .txt file.`;
  if (file.size > MAX_BYTES) return `${label} is larger than 5 MB.`;
  return null;
}

function validate() {
  const resume = form.resume.files[0];
  if (!resume && form.resume_text.value.trim().length < 10) return "Upload your resume or type your technical skills.";
  const jobFile = form.job_file.files[0];
  if (!jobFile && form.job_text.value.trim().length < 50) return "Upload a job description file or paste at least 50 characters.";
  return (resume && checkFile(resume, "Resume")) || (jobFile && checkFile(jobFile, "Job description")) || null;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  formError.hidden = true;
  const problem = validate();
  if (problem) return showError(problem);

  const data = new FormData(form);
  // Don't send empty optional fields: the API expects them to be absent, not "".
  for (const key of ["hours_per_day", "deadline", "job_text", "resume_text"]) {
    if (!String(data.get(key) ?? "").trim()) data.delete(key);
  }
  for (const key of ["resume", "job_file"]) {
    if (!form[key].files[0]) data.delete(key);
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Analyzing…";
  try {
    const response = await fetch("/analyze", { method: "POST", body: data });
    const body = await response.json();
    if (!response.ok) {
      // FastAPI returns either a string or a list of validation errors in "detail".
      const detail = Array.isArray(body.detail)
        ? body.detail.map((d) => `${d.loc.at(-1)}: ${d.msg}`).join("; ")
        : body.detail;
      throw new Error(detail || "Analysis failed.");
    }
    renderResults(body);
  } catch (err) {
    showError(err.message === "Failed to fetch" ? "Cannot reach the server. Is it running?" : err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Analyze";
  }
});

const pct = (v) => (v === null || v === undefined ? "n/a" : `${v}%`);

function chipList(items, cls, emptyText) {
  if (!items.length) return `<p class="muted">${emptyText}</p>`;
  return `<ul class="chips">${items
    .map((i) => `<li class="chip ${cls}" title="${esc(i.reason)}">${esc(i.skill)}</li>`)
    .join("")}</ul>`;
}

function renderSteps(steps) {
  return steps.map((step) => `
    <div class="step ${step.fits_deadline ? "" : "deferred"}">
      <label><input type="checkbox" class="done-box"> Mark done</label>
      <h4>${step.order}. ${esc(step.skill)} (${esc(step.priority)} priority)</h4>
      <p class="muted">${esc(step.reason)} · ~${step.estimated_hours} h · ${esc(step.day_range)}
        ${step.fits_deadline ? "" : " · <b>beyond your deadline</b>"}</p>
      ${step.topics.length ? `<p><b>Learn:</b> ${esc(step.topics.join(" → "))}</p>` : ""}
      <p><b>Practice:</b> ${esc(step.exercise)}</p>
      ${step.resources.map((u) => `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(u)}</a>`).join("<br>")}
    </div>`).join("");
}

function renderRequirements(matches) {
  if (!matches.length) return '<p class="muted">No requirement sentences found.</p>';
  return `<table class="req"><thead><tr><th>Job requirement</th><th>Closest line in your resume</th><th>Match</th></tr></thead>
    <tbody>${matches.map((m) => `<tr>
      <td>${esc(m.requirement)}</td>
      <td>${esc(m.closest_resume_line)}</td>
      <td><span class="badge ${m.match.replace(" ", "-")}">${esc(m.match)}</span>
        <small class="muted">${m.similarity.toFixed(2)}${m.skills_found.length ? ` · ${esc(m.skills_found.join(", "))}` : ""}</small></td>
    </tr>`).join("")}</tbody></table>`;
}

function renderResults(r) {
  const s = r.score;
  results.innerHTML = `
    <div class="card">
      <h2>Your match</h2>
      <div class="scores">
        <div class="score"><b>${s.overall}</b>Overall (heuristic)</div>
        <div class="score"><b>${pct(s.required_coverage)}</b>Required skills</div>
        <div class="score"><b>${pct(s.preferred_coverage)}</b>Preferred skills</div>
        <div class="score"><b>${s.semantic_match}%</b>Semantic match</div>
      </div>
      <p class="muted">${esc(s.formula)}. ${esc(s.disclaimer)}</p>
    </div>

    <div class="card">
      <h3>Skills you're missing (required)</h3>${chipList(r.missing_required, "missing", "None. Nice!")}
      <h3>Skills you're missing (nice to have)</h3>${chipList(r.missing_preferred, "missing", "None.")}
      <h3>Skills you have</h3>${chipList(r.matched.filter((m) => m.evidence !== "alternative"), "matched", "No matching skills found.")}
      ${r.matched.some((m) => m.evidence === "alternative") ? `<h3>Not needed: you have an accepted alternative</h3>
        ${chipList(r.matched.filter((m) => m.evidence === "alternative"), "alt", "")}` : ""}
      <h3>Please check</h3>${chipList(r.uncertain, "uncertain", "Nothing uncertain.")}
      <p class="muted">Hover over a skill to see why it was classified that way.</p>
    </div>

    <div class="card">
      <h3>Learning plan (in order)</h3>
      <p class="muted">${r.roadmap.total_hours} h total at ${r.roadmap.hours_per_day} h/day ≈ ${r.roadmap.estimated_days} days.
        ${esc(r.roadmap.note)}</p>
      ${r.roadmap.deferred_skills.length ? `<p class="error">Won't fit before your deadline: ${esc(r.roadmap.deferred_skills.join(", "))}</p>` : ""}
      ${renderSteps(r.roadmap.steps) || '<p class="muted">No missing skills, so no plan needed.</p>'}
    </div>

    <div class="card">
      <h3>Requirement match (semantic search)</h3>
      <p class="muted">For each job requirement, the most similar line in your resume, found with a sentence-embedding model.</p>
      ${renderRequirements(r.requirement_matches)}
    </div>

    ${r.eligibility.length ? `<div class="card"><h3>Eligibility (check yourself, not scored)</h3>
      <ul>${r.eligibility.map((e) => `<li>${esc(e)}</li>`).join("")}</ul></div>` : ""}

    <div class="card">
      <h3>Recommendations</h3>
      <ul>${r.recommendations.map((x) => `<li>${esc(x)}</li>`).join("") || "<li>None.</li>"}</ul>
      <h3>Limitations</h3>
      <ul>${r.limitations.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
    </div>`;

  results.hidden = false;
  results.querySelectorAll(".done-box").forEach((box) =>
    box.addEventListener("change", () => box.closest(".step").classList.toggle("done", box.checked)));
  results.scrollIntoView({ behavior: "smooth" });
}
