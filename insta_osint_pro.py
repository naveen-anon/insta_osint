import instaloader
import re
import requests
from datetime import datetime
from collections import Counter
from rich.console import Console
from rich.table import Table
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

console = Console()

# ================= TOR / PROXY =================

def tor_session():
    s = requests.Session()
    s.proxies = {
        "http": "socks5h://127.0.0.1:9050",
        "https": "socks5h://127.0.0.1:9050"
    }
    return s

# ================= EXTRACTORS =================

def extract_hashtags(text):
    return re.findall(r"#(\w+)", text) if text else []

def extract_numbers(text):
    return re.findall(r"(?:\+?\d{1,3}[\s\-]?)?\d{10}", text) if text else []

def extract_emails(text):
    return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text) if text else []

# ================= LOCATION =================

KNOWN_LOCATIONS = [
    "india","delhi","mumbai","kolkata","chennai","bangalore",
    "usa","uk","london","canada","dubai","uae","pakistan"
]

def infer_location(text):
    found = []
    if text:
        text = text.lower()
        for loc in KNOWN_LOCATIONS:
            if loc in text:
                found.append(loc.title())
    return list(set(found))

# ================= GMAIL OSINT =================

def generate_gmail_candidates(username, full_name):
    candidates = set()
    clean = re.sub(r"[^a-zA-Z0-9]", "", username.lower())
    candidates.add(f"{clean}@gmail.com")
    candidates.add(f"{clean}123@gmail.com")

    if "_" in username:
        p = username.split("_")
        candidates.add(f"{p[0]}.{p[-1]}@gmail.com")

    if full_name:
        n = full_name.lower().split()
        if len(n) >= 2:
            candidates.add(f"{n[0]}{n[-1]}@gmail.com")
            candidates.add(f"{n[0]}.{n[-1]}@gmail.com")

    return sorted(candidates)

# ================= USERNAME FOOTPRINT =================

PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "Twitter": "https://twitter.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "Telegram": "https://t.me/{}"
}

def username_footprint(username, use_tor=False):
    found = {}
    session = tor_session() if use_tor else requests
    for name, url in PLATFORMS.items():
        try:
            r = session.get(url.format(username), timeout=8)
            if r.status_code == 200:
                found[name] = url.format(username)
        except:
            pass
    return found

# ================= ANALYSIS =================

def engagement_ratio(posts, followers):
    if not posts or followers == 0:
        return 0
    avg = sum(p.likes for p in posts) / len(posts)
    return round((avg / followers) * 100, 2)

def scam_score(profile):
    score = 0
    if profile.followers < 100: score += 2
    if profile.mediacount < 3: score += 2
    if profile.followees > profile.followers * 3: score += 2
    if not profile.biography: score += 1
    return min(score, 10)

# ================= PDF REPORT =================

def generate_pdf(username, data):
    file = f"{username}_OSINT_Report.pdf"
    c = canvas.Canvas(file, pagesize=A4)
    w, h = A4
    y = h - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Instagram OSINT Report")
    y -= 30
    c.setFont("Helvetica", 11)

    for k, v in data.items():
        c.drawString(40, y, f"{k}: {v}")
        y -= 18
        if y < 50:
            c.showPage()
            y = h - 40

    c.save()
    return file

# ================= MAIN OSINT =================

def instagram_osint(username, use_tor=False):
    L = instaloader.Instaloader(download_pictures=False, save_metadata=False)
    profile = instaloader.Profile.from_username(L.context, username)

    if profile.is_private:
        console.print("[red]Private account — OSINT limited[/red]")
        return

    console.rule("[bold cyan]INSTAGRAM OSINT ULTIMATE")

    console.print(f"[green]Username:[/green] {profile.username}")
    console.print(f"[green]Name:[/green] {profile.full_name}")
    console.print(f"[green]Followers:[/green] {profile.followers}")
    console.print(f"[green]Following:[/green] {profile.followees}")
    console.print(f"[green]Posts:[/green] {profile.mediacount}")

    hashtags, emails, numbers, locations = [], set(), set(), []

    posts, excel_rows = [], []

    for i, post in enumerate(profile.get_posts(), start=1):
        if i > 6: break
        posts.append(post)

        if post.caption:
            hashtags += extract_hashtags(post.caption)
            emails.update(extract_emails(post.caption))
            numbers.update(extract_numbers(post.caption))
            locations += infer_location(post.caption)

        excel_rows.append([post.date_utc.strftime("%Y-%m-%d"), post.likes, post.comments])

    er = engagement_ratio(posts, profile.followers)
    risk = scam_score(profile)

    console.rule("[bold yellow]Analysis")
    console.print(f"Engagement Ratio : [cyan]{er}%[/cyan]")
    console.print(f"Scam Risk Score  : [red]{risk}/10[/red]")

    # ---------- Gmail ----------
    console.rule("[bold magenta]Possible Gmail Accounts (OSINT)")
    for g in generate_gmail_candidates(profile.username, profile.full_name):
        console.print(f"[green]{g}[/green]")

    # ---------- Location ----------
    if locations:
        console.print("\n[bold green]Possible Locations:[/bold green]", ", ".join(set(locations)))

    # ---------- Footprint ----------
    console.rule("[bold cyan]Username Footprint")
    fp = username_footprint(username, use_tor)
    if fp:
        for k, v in fp.items():
            console.print(f"{k}: {v}")
    else:
        console.print("[yellow]No footprint found[/yellow]")

    # ---------- Excel ----------
    wb = Workbook()
    ws = wb.active
    ws.append(["Date", "Likes", "Comments"])
    for r in excel_rows:
        ws.append(r)
    excel_file = f"{username}_posts.xlsx"
    wb.save(excel_file)

    # ---------- PDF ----------
    pdf_data = {
        "Username": profile.username,
        "Full Name": profile.full_name,
        "Followers": profile.followers,
        "Following": profile.followees,
        "Posts": profile.mediacount,
        "Engagement Ratio": f"{er}%",
        "Scam Risk Score": f"{risk}/10",
        "Emails Found": ", ".join(emails),
        "Phone Numbers": ", ".join(numbers),
        "Locations": ", ".join(set(locations))
    }

    pdf_file = generate_pdf(username, pdf_data)

    console.print(f"\n[bold green]✔ Excel saved:[/bold green] {excel_file}")
    console.print(f"[bold green]✔ PDF saved:[/bold green] {pdf_file}")

# ================= MENU =================

def menu():
    while True:
        console.print("""
[bold cyan]
====================================
 INSTAGRAM OSINT ULTIMATE
====================================
1. Run OSINT Scan (Normal)
2. Run OSINT Scan (TOR)
3. Exit
====================================
[/bold cyan]
""")
        ch = input("Select option: ").strip()
        if ch == "1":
            u = input("Enter Instagram username: ").strip()
            instagram_osint(u, False)
        elif ch == "2":
            u = input("Enter Instagram username: ").strip()
            instagram_osint(u, True)
        elif ch == "3":
            console.print("[green]Bye 👋[/green]")
            break
        else:
            console.print("[red]Invalid option[/red]")

# ================= RUN =================

if __name__ == "__main__":
    menu()
