# Bursa Nilüfer TSP – Algoritma Görselleştiricisi

Bursa **Nilüfer** mahalleleri üzerinde Travelling Salesman Problem (TSP) için beş optimizasyon algoritmasını gerçek yol ağıyla karşılaştıran etkileşimli web uygulaması.

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
- Sonuç tablosu + kazanan turun haritası (pencere kapatmadan)
- Tam ekran destekli HTML/CSS arayüz

## Kurulum

```powershell
py -3 -m pip install -r requirements.txt
```

## Çalıştırma

```powershell
py -3 main.py
```

Program algoritmaları çalıştırır, `web/data.json` üretir ve tarayıcıda arayüzü açar:

`http://127.0.0.1:8765/index.html`

Durdurmak için terminalde `Ctrl+C`.

### Kısayollar

- `Space` — oynat / duraklat
- `R` — sonuçları göster
- `Esc` — sonuçlardan yarışa dön

## Proje yapısı

```
main.py                 # Giriş noktası
algorithms/             # Greedy, PSO, ACO, SA, GA
tsp/
  geo.py                # Nilüfer konumları, haversine
  roads.py              # OSM yol ağı ve rota geometrisi
  problem.py            # TSP problemi
  web_export.py         # JSON veri üretimi
  webapp.py             # Yerel HTTP sunucu
web/                    # HTML / CSS / JS arayüz
```

## Notlar

- İlk çalışmada Nilüfer yol ağı indirilir ve `.cache/` altına kaydedilir.
- Mesafe birimi kilometredir (yol üstü en kısa rota).
- Ödev kapsamında incelenen kütüphaneler: scikit-opt, MEALPY; bu demoda eğitim amaçlı sıfırdan implementasyon + OSMnx kullanılmıştır.
