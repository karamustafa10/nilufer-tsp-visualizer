const state = {
  data: null,
  frame: 0,
  playing: true,
  timer: null,
};

const els = {
  play: document.getElementById("btn-play"),
  slider: document.getElementById("frame-slider"),
  frameLabel: document.getElementById("frame-label"),
  meta: document.getElementById("chart-meta"),
  stats: document.getElementById("stats-line"),
  params: document.getElementById("params-line"),
  result: document.getElementById("result-line"),
  canvas: document.getElementById("bar-chart"),
  tbody: document.querySelector("#items-table tbody"),
};

function drawChart(selectedSet) {
  const data = state.data;
  if (!data) return;
  const items = data.problem.items;
  const canvas = els.canvas;
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth || 720;
  const cssH = 320;
  canvas.width = Math.round(cssW * dpr);
  canvas.height = Math.round(cssH * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);

  const padL = 36;
  const padR = 12;
  const padT = 18;
  const padB = 36;
  const plotW = cssW - padL - padR;
  const plotH = cssH - padT - padB;
  const maxRatio = Math.max(...items.map((it) => it.ratio), 0.01);
  const barGap = 4;
  const barW = Math.max(6, (plotW - barGap * (items.length - 1)) / items.length);

  // Eksen çizgisi
  ctx.strokeStyle = "rgba(154,175,163,0.35)";
  ctx.beginPath();
  ctx.moveTo(padL, padT + plotH);
  ctx.lineTo(padL + plotW, padT + plotH);
  ctx.stroke();

  items.forEach((it, i) => {
    const h = (it.ratio / maxRatio) * plotH;
    const x = padL + i * (barW + barGap);
    const y = padT + plotH - h;
    const selected = selectedSet.has(it.id);
    ctx.fillStyle = selected ? "#66bb6a" : "#4a6356";
    ctx.fillRect(x, y, barW, h);

    ctx.fillStyle = selected ? "#edf3ee" : "#9aafa3";
    ctx.font = "10px DM Sans, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(String(it.id + 1), x + barW / 2, padT + plotH + 14);
  });

  ctx.fillStyle = "#9aafa3";
  ctx.font = "11px DM Sans, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("Değer / ağırlık oranı  ·  yeşil = seçildi", padL, 12);
}

function renderTable(selectedSet) {
  const items = state.data.problem.items;
  const unitW = state.data.problem.unit_weight;
  const unitV = state.data.problem.unit_value;
  els.tbody.innerHTML = items
    .map((it) => {
      const selected = selectedSet.has(it.id);
      return `<tr class="${selected ? "is-selected" : ""}">
        <td><span class="mark" aria-hidden="true"></span></td>
        <td>${it.label}</td>
        <td>${it.weight.toFixed(1)} ${unitW}</td>
        <td>${it.value.toFixed(0)} ${unitV}</td>
        <td>${it.ratio.toFixed(2)}</td>
      </tr>`;
    })
    .join("");
}

function renderFrame(frame) {
  const { data } = state;
  if (!data) return;
  const f = data.frames[frame];
  state.frame = frame;
  els.slider.value = String(frame);
  els.frameLabel.textContent = `${frame + 1} / ${data.frames.length}`;

  const selectedSet = new Set(f.selected);
  drawChart(selectedSet);
  renderTable(selectedSet);

  const p = data.problem;
  els.stats.textContent =
    `Toplam ${f.value.toFixed(0)} ${p.unit_value}  ·  ${f.weight.toFixed(1)} / ${p.capacity.toFixed(1)} ${p.unit_weight}`;
  els.meta.textContent = `İterasyon ${f.iteration} · ${f.info}`;
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
  const res = await fetch("odev3-data.json", { cache: "no-store" });
  if (!res.ok) throw new Error("odev3-data.json bulunamadı. py -3 main.py --export-odev3 çalıştırın.");
  const data = await res.json();
  state.data = data;

  const p = data.params;
  els.params.textContent =
    `Parametreler: karınca=${p.n_ants}, iterasyon=${p.n_iterations}, ` +
    `α=${p.alpha}, β=${p.beta}, ρ=${p.rho}, Q=${p.q}`;

  const pr = data.problem;
  els.result.textContent =
    `Bulunan en iyi seçim: ${data.final_value.toFixed(0)} ${pr.unit_value} ` +
    `(${data.final_weight.toFixed(1)} / ${pr.capacity.toFixed(1)} ${pr.unit_weight}, ` +
    `${data.final_iterations} iterasyon, ${data.elapsed_sec.toFixed(3)} s)`;

  els.slider.max = String(data.frames.length - 1);
  renderFrame(0);
  state.timer = setInterval(tick, data.interval_ms || 140);
  window.addEventListener("resize", () => {
    const f = data.frames[state.frame];
    drawChart(new Set(f.selected));
  });
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
