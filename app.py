import os
import datetime
import psycopg2
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
TARGET_TABUNGAN = 5000000

# Konfigurasi Cloudinary dari Vercel Environment Variables
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
    secure = True
)

def init_db():
    if not DATABASE_URL:
        return
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    # Pastikan tabel utama ada
    c.execute('CREATE TABLE IF NOT EXISTS tabungan (id SERIAL PRIMARY KEY, nama VARCHAR(50), jumlah INTEGER, tipe VARCHAR(50), tanggal VARCHAR(50), catatan TEXT)')
    
    # Cek dan tambah kolom catatan jika belum ada
    c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='tabungan' AND column_name='catatan'")
    if not c.fetchone():
        c.execute("ALTER TABLE tabungan ADD COLUMN catatan TEXT DEFAULT '-'")
        
    # Cek dan tambah kolom foto jika belum ada
    c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='tabungan' AND column_name='foto'")
    if not c.fetchone():
        c.execute("ALTER TABLE tabungan ADD COLUMN foto TEXT")
        
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if not DATABASE_URL:
        return "ERROR: DATABASE_URL belum diatur di Vercel!"
    init_db()
    
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT * FROM tabungan ORDER BY id DESC')
    data = c.fetchall()
    c.execute('SELECT SUM(jumlah) FROM tabungan')
    total_tuple = c.fetchone()
    total = total_tuple[0] if total_tuple[0] else 0
    conn.close()
    
    persentase = (total / TARGET_TABUNGAN) * 100 if TARGET_TABUNGAN > 0 else 0
    if persentase > 100: persentase = 100
    
    return render_template('index.html', data=data, total=total, target=TARGET_TABUNGAN, persentase=persentase)

@app.route('/tambah', methods=['POST'])
def tambah():
    nama = request.form['nama']
    jumlah = request.form['jumlah']
    tipe = request.form['tipe']
    catatan = request.form.get('catatan', '-')
    tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Proses Upload Foto
    foto_url = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file.filename != '':
            try:
                upload_result = cloudinary.uploader.upload(file)
                foto_url = upload_result['secure_url']
            except Exception as e:
                print("Error upload:", e)

    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    
    # Insert data ke database
    if foto_url:
        c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal, catatan, foto) VALUES (%s, %s, %s, %s, %s, %s)', (nama, jumlah, tipe, tanggal, catatan, foto_url))
    else:
        c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal, catatan) VALUES (%s, %s, %s, %s, %s)', (nama, jumlah, tipe, tanggal, catatan))
        
    conn.commit()
    conn.close()
    
    return redirect('/?status=sukses')
