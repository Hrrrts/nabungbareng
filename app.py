from flask import Flask, render_template, request, redirect
import sqlite3
import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('nabung.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tabungan (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, jumlah INTEGER, tipe TEXT, tanggal TEXT)')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    init_db() # Memastikan database otomatis terbuat
    conn = sqlite3.connect('nabung.db')
    c = conn.cursor()
    c.execute('SELECT * FROM tabungan ORDER BY id DESC')
    data = c.fetchall()
    c.execute('SELECT SUM(jumlah) FROM tabungan')
    total = c.fetchone()[0] or 0
    conn.close()
    return render_template('index.html', data=data, total=total)

@app.route('/tambah', methods=['POST'])
def tambah():
    nama = request.form['nama']
    jumlah = request.form['jumlah']
    tipe = request.form['tipe']
    tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = sqlite3.connect('nabung.db')
    c = conn.cursor()
    c.execute('INSERT INTO tabungan (nama, jumlah, tipe, tanggal) VALUES (?, ?, ?, ?)', (nama, jumlah, tipe, tanggal))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
