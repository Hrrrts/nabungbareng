import os
import datetime
import psycopg2
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# --- PENGATURAN TARGET (BISA DIUBAH) ---
DATABASE_URL = os.environ.get('DATABASE_URL')
TARGET_TABUNGAN = 37500000
TANGGAL_MULAI = datetime.date(2026, 1, 1)
TANGGAL_TARGET = datetime.date(2027, 7, 29)
# ---------------------------------------

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
    c.execute('CREATE TABLE IF NOT EXISTS tabungan (id SERIAL PRIMARY KEY, nama VARCHAR(50), jumlah INTEGER, tipe VARCHAR(50), tanggal VARCHAR(50), catatan TEXT, foto TEXT)')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if not DATABASE_URL:
        return "ERROR: DATABASE_URL belum diatur di Vercel!"
    init_db()
    
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    
    # Data Ikhsan
    c.execute("SELECT * FROM tabungan WHERE nama='Ikhsan' ORDER BY id DESC")
    data_ikhsan = c.fetchall()
    c.execute("SELECT SUM(jumlah) FROM tabungan WHERE nama='Ikhsan'")
    total_ikhsan = c.fetchone()[0] or 0
    
    # Data Febri
    c.execute("SELECT * FROM tabungan WHERE nama='Febri' ORDER BY id DESC")
    data_febri = c.fetchall()
    c.execute("SELECT SUM(jumlah) FROM tabungan WHERE nama='Febri'")
    total_febri = c.fetchone()[0] or 0
    
    conn.close()
    
    total_semua = total_ikhsan + total_febri
    sisa_dana = TARGET_TABUNGAN - total_semua
    
    # Hitung sisa hari
    sisa_waktu = (TANGGAL_TARGET - datetime.date.today()).days
    if sisa_waktu < 0: sisa_waktu = 0
    
    return render_template('index.html', 
                           data_ikhsan=data_ikhsan, total_ikhsan=total_ikhsan,
                           data_febri=data_febri, total_febri=total_febri,
                           total_semua=total_semua, target=TARGET_TABUNGAN, 
                           sisa_dana=sisa_dana, sisa_waktu=sisa_waktu,
                           tgl_mulai=TANGGAL_MULAI.strftime('%d %B %Y'),
                           tgl_target=TANGGAL_TARGET.strftime('%d %B %Y'))

@app.route('/tambah', methods=['POST'])
def tambah():
    nama = request.form['nama']
    jumlah = request.form['jumlah']
    tipe = request.form['tipe']
    catatan = request.form.get('catatan', '-')
    
    # Format tanggal sederhana
    tanggal = datetime.datetime.now().strftime("%d %B %Y")
    
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
    if foto_url:
        c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal, catatan, foto) VALUES (%s, %s, %s, %s, %s, %s)', (nama, jumlah, tipe, tanggal, catatan, foto_url))
    else:
        c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal, catatan) VALUES (%s, %s, %s, %s, %s)', (nama, jumlah, tipe, tanggal, catatan))
    conn.commit()
    conn.close()
    
    return redirect('/?status=sukses')

@app.route('/hapus_semua', methods=['POST'])
def hapus_semua():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('TRUNCATE TABLE tabungan RESTART IDENTITY')
    conn.commit()
    conn.close()
    return redirect('/?status=reset')

