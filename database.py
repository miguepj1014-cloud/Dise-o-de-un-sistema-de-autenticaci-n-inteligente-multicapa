import sqlite3
def crear_bd():
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        llave_maestra TEXT,
        categoria TEXT,
        the_word TEXT,
        email TEXT UNIQUE,
        Numtelefono TEXT UNIQUE,
        ip TEXT,
        ubicacion TEXT,
        fecha_registro TEXT,
        dispositivo TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accesos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        ip TEXT,
        ubicacion TEXT,
        dispositivo TEXT,
        fecha TEXT,
        exito INTEGER
    )
    """)
    conn.commit()
    conn.close()
def obtener_usuario(username):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT password_hash, categoria, the_word
        FROM usuarios
        WHERE username = ?
    """, (username,))
    fila = cursor.fetchone()
    conn.close()
    return fila
#////////////////////////////////#
def insertar_usuario(username, password_hash, llave_maestra, categoria, the_word, email, telefono, ip, ubicacion, fecha, dispositivo):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usuarios 
        (username, password_hash, llave_maestra, categoria, the_word, email, Numtelefono, ip, ubicacion, fecha_registro, dispositivo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, password_hash, llave_maestra, categoria, the_word, email, telefono, ip, ubicacion, fecha, dispositivo))
    conn.commit()
    conn.close()
def registrar_acceso(username, ip, ubicacion, dispositivo, fecha, exito):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO accesos (username, ip, ubicacion, dispositivo, fecha, exito)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, ip, ubicacion, dispositivo, fecha, exito))
    conn.commit()
    conn.close()