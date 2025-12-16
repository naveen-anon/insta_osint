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

# ================== EXTRA TOOLS ==================

def username_pattern_score(username):
    score = 0
    if re.search(r"\d{4,}", username):
        score += 2
    if "_" in username:
        score += 1
    if len(username) > 15:
        score += 1
    return score

def follower_following_ratio(followers, following):
    if following == 0:
        return 0
    return round(followers / following, 2)

def account_age_estimate(first_post_date):
    days = (datetime.utcnow() - first_post_date).days
    return f"{days} days (approx)"

# ================== SCAM SCORE ==================

def scam_score(profile, username_score):
    score = username_score

    if profile.followers < 100:
        score += 2
    if profile.mediacount < 3:
        score += 2
    if profile.followees > profile.followers * 3:
        score += 2
    if not profile.biography:
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

    try:
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

        ratio = follower_following_ratio(profile.followers, profile.followees)
        print(f"F/F Ratio  : {ratio}")

        # ---------- COLLECT ----------
        hashtags = []
        numbers = set(extract_numbers(profile.biography))
        emails = set(extract_emails(profile.biography))
        link_numbers = set(extract_numbers_from_links(profile.biography))

        posts_data = []
        recent_posts = []
        first_post_date = None

        for i, post in enumerate(profile.get_posts(), start=1):
            if i > 6:
                break

            recent_posts.append(post)
            if not first_post_date:
                first_post_date = post.date_utc

            if post.caption:
                hashtags.extend(extract_hashtags(post.caption))
                numbers.update(extract_numbers(post.caption))
                emails.update(extract_emails(post.caption))
                link_numbers.update(extract_numbers_from_links(post.caption))

            posts_data.append([
                post.date_utc.strftime("%Y-%m-%d"),
                post.likes,
                post.comments
            ])

        # ---------- ANALYSIS ----------
        er = engagement_ratio(recent_posts, profile.followers)
        username_score = username_pattern_score(profile.username)
        risk = scam_score(profile, username_score)

        print("\n========== ANALYSIS ==========")
        print(f"Engagement Ratio : {er}%")
        print(f"Scam Risk Score  : {risk}/10")

        if first_post_date:
            print("Account Age     :", account_age_estimate(first_post_date))

        print("\nEmails Found:")
        for e in emails:
            print(" ", e)

        print("\nPhone Numbers:")
        for n in numbers.union(link_numbers):
            print(" ", n)

        print("\nTop Hashtags:")
        for h in set(hashtags[:5]):
            print(" #", h)

        # ---------- CSV EXPORT ----------
        csv_file = f"{username}_posts.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Likes", "Comments"])
            writer.writerows(posts_data)

        # ---------- TXT REPORT ----------
        txt_file = f"{username}_report.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"Username: {profile.username}\n")
            f.write(f"Followers: {profile.followers}\n")
            f.write(f"Following: {profile.followees}\n")
            f.write(f"Engagement Ratio: {er}%\n")
            f.write(f"Scam Risk Score: {risk}/10\n\n")
            f.write("Emails:\n")
            for e in emails:
                f.write(e + "\n")

        print(f"\n[✔] CSV saved: {csv_file}")
        print(f"[✔] TXT report saved: {txt_file}")

    except Exception as e:
        print("[!] Error:", e)

# ================== MENU ==================

def menu():
    while True:
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
        elif choice == "2":
            print("Bye 👋")
            break
        else:
            print("Invalid option!")

# ================== RUN ==================

if __name__ == "__main__":
    menu()
