/**
 * Craft Keeper — Preserving Living Audiovisual Heritage
 * Main Client Application & Prototype Interactions
 */

// Embedded default sample guide for instant offline Demo Mode (<0.2s)
const DEFAULT_SAMPLE_GUIDE = {
  title: "Traditional Mysuru Paak (Sample Heritage Sweet)",
  detected_language: "Kannada",
  category: "recipe",
  summary: "A traditional Karnataka melt-in-mouth confection prepared from sieved gram flour, hot clarified butter (ghee), and one-string sugar syrup. (NOTE: This is a synthetic sample created by the project maintainer for testing and demonstration, not recorded from a living individual).",
  metadata: {
    knowledge_holder: "Ajji (Grandmother)",
    community: "Karnataka Traditional Confectioners Guild",
    place: "Mysuru, Karnataka",
    language: "Kannada",
    occasion_or_context: "Deepavali festive preparation",
    source_video_license_or_permission: "Sample written by the developer. Not a real person's knowledge.",
    anonymity_requested: false,
    consent_confirmed: true,
    model_used: "mock",
    frames_used: 6,
    frame_mode: "mock_frames",
    source_filename: "sample_mysuru_paak_demo.mp4",
    approx_duration_seconds: 69.2,
    generated_at: new Date().toISOString()
  },
  ingredients_or_materials: [
    { name: "Besan (Bengal gram flour / ಕಡಲೆ ಹಿಟ್ಟು)", quantity: "1 cup (approx. 100g)", note: "Sieved twice through a fine mesh sieve to eliminate lumps" },
    { name: "Pure Desi Ghee (Clarified butter / ತುಪ್ಪ)", quantity: "2 cups (approx. 400ml)", note: "Kept gently heated and melted in a side saucepan throughout preparation" },
    { name: "Sugar (Granulated cane sugar / ಸಕ್ಕರೆ)", quantity: "2 cups (approx. 350g)", note: "Refined white or raw cane sugar" },
    { name: "Water", quantity: "1/2 cup", note: "Just sufficient to submerge and dissolve the sugar" }
  ],
  tools: [
    "Heavy-bottomed iron or brass kadai (deep frying pan)",
    "Small sauce pan with ladle (for continuous hot ghee addition)",
    "Sturdy long-handled wooden spatula",
    "Greased high-rimmed metal tray or rectangular tin",
    "Straight-edge pastry knife for scoring warm squares"
  ],
  steps: [
    {
      number: 1,
      approx_start_seconds: 8.0,
      instruction: "Sieve the gram flour twice into a wide bowl. Fold in two tablespoons of warm melted ghee to create a loose, clump-free paste.",
      spoken_tip: "Rubbing warm ghee into the dry flour before it touches the boiling syrup stops lumps from ever forming in the kadai."
    },
    {
      number: 2,
      approx_start_seconds: 21.0,
      instruction: "In a heavy-bottomed kadai over medium heat, dissolve two cups of sugar in half a cup of water and boil until one-string consistency (oru kambi padam) is achieved.",
      spoken_tip: "Dip your ladle, let a drop cool slightly, and test between thumb and forefinger—it must pull into a continuous thin single string before you add the flour."
    },
    {
      number: 3,
      approx_start_seconds: 38.0,
      instruction: "Lower the flame to low and pour the gram flour paste into the bubbling syrup in a steady stream, stirring continuously in one direction with a wooden spatula.",
      spoken_tip: "Keep the ladle moving along the bottom of the pan so the gram flour cooks evenly without catching or scorching."
    },
    {
      number: 4,
      approx_start_seconds: 47.0,
      instruction: "Ladle in boiling hot ghee one ladle at a time. Stir continuously until the mixture absorbs the ghee completely before ladling in the next portion.",
      spoken_tip: "The ghee must be hot when added. If you ladle cold ghee into the mixture, the sugar will seize and you lose the porous structure."
    },
    {
      number: 5,
      approx_start_seconds: 59.0,
      instruction: "Observe the mixture frothing vigorously with honey-comb pores. When the mass leaves the sides of the pan and ghee separates at the edges, instantly transfer into the greased tray.",
      spoken_tip: "Do not scrape the bottom or press down hard; let it settle naturally so the iconic porous honeycomb texture remains airy."
    }
  ],
  tips: [
    "The secret to honeycomb pores is adding smoking-hot ghee in alternating ladles while stirring vigorously.",
    "Never press down or smooth the top surface once poured into the tray; flattening it destroys the internal aeration.",
    "Slice into neat diamonds or squares while still warm (approx. 10 minutes after pouring); once completely cooled, it becomes too brittle to slice cleanly."
  ],
  safety_notes: [
    "Molten sugar syrup and boiling ghee reach over 120°C (250°F) and bubble aggressively; wear long sleeves and keep children away from the stove.",
    "Use a deep, heavy kadai with sturdy heat-proof handles to prevent tipping during rapid stirring.",
    "Keep a flat heat-resistant surface ready for the greased tray before beginning the cook."
  ],
  uncertain_items: [
    {
      what: "Exact flame setting during initial ghee ladling",
      reason: "The audio was partially obscured by bubbling sounds around 0:42. A medium-low flame is standard, but verify with your stove."
    },
    {
      what: "Resting time before scoring",
      reason: "The speaker said 'few minutes' without specifying an exact duration; standard culinary practice is 8 to 12 minutes."
    }
  ]
};

