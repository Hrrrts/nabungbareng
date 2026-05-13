import os
import datetime
import psycopg2
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
TARGET_TABUNGAN = 5000000  # Ganti angka ini sesuai target kalian

def init_db():
    if not DATABASE_URL:
        return
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    # Tambah kolom catatan (jika belum ada, kita biarkan aman dengan script ini)
    c.execute('CREATE TABLE IF NOT EXISTS tabungan (id SERIAL PRIMARY KEY, nama VARCHAR(50), jumlah INTEGER, tipe VARCHAR(50), tanggal VARCHAR(50), catatan TEXT)')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if not DATABASE_URL:
        return "ERROR: DATABASE_URL belum diatur di menu Environment Variables Vercel!"
    init_db()
    
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    
    # Cek apakah kolom catatan sudah ada (buat handle update tabel lama)
    c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='tabungan' AND column_name='catatan'")
    if not c.fetchone():
        c.execute("ALTER TABLE tabungan ADD COLUMN catatan TEXT DEFAULT '-'")
        conn.commit()

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
    
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal, catatan) VALUES (%s, %s, %s, %s, %s)', (nama, jumlah, tipe, tanggal, catatan))
    conn.commit()
    conn.close()
    
    # Redirect dengan penanda sukses
    return redirect('/?status=sukses')

