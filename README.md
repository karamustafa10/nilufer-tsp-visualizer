# Bursa Nilüfer TSP – Algoritma Görselleştiricisi

Bursa **Nilüfer** mahalleleri üzerinde Travelling Salesman Problem (TSP) için beş optimizasyon algoritmasını gerçek yol ağıyla karşılaştıran etkileşimli web uygulaması.

## Canlı demo

Buradan bakabilirsiniz (kurulum gerekmez):

**https://karamustafa10.github.io/nilufer-tsp-visualizer/**

Ödev 2 (TSP + Genetik Algoritma) sayfası:

**https://karamustafa10.github.io/nilufer-tsp-visualizer/odev2.html**

## Algoritmalar

| Algoritma | Kısa ad |
|-----------|---------|
| Greedy Search (en yakın komşu) | Greedy |
| Particle Swarm Optimization | PSO |
| Ant Colony Optimization | ACO |
| Simulated Annealing | SA |
| Genetic Algorithm | GA |

## Özellikler

- OpenStreetMap yol ağı (OSMnx) ile gerçek rota ve mesafe
- 5 algoritmanın senkron animasyonu (Leaflet haritalar)
- Canlı skor paneli
- Sonuç tablosu + kazanan turun haritası
- Tam ekran destekli HTML/CSS arayüz

## Yerel geliştirme

```powershell
py -3 -m pip install -r requirements.txt
py -3 main.py
```

Sadece `web/data.json` üretmek (Pages demosunu güncellemek için):

```powershell
py -3 main.py --export-only
```

Yerel arayüz: `http://127.0.0.1:8765/index.html` — durdurmak için `Ctrl+C`.

### Kısayollar

- `Space` — oynat / duraklat
- `R` — sonuçları göster
- `Esc` — sonuçlardan yarışa dön

## Proje yapısı

```
main.py                 # Giriş noktası
algorithms/             # Greedy, PSO, ACO, SA, GA
tsp/                    # TSP, yollar, web export
web/                    # Statik arayüz (GitHub Pages)
```

## Notlar

- İlk çalışmada Nilüfer yol ağı indirilir ve `.cache/` altına kaydedilir.
- Mesafe birimi kilometredir (yol üstü en kısa rota).
- `web/data.json` önceden üretilmiş demo verisidir; canlı sayfa bunu kullanır.