// Application State
let currentGuide = null;
let uploadedFile = null;
let isAnonymous = false;
let isConsentGiven = false;
let currentStepIndex = 1;

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initDropzone();
  initFormControls();
  initFAQ();
  initModals();
  fetchBackendHealth();
});

// Toast notification helper
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      ${type === 'success' ? '<polyline points="20 6 9 17 4 12"></polyline>' : 
        type === 'error' ? '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>' :
        '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>'}
    </svg>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("show"));

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Backend Health
async function fetchBackendHealth() {
  const chip = document.getElementById("backendStatusChip");
  const chipText = document.getElementById("backendChipText");
  const privacyText = document.getElementById("privacyCardText");

  try {
    const res = await fetch("/api/health");
    if (!res.ok) throw new Error("Health endpoint offline");
    const data = await res.json();
    const backend = data.backend || "mock";

    if (chipText) {
      if (backend === "mock") {
        chipText.textContent = "Mode: Mock (Offline Sample)";
      } else if (backend.includes("local")) {
        chipText.textContent = "Mode: Gemma 4 Local (CPU)";
      } else if (backend.includes("hosted")) {
        chipText.textContent = "Mode: Gemma 4 Hosted";
      } else {
        chipText.textContent = `Mode: ${backend}`;
      }
    }

    if (privacyText) {
      if (backend === "mock" || backend.includes("local")) {
        privacyText.innerHTML = "<strong>Your video stays on this computer.</strong> Audio, frames, and structured text are processed locally without network access.";
      } else {
        privacyText.innerHTML = "<strong>Cloud processing active:</strong> Audio transcript and frames are sent to the model provider (Google AI Studio Free Tier).";
      }
    }
  } catch (err) {
    if (chipText) chipText.textContent = "Mode: Mock (Default)";
  }
}

