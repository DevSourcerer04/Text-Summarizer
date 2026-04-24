const form = document.getElementById("summarize-form");
const summaryOutput = document.getElementById("summary-output");
const statusChip = document.getElementById("status-chip");
const submitBtn = document.getElementById("submit-btn");

function setStatus(state, label) {
  statusChip.className = "chip";
  if (state) {
    statusChip.classList.add(state);
  }
  statusChip.textContent = label;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const text = String(formData.get("text") || "").trim();
  const minLength = Number(formData.get("min_length"));
  const maxLength = Number(formData.get("max_length"));

  if (!text) {
    setStatus("error", "Input Error");
    summaryOutput.textContent = "Please enter text to summarize.";
    return;
  }

  if (Number.isNaN(minLength) || Number.isNaN(maxLength) || minLength >= maxLength) {
    setStatus("error", "Input Error");
    summaryOutput.textContent = "Please keep min length smaller than max length.";
    return;
  }

  try {
    submitBtn.disabled = true;
    setStatus("loading", "Processing");
    summaryOutput.textContent = "Generating summary...";

    const response = await fetch("/summarize", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        min_length: minLength,
        max_length: maxLength,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Request failed");
    }

    summaryOutput.textContent = payload.summary;
    setStatus("ok", "Done");
  } catch (error) {
    setStatus("error", "Failed");
    summaryOutput.textContent = error.message || "Something went wrong while summarizing.";
  } finally {
    submitBtn.disabled = false;
  }
});
