import json
import os
import requests
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
    return datetime.now(tz_wib).strftime("%A, %d %B %Y")

def fetch_asset_image(keyword):
    try:
        url = f"https://api.unsplash.com/photos/random?query={keyword}&orientation=landscape"
        headers = {"Authorization": f"Client-ID {os.environ.get('UNSPLASH_ACCESS_KEY', 'demo')}"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('urls', {}).get('regular', '')
    except:
        pass
    return f"https://source.unsplash.com/featured/?{keyword.replace(' ', ',')}"

def load_top5(filename="top5.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_article(content, filename="Artikel.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def send_article_to_telegram(title, subtitle, content, seo, tags, assets):
    """Kirim satu artikel utuh ke Telegram sebagai pesan terpisah."""
    import subprocess
    
    # Bangun pesan dengan format Markdown Telegram
    message = f"*📰 {title}*\n"
    message += f"_ {subtitle}_\n\n"
    message += f"{content}\n\n"
    message += f"🔍 *SEO:* {seo}\n"
    message += f"🏷️ *Tags:* {tags}\n"
    if assets:
        message += f"🖼️ *Assets:* {assets[0]}"
    
    # Potong jika > 4096 karakter
    if len(message) > 4096:
        message = message[:4093] + "..."
    
    subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
        "-F", f"chat_id={os.environ['TELEGRAM_CHAT_ID']}",
        "-F", f"text={message}",
        "-F", "parse_mode=Markdown"
    ])

# ================================
# WRITER CORE
# ================================

def write_full_article(article, index):
    prompt = f"""Anda adalah penulis senior untuk newsletter "The Quartr" yang berbasis di Indonesia.

Tugas: Tulislah artikel berita (300-400 kata) berdasarkan berita di bawah ini dengan mengikuti **Framework 4A**:

1. **Alert**: Paragraf pembuka yang menarik perhatian.
2. **Analysis**: Analisis dampak makro dan mikro.
3. **Angle**: Sudut pandang unik untuk pembaca umum.
4. **Action**: Ajakan atau pertanyaan reflektif.

📌 FORMAT OUTPUT (WAJIB):
- **Judul Alternatif**: Judul baru menarik, tanpa emoticon, max 10 kata.
- **Subtitle**: 1 kalimat, max 15 kata, merangkum esensi.
- **Konten**: 300-400 kata, paragraf mengalir (Alert → Analysis → Angle → Action).
- **Kalimat SEO**: 1 kalimat dengan keyword utama.
- **Tag**: 5-7 kata kunci, dipisahkan koma.
- **Assets**: 1-2 link gambar gratis (Unsplash/Pexels).

📰 DATA BERITA:
Judul: {article['title']}
Ringkasan: {article.get('summary', '')}
Skor: {article.get('score', 3)}
Alasan: {article.get('reason', '')}

Output: Berikan dalam format JSON **tanpa komentar tambahan**:
{{
  "title": "judul alternatif",
  "subtitle": "subtitle singkat",
  "content": "teks artikel lengkap (300-400 kata)",
  "seo": "kalimat SEO",
  "tags": "tag1, tag2, tag3",
  "assets": ["url_gambar1", "url_gambar2"]
}}
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Anda adalah jurnalis berpengalaman dengan gaya santai-informatif. Output selalu JSON valid."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    try:
        data = json.loads(response.choices[0].message.content)
        if not data.get('assets'):
            keyword = data.get('tags', '').split(',')[0].strip() if data.get('tags') else article['title'][:30]
            data['assets'] = [fetch_asset_image(keyword)]
        return data
    except:
        print(f"Gagal parsing JSON untuk artikel {index}.")
        return {
            "title": article['title'],
            "subtitle": "Ringkasan berita hari ini",
            "content": response.choices[0].message.content[:500],
            "seo": article['title'],
            "tags": "berita, teknologi, bisnis",
            "assets": [fetch_asset_image("technology")]
        }

def format_article_text(data, index):
    """Format untuk file .txt (arsip)."""
    text = f"📰 ARTIKEL #{index}\n\n"
    text += f"Judul: {data['title']}\n"
    text += f"Subtitle: {data['subtitle']}\n\n"
    text += f"Konten:\n{data['content']}\n\n"
    text += f"Kalimat SEO: {data['seo']}\n"
    text += f"Tags: {data['tags']}\n"
    text += f"Assets (Gambar):\n"
    for asset in data.get('assets', []):
        text += f"- {asset}\n"
    text += "\n" + "="*60 + "\n\n"
    return text

if __name__ == "__main__":
    print("📖 Membaca top5.json...")
    top5 = load_top5()
    if not top5:
        print("Tidak ada top5.json. Jalankan curator dulu.")
        exit(0)

    top5_sorted = sorted(top5, key=lambda x: x.get('score', 0), reverse=True)

    full_archive = f"The Quartr - Newsletter {get_current_date_wib()}\n\n"
    full_archive += "="*50 + "\n\n"

    for idx, article in enumerate(top5_sorted, 1):
        print(f"✍️ Menulis artikel #{idx}: {article['title']}")
        data = write_full_article(article, idx)
        
        # Kirim ke Telegram sebagai pesan terpisah
        send_article_to_telegram(
            title=data['title'],
            subtitle=data['subtitle'],
            content=data['content'],
            seo=data['seo'],
            tags=data['tags'],
            assets=data.get('assets', [])
        )
        print(f"  ✅ Terkirim ke Telegram")
        
        # Simpan ke arsip
        full_archive += format_article_text(data, idx)

    # Simpan file arsip
    save_article(full_archive, "Artikel.txt")
    print("✅ Artikel.txt berhasil dibuat.")
