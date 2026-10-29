/* global L */

const state = {
  data: null,
  frame: 0,
  playing: true,
  timer: null,
  map: null,
  route: null,
};

const els = {
  play: document.getElementById("btn-play"),
  slider: document.getElementById("frame-slider"),
  frameLabel: document.getElementById("frame-label"),
  meta: document.getElementById("map-meta"),
  params: document.getElementById("params-line"),
  result: document.getElementById("result-line"),
};

function tileLayer() {
  return L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    { maxZoom: 18, attribution: "Tiles &copy; Esri" }
  );
}

function renderFrame(frame) {
  const { data } = state;
  if (!data) return;
  const frames = data.frames;
  const f = frames[frame];
  state.frame = frame;
  els.slider.value = String(frame);
  els.frameLabel.textContent = `${frame + 1} / ${frames.length}`;
  state.route.setLatLngs(f.route || []);
  els.meta.textContent =
    `Nesil ${f.iteration} · bu nesil ${f.cost.toFixed(2)} ${data.unit} · en iyi ${f.best_cost.toFixed(2)} ${data.unit}`;
}

function tick() {
  if (!state.playing || !state.data) return;
  const next = state.frame + 1;
  if (next >= state.data.frames.length) {
    state.playing = false;
    els.play.textContent = "Oynat";
    return;
  }
  renderFrame(next);
}

async function boot() {
  const res = await fetch("odev2-data.json", { cache: "no-store" });
  if (!res.ok) throw new Error("odev2-data.json bulunamadı. py -3 main.py --export-odev2 çalıştırın.");
  const data = await res.json();
  state.data = data;

  els.params.textContent =
    `Parametreler: popülasyon=${data.params.population_size}, nesil=${data.params.n_generations}, ` +
    `çaprazlama=${data.params.crossover_rate}, mutasyon=${data.params.mutation_rate}, ` +
    `turnuva=${data.params.tournament_size}, elitizm=${data.params.elitism}`;

  els.result.textContent =
    `Bulunan en iyi tur: ${data.final_cost.toFixed(2)} ${data.unit} ` +
    `(${data.final_iterations} nesil, ${data.elapsed_sec.toFixed(3)} s)`;

  els.slider.max = String(data.frames.length - 1);

  const map = L.map("map", { zoomControl: true });
  tileLayer().addTo(map);
  data.points.forEach((p) => {
    L.circleMarker([p.lat, p.lon], {
      radius: 6,
      color: "#fff",
      weight: 1.5,
      fillColor: "#1d4f7a",
      fillOpacity: 1,
    })
      .bindTooltip(p.label)
      .addTo(map);
  });
  const route = L.polyline([], { color: "#66bb6a", weight: 4.5, opacity: 0.95 }).addTo(map);
  map.fitBounds([
    [data.bounds.south, data.bounds.west],
    [data.bounds.north, data.bounds.east],
  ]);
  state.map = map;
  state.route = route;

  renderFrame(0);
  state.timer = setInterval(tick, data.interval_ms || 120);
  setTimeout(() => map.invalidateSize(), 80);
}

els.play.addEventListener("click", () => {
  state.playing = !state.playing;
  els.play.textContent = state.playing ? "Duraklat" : "Oynat";
});

els.slider.addEventListener("input", (e) => {
  state.playing = false;
  els.play.textContent = "Oynat";
  renderFrame(Number(e.target.value));
});

boot().catch((err) => {
  els.meta.textContent = String(err.message || err);
  console.error(err);
});
