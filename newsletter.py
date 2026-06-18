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

def get_date_formatted():
    tz_wib = timezone(timedelta(hours=7))
    return datetime.now(tz_wib).strftime("%A, %d %B %Y")

def load_top5(filename="top5.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def load_articles_txt(filename="Artikel.txt"):
    """
    Parsing Artikel.txt dengan format:
    📰 ARTIKEL #1

    Judul: ...
    Subtitle: ...
    Konten:
    [isi artikel]
    Kalimat SEO: ...
    Tags: ...
    Assets: ...
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
    except:
        return []

    articles = []
    # Split berdasarkan ARTIKEL #N
    blocks = re.split(r'📰 ARTIKEL #\d+\n+', content)
    for block in blocks[1:]:  # skip header
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
                # Simpan current content sebelum berakhir
                if current_key == 'content':
                    article[current_key] = '\n'.join(current_value).strip()
                current_key = None
                current_value = []
            else:
                if current_key:
                    current_value.append(line)

        # Simpan sisa
        if current_key and current_key == 'content':
            article[current_key] = '\n'.join(current_value).strip()

        if article:
            articles.append(article)

    return articles

def generate_hook(articles):
    prompt = f"""Anda adalah penulis untuk newsletter "The Quartr". 
Buatlah paragraf pembuka (hook) yang menarik untuk newsletter hari ini.

📌 Gaya penulisan:
- Santai namun profesional, seperti teman yang cerdas.
- Jangan gunakan kata slang seperti "lo", "gue", "anjay", "bayangin lo", dll.
- Jangan berlebihan atau hiperbola.
- 1 paragraf (50-80 kata), mengalir, dan relevan dengan berita hari ini.

Berita hari ini:
"""
    for art in articles[:5]:
        prompt += f"\n- {art.get('title', '')}"
    prompt += "\n\nOutput: Hanya teks hook, tanpa embel-embel."

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Anda penulis newsletter dengan gaya santai-profesional."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_quarter_time(articles):
    prompt = f"""Anda adalah penulis untuk newsletter "The Quartr". 
Buatlah konten untuk segmen "Quarter Time" — bagian ringan yang memberikan nilai tambah.

📌 Gaya penulisan:
- Santai namun profesional, seperti teman yang cerdas.
- Jangan gunakan kata slang seperti "lo", "gue", "anjay", dll.
- Jangan berlebihan atau hiperbola.
- 1-2 paragraf (80-120 kata), isinya bisa: rekomendasi buku/podcast, kutipan inspiratif, analisis tren, atau fakta menarik.
- Relevan dengan tema berita hari ini.

Berita hari ini:
"""
    for art in articles[:5]:
        prompt += f"\n- {art.get('title', '')}"
    prompt += "\n\nOutput: Hanya teks Quarter Time, tanpa embel-embel."

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Anda penulis newsletter dengan gaya santai-profesional."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_quiz(articles):
    prompt = f"""Anda adalah penulis untuk newsletter "The Quartr". 
Buatlah kuis mini (1 pertanyaan pilihan ganda) berdasarkan berita hari ini.

📌 Aturan:
- 1 pertanyaan dengan 4 opsi (A, B, C, D).
- Pertanyaan harus menarik, tidak terlalu mudah.
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
        prompt += f"\n- {art.get('title', '')}"
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
        return json.loads(response.choices[0].message.content)
    except:
        return {
            "question": "Apa berita utama yang paling menarik perhatian Anda hari ini?",
            "options": ["A. Amazon chip AI", "B. SpaceX akuisisi", "C. Apple Brasil", "D. Startup AI"],
            "answer": "A"
        }

def generate_subject(articles):
    prompt = f"""Anda adalah penulis untuk newsletter "The Quartr". 
Buatlah subjek email (1 kalimat, 10-15 kata) yang menarik dan profesional.

📌 Gaya:
- Menarik, membuat penasaran, tapi tidak clickbait.
- Mencerminkan tema utama hari ini.
- Gunakan bahasa Indonesia yang baik, tanpa slang.

Berita hari ini:
"""
    for art in articles[:3]:
        prompt += f"\n- {art.get('title', '')}"
    prompt += "\n\nOutput: Hanya teks subjek, tanpa tanda kutip atau embel-embel."

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Anda ahli menulis subjek email yang profesional."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def format_newsletter(articles, hook, quarter_time, quiz_data, subject, date):
    text = f"📰 **{subject}**\n\n"
    text += f"*The Quartr — {date}*\n\n"
    text += "──────────────────────────────────────────────────\n\n"

    # Hook
    text += "## 🎯 The Hook\n"
    text += f"{hook}\n\n"
    text += "──────────────────────────────────────────────────\n\n"

    # Core Stories
    text += "## 📌 The Core Stories\n\n"
    for idx, art in enumerate(articles[:5], 1):
        title = art.get('title', f'Berita {idx}')
        content = art.get('content', '')
        if not content:
            content = "Konten tidak tersedia."
        text += f"### {idx}. {title}\n"
        text += f"{content}\n\n"
    text += "──────────────────────────────────────────────────\n\n"

    # Quarter Time
    text += "## 🧠 Quarter Time\n"
    text += f"{quarter_time}\n\n"
    text += "──────────────────────────────────────────────────\n\n"

    # Gamification
    text += "## 🎮 Gamification\n"
    text += f"**Kuis Mini:**\n"
    text += f"{quiz_data.get('question', '')}\n"
    for opt in quiz_data.get('options', []):
        text += f"- {opt}\n"
    text += f"\n*Jawaban: {quiz_data.get('answer', '')}*\n\n"
    text += "──────────────────────────────────────────────────\n\n"

    # Footer
    text += "📬 **Ikuti The Quartr setiap hari**\n"
    text += "Dapatkan 5 berita bisnis & teknologi terbaik setiap pagi.\n"
    text += "🔗 [Subscribe di Substack](link-substack) | [Telegram](link-telegram)\n\n"
    text += "💬 Ada masukan? Balas email ini — saya selalu senang ngobrol.\n"

    return text

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

    with open("newsletter_substack.txt", "w", encoding="utf-8") as f:
        f.write(newsletter)

    print("✅ Newsletter siap di-copy ke Substack!")
    print("📄 File: newsletter_substack.txt")
    print(f"📧 Subjek: {subject}")
