import os
import datetime
import psycopg2
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Mengambil kunci database dari pengaturan Vercel
DATABASE_URL = os.environ.get('DATABASE_URL')

def init_db():
    if not DATABASE_URL:
        return
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tabungan (id SERIAL PRIMARY KEY, nama VARCHAR(50), jumlah INTEGER, tipe VARCHAR(50), tanggal VARCHAR(50))')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if not DATABASE_URL:
        return "ERROR: DATABASE_URL belum diatur di menu Environment Variables Vercel!"
    init_db()
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT * FROM tabungan ORDER BY id DESC')
    data = c.fetchall()
    c.execute('SELECT SUM(jumlah) FROM tabungan')
    total_tuple = c.fetchone()
    total = total_tuple[0] if total_tuple[0] else 0
    conn.close()
    return render_template('index.html', data=data, total=total)

@app.route('/tambah', methods=['POST'])
def tambah():
    nama = request.form['nama']
    jumlah = request.form['jumlah']
    tipe = request.form['tipe']
    tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal) VALUES (%s, %s, %s, %s)', (nama, jumlah, tipe, tanggal))
    conn.commit()
    conn.close()
    return redirect('/')

# Vercel butuh variabel 'app' terekspos, jadi ini cukup.
