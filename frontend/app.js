// Clean Stream Ripper - Frontend Logic with In-App Search & Embedded Viewer
document.addEventListener("DOMContentLoaded", () => {
  const urlInput = document.getElementById("urlInput");
  const btnPaste = document.getElementById("btnPaste");
  const btnInspect = document.getElementById("btnInspect");
  const inspectSpinner = document.getElementById("inspectSpinner");
  const inspectText = document.getElementById("inspectText");

  // Search results elements
  const searchCard = document.getElementById("searchCard");
  const searchResultsList = document.getElementById("searchResultsList");
  const btnCloseSearch = document.getElementById("btnCloseSearch");

  // Preview elements
  const previewCard = document.getElementById("previewCard");
  const metaTitle = document.getElementById("metaTitle");
  const channelName = document.getElementById("channelName");
  const metaDurationText = document.getElementById("metaDurationText");

  // Mode and format selectors
  const btnModeVideo = document.getElementById("btnModeVideo");
  const btnModeAudio = document.getElementById("btnModeAudio");
  const videoQualityBox = document.getElementById("videoQualityBox");
  const audioFormatBox = document.getElementById("audioFormatBox");
  const selectResolution = document.getElementById("selectResolution");
  const selectAudioFormat = document.getElementById("selectAudioFormat");

  // Trimmer elements
  const chkTrim = document.getElementById("chkTrim");
  const trimInputsRow = document.getElementById("trimInputsRow");
  const trimStart = document.getElementById("trimStart");
  const trimEnd = document.getElementById("trimEnd");
  const btnSetStartCurrent = document.getElementById("btnSetStartCurrent");
  const btnSetEndCurrent = document.getElementById("btnSetEndCurrent");
  const btnPreviewTrim = document.getElementById("btnPreviewTrim");

  // Download & Progress elements
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
  const completeFilePath = document.getElementById("completeFilePath");
  const btnOpenFolder = document.getElementById("btnOpenFolder");
  const btnOpenFile = document.getElementById("btnOpenFile");
  const btnDownloadFile = document.getElementById("btnDownloadFile");
  const btnReset = document.getElementById("btnReset");

  let currentMode = "video";
  let activeEventSource = null;
  let ytPlayer = null;
  let isPlayerApiReady = false;
  let auditionInterval = null;
  let lastCompletedFile = null;

  btnOpenFolder.addEventListener("click", async () => {
    try {
      await fetch("/api/open-folder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: lastCompletedFile }),
      });
    } catch (e) {
      console.error(e);
    }
  });

  btnOpenFile.addEventListener("click", async () => {
    try {
      await fetch("/api/open-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: lastCompletedFile }),
      });
    } catch (e) {
      console.error(e);
    }
  });

  // Window callback for YouTube IFrame API
  window.onYouTubeIframeAPIReady = () => {
    isPlayerApiReady = true;
  };

  // 1. Dynamic Input Label: Change button to "Search" if text isn't a direct URL
  function isDirectUrl(val) {
    return /^https?:\/\//i.test(val.trim()) || /youtu\.?be/i.test(val.trim());
  }

  urlInput.addEventListener("input", () => {
    const val = urlInput.value.trim();
    if (!val) {
      inspectText.textContent = "Inspect";
    } else if (isDirectUrl(val)) {
      inspectText.textContent = "Inspect";
    } else {
      inspectText.textContent = "Search";
    }
  });

  // 2. Clipboard Paste Handler
  btnPaste.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        urlInput.value = text.trim();
        urlInput.dispatchEvent(new Event("input"));
        handleInspectOrSearch();
      }
    } catch (err) {
      urlInput.focus();
    }
  });

  // 3. Inspect or Search Action
  function handleInspectOrSearch() {
    const val = urlInput.value.trim();
    if (!val) {
      urlInput.focus();
      return;
    }

    if (isDirectUrl(val)) {
      searchCard.classList.add("hidden");
      inspectVideo(val);
    } else {
      performSearch(val);
    }
  }

  btnInspect.addEventListener("click", handleInspectOrSearch);
  urlInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleInspectOrSearch();
  });

  // 4. In-App YouTube Search
  async function performSearch(query) {
    inspectSpinner.classList.remove("hidden");
    inspectText.textContent = "Searching...";
    btnInspect.disabled = true;
    previewCard.classList.add("hidden");
    progressCard.classList.add("hidden");
    completeCard.classList.add("hidden");

    try {
      const resp = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit: 6 }),
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Search failed");
      }

      const { results } = await resp.json();
      renderSearchResults(results);
    } catch (err) {
      alert(`Search error: ${err.message}`);
    } finally {
      inspectSpinner.classList.add("hidden");
      inspectText.textContent = "Search";
      btnInspect.disabled = false;
    }
  }

  function renderSearchResults(results) {
    searchResultsList.innerHTML = "";
    if (!results || results.length === 0) {
      searchResultsList.innerHTML = `<div style="padding: 16px; text-align: center; color: var(--text-faint);">No videos found for query.</div>`;
      searchCard.classList.remove("hidden");
      return;
    }

    results.forEach((item) => {
      const div = document.createElement("div");
      div.className = "search-result-item";
      div.innerHTML = `
        <div class="search-item-thumb-box">
          <img class="search-item-thumb" src="${item.thumbnail}" alt="" loading="lazy">
          <span class="search-item-dur">${item.duration_str}</span>
        </div>
        <div class="search-item-info">
          <div class="search-item-title">${item.title}</div>
          <div class="search-item-channel">${item.channel}</div>
        </div>
      `;

      div.addEventListener("click", () => {
        urlInput.value = item.url;
        urlInput.dispatchEvent(new Event("input"));
        searchCard.classList.add("hidden");
        inspectVideo(item.url);
      });

      searchResultsList.appendChild(div);
    });

    searchCard.classList.remove("hidden");
    searchCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  btnCloseSearch.addEventListener("click", () => {
    searchCard.classList.add("hidden");
  });

  // 5. Inspect Video & Initialize Embedded Viewer
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
      metaDurationText.textContent = data.duration_str;
      trimStart.value = "00:00:00";
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

      // Initialize or load video into YouTube Embedded Player
      initOrLoadPlayer(data.id);

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

  function initOrLoadPlayer(videoId) {
    if (ytPlayer && typeof ytPlayer.loadVideoById === "function") {
      ytPlayer.loadVideoById(videoId);
    } else {
      ytPlayer = new YT.Player("ytPlayer", {
        height: "100%",
        width: "100%",
        videoId: videoId,
        playerVars: {
          autoplay: 0,
          controls: 1,
          modestbranding: 1,
          rel: 0,
          fs: 1,
        },
      });
    }
  }

  // 6. Time Formatting & Trimmer Sync Helpers
  function formatSeconds(sec) {
    const total = Math.floor(sec || 0);
    const s = total % 60;
    const m = Math.floor(total / 60) % 60;
    const h = Math.floor(total / 3600);
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }

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

  btnSetStartCurrent.addEventListener("click", () => {
    if (ytPlayer && typeof ytPlayer.getCurrentTime === "function") {
      const curr = ytPlayer.getCurrentTime();
      trimStart.value = formatSeconds(curr);
    }
  });

  btnSetEndCurrent.addEventListener("click", () => {
    if (ytPlayer && typeof ytPlayer.getCurrentTime === "function") {
      const curr = ytPlayer.getCurrentTime();
      trimEnd.value = formatSeconds(curr);
    }
  });

  // Audition / Test Play the trimmed segment in the viewer
  btnPreviewTrim.addEventListener("click", () => {
    if (!ytPlayer || typeof ytPlayer.seekTo !== "function") return;

    if (auditionInterval) {
      clearInterval(auditionInterval);
      auditionInterval = null;
    }

    const startSec = parseTimeToSeconds(trimStart.value) || 0;
    const endSec = parseTimeToSeconds(trimEnd.value);

    ytPlayer.seekTo(startSec, true);
    ytPlayer.playVideo();

    if (endSec && endSec > startSec) {
      auditionInterval = setInterval(() => {
        if (ytPlayer && typeof ytPlayer.getCurrentTime === "function") {
          const curr = ytPlayer.getCurrentTime();
          if (curr >= endSec) {
            ytPlayer.pauseVideo();
            clearInterval(auditionInterval);
            auditionInterval = null;
          }
        }
      }, 250);
    }
  });

  // 7. Toggle Mode (Video / Audio)
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

  // 8. Trimmer section toggle
  chkTrim.addEventListener("change", () => {
    if (chkTrim.checked) {
      trimInputsRow.classList.remove("hidden");
    } else {
      trimInputsRow.classList.add("hidden");
    }
  });

  // 9. Start Download Job & Listen for SSE
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

    // Pause player if playing
    if (ytPlayer && typeof ytPlayer.pauseVideo === "function") {
      ytPlayer.pauseVideo();
    }

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

    lastCompletedFile = data.filename;
    completeFileName.textContent = data.display_name || data.filename;
    completeFilePath.textContent = `📁 ${data.full_path || "Downloads\\Clean Stream Ripper"}`;

    if (data.download_url) {
      btnDownloadFile.href = data.download_url;
      btnDownloadFile.setAttribute("download", data.display_name || data.filename);
    }

    completeCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  btnReset.addEventListener("click", () => {
    completeCard.classList.add("hidden");
    previewCard.classList.add("hidden");
    urlInput.value = "";
    urlInput.dispatchEvent(new Event("input"));
    urlInput.focus();
  });
});
