import os
import datetime
import psycopg2
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
TARGET_TABUNGAN = 100000000
PIN_RAHASIA = "1234"  # <-- GANTI PIN KALIAN DI SINI

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
    
    c.execute("SELECT * FROM tabungan WHERE nama='Ikhsan' ORDER BY id DESC")
    data_ikhsan = c.fetchall()
    c.execute("SELECT SUM(jumlah) FROM tabungan WHERE nama='Ikhsan'")
    total_ikhsan = c.fetchone()[0] or 0
    
    c.execute("SELECT * FROM tabungan WHERE nama='Febri' ORDER BY id DESC")
    data_febri = c.fetchall()
    c.execute("SELECT SUM(jumlah) FROM tabungan WHERE nama='Febri'")
    total_febri = c.fetchone()[0] or 0
    
    conn.close()
    
    total_semua = total_ikhsan + total_febri
    sisa_dana = TARGET_TABUNGAN - total_semua
    if sisa_dana < 0: sisa_dana = 0
    
    persentase = (total_semua / TARGET_TABUNGAN) * 100 if TARGET_TABUNGAN > 0 else 0
    if persentase > 100: persentase = 100
    
    return render_template('index.html', 
                           data_ikhsan=data_ikhsan, total_ikhsan=total_ikhsan,
                           data_febri=data_febri, total_febri=total_febri,
                           total_semua=total_semua, target=TARGET_TABUNGAN, 
                           sisa_dana=sisa_dana, persentase=persentase)

@app.route('/tambah', methods=['POST'])
def tambah():
    pin_input = request.form.get('pin')
    if pin_input != PIN_RAHASIA:
        return redirect('/?status=pin_salah')

    nama = request.form['nama']
    jumlah = int(request.form['jumlah_asli']) # Ambil angka murni tanpa titik
    
    # Waktu pakai WIB (+7 jam)
    tz = datetime.timezone(datetime.timedelta(hours=7))
    tanggal = datetime.datetime.now(tz).strftime("%d %b %Y - %H:%M")
    
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
    # Tipe dan catatan diisi default '-' karena sudah dihapus dari form
    if foto_url:
        c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal, catatan, foto) VALUES (%s, %s, %s, %s, %s, %s)', (nama, jumlah, '-', tanggal, '-', foto_url))
    else:
        c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal, catatan) VALUES (%s, %s, %s, %s, %s)', (nama, jumlah, '-', tanggal, '-'))
    conn.commit()
    conn.close()
    
    return redirect('/?status=sukses')

@app.route('/halaman_reset')
def halaman_reset():
    return render_template('reset.html')

@app.route('/hapus_semua', methods=['POST'])
def hapus_semua():
    pin_input = request.form.get('pin')
    if pin_input != PIN_RAHASIA:
        return redirect('/halaman_reset?status=pin_salah')
    
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('TRUNCATE TABLE tabungan RESTART IDENTITY')
    conn.commit()
    conn.close()
    return redirect('/?status=reset_sukses')
