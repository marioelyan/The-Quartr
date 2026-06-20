import os
import re
from datetime import datetime
from supabase import create_client

# Inisialisasi Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase = create_client(url, key)

def parse_final_edition(filename="final_edition.txt"):
    """
    Parsing file final_edition.txt untuk ekstrak:
    - judul (dari baris pertama setelah 📰)
    - hook (dari ## 🎯 The Hook)
    - quarter_time (dari ## 🧠 Quarter Time)
    - quiz (dari ## 🎮 Gamification)
    - content (seluruh teks)
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ final_edition.txt tidak ditemukan.")
        return None

    # Ekstrak judul (baris pertama setelah 📰)
    title_match = re.search(r'📰 \*\*(.*?)\*\*', content)
    title = title_match.group(1).strip() if title_match else ""

    # Ekstrak Hook
    hook_match = re.search(r'## 🎯 The Hook\n(.*?)\n\n📌', content, re.DOTALL)
    hook = hook_match.group(1).strip() if hook_match else ""

    # Ekstrak Quarter Time
    qt_match = re.search(r'## 🧠 Quarter Time\n(.*?)\n\n## 🎮', content, re.DOTALL)
    quarter_time = qt_match.group(1).strip() if qt_match else ""

    # Ekstrak Kuis
    quiz_match = re.search(r'## 🎮 Gamification\n(.*?)\n\n📬', content, re.DOTALL)
    quiz = quiz_match.group(1).strip() if quiz_match else ""

    return {
        "title": title,
        "content": content,
        "hook": hook,
        "quarter_time": quarter_time,
        "quiz": quiz
    }

def upload_final_edition(data):
    """Upload edisi final ke Supabase."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Cek apakah sudah ada edisi untuk hari ini
    existing = supabase.table("final_editions") \
        .select("id") \
        .eq("published_date", today) \
        .execute()

    row = {
        "published_date": today,
        "title": data["title"],
        "content": data["content"],
        "hook": data["hook"],
        "quarter_time": data["quarter_time"],
        "quiz": data["quiz"]
    }

    if existing.data:
        # Update jika sudah ada
        result = supabase.table("final_editions") \
            .update(row) \
            .eq("published_date", today) \
            .execute()
        print(f"✅ Edisi {today} berhasil diUPDATE di Supabase.")
    else:
        # Insert baru
        result = supabase.table("final_editions") \
            .insert(row) \
            .execute()
        print(f"✅ Edisi {today} berhasil diINSERT ke Supabase.")

    return result

if __name__ == "__main__":
    print("📖 Membaca final_edition.txt...")
    data = parse_final_edition("final_edition.txt")
    if not data:
        print("❌ Gagal parsing. Pastikan file final_edition.txt ada dan sesuai format.")
        exit(1)

    print(f"📌 Judul: {data['title']}")
    print(f"📝 Panjang konten: {len(data['content'])} karakter")
    print("📤 Mengupload ke Supabase...")
    upload_final_edition(data)
    print("✅ Selesai.")