// Navigation between Page 1 (Landing) and Page 2 (Workspace)
function initNavigation() {
  const pageLanding = document.getElementById("pageLanding");
  const pageWorkspace = document.getElementById("pageWorkspace");
  const navWorkspaceBtns = document.querySelectorAll(".btn-open-workspace");
  const navLandingBtns = document.querySelectorAll(".btn-open-landing");
  const mobileToggle = document.getElementById("mobileMenuToggle");
  const navMenu = document.getElementById("navMenu");

  function showWorkspace() {
    pageLanding.style.display = "none";
    pageWorkspace.style.display = "block";
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (navMenu) navMenu.classList.remove("open");
  }

  function showLanding() {
    pageWorkspace.style.display = "none";
    pageLanding.style.display = "block";
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (navMenu) navMenu.classList.remove("open");
  }

  navWorkspaceBtns.forEach(btn => btn.addEventListener("click", (e) => {
    e.preventDefault();
    showWorkspace();
  }));

  navLandingBtns.forEach(btn => btn.addEventListener("click", (e) => {
    e.preventDefault();
    showLanding();
  }));

  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener("click", () => {
      navMenu.classList.toggle("open");
    });
  }

  // Sticky Nav Shadow
  const siteNav = document.getElementById("siteNav");
  window.addEventListener("scroll", () => {
    if (window.scrollY > 10) {
      siteNav.classList.add("scrolled");
    } else {
      siteNav.classList.remove("scrolled");
    }
  });

  // Stepper Items click navigation
  const stepperButtons = document.querySelectorAll(".stepper-item");
  stepperButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetStep = parseInt(btn.dataset.step, 10);
      setWorkspaceStep(targetStep);
      const targetElement = document.getElementById(`workspaceSection${targetStep}`);
      if (targetElement) {
        targetElement.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });
}

function setWorkspaceStep(stepNum) {
  currentStepIndex = stepNum;
  document.querySelectorAll(".stepper-item").forEach(item => {
    const s = parseInt(item.dataset.step, 10);
    item.classList.remove("active", "completed");
    if (s === stepNum) item.classList.add("active");
    else if (s < stepNum) item.classList.add("completed");
  });
}

// Dropzone & File Upload States
function initDropzone() {
  const dropzone = document.getElementById("videoDropzone");
  const fileInput = document.getElementById("videoFileInput");
  const stateEmpty = document.getElementById("dropzoneEmpty");
  const stateUploaded = document.getElementById("dropzoneUploaded");
  const stateError = document.getElementById("dropzoneError");
  const uploadedFilename = document.getElementById("uploadedFilename");
  const uploadedMeta = document.getElementById("uploadedMeta");
  const btnRemoveFile = document.getElementById("btnRemoveFile");
  const btnChooseAnother = document.getElementById("btnChooseAnother");

  if (!dropzone || !fileInput) return;

  ["dragenter", "dragover"].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("drag-over");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFileSelection(files[0]);
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) handleFileSelection(e.target.files[0]);
  });

  if (btnRemoveFile) {
    btnRemoveFile.addEventListener("click", (e) => {
      e.stopPropagation();
      resetDropzone();
    });
  }

  if (btnChooseAnother) {
    btnChooseAnother.addEventListener("click", (e) => {
      e.stopPropagation();
      resetDropzone();
      fileInput.click();
    });
  }

  function handleFileSelection(file) {
    // Validation
    const validExtensions = [".mp4", ".mov", ".webm"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    const maxSize = 100 * 1024 * 1024; // 100 MB

    if (!validExtensions.includes(ext)) {
      showErrorState(`Unsupported file type (${ext}). Please upload an MP4, MOV, or WebM video recording.`);
      return;
    }

    if (file.size > maxSize) {
      showErrorState(`File exceeds 100 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB). Please select a shorter clip under 5 minutes.`);
      return;
    }

    uploadedFile = file;
    stateEmpty.style.display = "none";
    stateError.style.display = "none";
    stateUploaded.style.display = "flex";

    if (uploadedFilename) uploadedFilename.textContent = file.name;
    if (uploadedMeta) {
      uploadedMeta.textContent = `${(file.size / (1024 * 1024)).toFixed(1)} MB • Video Recording`;
    }

    showToast(`Video "${file.name}" ready for processing`, "success");
    setWorkspaceStep(2);
  }

  function showErrorState(msg) {
    uploadedFile = null;
    stateEmpty.style.display = "none";
    stateUploaded.style.display = "none";
    stateError.style.display = "flex";
    const errorMsgElem = document.getElementById("dropzoneErrorText");
    if (errorMsgElem) errorMsgElem.textContent = msg;
    showToast(msg, "error");
  }

  function resetDropzone() {
    uploadedFile = null;
    fileInput.value = "";
    stateUploaded.style.display = "none";
    stateError.style.display = "none";
    stateEmpty.style.display = "flex";
  }

  // Simulation handlers for testing error flows
  const btnSimulateError = document.getElementById("btnSimulateFileError");
  if (btnSimulateError) {
    btnSimulateError.addEventListener("click", () => {
      showErrorState("File size exceeds 100 MB limit (148.2 MB). Please select a 2 to 3 minute clip under 100 MB.");
    });
  }
}

