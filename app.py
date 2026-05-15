import os
import datetime
import psycopg2
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')

PIN_AKUN = {
    "Ikhsan": "080907",
    "Febri": "756477"
}
PIN_MASTER = "000000"

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
    # Tabel Pemasukan
    c.execute('CREATE TABLE IF NOT EXISTS tabungan (id SERIAL PRIMARY KEY, nama VARCHAR(50), jumlah INTEGER, tipe VARCHAR(50), tanggal VARCHAR(50), catatan TEXT, foto TEXT)')
    # Tabel Pengeluaran Baru
    c.execute('CREATE TABLE IF NOT EXISTS pengeluaran (id SERIAL PRIMARY KEY, nama VARCHAR(50), jumlah INTEGER, keperluan TEXT, tanggal VARCHAR(50), foto TEXT)')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if not DATABASE_URL:
        return "ERROR: DATABASE_URL belum diatur di Vercel!"
    init_db()
    
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    
    # Data Pemasukan
    c.execute("SELECT * FROM tabungan WHERE nama='Ikhsan' ORDER BY id DESC")
    data_ikhsan = c.fetchall()
    c.execute("SELECT SUM(jumlah) FROM tabungan WHERE nama='Ikhsan'")
    total_ikhsan = c.fetchone()[0] or 0
    
    c.execute("SELECT * FROM tabungan WHERE nama='Febri' ORDER BY id DESC")
    data_febri = c.fetchall()
    c.execute("SELECT SUM(jumlah) FROM tabungan WHERE nama='Febri'")
    total_febri = c.fetchone()[0] or 0
    
    # Data Pengeluaran
    c.execute("SELECT SUM(jumlah) FROM pengeluaran")
    total_pengeluaran = c.fetchone()[0] or 0
    
    conn.close()
    
    total_tabungan = total_ikhsan + total_febri
    saldo_akhir = total_tabungan - total_pengeluaran
    
    return render_template('index.html', 
                           data_ikhsan=data_ikhsan, total_ikhsan=total_ikhsan,
                           data_febri=data_febri, total_febri=total_febri,
                           total_tabungan=total_tabungan, total_pengeluaran=total_pengeluaran,
                           saldo_akhir=saldo_akhir)

@app.route('/tambah', methods=['POST'])
def tambah():
    nama = request.form.get('nama')
    pin_input = request.form.get('pin_rahasia')
    
    if PIN_AKUN.get(nama) != pin_input:
        return redirect('/?status=pin_salah')

    try:
        jumlah = int(request.form['jumlah_asli'])
    except:
        return redirect('/?status=error')
    
    tz = datetime.timezone(datetime.timedelta(hours=7))
    tanggal = datetime.datetime.now(tz).strftime("%d %b %Y - %H:%M WIB")
    foto_b64 = request.form.get('foto_b64', '')
    foto_url = None

    if foto_b64 != '':
        try:
            upload_result = cloudinary.uploader.upload(foto_b64)
            foto_url = upload_result['secure_url']
        except Exception as e:
            print("Error Cloudinary:", e)

    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    if foto_url:
        c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal, catatan, foto) VALUES (%s, %s, %s, %s, %s, %s)', (nama, jumlah, '-', tanggal, '-', foto_url))
    else:
        c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal, catatan) VALUES (%s, %s, %s, %s, %s)', (nama, jumlah, '-', tanggal, '-'))
    conn.commit()
    conn.close()
    return redirect('/?status=sukses')

# --- RUTE PENGELUARAN ---
@app.route('/pengeluaran')
def halaman_pengeluaran():
    if not DATABASE_URL:
        return "ERROR: DATABASE_URL belum diatur!"
    
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT * FROM pengeluaran ORDER BY id DESC")
    data_pengeluaran = c.fetchall()
    c.execute("SELECT SUM(jumlah) FROM pengeluaran")
    total_pengeluaran = c.fetchone()[0] or 0
    conn.close()
    
    return render_template('pengeluaran.html', data_pengeluaran=data_pengeluaran, total_pengeluaran=total_pengeluaran)

@app.route('/tambah_pengeluaran', methods=['POST'])
def tambah_pengeluaran():
    nama = request.form.get('nama')
    keperluan = request.form.get('keperluan')
    pin_input = request.form.get('pin_rahasia')
    
    if PIN_AKUN.get(nama) != pin_input:
        return redirect('/pengeluaran?status=pin_salah')

    try:
        jumlah = int(request.form['jumlah_asli'])
    except:
        return redirect('/pengeluaran?status=error')
    
    tz = datetime.timezone(datetime.timedelta(hours=7))
    tanggal = datetime.datetime.now(tz).strftime("%d %b %Y - %H:%M WIB")
    foto_b64 = request.form.get('foto_b64', '')
    foto_url = None

    if foto_b64 != '':
        try:
            upload_result = cloudinary.uploader.upload(foto_b64)
            foto_url = upload_result['secure_url']
        except Exception as e:
            pass

    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    if foto_url:
        c.execute('INSERT INTO pengeluaran (nama, jumlah, keperluan, tanggal, foto) VALUES (%s, %s, %s, %s, %s)', (nama, jumlah, keperluan, tanggal, foto_url))
    else:
        c.execute('INSERT INTO pengeluaran (nama, jumlah, keperluan, tanggal) VALUES (%s, %s, %s, %s)', (nama, jumlah, keperluan, tanggal))
    conn.commit()
    conn.close()
    return redirect('/pengeluaran?status=sukses')

# --- RUTE RESET ---
@app.route('/halaman_reset')
def halaman_reset():
    return render_template('reset.html')

@app.route('/hapus_semua', methods=['POST'])
def hapus_semua():
    pin_input = request.form.get('pin')
    if pin_input != PIN_MASTER:
        return redirect('/halaman_reset?status=pin_salah')
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('TRUNCATE TABLE tabungan RESTART IDENTITY')
    c.execute('TRUNCATE TABLE pengeluaran RESTART IDENTITY')
    conn.commit()
    conn.close()
    return redirect('/?status=reset_sukses')
