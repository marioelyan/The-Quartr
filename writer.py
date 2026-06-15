import json
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

def load_top5(filename="top5.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def write_article(article):
    """Generate artikel pendek (150-200 kata) dari satu berita"""
    prompt = f"""Anda adalah jurnalis teknologi startup. Tulislah artikel singkat (150-200 kata) berdasarkan berita berikut:

Judul: {article['title']}
Ringkasan: {article.get('summary', '')}
Alasan penting: {article.get('curation_reason', '')}

Gaya penulisan: informatif, jelas, dan enak dibaca. Gunakan bahasa Indonesia yang baik.
Output hanya teks artikel, tanpa judul ulang atau embel-embel.
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Anda seorang jurnalis berpengalaman di bidang startup dan teknologi."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def send_to_telegram(article_text, title):
    """Kirim satu artikel ke Telegram sebagai pesan teks"""
    import subprocess
    caption = f"📝 *{title}*\n\n{article_text}"
    if len(caption) > 4096:
        caption = caption[:4093] + "..."
    subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
        "-F", f"chat_id={os.environ['TELEGRAM_CHAT_ID']}",
        "-F", f"text={caption}",
        "-F", "parse_mode=Markdown"
    ])

def save_article_to_file(article_text, title, idx):
    """Simpan artikel ke file (opsional)"""
    filename = f"article_{idx}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{title}\n\n{article_text}")
    return filename

if __name__ == "__main__":
    print("📖 Membaca top5.json...")
    top5 = load_top5()
    if not top5:
        print("Tidak ada top5.json. Jalankan curator dulu.")
        exit(0)
    
    print(f"✍️ Menulis {len(top5)} artikel...")
    for idx, article in enumerate(top5, 1):
        print(f"  [{idx}/{len(top5)}] {article['title']}")
        text = write_article(article)
        
        # Kirim ke Telegram
        send_to_telegram(text, article['title'])
        print(f"    ✅ Terkirim ke Telegram")
        
        # Opsional: simpan ke file
        save_article_to_file(text, article['title'], idx)
    
    print("✅ Semua artikel selesai ditulis dan dikirim.")
