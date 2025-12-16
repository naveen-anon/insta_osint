# 📸 Instagram OSINT Pro Tool

A **professional, ethical Instagram OSINT (Open Source Intelligence) tool** built with Python and Instaloader.  
This tool analyzes **publicly available Instagram profile data only** — no hacking, no brute force, no private access.

---

## 🚀 Features

- 📄 Public profile information extraction  
- 📧 Email extractor (bio & captions)  
- 📞 Phone number extractor (bio, captions, WhatsApp/Telegram links)  
- 📊 Engagement ratio calculation  
- 🕵️ Fake / Scam profile risk scoring  
- 📁 CSV export (Excel compatible)  
- 🖥 Menu-based CLI (clean & professional)  
- 📱 Works on **Termux, Linux, and Windows**

---

## ⚠️ Disclaimer

> This project is for **educational and ethical OSINT purposes only**.
>
> - Works **ONLY on public Instagram profiles**
> - Does **NOT** bypass login, security, or privacy
> - The author is **not responsible for misuse**

Always respect local laws and platform terms of service.

---

## 🛠 Requirements

- Python **3.9 or higher**
- Internet connection
- Basic command-line knowledge

---

## 📦 Installation

### 🔹 Termux (Android)

Update packages and install dependencies:

```bash
pkg update && pkg upgrade -y
pkg install python git -y
pip install --upgrade pip
pip install instaloader
git clone https://github.com/naveen-anon/insta_osint.git
cd instagram-osint-pro
python3 instagram-osint-pro.py

> - made by @naveen_anon 
