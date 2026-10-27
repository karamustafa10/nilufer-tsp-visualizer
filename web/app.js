/* global L */

const state = {
  data: null,
  frame: 0,
  playing: true,
  timer: null,
  maps: [],
  routes: [],
  winnerMap: null,
  winnerRoute: null,
  resultsOpen: false,
};

const els = {
  maps: document.getElementById("maps"),
  scores: document.getElementById("live-scores"),
  status: document.getElementById("status-line"),
  slider: document.getElementById("frame-slider"),
  frameLabel: document.getElementById("frame-label"),
  btnPlay: document.getElementById("btn-play"),
  btnResults: document.getElementById("btn-results"),
  btnFullscreen: document.getElementById("btn-fullscreen"),
  btnBack: document.getElementById("btn-back"),
  raceView: document.getElementById("race-view"),
  resultsView: document.getElementById("results-view"),
  resultsTable: document.querySelector("#results-table tbody"),
  winnerTitle: document.getElementById("winner-title"),
};

function tileLayer() {
  // Esri: API anahtari gerektirmez; OSM bazi ortamlarda 403 verebiliyor
  return L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    {
      maxZoom: 18,
      attribution: "Tiles &copy; Esri",
    }
  );
}

function fitBounds(map, bounds) {
  map.fitBounds([
    [bounds.south, bounds.west],
    [bounds.north, bounds.east],
  ]);
}

function createMapCard(algo, bounds, points) {
  const card = document.createElement("article");
  card.className = "map-card";
  card.innerHTML = `
    <h3 class="card-title" style="color:${algo.color}">${algo.name}</h3>
    <p class="card-meta">…</p>
    <div class="map-el"></div>
  `;
  const mapEl = card.querySelector(".map-el");
  mapEl.style.height = "100%";
  els.maps.appendChild(card);

  const map = L.map(mapEl, {
    zoomControl: false,
    attributionControl: false,
    dragging: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    boxZoom: false,
    keyboard: false,
  });
  tileLayer().addTo(map);
  fitBounds(map, bounds);

  points.forEach((p) => {
    L.circleMarker([p.lat, p.lon], {
      radius: 5,
      color: "#fff",
      weight: 1.5,
      fillColor: "#1d4f7a",
      fillOpacity: 1,
    })
      .bindTooltip(p.label, { direction: "top", offset: [0, -6] })
      .addTo(map);
  });

  const route = L.polyline([], {
    color: algo.color,
    weight: 4,
    opacity: 0.92,
  }).addTo(map);

  return {
    card,
    map,
    route,
    meta: card.querySelector(".card-meta"),
    name: algo.name,
    color: algo.color,
  };
}

function renderFrame(frame) {
  const { data } = state;
  if (!data) return;
  state.frame = frame;
  els.slider.value = String(frame);
  els.frameLabel.textContent = `${frame + 1} / ${data.meta.n_frames}`;

  const scores = data.algorithms
    .map((algo, i) => {
      const f = algo.frames[frame];
      state.routes[i].setLatLngs(f.route || []);
      state.maps[i].meta.textContent = `iter ${f.iteration}\nen iyi ${f.best_cost.toFixed(2)} ${data.meta.unit}`;
      return {
        name: algo.name,
        color: algo.color,
        cost: f.best_cost,
      };
    })
    .sort((a, b) => a.cost - b.cost);

  els.scores.innerHTML = scores
    .map(
      (s, idx) => `
      <li>
        <span class="rank" style="outline:2px solid ${s.color}">${idx + 1}</span>
        <span class="name">${s.name}</span>
        <span class="cost">${s.cost.toFixed(2)} ${data.meta.unit}</span>
      </li>`
    )
    .join("");

  els.status.textContent = `Lider: ${scores[0].name} · ${scores[0].cost.toFixed(2)} ${data.meta.unit}`;
}

function tick() {
  if (!state.data || !state.playing || state.resultsOpen) return;
  const next = state.frame + 1;
  if (next >= state.data.meta.n_frames) {
    state.playing = false;
    els.btnPlay.textContent = "Oynat";
    els.status.textContent = "Animasyon bitti — Sonuçları Göster’e tıklayın";
    els.btnResults.classList.add("pulse");
    return;
  }
  renderFrame(next);
}

function startTimer() {
  clearInterval(state.timer);
  const ms = state.data?.meta?.interval_ms || 140;
  state.timer = setInterval(tick, ms);
}