// Form Controls & Interactive Triggers
function initFormControls() {
  const anonymityToggle = document.getElementById("anonymityToggle");
  const consentCheckbox = document.getElementById("consentCheckbox");
  const btnGenerate = document.getElementById("btnGenerateGuide");
  const btnDemoMode = document.getElementById("btnDemoMode");
  const heroTryBtn = document.getElementById("heroTryBtn");

  if (anonymityToggle) {
    anonymityToggle.addEventListener("change", (e) => {
      isAnonymous = e.target.checked;
      updateCreditDisplay();
    });
  }

  if (consentCheckbox && btnGenerate) {
    consentCheckbox.addEventListener("change", (e) => {
      isConsentGiven = e.target.checked;
      btnGenerate.disabled = !isConsentGiven;
    });
  }

  if (btnGenerate) {
    btnGenerate.addEventListener("click", startGuideGeneration);
  }

  if (btnDemoMode) {
    btnDemoMode.addEventListener("click", () => {
      loadSampleResult(DEFAULT_SAMPLE_GUIDE);
      showToast("Demo guide loaded instantly", "success");
    });
  }

  // Export buttons
  const btnDownloadMd = document.getElementById("btnDownloadMarkdown");
  const btnDownloadJson = document.getElementById("btnDownloadJson");

  if (btnDownloadMd) {
    btnDownloadMd.addEventListener("click", () => {
      if (!currentGuide) {
        showToast("Please generate or load a guide first", "error");
        return;
      }
      exportMarkdownFile(currentGuide);
    });
  }

  if (btnDownloadJson) {
    btnDownloadJson.addEventListener("click", () => {
      if (!currentGuide) {
        showToast("Please generate or load a guide first", "error");
        return;
      }
      exportJsonFile(currentGuide);
    });
  }

  // Timeout recovery simulation button
  const btnSimulateTimeout = document.getElementById("btnSimulateTimeout");
  if (btnSimulateTimeout) {
    btnSimulateTimeout.addEventListener("click", () => {
      showTimeoutModal();
    });
  }
}

