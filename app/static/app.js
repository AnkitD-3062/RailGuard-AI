const form = document.querySelector("#analysis-form");
const fileInput = document.querySelector("#video-file");
const fileName = document.querySelector("#file-name");
const progress = document.querySelector("#progress");
const submit = document.querySelector("#submit");
const result = document.querySelector("#result");

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
    const response = await fetch("/api/analyse", { method: "POST", body: new FormData(form) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Analysis failed.");

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
    progress.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
});