function showResults() {
  const { data } = state;
  if (!data) return;
  state.resultsOpen = true;
  state.playing = false;
  els.btnPlay.textContent = "Oynat";

  // Leaflet pane'leri z-index ile uste cikmasin diye yaris haritalarini tamamen gizle
  els.raceView.classList.add("is-hidden");
  els.resultsView.classList.remove("hidden");
  els.resultsView.setAttribute("aria-hidden", "false");
  els.btnResults.textContent = "Yarışa Dön";
  els.btnResults.classList.remove("pulse");

  const ranked = [...data.algorithms].sort((a, b) => a.final_cost - b.final_cost);
  els.resultsTable.innerHTML = ranked
    .map(
      (a, i) => `
      <tr class="${i === 0 ? "winner" : ""}">
        <td>${i + 1}</td>
        <td><span class="swatch" style="background:${a.color}"></span>${a.name}</td>
        <td>${a.final_cost.toFixed(2)} ${data.meta.unit}</td>
        <td>${a.final_iterations}</td>
        <td>${a.elapsed_sec.toFixed(3)} s</td>
      </tr>`
    )
    .join("");

  const winner = ranked[0];
  els.winnerTitle.textContent = `En iyi tur: ${winner.name} (${winner.final_cost.toFixed(2)} ${data.meta.unit})`;

  requestAnimationFrame(() => {
    if (!state.winnerMap) {
      state.winnerMap = L.map("winner-map", {
        zoomControl: true,
        attributionControl: true,
      });
      tileLayer().addTo(state.winnerMap);
      data.points.forEach((p) => {
        L.circleMarker([p.lat, p.lon], {
          radius: 6,
          color: "#fff",
          weight: 1.5,
          fillColor: "#1d4f7a",
          fillOpacity: 1,
        })
          .bindTooltip(p.label)
          .addTo(state.winnerMap);
      });
      state.winnerRoute = L.polyline([], { color: winner.color, weight: 5 }).addTo(state.winnerMap);
    }
    state.winnerRoute.setStyle({ color: winner.color });
    state.winnerRoute.setLatLngs(winner.final_route || []);
    fitBounds(state.winnerMap, data.bounds);
    // Panel acildiktan sonra boyut olcumu
    [50, 150, 300].forEach((ms) => {
      setTimeout(() => {
        if (state.winnerMap) state.winnerMap.invalidateSize();
      }, ms);
    });
  });
}

function hideResults() {
  state.resultsOpen = false;
  els.resultsView.classList.add("hidden");
  els.resultsView.setAttribute("aria-hidden", "true");
  els.raceView.classList.remove("is-hidden");
  els.btnResults.textContent = "Sonuçları Göster";
  state.maps.forEach((m) => {
    [40, 120].forEach((ms) => setTimeout(() => m.map.invalidateSize(), ms));
  });
}

async function enterFullscreen() {
  const root = document.documentElement;
  if (!document.fullscreenElement) {
    try {
      await root.requestFullscreen();
      els.btnFullscreen.textContent = "Çık";
    } catch (_) {
      /* tarayici engelleyebilir */
    }
  } else {
    await document.exitFullscreen();
    els.btnFullscreen.textContent = "Tam Ekran";
  }
}

async function boot() {
  els.status.textContent = "Veri yükleniyor…";
  const res = await fetch("data.json", { cache: "no-store" });
  if (!res.ok) throw new Error("data.json bulunamadı. Önce python main.py çalıştırın.");
  const data = await res.json();
  state.data = data;

  document.title = `${data.meta.region} – TSP`;
  document.querySelector(".brand h1").textContent = data.meta.region.replace(" (gercek yollar)", "");
  document.querySelector(".eyebrow").textContent =
    `${data.meta.n_points} nokta · gerçek yollar · seed ${data.meta.seed}`;

  els.slider.max = String(data.meta.n_frames - 1);
  els.maps.innerHTML = "";
  state.maps = [];
  state.routes = [];

  data.algorithms.forEach((algo) => {
    const created = createMapCard(algo, data.bounds, data.points);
    state.maps.push(created);
    state.routes.push(created.route);
  });

  // 6. kart yok; scoreboard yan panelde
  setTimeout(() => state.maps.forEach((m) => m.map.invalidateSize()), 80);

  renderFrame(0);
  startTimer();
  els.status.textContent = "Animasyon oynatılıyor";

  // Tarayicilar jest olmadan fullscreen'i engelleyebilir; yine de dene
  enterFullscreen();
}

els.btnPlay.addEventListener("click", () => {
  state.playing = !state.playing;
  els.btnPlay.textContent = state.playing ? "Duraklat" : "Oynat";
  if (state.playing && state.resultsOpen) hideResults();
});

els.slider.addEventListener("input", (e) => {
  state.playing = false;
  els.btnPlay.textContent = "Oynat";
  renderFrame(Number(e.target.value));
});

els.btnResults.addEventListener("click", () => {
  if (state.resultsOpen) hideResults();
  else showResults();
});
els.btnBack.addEventListener("click", hideResults);
els.btnFullscreen.addEventListener("click", enterFullscreen);

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && state.resultsOpen) hideResults();
  if (e.key === " " && e.target === document.body) {
    e.preventDefault();
    els.btnPlay.click();
  }
  if ((e.key === "r" || e.key === "R") && !state.resultsOpen) showResults();
});

document.addEventListener("fullscreenchange", () => {
  els.btnFullscreen.textContent = document.fullscreenElement ? "Çık" : "Tam Ekran";
  state.maps.forEach((m) => setTimeout(() => m.map.invalidateSize(), 80));
  if (state.winnerMap) setTimeout(() => state.winnerMap.invalidateSize(), 80);
});

boot().catch((err) => {
  els.status.textContent = String(err.message || err);
  console.error(err);
});
