import json
import os
import re
from openai import OpenAI
from datetime import datetime, timedelta, timezone

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

# ================================
# TOOLS
# ================================

def get_current_date_wib():
    tz_wib = timezone(timedelta(hours=7))
    return datetime.now(tz_wib)

def get_date_formatted():
    tz_wib = timezone(timedelta(hours=7))
    return datetime.now(tz_wib).strftime("%A, %d %B %Y")

def load_top5(filename="top5.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def load_articles_txt(filename="Artikel.txt"):
    """
    Parsing Artikel.txt untuk mengekstrak judul dan konten setiap artikel.
    Format yang diharapkan:
    📰 ARTIKEL #1
    Judul: ...
    Subtitle: ...
    Konten: ...
    ...
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
    except:
        return []
    
    articles = []
    # Split berdasarkan ARTIKEL #N
    blocks = re.split(r'📰 ARTIKEL #\d+\n\n', content)
    for block in blocks[1:]:  # skip bagian header
        lines = block.strip().split('\n')
        article = {}
        current_key = None
        current_value = []
        for line in lines:
            if line.startswith('Judul: '):
                if current_key:
                    article[current_key] = '\n'.join(current_value).strip()
                current_key = 'title'
                current_value = [line.replace('Judul: ', '')]
            elif line.startswith('Subtitle: '):
                if current_key:
                    article[current_key] = '\n'.join(current_value).strip()
                current_key = 'subtitle'
                current_value = [line.replace('Subtitle: ', '')]
            elif line.startswith('Konten:'):
                if current_key:
                    article[current_key] = '\n'.join(current_value).strip()
                current_key = 'content'
                current_value = []
            elif line.startswith('Kalimat SEO:') or line.startswith('Tags:') or line.startswith('Assets'):
                continue
            else:
                if current_key:
                    current_value.append(line)
        if current_key:
            article[current_key] = '\n'.join(current_value).strip()
        if article:
            articles.append(article)
    return articles

def generate_hook(articles):
    """Menghasilkan hook: komentar santai atau fakta unik hari ini."""
    prompt = f"""Anda adalah penulis newsletter "The Quartr". 
Buatlah pembuka (hook) yang santai, engaging, dan relevan untuk newsletter hari ini.

📌 Aturan:
- Hook harus berupa 1 paragraf pendek (50-80 kata) yang menarik perhatian.
- Bisa berupa fakta unik, pertanyaan retoris, atau komentar ringan tentang berita hari ini.
- Gunakan bahasa Indonesia santai, seperti berbicara dengan teman pintar.
- Jangan gunakan emoji berlebihan (maks 1-2).

Berita hari ini:
"""
    for art in articles[:5]:
        prompt += f"\n- {art.get('title', '')} | {art.get('subtitle', '')}"
    prompt += "\n\nOutput: Hanya teks hook, tanpa judul atau embel-embel."

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Anda penulis newsletter yang santai dan engaging."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_quarter_time(articles):
    """Menghasilkan konten untuk segmen Quarter Time (rekomendasi)."""
    prompt = f"""Anda adalah penulis newsletter "The Quartr". 
Buatlah konten untuk segmen "Quarter Time" — bagian ringan di tengah newsletter yang memberikan nilai tambah.

📌 Tujuan Quarter Time:
- Memberikan perspektif atau insight unik yang tidak ada di berita utama.
- Bisa berupa: rekomendasi buku/podcast, kutipan inspiratif, analisis tren, atau fakta menarik.

📌 Aturan:
- 1-2 paragraf (80-120 kata).
- Relevan dengan tema berita hari ini (bisnis, teknologi, startup).
- Gaya santai, seperti obrolan ringan.

Berita hari ini:
"""
    for art in articles[:5]:
        prompt += f"\n- {art.get('title', '')}"
    prompt += "\n\nOutput: Hanya teks Quarter Time, tanpa judul atau embel-embel."

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Anda penulis newsletter yang insightful dan santai."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_quiz(articles):
    """Menghasilkan kuis mini untuk segmen gamification."""
    prompt = f"""Anda adalah penulis newsletter "The Quartr". 
Buatlah kuis mini (1 pertanyaan pilihan ganda) berdasarkan berita hari ini untuk segmen "Gamification".

📌 Aturan:
- 1 pertanyaan pilihan ganda dengan 4 opsi (A, B, C, D).
- Pertanyaan harus terkait dengan salah satu berita hari ini.
- Sertakan jawaban yang benar.

Format output JSON:
{{
  "question": "teks pertanyaan",
  "options": ["A. opsi 1", "B. opsi 2", "C. opsi 3", "D. opsi 4"],
  "answer": "A"
}}

Berita hari ini:
"""
    for art in articles[:5]:
        prompt += f"\n- {art.get('title', '')} | {art.get('subtitle', '')}"
    prompt += "\n\nOutput: JSON valid, tanpa komentar tambahan."

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Anda pembuat kuis yang kreatif."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    try:
        data = json.loads(response.choices[0].message.content)
        return data
    except:
        return {
            "question": "Apa berita utama hari ini?",
            "options": ["A. SpaceX IPO", "B. AI coding", "C. Regulasi baru", "D. Semua benar"],
            "answer": "D"
        }

def generate_subject(articles):
    """Menghasilkan subjek email yang menarik (10-15 kata)."""
    prompt = f"""Anda adalah penulis newsletter "The Quartr". 
Buatlah subjek email (1 kalimat, 10-15 kata) yang menarik dan merangkum isi newsletter hari ini.

📌 Aturan:
- Menarik, membuat penasaran, tapi tidak clickbait.
- Mencerminkan tema utama hari ini.

Berita hari ini:
"""
    for art in articles[:3]:
        prompt += f"\n- {art.get('title', '')}"
    prompt += "\n\nOutput: Hanya teks subjek, tanpa tanda kutip atau embel-embel."

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Anda ahli menulis subjek email yang menarik."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def format_newsletter(articles, hook, quarter_time, quiz_data, subject, date):
    """Menyusun newsletter lengkap sesuai format."""
    # Judul
    text = f"📰 **{subject}**\n\n"
    text += f"*The Quartr — {date}*\n\n"
    text += "─" * 50 + "\n\n"

    # 1. The Hook
    text += "## 🎯 The Hook\n"
    text += f"{hook}\n\n"
    text += "─" * 50 + "\n\n"

    # 2. The Core Stories (5 berita)
    text += "## 📌 The Core Stories\n\n"
    for idx, art in enumerate(articles[:5], 1):
        title = art.get('title', f'Berita {idx}')
        content = art.get('content', '')
        # Pastikan konten tidak kosong
        if not content:
            content = "Konten tidak tersedia."
        text += f"### {idx}. {title}\n"
        text += f"{content}\n\n"
    text += "─" * 50 + "\n\n"

    # 3. Quarter Time
    text += "## 🧠 Quarter Time\n"
    text += f"{quarter_time}\n\n"
    text += "─" * 50 + "\n\n"

    # 4. Gamification / Interactive
    text += "## 🎮 Gamification\n"
    text += f"**Kuis Mini:**\n"
    text += f"{quiz_data.get('question', '')}\n"
    for opt in quiz_data.get('options', []):
        text += f"- {opt}\n"
    text += f"\n*Jawaban: {quiz_data.get('answer', '')}*\n\n"
    text += "─" * 50 + "\n\n"

    # Footer
    text += "📬 **Ikuti The Quartr setiap hari**\n"
    text += "Dapatkan 5 berita bisnis & teknologi terbaik setiap pagi.\n"
    text += "🔗 [Subscribe di Substack](link-substack) | [Telegram](link-telegram)\n\n"
    text += "💬 Ada masukan? Balas email ini — saya selalu senang ngobrol.\n"

    return text

# ================================
# MAIN
# ================================

if __name__ == "__main__":
    print("📖 Membaca top5.json...")
    top5 = load_top5()
    if not top5:
        print("❌ top5.json tidak ditemukan. Jalankan curator dulu.")
        exit(0)

    print("📖 Membaca Artikel.txt untuk konten...")
    articles = load_articles_txt("Artikel.txt")
    if not articles:
        print("⚠️ Artikel.txt tidak ditemukan atau kosong. Gunakan data dari top5.json.")
        # Fallback: gunakan top5
        articles = []
        for item in top5:
            articles.append({
                "title": item.get("title", ""),
                "subtitle": item.get("reason", ""),
                "content": item.get("summary", "")
            })

    print("🤖 Menghasilkan hook...")
    hook = generate_hook(articles)

    print("🧠 Menghasilkan Quarter Time...")
    quarter_time = generate_quarter_time(articles)

    print("🎮 Menghasilkan kuis...")
    quiz_data = generate_quiz(articles)

    print("📧 Menghasilkan subjek email...")
    subject = generate_subject(articles)

    date = get_date_formatted()

    print("📝 Menyusun newsletter...")
    newsletter = format_newsletter(articles, hook, quarter_time, quiz_data, subject, date)

    # Simpan sebagai file .txt
    with open("newsletter_substack.txt", "w", encoding="utf-8") as f:
        f.write(newsletter)

    print("✅ Newsletter siap di-copy ke Substack!")
    print("📄 File: newsletter_substack.txt")
    print(f"📧 Subjek: {subject}")

    # Opsional: tampilkan preview
    print("\n--- PREVIEW ---")
    print(newsletter[:500] + "...\n")
