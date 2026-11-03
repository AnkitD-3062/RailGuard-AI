const form = document.querySelector("#analysis-form");
const fileInput = document.querySelector("#video-file");
const fileName = document.querySelector("#file-name");
const progress = document.querySelector("#progress");
const submit = document.querySelector("#submit");
const result = document.querySelector("#result");
// A relative URL works when the app is served by FastAPI. This fallback also
// supports opening index.html directly during local development.
const analyseUrl = window.location.protocol === "file:"
  ? "http://127.0.0.1:8000/api/analyse"
  : "/api/analyse";

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "No video selected";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const selected = fileInput.files[0];
  if (!selected) return;

  submit.disabled = true;
  progress.textContent = "Sampling video frames and evaluating safety risk…";
  result.classList.add("hidden");
  try {
    const response = await fetch(analyseUrl, { method: "POST", body: new FormData(form) });
    const raw = await response.text();
    let data = {};
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      if (!response.ok) throw new Error(`Server error (${response.status}). Please restart RailGuard AI and try again.`);
      throw new Error("The server returned an invalid response.");
    }
    if (!response.ok) throw new Error(data.detail || `Analysis failed (HTTP ${response.status}).`);

    document.querySelector("#risk-badge").textContent = data.risk_level;
    document.querySelector("#risk-badge").className = `risk-badge ${data.risk_level.toLowerCase()}`;
    document.querySelector("#message").textContent = data.message;
    document.querySelector("#risk-score").textContent = data.risk_score;
    document.querySelector("#peak-people").textContent = data.peak_people;
    document.querySelector("#average-people").textContent = data.average_people;
    document.querySelector("#intrusions").textContent = data.track_intrusion_frames;
    result.classList.remove("hidden");
    progress.textContent = `Analysis complete: ${data.sampled_frames} frames sampled.`;
  } catch (error) {
    progress.textContent = error instanceof TypeError
      ? "Cannot reach RailGuard AI. Run .\\start.ps1, then open http://127.0.0.1:8000."
      : error.message;
  } finally {
    submit.disabled = false;
  }
});
