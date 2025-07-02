#  Saphy v2.0 - Firepower Edition

**Saphy** is a high-performance, modular Layer 4 and Layer 7 **DDoS testing tool** developed for educational and research purposes. 

---

## 🚀 Features

- ✅ **Layer 4 & Layer 7 DDoS Modules**
- 🌐 **Cloudflare Bypass** via `cloudscraper`
- 🧠 **Dynamic Attack Mode Suggestion System**
- 🦾 **Multiple Attack Modes**, including:
  - Random URI Flood
  - Slowloris
  - User-Agent Swarm
  - Cache Bypass Flood
  - POST Data Flood
  - Cookie Bomb
  - Random Method Flood
  - Referer Spam
  - HEAD Flood
  - Headless Browser Flood (Planned)
- 📊 **Real-Time Stats Dashboard**
- 🌍 **Rotating Proxies** & **User-Agent Spoofing**
- 🔐 **Botnets & OSINT Scraping (Coming Soon)**

---

## 📦 Requirements

- Python 3.8+
- `requests`, `cloudscraper`, `colorama`, `aiohttp`, `beautifulsoup4`, etc.
- Linux or Termux recommended (Windows partially supported)

```bash
git clone https://github.com/Lynss-09/saphy
cd saphy
pip install -r requirements.txt
python3 main.py
