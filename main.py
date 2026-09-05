import os
import requests
import feedparser
import schedule
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load rahasia dari file .env untuk test lokal
load_dotenv()

# Ambil data rahasia
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Set up Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

def fetch_ai_news():
    # Mengambil berita AI spesifik dari Google News dari 24 jam terakhir
    url = "https://news.google.com/rss/search?q=(ChatGPT+OR+Claude+OR+Gemini+OR+DeepSeek+OR+Qwen+OR+Kimi)+when:1d&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    news_list = []
    
    for entry in feed.entries[:20]: # Ambil 20 berita teratas
        news_list.append(f"- {entry.title} ({entry.link})")
    return "\n".join(news_list)

def analyze_and_filter_news(news_text):
    if not news_text:
        return None

    # Prompt instruksi super ketat untuk AI
    prompt = f"""
    Kamu adalah pengamat AI global. Ini adalah daftar berita AI dari website hari ini.
    Tugasmu:
    1. Baca judul-judul berita ini. Carilah HANYA berita yang memiliki dampak global yang sangat masif, berpotensi viral besar, atau merubah perilaku masyarakat (contoh: model AGI rilis, fitur baru yang menghancurkan suatu industri, regulasi dunia).
    2. Berita ini harus terkait platform seperti ChatGPT, Claude, Gemini, DeepSeek, Qwen, Kimi, atau sejenisnya.
    3. JIKA HARI INI TIDAK ADA berita yang dampaknya sebesar itu (hanya sekadar update minor/tutorial/berita standar), balas dengan TEPAT satu kata ini saja: SKIP_HARI_INI
    4. JIKA ADA berita yang sangat berdampak, tuliskan ringkasannya dalam bahasa Indonesia. Jelaskan KENAPA ini berdampak besar, dan sertakan link beritanya.

    Daftar Berita:
    {news_text}
    """
    
    # Minta AI berpikir
    model = genai.GenerativeModel('gemini-3.6-flash')
    response = model.generate_content(prompt)
    result = response.text.strip()

    if "SKIP_HARI_INI" in result:
        return None
    return result

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def job():
    print("Mengecek berita hari ini...")
    news_data = fetch_ai_news()
    hasil = analyze_and_filter_news(news_data)
    
    if hasil:
        pesan = f"🚨 **URGENT AI NEWS UPDATE** 🚨\n\n{hasil}"
        send_telegram(pesan)
        print("Berita viral ditemukan dan terkirim!")
    else:
        print("Hari ini tidak ada berita AI dengan dampak global besar. Bot diam.")

def main():
    print("Bot menyala 24/7! Menjadwalkan cek setiap 06:30 WIB...")
    
    # Server Railway berjalan di zona waktu UTC.
    # Jam 06:30 Pagi WIB (Waktu Indonesia Barat) sama dengan Jam 23:30 malam UTC (hari sebelumnya)
    schedule.every().day.at("23:30").do(job)
    
    # Untuk test lokal langsung jalankan 1 kali saat dihidupkan, hapus tanda '#' di bawah ini jika mau
    job() 

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()