// 4-Stage Progress Animation and Pipeline Execution
async function startGuideGeneration() {
  if (!isConsentGiven) {
    showToast("Consent required: Please check permission before generating", "error");
    return;
  }

  setWorkspaceStep(3);

  const progressSection = document.getElementById("progressPanel");
  const emptyResultSection = document.getElementById("emptyResultState");
  const activeResultSection = document.getElementById("activeResultCard");

  if (progressSection) progressSection.style.display = "flex";
  if (emptyResultSection) emptyResultSection.style.display = "none";
  if (activeResultSection) activeResultSection.style.display = "none";

  const stages = [
    { id: "stageExtract", text: "Extracting 16kHz audio & key visual frames..." },
    { id: "stageTranscribe", text: "Transcribing spoken craft explanations..." },
    { id: "stageStructure", text: "Structuring ingredients, steps & oral tips..." },
    { id: "stageCheck", text: "Checking model uncertainties & safety cautions..." }
  ];

  const statusLabel = document.getElementById("progressStatusLabel");

  for (let i = 0; i < stages.length; i++) {
    // Highlight stage
    stages.forEach((s, idx) => {
      const el = document.getElementById(s.id);
      if (!el) return;
      el.classList.remove("active", "completed");
      if (idx === i) el.classList.add("active");
      else if (idx < i) el.classList.add("completed");
    });

    if (statusLabel) statusLabel.textContent = stages[i].text;
    await new Promise(r => setTimeout(r, 650));
  }

  // Mark all completed
  stages.forEach(s => {
    const el = document.getElementById(s.id);
    if (el) {
      el.classList.remove("active");
      el.classList.add("completed");
    }
  });

  if (progressSection) progressSection.style.display = "none";

  // Build guide with user-entered form details
  const personName = document.getElementById("personNameInput")?.value.trim() || "Ajji (Grandmother)";
  const community = document.getElementById("communityInput")?.value.trim() || "Karnataka Traditional Artisans";
  const place = document.getElementById("placeInput")?.value.trim() || "Mysuru, Karnataka";
  const language = document.getElementById("languageSelect")?.value || "Kannada";

  const generatedGuide = JSON.parse(JSON.stringify(DEFAULT_SAMPLE_GUIDE));
  generatedGuide.metadata.knowledge_holder = isAnonymous ? "Anonymous" : personName;
  generatedGuide.metadata.community = community;
  generatedGuide.metadata.place = place;
  generatedGuide.metadata.language = language;
  generatedGuide.metadata.source_filename = uploadedFile ? uploadedFile.name : "uploaded_video.mp4";
  generatedGuide.metadata.model_used = "mock";
  generatedGuide.metadata.generated_at = new Date().toISOString();

  loadSampleResult(generatedGuide);
  setWorkspaceStep(4);
  showToast("Guide generated successfully! Please review before sharing.", "success");
}

