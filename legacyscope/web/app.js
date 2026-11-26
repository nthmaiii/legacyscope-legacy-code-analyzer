const state = {
  samples: [],
  result: null,
  file: null,
  loadingTimer: null,
  loadingIndex: 0,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function number(value) {
  return new Intl.NumberFormat("vi-VN").format(Number(value || 0));
}

function showToast(message, type = "error") {
  const toast = $("#toast");
  toast.textContent = message;
  toast.className = `toast visible ${type}`;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => {
    toast.className = "toast";
  }, 5200);
}

function showView(name) {
  $("#uploadView").classList.toggle("hidden", name !== "upload");
  $("#loadingView").classList.toggle("hidden", name !== "loading");
  $("#resultView").classList.toggle("hidden", name !== "result");
  $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.nav === name));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setFile(file) {
  state.file = file;
  const dropzone = $("#dropzone");
  if (file) {
    $("#dropTitle").textContent = file.name;
    $("#dropHint").textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB · sẵn sàng phân tích`;
    dropzone.classList.add("has-file");
  } else {
    $("#dropTitle").textContent = "Kéo thả tệp ZIP vào đây";
    $("#dropHint").textContent = "hoặc bấm để chọn từ máy tính";
    dropzone.classList.remove("has-file");
  }
}

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Có lỗi xảy ra khi gọi máy chủ.");
  }
  return data;
}

function renderSamples() {
  const grid = $("#sampleGrid");
  if (!state.samples.length) {
    grid.innerHTML = `<div class="panel-card"><p class="summary-text">Chưa có bộ mã nguồn mẫu.</p></div>`;
    return;
  }
  grid.innerHTML = state.samples.map((sample) => `
    <article class="sample-card">
      <div class="sample-top">
        <div class="sample-icon">
          <svg viewBox="0 0 24 24"><path d="M4 7.5 12 3l8 4.5-8 4.5-8-4.5Zm0 5L12 17l8-4.5M4 17l8 4.5 8-4.5"/></svg>
        </div>
        <span class="sample-year">LEGACY · ${esc(sample.year)}</span>
      </div>
      <h4>${esc(sample.name)}</h4>
      <p>${esc(sample.description)}</p>
      <div class="tag-row">
        ${sample.languages.map((language) => `<span class="tag">${esc(language)}</span>`).join("")}
        <span class="tag">${esc(sample.scale)}</span>
      </div>
      <div class="sample-meta">
        <span>Đã sẵn sàng phân tích</span>
        <button class="secondary-button analyze-sample" data-sample="${esc(sample.id)}">
          Phân tích mẫu
          <svg viewBox="0 0 24 24"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>
        </button>
      </div>
    </article>
  `).join("") + `
    <article class="sample-card upload-cta-card">
      <div class="sample-top">
        <div class="sample-icon upload-icon">
          <svg viewBox="0 0 24 24"><path d="M12 16V4m0 0 4 4m-4-4L8 8M5 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4"/></svg>
        </div>
        <span class="sample-year">CỦA BẠN</span>
      </div>
      <h4>Mã nguồn của bạn</h4>
      <p>Tải lên gói ZIP chứa mã nguồn Java và tệp SQL. Công cụ sẽ tự nhận diện cấu trúc dự án.</p>
      <div class="tag-row">
        <span class="tag">Java</span>
        <span class="tag">SQL</span>
        <span class="tag">ZIP ≤ 30 MB</span>
      </div>
      <div class="sample-meta">
        <span>Không gửi dữ liệu ra ngoài</span>
        <button class="secondary-button" id="sampleUploadButton">Chọn ZIP</button>
      </div>
    </article>
  `;
  $$(".analyze-sample").forEach((button) => {
    button.addEventListener("click", () => analyzeSample(button.dataset.sample, button.closest(".sample-card").querySelector("h4").textContent));
  });
  $("#sampleUploadButton")?.addEventListener("click", () => {
    $("#fileInput").click();
    $("#dropzone").scrollIntoView({ behavior: "smooth", block: "center" });
  });
}

function activateTab(name) {
  const tab = $(`.tab[data-tab="${name}"]`);
  if (!tab) return;
  $$(".tab").forEach((item) => item.classList.toggle("active", item === tab));
  $$(".tab-panel").forEach((panel) => panel.classList.toggle("hidden", panel.dataset.panel !== name));
}

function startLoading(projectName) {
  state.loadingIndex = 0;
  $("#loadingProject").textContent = projectName || "Đang chuẩn bị dữ liệu…";
  $$(".loading-step").forEach((step) => step.classList.remove("active", "done"));
  const steps = $$(".loading-step");
  if (steps[0]) steps[0].classList.add("active");
  clearInterval(state.loadingTimer);
  state.loadingTimer = setInterval(() => {
    if (state.loadingIndex >= steps.length - 1) return;
    steps[state.loadingIndex].classList.remove("active");
    steps[state.loadingIndex].classList.add("done");
    state.loadingIndex += 1;
    steps[state.loadingIndex].classList.add("active");
  }, 850);
  showView("loading");
}

function stopLoading() {
  clearInterval(state.loadingTimer);
  $$(".loading-step").forEach((step) => {
    step.classList.remove("active");
    step.classList.add("done");
  });
}

async function analyzeSample(sampleId, projectName) {
  startLoading(projectName);
  try {
    const data = await fetchJSON("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sample: sampleId }),
    });
    stopLoading();
    await new Promise((resolve) => setTimeout(resolve, 420));
    renderResult(data);
  } catch (error) {
    clearInterval(state.loadingTimer);
    showView("upload");
    showToast(error.message);
  }
}

async function analyzeUpload() {
  if (!state.file) {
    showToast("Bạn chưa chọn tệp ZIP.");
    return;
  }
  startLoading(state.file.name);
  const formData = new FormData();
  formData.append("file", state.file);
  try {
    const data = await fetchJSON("/api/analyze-upload", { method: "POST", body: formData });
    stopLoading();
    await new Promise((resolve) => setTimeout(resolve, 420));
    renderResult(data);
  } catch (error) {
    clearInterval(state.loadingTimer);
    showView("upload");
    showToast(error.message);
  }
}

function layerMap(result) {
  return Object.fromEntries((result.layers || []).map((layer) => [layer.key, layer.name]));
}

function statCard(label, value, hint, iconPath) {
  return `
    <div class="stat-card">
      <div class="stat-label"><span>${esc(label)}</span><span class="stat-icon"><svg viewBox="0 0 24 24">${iconPath}</svg></span></div>
      <strong>${esc(value)}</strong>
      <small>${esc(hint)}</small>
    </div>
  `;
}

function renderResult(result) {
  state.result = result;
  showView("result");
  const m = result.metrics || {};
  const summary = result.summary || {};
  $("#resultProject").textContent = result.project_name;
  $("#resultEyebrow").textContent = `Kết quả phân tích · ${result.analysis_id}`;
  $("#resultMeta").textContent = `${result.generated_at} · ${number(m.loc)} dòng mã · ${number(m.classes)} lớp · ${number(m.endpoints)} endpoint`;
  $("#pageTitle").textContent = "Kết quả phân tích";

  const score = Number(m.legacy_score || 0);
  const scoreColor = score >= 80 ? "#dc2626" : score >= 60 ? "#f59e0b" : "#10b981";
  $("#scoreRing").style.setProperty("--score", score);
  $("#scoreRing").style.setProperty("--score-color", scoreColor);
  $("#scoreValue").textContent = score;
  $("#scoreGrade").textContent = m.legacy_grade || "Chưa xác định";
  $("#scoreHint").textContent = score >= 80
    ? "Rủi ro rất cao — cần can thiệp trước khi thay đổi hệ thống."
    : score >= 60
      ? "Rủi ro cao — ưu tiên bảo mật, kiểm thử và tách phương thức dài."
      : score >= 40
        ? "Mức trung bình — nên cải thiện dần theo từng vòng bảo trì."
        : "Rủi ro thấp — có thể bảo trì và mở rộng tương đối an toàn.";
  $("#factFindings").textContent = number(m.findings_total);
  $("#factRules").textContent = number(m.business_rules);
  $("#factLayers").textContent = number(m.layers ? m.layers.length : (result.layers || []).length);

  $("#statGrid").innerHTML = [
    statCard("Tệp", number(m.files), "được quét", '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z"/><path d="M14 3v6h6"/>'),
    statCard("Dòng mã", number(m.loc), "LOC", '<path d="M5 7h14M5 12h14M5 17h9"/>'),
    statCard("Lớp", number(m.classes), `${number(m.methods)} phương thức`, '<path d="M4 6h16M4 12h16M4 18h16"/><path d="M8 3v18M16 3v18"/>'),
    statCard("API", number(m.endpoints), "endpoint", '<path d="M4 12h16M12 4v16"/><circle cx="12" cy="12" r="8"/>'),
    statCard("Bảng dữ liệu", number(m.tables), "quan hệ", '<ellipse cx="12" cy="5" rx="7" ry="3"/><path d="M5 5v7c0 1.7 3.1 3 7 3s7-1.3 7-3V5"/><path d="M5 12v7c0 1.7 3.1 3 7 3s7-1.3 7-3v-7"/>'),
    statCard("Vấn đề", number(m.findings_total), `${number(m.findings_high)} mức cao`, '<path d="M12 3 2.8 20h18.4L12 3Z"/><path d="M12 9v5M12 17h.01"/>'),
  ].join("");

  const layers = layerMap(result);
  $("#qualityImage").src = result.diagrams.quality;
  $("#architectureImage").src = result.diagrams.architecture;
  $("#dependencyImage").src = result.diagrams.dependency;
  $("#classImage").src = result.diagrams.class;
  $("#erdImage").src = result.diagrams.erd;
  $("#downloadDocx").href = result.artifacts.docx;
  $("#downloadPackage").href = result.artifacts.package || result.artifacts.docx;

  $("#overviewSummary").textContent = result.overview?.summary || "Không có tóm tắt.";
  $("#overviewRecommendations").innerHTML = (result.overview?.recommendations || [])
    .map((item, index) => `<div class="stack-item"><span>${String(index + 1).padStart(2, "0")}</span><div>${esc(item)}</div></div>`)
    .join("");

  renderFindingsTable($("#overviewFindings"), (result.findings || []).slice(0, 5), true);
  $("#overviewFindingCount").textContent = `${number(m.findings_total)} vấn đề`;

  renderLayers(result.layers || []);
  renderClasses(result.classes || [], layers);
  renderApis(result.endpoints || []);
  renderTables(result.tables || []);
  renderRules(result.business_rules || []);
  renderArtifacts(result);
  renderIssues(result.findings || []);
  renderSpecMeta(result);

  const requestedTab = new URLSearchParams(window.location.search).get("tab") || "overview";
  activateTab(requestedTab);
  bindSearch("#classSearch", "#classTable");
  bindSearch("#apiSearch", "#apiTable");
  bindSearch("#issueSearch", "#issueTable");
}

function renderLayers(layers) {
  const rows = layers.map((layer) => [
    `<strong>${esc(layer.name)}</strong>`,
    number(layer.classes.length),
    number(layer.methods),
    number(layer.loc),
  ]);
  $("#layerTable").innerHTML = tableHTML(["Tầng", "Lớp", "Phương thức", "Dòng"], rows, []);
}

function renderClasses(classes, layers) {
  const rows = classes.map((cls) => [
    `<strong>${esc(cls.name)}</strong><div class="path">${esc(cls.kind)}${cls.extends ? " · extends " + esc(cls.extends) : ""}</div>`,
    `<span class="tag">${esc(layers[cls.layer] || cls.layer)}</span>`,
    number(cls.methods.length),
    number((state.result.dependencies || []).filter((dep) => dep.source === cls.name).length),
    `<span class="path">${esc(cls.file)}</span>`,
  ]);
  $("#classTable").innerHTML = tableHTML(["Lớp", "Tầng", "Phương thức", "Phụ thuộc", "Tệp"], rows, []);
}

function renderApis(endpoints) {
  const rows = endpoints.map((endpoint) => [
    `<span class="tag">${esc(endpoint.http_method)}</span>`,
    `<span class="mono">${esc(endpoint.path)}</span>`,
    esc(endpoint.handler),
    esc(endpoint.class_name),
  ]);
  $("#apiTable").innerHTML = tableHTML(["HTTP", "Đường dẫn", "Handler", "Lớp"], rows, []);
}

function renderTables(tables) {
  const rows = tables.map((table) => [
    `<strong>${esc(table.name)}</strong>`,
    number(table.columns.length),
    esc(table.primary_key || "—"),
    esc(table.foreign_keys.join("; ") || "—"),
  ]);
  $("#tableList").innerHTML = tableHTML(["Bảng", "Cột", "Khóa chính", "Khóa ngoại"], rows, []);
}

function renderRules(rules) {
  $("#ruleCount").textContent = number(rules.length);
  const rows = rules.map((rule) => [
    `<strong>${esc(rule.title)}</strong>`,
    `<span class="mono">${esc(rule.condition)}</span>`,
    esc(rule.action),
  ]);
  $("#ruleTable").innerHTML = tableHTML(["Vị trí", "Điều kiện", "Hành vi"], rows, []);
}

function renderFindingsTable(table, findings, compact = false) {
  const rows = findings.map((finding) => {
    const severityClass = finding.severity === "Cao" ? "high" : finding.severity === "Trung bình" ? "medium" : "low";
    const file = finding.file ? `<span class="path">${esc(finding.file)}</span>` : "—";
    return [
      `<span class="severity ${severityClass}">${esc(finding.severity)}</span>`,
      esc(finding.title),
      compact ? esc(finding.category) : file,
    ];
  });
  table.innerHTML = tableHTML(compact ? ["Mức độ", "Vấn đề", "Nhóm"] : ["Mức độ", "Vấn đề", "Tệp"], rows, []);
}

function renderIssues(findings) {
  const rows = findings.map((finding) => {
    const severityClass = finding.severity === "Cao" ? "high" : finding.severity === "Trung bình" ? "medium" : "low";
    return [
      `<span class="severity ${severityClass}">${esc(finding.severity)}</span>`,
      esc(finding.category),
      `<strong>${esc(finding.title)}</strong><div class="path">${esc(finding.description)}</div>`,
      finding.file ? `<span class="path">${esc(finding.file)}</span>` : "—",
    ];
  });
  $("#issueTable").innerHTML = tableHTML(["Mức độ", "Nhóm", "Vấn đề", "Tệp"], rows, []);
}

function renderArtifacts(result) {
  const artifacts = result.artifacts || {};
  const cards = [
    {
      title: "Báo cáo Word",
      description: "Đặc tả kỹ thuật đầy đủ, có mục lục, bảng và sơ đồ.",
      href: artifacts.docx,
      icon: '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z"/><path d="M14 3v6h6"/>',
      link: "Tải .docx",
    },
    {
      title: "Gói kết quả",
      description: "ZIP gồm báo cáo, sơ đồ PNG, Mermaid và JSON.",
      href: artifacts.package,
      icon: '<path d="M4 7.5 12 3l8 4.5-8 4.5-8-4.5Zm0 5L12 17l8-4.5M4 17l8 4.5 8-4.5"/>',
      link: "Tải .zip",
    },
    {
      title: "Markdown",
      description: "Bản đặc tả nhẹ để đưa vào Git hoặc wiki.",
      href: artifacts.markdown,
      icon: '<path d="M4 5h16v14H4z"/><path d="M8 9v6m0-6-2 2m2-2 2 2M16 15v-6m0 6-2-2m2 2 2-2"/>',
      link: "Tải .md",
    },
  ];
  $("#artifactGrid").innerHTML = cards.map((card) => `
    <article class="artifact-card">
      <div class="artifact-icon"><svg viewBox="0 0 24 24">${card.icon}</svg></div>
      <h4>${esc(card.title)}</h4>
      <p>${esc(card.description)}</p>
      ${card.href ? `<a href="${esc(card.href)}" download>${esc(card.link)} →</a>` : `<span class="tag">Không khả dụng</span>`}
    </article>
  `).join("");

  $("#specContents").innerHTML = [
    "Thông tin chung và chỉ số dự án",
    "Kiến trúc phân tầng được phục hồi",
    "Danh mục module và trách nhiệm",
    "Danh mục lớp, phương thức, phụ thuộc",
    "Danh mục API và luồng xử lý",
    "Mô hình dữ liệu và quan hệ khóa ngoại",
    "Quy tắc nghiệp vụ ứng viên",
    "Đánh giá chất lượng và khuyến nghị",
    "Phụ lục tệp và sơ đồ Mermaid",
  ].map((item, index) => `<div class="stack-item"><span>${String(index + 1).padStart(2, "0")}</span><div>${esc(item)}</div></div>`).join("");
}

function renderSpecMeta(result) {
  const m = result.metrics || {};
  const items = [
    ["Mã phân tích", result.analysis_id],
    ["Thời điểm sinh", result.generated_at],
    ["Nguồn dữ liệu", result.root],
    ["Số tệp", number(m.files)],
    ["Số lớp", number(m.classes)],
    ["Số quy tắc", number(m.business_rules)],
    ["Chỉ số rủi ro", `${m.legacy_score}/100`],
  ];
  $("#specMeta").innerHTML = items.map(([label, value]) => `
    <div class="meta-row"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>
  `).join("");
}

function tableHTML(headers, rows, classes) {
  if (!rows.length) {
    return `<tbody><tr><td colspan="${headers.length}" style="text-align:center;color:#94a3b8;padding:24px">Không có dữ liệu</td></tr></tbody>`;
  }
  return `
    <thead><tr>${headers.map((header) => `<th>${esc(header)}</th>`).join("")}</tr></thead>
    <tbody>${rows.map((row) => `<tr>${row.map((cell, index) => `<td class="${classes[index] || ""}">${cell}</td>`).join("")}</tr>`).join("")}</tbody>
  `;
}

function bindSearch(inputSelector, tableSelector) {
  const input = $(inputSelector);
  const table = $(tableSelector);
  if (!input || !table || input.dataset.bound) return;
  input.dataset.bound = "1";
  input.addEventListener("input", () => {
    const term = input.value.trim().toLowerCase();
    table.querySelectorAll("tbody tr").forEach((row) => {
      row.style.display = row.textContent.toLowerCase().includes(term) ? "" : "none";
    });
  });
}

function bindTabs() {
  $("#tabs").addEventListener("click", (event) => {
    const tab = event.target.closest(".tab");
    if (!tab) return;
    activateTab(tab.dataset.tab);
  });
}

function bindEvents() {
  const dropzone = $("#dropzone");
  const fileInput = $("#fileInput");
  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") fileInput.click();
  });
  fileInput.addEventListener("change", () => setFile(fileInput.files[0] || null));
  ["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.add("dragover");
  }));
  ["dragleave", "drop"].forEach((name) => dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragover");
  }));
  dropzone.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0];
    if (file && file.name.toLowerCase().endsWith(".zip")) {
      setFile(file);
    } else {
      showToast("Vui lòng chọn tệp ZIP.");
    }
  });
  $("#uploadButton").addEventListener("click", analyzeUpload);
  $("#newAnalysisButton").addEventListener("click", () => {
    state.file = null;
    setFile(null);
    showView("upload");
    $("#pageTitle").textContent = "Phân tích mã nguồn cũ";
  });
  $("#menuButton").addEventListener("click", () => {
    $("#sidebar").classList.add("open");
    $("#sidebarBackdrop").classList.add("open");
  });
  $("#sidebarBackdrop").addEventListener("click", () => {
    $("#sidebar").classList.remove("open");
    $("#sidebarBackdrop").classList.remove("open");
  });
  $$(".nav-item").forEach((item) => item.addEventListener("click", () => {
    $("#sidebar").classList.remove("open");
    $("#sidebarBackdrop").classList.remove("open");
  }));
  bindTabs();
}

async function init() {
  bindEvents();
  try {
    const data = await fetchJSON("/api/samples");
    state.samples = data.samples || [];
    renderSamples();
  } catch (error) {
    showToast("Không tải được danh sách mẫu.");
  }
  const params = new URLSearchParams(window.location.search);
  if (params.get("auto") === "1" && params.get("sample")) {
    const sample = state.samples.find((item) => item.id === params.get("sample")) || state.samples[0];
    if (sample) analyzeSample(sample.id, sample.name);
  }
}

document.addEventListener("DOMContentLoaded", init);
