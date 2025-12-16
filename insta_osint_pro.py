import instaloader
import re
import csv
from datetime import datetime

# ================== EXTRACTORS ==================

def extract_hashtags(text):
    return re.findall(r"#(\w+)", text) if text else []

def extract_numbers(text):
    pattern = r"(?:\+?\d{1,3}[\s\-]?)?\d{10}"
    return re.findall(pattern, text) if text else []

def extract_emails(text):
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, text) if text else []

def extract_numbers_from_links(text):
    pattern = r"(?:wa\.me\/|t\.me\/\+?)(\d{10,13})"
    return re.findall(pattern, text) if text else []

# ================== SCAM SCORE ==================

def scam_score(profile):
    score = 0

    if profile.followers < 100:
        score += 2
    if profile.mediacount < 3:
        score += 2
    if profile.followees > profile.followers * 3:
        score += 2
    if not profile.biography:
        score += 1
    if not profile.profile_pic_url:
        score += 1

    return min(score, 10)

# ================== ENGAGEMENT ==================

def engagement_ratio(posts, followers):
    if followers == 0 or not posts:
        return 0
    avg_likes = sum(p.likes for p in posts) / len(posts)
    return round((avg_likes / followers) * 100, 2)

# ================== MAIN TOOL ==================

def instagram_osint(username):
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        save_metadata=False
    )

    profile = instaloader.Profile.from_username(L.context, username)

    if profile.is_private:
        print("\n[!] Private account — OSINT limited\n")
        return

    print("\n========== PROFILE INFO ==========")
    print(f"Username   : {profile.username}")
    print(f"Name       : {profile.full_name}")
    print(f"Followers  : {profile.followers}")
    print(f"Following  : {profile.followees}")
    print(f"Posts      : {profile.mediacount}")
    # ---------- COLLECT ----------
    hashtags = set()
    numbers = set(extract_numbers(profile.biography))
    emails = set(extract_emails(profile.biography))
    link_numbers = set(extract_numbers_from_links(profile.biography))

    posts_data = []
    recent_posts = []

    for i, post in enumerate(profile.get_posts(), start=1):
        if i > 6:
            break

        recent_posts.append(post)

        if post.caption:
            hashtags.update(extract_hashtags(post.caption))
            numbers.update(extract_numbers(post.caption))
            emails.update(extract_emails(post.caption))
            link_numbers.update(extract_numbers_from_links(post.caption))

        posts_data.append([
            post.date_utc.strftime("%Y-%m-%d"),
            post.likes,
            post.comments
        ])

    # ---------- ENGAGEMENT ----------
    er = engagement_ratio(recent_posts, profile.followers)

    # ---------- SCAM SCORE ----------
    risk = scam_score(profile)

    # ---------- OUTPUT ----------
    print("\n========== ANALYSIS ==========")
    print(f"Engagement Ratio : {er}%")
    print(f"Scam Risk Score  : {risk}/10")

    print("\nEmails Found:")
    for e in emails:
        print(" ", e)

    print("\nPhone Numbers:")
    for n in numbers.union(link_numbers):
        print(" ", n)

    print("\nHashtags:")
    for h in hashtags:
        print(" #", h)

    # ---------- CSV EXPORT ----------
    csv_file = f"{username}_posts.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Likes", "Comments"])
        writer.writerows(posts_data)

    print(f"\n[✔] CSV exported: {csv_file}")

# ================== MENU ==================

def menu():
    print("""
====================================
 INSTAGRAM OSINT PRO TOOL
====================================
1. Run OSINT scan
2. Exit
====================================
""")

    choice = input("Select option: ").strip()

    if choice == "1":
        user = input("Enter Instagram username: ").strip()
        instagram_osint(user)
    else:
        print("Bye 👋")

# ================== RUN ==================

if __name__ == "__main__":
    menu()
