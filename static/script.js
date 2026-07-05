document.addEventListener("DOMContentLoaded", () => {
  const status = document.getElementById("feature-status");
  const buttons = document.querySelectorAll(".feature-btn");
  const cropForm = document.getElementById("crop-form");
  const recommendationResult = document.getElementById("recommendation-result");
  const chatForm = document.getElementById("chat-form");
  const chatResult = document.getElementById("chat-result");
  const diseaseForm = document.getElementById("disease-form");
  const diseaseResult = document.getElementById("disease-result");
  const weatherForm = document.getElementById("weather-form");
  const weatherResult = document.getElementById("weather-result");

  const escapeHtml = (value) => String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");

  const renderError = (container, message) => {
    if (container) {
      container.innerHTML = `<div class="error-popup">${escapeHtml(message)}</div>`;
    }
  };

  const renderSuccess = (container, message) => {
    if (container) {
      container.innerHTML = `<div class="success-message">${escapeHtml(message)}</div>`;
    }
  };

  const setBusyState = (form, button, loadingText) => {
    if (button) {
      button.disabled = true;
      button.dataset.originalText = button.textContent;
      button.textContent = loadingText;
    }
    form?.classList.add("is-loading");
  };

  const clearBusyState = (form, button) => {
    if (button) {
      button.disabled = false;
      button.textContent = button.dataset.originalText || button.textContent;
      delete button.dataset.originalText;
    }
    form?.classList.remove("is-loading");
  };

  const submitJson = async (form, button, loadingText, url, onSuccess) => {
    if (!form) return;

    const formData = new FormData(form);
    setBusyState(form, button, loadingText);

    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok || data.status === "error") {
        renderError(form.nextElementSibling, data.message || "Something went wrong. Please try again.");
        return false;
      }

      onSuccess(data);
      return true;
    } catch (error) {
      renderError(form.nextElementSibling, "Unable to reach the service right now. Please try again.");
      return false;
    } finally {
      clearBusyState(form, button);
    }
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.dataset.target || "features";
      const section = document.getElementById(targetId);
      if (status) {
        status.textContent = button.dataset.message || "More details coming soon.";
      }
      if (section) {
        section.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  if (cropForm && recommendationResult) {
    cropForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submitButton = cropForm.querySelector("button[type='submit']");

      await submitJson(cropForm, submitButton, "Recommending crop...", "/recommend-crop", (data) => {
        renderSuccess(recommendationResult, `Recommendation ready for ${data.recommended_crop || "your farm"}.`);
        recommendationResult.innerHTML += `
          <h3>${escapeHtml(data.recommended_crop || "No recommendation yet")}</h3>
          <p><strong>Reason:</strong> ${escapeHtml(data.reason || "No reason available.")}</p>
          <p><strong>Source:</strong> ${escapeHtml(data.source || "local")}</p>
          <p>${escapeHtml(data.summary || "")}</p>
        `;
      });
    });
  }

  if (chatForm && chatResult) {
    chatForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submitButton = chatForm.querySelector("button[type='submit']");

      await submitJson(chatForm, submitButton, "Asking Gemini...", "/chat", (data) => {
        const summary = data.summary || data.reply || "No response returned.";
        const prevention = data.prevention || "Not available.";
        const monitoring = data.monitoring || "Not available.";
        const whenToSeekHelp = data.when_to_seek_help || "Not available.";

        renderSuccess(chatResult, "Your farming guidance is ready.");
        chatResult.innerHTML += `
          <h3>Gemini Guidance</h3>
          <p><strong>Summary:</strong> ${escapeHtml(summary)}</p>
          <p><strong>Prevention:</strong> ${escapeHtml(prevention)}</p>
          <p><strong>Monitoring:</strong> ${escapeHtml(monitoring)}</p>
          <p><strong>When to Seek Help:</strong> ${escapeHtml(whenToSeekHelp)}</p>
        `;

        if (!summary || summary.includes("Gemini API key") || summary.includes("Unable to reach Gemini") || summary.includes("Gemini 2.5 Flash")) {
          chatResult.innerHTML += '<div class="error-popup">The request used Gemini 2.5 Flash, but it could not be completed. Please verify your API key and access.</div>';
        }
      });
    });
  }

  if (diseaseForm && diseaseResult) {
    diseaseForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submitButton = diseaseForm.querySelector("button[type='submit']");

      await submitJson(diseaseForm, submitButton, "Analyzing image...", "/detect-disease", (data) => {
        renderSuccess(diseaseResult, "Disease analysis completed.");
        diseaseResult.innerHTML += `
          <h3>${escapeHtml(data.disease_name || "Disease not identified")}</h3>
          <p><strong>Symptoms:</strong> ${escapeHtml(data.symptoms || "Not available.")}</p>
          <p><strong>Treatment:</strong> ${escapeHtml(data.treatment || "Not available.")}</p>
          <p><strong>Organic Solution:</strong> ${escapeHtml(data.organic_solution || "Not available.")}</p>
          <p><strong>Chemical Solution:</strong> ${escapeHtml(data.chemical_solution || "Not available.")}</p>
          ${data.image_url ? `<img src="${escapeHtml(data.image_url)}" alt="Uploaded crop disease" class="disease-preview" />` : ""}
        `;
      });
    });
  }

  if (weatherForm && weatherResult) {
    weatherForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submitButton = weatherForm.querySelector("button[type='submit']");

      await submitJson(weatherForm, submitButton, "Checking weather...", "/weather", (data) => {
        renderSuccess(weatherResult, "Weather outlook loaded.");
        weatherResult.innerHTML += `
          <h3>${escapeHtml(data.city || "Weather")}</h3>
          <p><strong>Condition:</strong> ${escapeHtml(data.condition || "Not available.")}</p>
          <p><strong>Temperature:</strong> ${escapeHtml(data.temperature || "N/A")}</p>
          <p><strong>Humidity:</strong> ${escapeHtml(data.humidity || "N/A")}</p>
          <p><strong>Wind Speed:</strong> ${escapeHtml(data.wind_speed || "N/A")}</p>
          <p><strong>Farming Advice:</strong> ${escapeHtml(data.farming_advice || "Not available.")}</p>
        `;
      });
    });
  }
});
