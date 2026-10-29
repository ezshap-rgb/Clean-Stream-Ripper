// Clean Stream Ripper Frontend Logic
document.addEventListener("DOMContentLoaded", () => {
  const urlInput = document.getElementById("urlInput");
  const btnPaste = document.getElementById("btnPaste");
  const btnInspect = document.getElementById("btnInspect");
  const inspectSpinner = document.getElementById("inspectSpinner");
  const inspectText = document.getElementById("inspectText");

  const previewCard = document.getElementById("previewCard");
  const metaThumb = document.getElementById("metaThumb");
  const metaDuration = document.getElementById("metaDuration");
  const metaTitle = document.getElementById("metaTitle");
  const channelName = document.getElementById("channelName");

  const btnModeVideo = document.getElementById("btnModeVideo");
  const btnModeAudio = document.getElementById("btnModeAudio");
  const videoQualityBox = document.getElementById("videoQualityBox");
  const audioFormatBox = document.getElementById("audioFormatBox");
  const selectResolution = document.getElementById("selectResolution");
  const selectAudioFormat = document.getElementById("selectAudioFormat");

  const chkTrim = document.getElementById("chkTrim");
  const trimInputsRow = document.getElementById("trimInputsRow");
  const trimStart = document.getElementById("trimStart");
  const trimEnd = document.getElementById("trimEnd");

  const btnStartDownload = document.getElementById("btnStartDownload");
  const progressCard = document.getElementById("progressCard");
  const phasePill = document.getElementById("phasePill");
  const phaseText = document.getElementById("phaseText");
  const percentText = document.getElementById("percentText");
  const progressFill = document.getElementById("progressFill");
  const statSpeed = document.getElementById("statSpeed");
  const statSize = document.getElementById("statSize");
  const statEta = document.getElementById("statEta");

  const completeCard = document.getElementById("completeCard");
  const completeFileName = document.getElementById("completeFileName");
  const btnDownloadFile = document.getElementById("btnDownloadFile");
  const btnShareFile = document.getElementById("btnShareFile");
  const btnReset = document.getElementById("btnReset");

  let currentMode = "video";
  let activeEventSource = null;
  let downloadedFileUrl = null;

  // 1. Check for incoming URL from PWA Share Target (?url=... or ?text=...)
  function checkUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const shared = params.get("url") || params.get("text");
    if (shared) {
      // Find URL inside text if user shared YouTube text with title
      const urlMatch = shared.match(/https?:\/\/[^\s]+/);
      const urlToUse = urlMatch ? urlMatch[0] : shared;
      urlInput.value = urlToUse;
      inspectVideo(urlToUse);
    }
  }

  // 2. Clipboard Paste Handler
  btnPaste.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text && text.trim().startsWith("http")) {
        urlInput.value = text.trim();
        inspectVideo(text.trim());
      } else if (text) {
        urlInput.value = text.trim();
      }
    } catch (err) {
      urlInput.focus();
    }
  });

  // 3. Inspect Action
  btnInspect.addEventListener("click", () => {
    const url = urlInput.value.trim();
    if (url) {
      inspectVideo(url);
    } else {
      urlInput.focus();
    }
  });

  urlInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const url = urlInput.value.trim();
      if (url) inspectVideo(url);
    }
  });

  async function inspectVideo(url) {
    inspectSpinner.classList.remove("hidden");
    inspectText.textContent = "Loading...";
    btnInspect.disabled = true;
    previewCard.classList.add("hidden");
    progressCard.classList.add("hidden");
    completeCard.classList.add("hidden");

    try {
      const resp = await fetch("/api/info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Failed to inspect URL");
      }

      const data = await resp.json();
      metaTitle.textContent = data.title;
      channelName.textContent = data.channel;
      metaThumb.src = data.thumbnail;
      metaDuration.textContent = data.duration_str;
      trimEnd.value = data.duration_str;

      // Populate available video resolutions
      if (data.available_resolutions && data.available_resolutions.length > 0) {
        selectResolution.innerHTML = '<option value="best">Best Available (Auto)</option>';
        data.available_resolutions.forEach((res) => {
          const opt = document.createElement("option");
          opt.value = res;
          opt.textContent = `${res}p HD`;
          if (res === 1080) opt.selected = true;
          selectResolution.appendChild(opt);
        });
      }

      previewCard.classList.remove("hidden");
      previewCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (err) {
      alert(`Error fetching video info: ${err.message}`);
    } finally {
      inspectSpinner.classList.add("hidden");
      inspectText.textContent = "Inspect";
      btnInspect.disabled = false;
    }
  }

  // 4. Toggle Mode (Video / Audio)
  btnModeVideo.addEventListener("click", () => {
    currentMode = "video";
    btnModeVideo.className = "pill-btn active video-active";
    btnModeAudio.className = "pill-btn";
    videoQualityBox.classList.remove("hidden");
    audioFormatBox.classList.add("hidden");
  });

  btnModeAudio.addEventListener("click", () => {
    currentMode = "audio";
    btnModeAudio.className = "pill-btn active audio-active";
    btnModeVideo.className = "pill-btn";
    audioFormatBox.classList.remove("hidden");
    videoQualityBox.classList.add("hidden");
  });

  // 5. Trimmer section toggle
  chkTrim.addEventListener("change", () => {
    if (chkTrim.checked) {
      trimInputsRow.classList.remove("hidden");
    } else {
      trimInputsRow.classList.add("hidden");
    }
  });

  function parseTimeToSeconds(timeStr) {
    if (!timeStr) return null;
    const parts = timeStr.trim().split(":").map(Number);
    if (parts.some(isNaN)) return null;
    if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    } else if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    } else if (parts.length === 1) {
      return parts[0];
    }
    return null;
  }

  // 6. Start Download Job & Listen for SSE
  btnStartDownload.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) return;

    btnStartDownload.disabled = true;
    progressCard.classList.remove("hidden");
    completeCard.classList.add("hidden");
    progressFill.style.width = "0%";
    percentText.textContent = "0.0%";
    phaseText.textContent = "Initializing download...";
    progressCard.scrollIntoView({ behavior: "smooth", block: "nearest" });

    const payload = {
      url: url,
      mode: currentMode,
      quality: selectResolution.value,
      audio_format: selectAudioFormat.value,
      start_time: chkTrim.checked ? parseTimeToSeconds(trimStart.value) : null,
      end_time: chkTrim.checked ? parseTimeToSeconds(trimEnd.value) : null,
    };

    try {
      const resp = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Failed to start download");
      }

      const { job_id } = await resp.json();
      trackProgress(job_id);
    } catch (err) {
      alert(`Download start error: ${err.message}`);
      btnStartDownload.disabled = false;
      progressCard.classList.add("hidden");
    }
  });

  function trackProgress(job_id) {
    if (activeEventSource) {
      activeEventSource.close();
    }

    activeEventSource = new EventSource(`/api/progress/${job_id}`);

    activeEventSource.addEventListener("progress", (e) => {
      const data = JSON.parse(e.data);
      const progress = Math.min(Math.max(data.progress || 0, 0), 100);

      progressFill.style.width = `${progress}%`;
      percentText.textContent = `${progress.toFixed(1)}%`;

      if (data.phase === "downloading") {
        phaseText.textContent = currentMode === "video" ? "Downloading Video & Audio Streams..." : "Downloading Audio Stream...";
      } else if (data.phase === "muxing" || data.phase === "converting") {
        phaseText.textContent = "Muxing & Merging with FFmpeg...";
      }

      // Format Speed
      if (data.speed) {
        const mbps = (data.speed / (1024 * 1024)).toFixed(2);
        statSpeed.textContent = `Speed: ${mbps} MB/s`;
      }

      // Format Size
      if (data.downloaded_bytes && data.total_bytes) {
        const dlMB = (data.downloaded_bytes / (1024 * 1024)).toFixed(1);
        const totMB = (data.total_bytes / (1024 * 1024)).toFixed(1);
        statSize.textContent = `${dlMB} / ${totMB} MB`;
      }

      // Format ETA
      if (data.eta) {
        const m = Math.floor(data.eta / 60);
        const s = data.eta % 60;
        statEta.textContent = `ETA: ${m}:${s < 10 ? "0" : ""}${s}`;
      }

      if (data.status === "completed") {
        activeEventSource.close();
        handleDownloadComplete(data);
      } else if (data.status === "error") {
        activeEventSource.close();
        alert(`Download Error: ${data.error || "Unknown error occurred"}`);
        btnStartDownload.disabled = false;
        progressCard.classList.add("hidden");
      }
    });

    activeEventSource.addEventListener("error", () => {
      activeEventSource.close();
    });
  }

  function handleDownloadComplete(data) {
    btnStartDownload.disabled = false;
    progressCard.classList.add("hidden");
    completeCard.classList.remove("hidden");

    completeFileName.textContent = data.display_name || data.filename;
    downloadedFileUrl = data.download_url;
    btnDownloadFile.href = data.download_url;
    btnDownloadFile.setAttribute("download", data.display_name || data.filename);

    // Auto-trigger browser download dialog
    btnDownloadFile.click();

    // Check Web Share API support
    if (navigator.share) {
      btnShareFile.classList.remove("hidden");
      btnShareFile.onclick = async () => {
        try {
          await navigator.share({
            title: data.display_name,
            url: window.location.origin + data.download_url,
          });
        } catch (e) {
          console.log("Share skipped or canceled:", e);
        }
      };
    }

    completeCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  btnReset.addEventListener("click", () => {
    completeCard.classList.add("hidden");
    previewCard.classList.add("hidden");
    urlInput.value = "";
    urlInput.focus();
  });

  // Register service worker if available
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch((err) => {
      console.log("SW registration notice:", err);
    });
  }

  // Initial check
  checkUrlParams();
});
