import os
import re
import sys
from datetime import datetime
from supabase import create_client

# ========================================
# 1. AMBIL CREDENTIAL DARI ENVIRONMENT
# ========================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    print("❌ SUPABASE_URL tidak ditemukan di environment.")
    sys.exit(1)

if not SUPABASE_KEY:
    print("❌ SUPABASE_SERVICE_ROLE_KEY tidak ditemukan di environment.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Koneksi ke Supabase berhasil.")


# ========================================
# 2. PARSE FILE final_edition.txt
# ========================================

def parse_final_edition(filename="final_edition.txt"):
    """
    Membaca file final_edition.txt dan mengekstrak:
    - title   : dari 📰 **...**
    - hook    : dari ## 🎯 The Hook
    - quarter_time : dari ## 🧠 Quarter Time
    - quiz    : dari ## 🎮 Gamification
    - content : seluruh teks
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ File {filename} tidak ditemukan.")
        return None

    if not content.strip():
        print("❌ File kosong.")
        return None

    # === Ekstrak Judul ===
    title_match = re.search(r'📰 \*\*(.*?)\*\*', content)
    title = title_match.group(1).strip() if title_match else ""

    # === Ekstrak Hook ===
    hook_match = re.search(r'## 🎯 The Hook\n(.*?)\n\n📌', content, re.DOTALL)
    hook = hook_match.group(1).strip() if hook_match else ""

    # === Ekstrak Quarter Time ===
    qt_match = re.search(r'## 🧠 Quarter Time\n(.*?)\n\n## 🎮', content, re.DOTALL)
    quarter_time = qt_match.group(1).strip() if qt_match else ""

    # === Ekstrak Kuis ===
    quiz_match = re.search(r'## 🎮 Gamification\n(.*?)\n\n📬', content, re.DOTALL)
    quiz = quiz_match.group(1).strip() if quiz_match else ""

    return {
        "title": title,
        "content": content,
        "hook": hook,
        "quarter_time": quarter_time,
        "quiz": quiz
    }


# ========================================
# 3. UPLOAD KE SUPABASE
# ========================================

def upload_final_edition(data):
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
        "quiz": data["quiz"],
        "updated_at": datetime.now().isoformat()
    }

    try:
        if existing.data:
            # Update jika sudah ada
            supabase.table("final_editions") \
                .update(row) \
                .eq("published_date", today) \
                .execute()
            print(f"✅ Edisi {today} berhasil diUPDATE di Supabase.")
        else:
            # Insert baru
            supabase.table("final_editions") \
                .insert(row) \
                .execute()
            print(f"✅ Edisi {today} berhasil diINSERT ke Supabase.")
        return True
    except Exception as e:
        print(f"❌ Gagal upload: {e}")
        return False


# ========================================
# 4. MAIN
# ========================================

if __name__ == "__main__":
    print("📖 Membaca final_edition.txt...")
    data = parse_final_edition("final_edition.txt")

    if not data:
        print("❌ Gagal parsing. Pastikan file final_edition.txt ada dan sesuai format.")
        sys.exit(1)

    if not data["title"]:
        print("⚠️ Judul tidak ditemukan. Upload tetap dilanjutkan.")
    else:
        print(f"📌 Judul: {data['title'][:60]}...")

    print(f"📝 Panjang konten: {len(data['content'])} karakter")
    print("📤 Mengupload ke Supabase...")

    success = upload_final_edition(data)

    if success:
        print("✅ Selesai.")
        sys.exit(0)
    else:
        print("❌ Upload gagal.")
        sys.exit(1)
