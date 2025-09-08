from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# --- Helpers DB ---
def get_db_connection():
    conn = sqlite3.connect('perpus.db')
    conn.row_factory = sqlite3.Row
    return conn

def column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols

def init_db():
    conn = get_db_connection()
    # Tabel awal (bila belum ada)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS peminjaman (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_peminjam TEXT NOT NULL,
            nama_buku TEXT NOT NULL,
            tanggal_peminjaman DATE NOT NULL,
            tanggal_pengembalian DATE
        )
    ''')
    # Tambah kolom due_date jika belum ada (migrasi)
    if not column_exists(conn, 'peminjaman', 'due_date'):
        conn.execute('ALTER TABLE peminjaman ADD COLUMN due_date DATE')
        conn.commit()
    conn.close()

# --- Filters & globals ---
@app.context_processor
def inject_globals():
    # sediakan datetime & today_str ke template
    return {
        'datetime': datetime,
        'today_str': datetime.now().strftime('%Y-%m-%d')
    }

@app.template_filter('strptime')
def strptime_filter(date_string, format_string):
    return datetime.strptime(date_string, format_string)

@app.template_filter('indonesian_date')
def indonesian_date_filter(date_string):
    if not date_string:
        return '-'
    months = {
        'January': 'Januari', 'February': 'Februari', 'March': 'Maret',
        'April': 'April', 'May': 'Mei', 'June': 'Juni',
        'July': 'Juli', 'August': 'Agustus', 'September': 'September',
        'October': 'Oktober', 'November': 'November', 'December': 'Desember'
    }
    date_obj = datetime.strptime(date_string, '%Y-%m-%d')
    english_format = date_obj.strftime('%d %B %Y')
    for eng, ind in months.items():
        english_format = english_format.replace(eng, ind)
    return english_format

# --- Routes ---
@app.route('/')
def index():
    conn = get_db_connection()
    peminjaman = conn.execute('SELECT * FROM peminjaman ORDER BY id DESC').fetchall()
    conn.close()
    # today_str sudah diinject lewat context_processor
    return render_template('index.html', peminjaman=peminjaman)

@app.route('/tambah', methods=['GET', 'POST'])
def tambah():
    if request.method == 'POST':
        nama_peminjam = request.form.get('nama_peminjam', '').strip()
        nama_buku = request.form.get('nama_buku', '').strip()
        tanggal_peminjaman = request.form.get('tanggal_peminjaman')  # yyyy-mm-dd
        due_date = request.form.get('due_date')  # yyyy-mm-dd (Jatuh Tempo)
        # Saat tambah, tanggal_pengembalian (aktual) harus NULL/None
        tanggal_pengembalian = None

        if not nama_peminjam or not nama_buku or not tanggal_peminjaman or not due_date:
            flash('Semua field bertanda * wajib diisi!', 'error')
            return redirect(url_for('tambah'))

        # Validasi sederhana: due_date >= tanggal_peminjaman
        try:
            if datetime.strptime(due_date, '%Y-%m-%d') < datetime.strptime(tanggal_peminjaman, '%Y-%m-%d'):
                flash('Jatuh tempo tidak boleh lebih awal dari tanggal peminjaman.', 'error')
                return redirect(url_for('tambah'))
        except Exception:
            flash('Format tanggal tidak valid.', 'error')
            return redirect(url_for('tambah'))

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO peminjaman (nama_peminjam, nama_buku, tanggal_peminjaman, due_date, tanggal_pengembalian)
            VALUES (?, ?, ?, ?, ?)
        ''', (nama_peminjam, nama_buku, tanggal_peminjaman, due_date, tanggal_pengembalian))
        conn.commit()
        conn.close()

        flash('Data peminjaman berhasil ditambahkan!', 'success')
        return redirect(url_for('index'))

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('tambah.html', today=today)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db_connection()

    if request.method == 'POST':
        nama_peminjam = request.form.get('nama_peminjam', '').strip()
        nama_buku = request.form.get('nama_buku', '').strip()
        tanggal_peminjaman = request.form.get('tanggal_peminjaman')
        due_date = request.form.get('due_date')
        # tanggal_pengembalian aktual: dikirim via hidden input saat checkbox dicentang
        tanggal_pengembalian = request.form.get('tanggal_pengembalian') or None

        if not nama_peminjam or not nama_buku or not tanggal_peminjaman or not due_date:
            flash('Semua field bertanda * wajib diisi!', 'error')
            conn.close()
            return redirect(url_for('edit', id=id))

        # Validasi: due_date >= tanggal_peminjaman
        try:
            if datetime.strptime(due_date, '%Y-%m-%d') < datetime.strptime(tanggal_peminjaman, '%Y-%m-%d'):
                flash('Jatuh tempo tidak boleh lebih awal dari tanggal peminjaman.', 'error')
                conn.close()
                return redirect(url_for('edit', id=id))
        except Exception:
            flash('Format tanggal tidak valid.', 'error')
            conn.close()
            return redirect(url_for('edit', id=id))

        # Validasi: jika tanggal_pengembalian diisi, harus >= tanggal_peminjaman
        if tanggal_pengembalian:
            try:
                if datetime.strptime(tanggal_pengembalian, '%Y-%m-%d') < datetime.strptime(tanggal_peminjaman, '%Y-%m-%d'):
                    flash('Tanggal pengembalian tidak boleh lebih awal dari tanggal peminjaman.', 'error')
                    conn.close()
                    return redirect(url_for('edit', id=id))
            except Exception:
                flash('Format tanggal pengembalian tidak valid.', 'error')
                conn.close()
                return redirect(url_for('edit', id=id))

        conn.execute('''
            UPDATE peminjaman
            SET nama_peminjam = ?, nama_buku = ?, tanggal_peminjaman = ?, due_date = ?, tanggal_pengembalian = ?
            WHERE id = ?
        ''', (nama_peminjam, nama_buku, tanggal_peminjaman, due_date, tanggal_pengembalian, id))
        conn.commit()
        conn.close()

        flash('Data peminjaman berhasil diupdate!', 'success')
        return redirect(url_for('index'))

    data = conn.execute('SELECT * FROM peminjaman WHERE id = ?', (id,)).fetchone()
    conn.close()

    if data is None:
        flash('Data tidak ditemukan!', 'error')
        return redirect(url_for('index'))

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('edit.html', data=data, today=today)

@app.route('/hapus/<int:id>')
def hapus(id):
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM peminjaman WHERE id = ?', (id,)).fetchone()
    if data is None:
        conn.close()
        flash('Data tidak ditemukan!', 'error')
        return redirect(url_for('index'))

    conn.execute('DELETE FROM peminjaman WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Data peminjaman berhasil dihapus!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