// Populate and Display Guide in Workspace
function loadSampleResult(guide) {
  currentGuide = guide;

  const emptyState = document.getElementById("emptyResultState");
  const resultCard = document.getElementById("activeResultCard");
  if (emptyState) emptyState.style.display = "none";
  if (resultCard) resultCard.style.display = "flex";

  // Title & Summary
  const titleInput = document.getElementById("guideTitleInput");
  const summaryInput = document.getElementById("guideSummaryInput");
  if (titleInput) titleInput.value = guide.title;
  if (summaryInput) summaryInput.value = guide.summary;

  // Credit Line
  updateCreditDisplay();

  // Provenance Panel
  const provPath = document.getElementById("provPath");
  const provFrames = document.getElementById("provFrames");
  const provFile = document.getElementById("provFile");
  const provTime = document.getElementById("provTime");

  if (provPath) provPath.textContent = guide.metadata?.model_used || "mock";
  if (provFrames) provFrames.textContent = `${guide.metadata?.frames_used || 6} frames (${guide.metadata?.frame_mode || 'mock_frames'})`;
  if (provFile) provFile.textContent = guide.metadata?.source_filename || "sample_video.mp4";
  if (provTime) provTime.textContent = guide.metadata?.generated_at ? new Date(guide.metadata.generated_at).toLocaleTimeString() : "Just now";

  // Ingredients Table
  renderIngredients(guide.ingredients_or_materials || []);

  // Steps Table
  renderSteps(guide.steps || []);

  // Tips & Safety
  const tipsBox = document.getElementById("tipsInput");
  const safetyBox = document.getElementById("safetyInput");
  if (tipsBox) tipsBox.value = (guide.tips || []).map(t => "• " + t).join("\n");
  if (safetyBox) safetyBox.value = (guide.safety_notes || []).map(s => "• " + s).join("\n");

  // Uncertain Items
  renderUncertainItems(guide.uncertain_items || []);

  // Scroll into view
  resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

function updateCreditDisplay() {
  const creditElem = document.getElementById("creditLineText");
  if (!creditElem) return;

  const holder = isAnonymous ? "Anonymous" : (document.getElementById("personNameInput")?.value.trim() || currentGuide?.metadata?.knowledge_holder || "Ajji (Grandmother)");
  const comm = document.getElementById("communityInput")?.value.trim() || currentGuide?.metadata?.community || "Traditional Artisans";
  const place = document.getElementById("placeInput")?.value.trim() || currentGuide?.metadata?.place || "Mysuru, Karnataka";

  creditElem.innerHTML = `Knowledge shared by <strong>${holder}</strong>, ${comm}, ${place}`;
}

// Render Ingredients Table with Inline Add & Delete
function renderIngredients(items) {
  const container = document.getElementById("ingredientsTableBody");
  if (!container) return;
  container.innerHTML = "";

  items.forEach((item, idx) => {
    const row = document.createElement("tr");
    row.className = "editable-row";
    row.innerHTML = `
      <td><input type="text" value="${escapeHtml(item.name)}" oninput="updateIngredient(${idx}, 'name', this.value)" aria-label="Ingredient name"></td>
      <td style="width: 25%;"><input type="text" value="${escapeHtml(item.quantity || '')}" oninput="updateIngredient(${idx}, 'quantity', this.value)" aria-label="Quantity"></td>
      <td style="width: 35%;"><input type="text" value="${escapeHtml(item.note || '')}" oninput="updateIngredient(${idx}, 'note', this.value)" aria-label="Artisan note"></td>
      <td style="width: 48px; text-align: center;">
        <button type="button" class="btn-icon-danger" onclick="deleteIngredient(${idx})" title="Remove item" aria-label="Remove ingredient">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
        </button>
      </td>
    `;
    container.appendChild(row);
  });
}

window.updateIngredient = function(index, field, value) {
  if (currentGuide && currentGuide.ingredients_or_materials[index]) {
    currentGuide.ingredients_or_materials[index][field] = value;
  }
};

window.deleteIngredient = function(index) {
  if (currentGuide && currentGuide.ingredients_or_materials) {
    currentGuide.ingredients_or_materials.splice(index, 1);
    renderIngredients(currentGuide.ingredients_or_materials);
    showToast("Ingredient removed", "info");
  }
};

window.addIngredientRow = function() {
  if (!currentGuide) currentGuide = JSON.parse(JSON.stringify(DEFAULT_SAMPLE_GUIDE));
  currentGuide.ingredients_or_materials.push({ name: "New Ingredient", quantity: "", note: "" });
  renderIngredients(currentGuide.ingredients_or_materials);
};

// Render Steps Table with Inline Add & Delete
function renderSteps(steps) {
  const container = document.getElementById("stepsTableBody");
  if (!container) return;
  container.innerHTML = "";

  steps.forEach((step, idx) => {
    const row = document.createElement("tr");
    row.className = "editable-row";
    row.innerHTML = `
      <td style="width: 48px; font-weight: 600; color: var(--color-primary-green);">${step.number || (idx + 1)}</td>
      <td style="width: 90px;"><input type="text" value="${step.approx_start_seconds != null ? step.approx_start_seconds + 's' : ''}" oninput="updateStepTime(${idx}, this.value)" aria-label="Timestamp"></td>
      <td><textarea rows="2" oninput="updateStep(${idx}, 'instruction', this.value)" aria-label="Step instruction">${escapeHtml(step.instruction)}</textarea></td>
      <td style="width: 32%;"><textarea rows="2" oninput="updateStep(${idx}, 'spoken_tip', this.value)" aria-label="Spoken tip">${escapeHtml(step.spoken_tip || '')}</textarea></td>
      <td style="width: 48px; text-align: center;">
        <button type="button" class="btn-icon-danger" onclick="deleteStep(${idx})" title="Remove step" aria-label="Remove step">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
        </button>
      </td>
    `;
    container.appendChild(row);
  });
}

window.updateStep = function(index, field, value) {
  if (currentGuide && currentGuide.steps[index]) {
    currentGuide.steps[index][field] = value;
  }
};

window.updateStepTime = function(index, value) {
  if (currentGuide && currentGuide.steps[index]) {
    const num = parseFloat(value);
    currentGuide.steps[index].approx_start_seconds = isNaN(num) ? null : num;
  }
};

window.deleteStep = function(index) {
  if (currentGuide && currentGuide.steps) {
    currentGuide.steps.splice(index, 1);
    currentGuide.steps.forEach((s, idx) => s.number = idx + 1);
    renderSteps(currentGuide.steps);
    showToast("Step removed", "info");
  }
};

window.addStepRow = function() {
  if (!currentGuide) currentGuide = JSON.parse(JSON.stringify(DEFAULT_SAMPLE_GUIDE));
  const newNum = currentGuide.steps.length + 1;
  currentGuide.steps.push({ number: newNum, approx_start_seconds: null, instruction: "New step instruction", spoken_tip: "" });
  renderSteps(currentGuide.steps);
};

// Render Uncertain Items ("Please check these") with Interactive Mark as Checked
function renderUncertainItems(items) {
  const container = document.getElementById("uncertainItemsList");
  if (!container) return;
  container.innerHTML = "";

  if (items.length === 0) {
    container.innerHTML = `<div style="font-style: italic; color: var(--color-muted); font-size: 0.9375rem;">No uncertainties flagged by model.</div>`;
    return;
  }

  items.forEach((item, idx) => {
    const row = document.createElement("div");
    row.className = "uncertain-item-row";
    row.id = `uncertainRow${idx}`;
    row.innerHTML = `
      <div>
        <div class="uncertain-title"><strong>${escapeHtml(item.what)}</strong></div>
        <div style="font-size: 0.8125rem; color: var(--color-muted); margin-top: 2px;">${escapeHtml(item.reason)}</div>
      </div>
      <div style="display: flex; gap: 8px; flex-shrink: 0;">
        <button type="button" class="btn btn-secondary btn-small" onclick="toggleUncertainChecked(${idx})" id="btnCheckUncertain${idx}">
          ✓ Mark as checked
        </button>
      </div>
    `;
    container.appendChild(row);
  });
}

window.toggleUncertainChecked = function(index) {
  const row = document.getElementById(`uncertainRow${index}`);
  const btn = document.getElementById(`btnCheckUncertain${index}`);
  if (!row || !btn) return;

  const isChecked = row.classList.toggle("checked");
  if (isChecked) {
    btn.textContent = "✓ Checked";
    btn.classList.add("btn-primary");
    btn.classList.remove("btn-secondary");
    showToast("Marked detail as verified", "success");
  } else {
    btn.textContent = "✓ Mark as checked";
    btn.classList.add("btn-secondary");
    btn.classList.remove("btn-primary");
  }
};

// Export to Markdown & JSON
function exportMarkdownFile(guide) {
  const title = document.getElementById("guideTitleInput")?.value || guide.title || "Heritage Guide";
  const summary = document.getElementById("guideSummaryInput")?.value || guide.summary || "";
  const holder = isAnonymous ? "Anonymous" : (document.getElementById("personNameInput")?.value || guide.metadata?.knowledge_holder || "Anonymous");
  const community = document.getElementById("communityInput")?.value || guide.metadata?.community || "";
  const place = document.getElementById("placeInput")?.value || guide.metadata?.place || "";
  const language = document.getElementById("languageSelect")?.value || guide.metadata?.language || "";

  let md = `# ${title}\n\n`;
  md += `> **AI-Generated Draft:** A human practitioner must review this guide before sharing.\n\n`;
  md += `**Knowledge shared by:** ${holder}${community ? ', ' + community : ''}${place ? ', ' + place : ''}\n\n`;
  if (language) md += `**Language:** ${language}\n\n`;
  if (summary) md += `## Overview\n\n${summary}\n\n`;

  md += `## Ingredients / Materials\n\n`;
  (guide.ingredients_or_materials || []).forEach(ing => {
    md += `- **${ing.name}**: ${ing.quantity || 'to taste'}${ing.note ? ' (' + ing.note + ')' : ''}\n`;
  });

  md += `\n## Step-by-Step Instructions\n\n`;
  (guide.steps || []).forEach(st => {
    const time = st.approx_start_seconds != null ? ` [${st.approx_start_seconds}s]` : '';
    md += `### Step ${st.number}${time}\n\n${st.instruction}\n\n`;
    if (st.spoken_tip) md += `*Artisan Tip:* "${st.spoken_tip}"\n\n`;
  });

  if (guide.tips && guide.tips.length > 0) {
    md += `## Rules of Thumb & Wisdom\n\n`;
    guide.tips.forEach(t => md += `- ${t}\n`);
    md += `\n`;
  }

  if (guide.safety_notes && guide.safety_notes.length > 0) {
    md += `## Safety Precautions\n\n`;
    guide.safety_notes.forEach(s => md += `- ⚠️ ${s}\n`);
    md += `\n`;
  }

  md += `---\n\n*Preserved with [Craft Keeper](https://github.com/Veeresh23-06/Craft-keeper) — Open-source audiovisual heritage preservation.*`;

  downloadBlob(md, `${slugify(title)}.md`, "text/markdown");
  showToast("Markdown guide downloaded", "success");
}

function exportJsonFile(guide) {
  const title = document.getElementById("guideTitleInput")?.value || guide.title || "heritage_guide";
  const jsonStr = JSON.stringify(guide, null, 2);
  downloadBlob(jsonStr, `${slugify(title)}.json`, "application/json");
  showToast("JSON data downloaded", "success");
}

function downloadBlob(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
}

function slugify(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "guide";
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// FAQ Accordion
function initFAQ() {
  const accordionHeaders = document.querySelectorAll(".accordion-header");
  accordionHeaders.forEach(header => {
    header.addEventListener("click", () => {
      const item = header.parentElement;
      const isOpen = item.classList.contains("open");
      document.querySelectorAll(".accordion-item").forEach(i => i.classList.remove("open"));
      if (!isOpen) item.classList.add("open");
    });
  });
}

// Modals Handling
function initModals() {
  // Video Demo Modal
  const modalVideo = document.getElementById("modalVideoDemo");
  const btnWatchDemo = document.getElementById("btnWatchDemo");
  const btnCloseVideo = document.getElementById("btnCloseVideoModal");

  if (btnWatchDemo && modalVideo) {
    btnWatchDemo.addEventListener("click", () => modalVideo.classList.add("open"));
  }
  if (btnCloseVideo && modalVideo) {
    btnCloseVideo.addEventListener("click", () => modalVideo.classList.remove("open"));
  }

  // Component Library Modal
  const modalComp = document.getElementById("modalComponentLibrary");
  const btnOpenComp = document.getElementById("btnOpenComponentLibrary");
  const btnCloseComp = document.getElementById("btnCloseCompModal");

  if (btnOpenComp && modalComp) {
    btnOpenComp.addEventListener("click", () => modalComp.classList.add("open"));
  }
  if (btnCloseComp && modalComp) {
    btnCloseComp.addEventListener("click", () => modalComp.classList.remove("open"));
  }

  // Close on backdrop click
  document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.classList.remove("open");
    });
  });
}

function showTimeoutModal() {
  const modal = document.getElementById("modalTimeout");
  if (modal) modal.classList.add("open");
}

window.closeTimeoutModal = function() {
  const modal = document.getElementById("modalTimeout");
  if (modal) modal.classList.remove("open");
};

window.recoverWithDemo = function() {
  closeTimeoutModal();
  loadSampleResult(DEFAULT_SAMPLE_GUIDE);
  showToast("Loaded sample guide via Demo Mode", "success");
};
