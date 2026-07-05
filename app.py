from flask import Flask, request, jsonify, render_template, session
from email_service import (enviar_llave_desde_bd,enviar_codigo)
from wasap import enviar_llave_wasap
from auth import registrar_usuario_logica
from datetime import datetime
from flask_cors import CORS
from security import generar_codigo
import sqlite3
import bcrypt
import requests
import platform
import numpy as np
from dotenv import load_dotenv
import os
load_dotenv() 
puerto_api = os.getenv("PORT_API", "5000")
puerto_frontend = os.getenv("PORT_FRONTEND", "5050")
status_debug = os.getenv("DEBUG", "true")
app = Flask(__name__)
app.secret_key = "mi_clave_secreta"
CORS(app, supports_credentials=True)
def obtener_ip():
    try:
        return requests.get(
            "https://api.ipify.org"
        ).text
    except:
        return "Desconocida"
def obtener_ubicacion(ip):
    try:

        data = requests.get(
            f"http://ip-api.com/json/{ip}"
        ).json()
        return (
            f"{data.get('city','Desconocida')}, "
            f"{data.get('country','Desconocido')}"
        )
    except:

        return "Ubicación desconocida"
def obtener_dispositivo():
    return (
        platform.system()
        + " "
        + platform.release()
    )
def registrar_acceso(
    username,
    ip,
    ubicacion,
    dispositivo,
    exito
):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accesos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        ip TEXT,
        ubicacion TEXT,
        dispositivo TEXT,
        exito TEXT,
        fecha TEXT
    )
    """)
    cursor.execute("""
    INSERT INTO accesos
    (
        username,
        ip,
        ubicacion,
        dispositivo,
        exito,
        fecha
    )
    VALUES (?,?,?,?,?,?)
    """,
    (
        username,
        ip,
        ubicacion,
        dispositivo,
        exito,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))
    conn.commit()
    conn.close()
CORS(
    app,
    supports_credentials=True,
    origins=["http://localhost:"+puerto_frontend]
)
@app.route('/')
def home():
    return render_template('login.html')
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get('password')
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
        password_hash,
        ip,
        ubicacion,
        dispositivo
        FROM usuarios 
        WHERE username = ?
        """,
        (username,)
    )
    usuario = cursor.fetchone()
    conn.close()
    if usuario is None:
        return jsonify({
            "redirect": "/password_incorrecta"
        })
    password_hash = usuario[0]
    if bcrypt.checkpw(
        password.encode(),
        password_hash.encode()
    ):
        ip_guardada = usuario[1]
        ubicacion_guardada = usuario[2]
        dispositivo_guardado = usuario[3]
        ip_actual = obtener_ip()
        ubicacion_actual = obtener_ubicacion(ip_actual)
        dispositivo_actual = obtener_dispositivo()
        hora_actual = datetime.now().hour
        print(ip_actual , ip_guardada ,ubicacion_actual,ubicacion_guardada ,dispositivo_actual ,dispositivo_guardado)
        riesgo = "BAJO"
        if (
            ip_actual == ip_guardada and
            ubicacion_actual == ubicacion_guardada and
            dispositivo_actual == dispositivo_guardado
        ):

            riesgo = "BAJO"
        elif (ubicacion_actual == ubicacion_guardada and (ip_actual != ip_guardada or dispositivo_actual != dispositivo_guardado)
        ):

            riesgo = "MEDIO"
        else:

            riesgo = "ALTO"
        conn = sqlite3.connect("usuarios.db")
        cursor = conn.cursor()
        # =========================
        # 1. Contar intentos
        cursor.execute("""
        SELECT COUNT(*) 
        FROM accesos 
        WHERE username = ?
        """, (username,))
        result = cursor.fetchone()
        print("DEBUG result:", result)
        intentos_fallidos = result[0] if result else 0
        print("INTENTOS:", intentos_fallidos)
        # =========================
        # 2. Login actual como vector
        login_vector = np.array([
            1 if ip_actual == ip_guardada else 0,
            1 if ubicacion_actual == ubicacion_guardada else 0,
            1 if dispositivo_actual == dispositivo_guardado else 0,
            hora_actual / 24
        ])
        # =========================
        # 3. Obtener historial real
        cursor.execute("""
            SELECT ip, ubicacion, dispositivo, fecha
            FROM accesos
            WHERE username = ?
        """, (username,))
        rows = cursor.fetchall()
        # =========================
        # 4. Construir vectores reales del historial
        historial_vectors = []
        for ip, ubicacion, dispositivo, fecha in rows:
            vec = np.array([
                1 if ip == ip_guardada else 0,
                1 if ubicacion == ubicacion_guardada else 0,
                1 if dispositivo == dispositivo_guardado else 0,
                int(fecha.split(" ")[1].split(":")[0]) / 24  # hora desde timestamp
            ])
            historial_vectors.append(vec)
        historial_matrix = np.array(historial_vectors)
        # =========================
        # 5. Perfil real del usuario
        user_profile = np.mean(historial_matrix, axis=0)
        # =========================
        # 6. Score de riesgo (distancia)
        risk_score = np.linalg.norm(login_vector - user_profile)
        # =========================
        # 7. Normalizar riesgo (opcional pero recomendado)
        risk_score = risk_score / np.sqrt(len(login_vector))
        conn.close()
        registrar_acceso(
            username,
            ip_actual,
            ubicacion_actual,
            dispositivo_actual,
            exito=0 if riesgo == "ALTO" else 1
        )
        if riesgo == "ALTO":
            return jsonify({
                "success":False,
                "message":"No se pudo validar el acceso"

            })
        print("RIESGO CLÁSICO:", riesgo)
        print("RIESGO NUMPY:", float(risk_score))
        session["usuario_2fa"] = username
        return jsonify({
            "success": True,
            "message":
            "Verificación requerida"
        })
    session["usuario_recuperacion"] = username
    return jsonify({

        "redirect": "/password_incorrecta"
    })
@app.route('/verificar_llave', methods=['POST'])
def verificar_llave():
    data = request.get_json()
    llave_usuario = data.get('llave')
    llave_real = session.get("llave_enviada")
    if llave_usuario == llave_real:
        session["username"] = session.get(
            "usuario_recuperacion"
        )
        return jsonify({
            "success": True
        })
    return jsonify({
        "success": False,
        "message": "Llave incorrecta"
    })
@app.route('/enviar_llave', methods=['POST'])
def enviar_llave():
    print("SESSION:", dict(session))
    username = session.get("usuario_recuperacion")
    print("USERNAME:", username)
    if not username:
        return jsonify({
            "success": False,
            "message": "No hay usuario en sesión"
        })
    llave = enviar_llave_desde_bd(username)
    if not llave:
        return jsonify({
            "success": False,
            "message": "Usuario no encontrado"
        })
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Numtelefono
        FROM usuarios
        WHERE username = ?
    """, (username,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        telefono = resultado[0]
        enviar_llave_wasap(
            telefono,
            llave
        )
    print("Usuario:", username)
    print("Llave enviada:", llave)
    session["llave_enviada"] = llave
    return jsonify({
        "success": True,
        "message": "Llave enviada por correo y WhatsApp"
    })
@app.route('/registro')
def vista_registro():
    return render_template('registro.html')
@app.route('/registrar', methods=['POST'])
def registrar_usuario():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    Numtelefono = data.get('telefono')
    categoria = data.get('categoria')
    the_word = data.get('the_word')
    resultado = registrar_usuario_logica(
        username,
        password,
        categoria,
        the_word,
        email,
        Numtelefono
    )
    if resultado:
        return jsonify({"message": resultado})
    else:
        return jsonify({"message": "Error al registrar"})
@app.route('/datos_perfil')
def datos_perfil():
    print("SESSION:", dict(session))
    username = session.get("usuario_2fa")
    if(username == None):
        username = session.get("username")
    print("USERNAME:", username)
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username,
               password_hash,
               email,
               Numtelefono
        FROM usuarios
        WHERE username = ?
    """, (username,))
    usuario = cursor.fetchone()
    conn.close()
    if usuario:
        return jsonify({
            "username": usuario[0],
            "password": "••••••••",
            "email": usuario[2],
            "telefono": usuario[3]
        })
    return jsonify({"error": "Usuario no encontrado"})
@app.route('/perfil')
def perfil():
    return render_template('perfil.html')
@app.route('/password_incorrecta')
def password_incorrecta():
    return render_template('error_password.html')
@app.route('/recuperar')
def recuperar():
    return render_template('recuperar.html')
@app.route('/llave_maestra')
def llave_maestra():
    return render_template('llave_maestra.html')
@app.route('/palabra_seguridad')
def palabra_seguridad():
    username = session.get("usuario_recuperacion")
    if not username:
        return "No hay usuario para recuperar"
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT the_word
        FROM usuarios
        WHERE username = ?
    """,(username,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado is None:
        return "Usuario no encontrado"
    palabra = resultado[0]
    return render_template(
        "palabra_seguridad.html",
        palabra=palabra
    )
@app.route('/verificar_palabra', methods=['POST'])
def verificar_palabra():
    data = request.get_json()
    palabra_usuario = data.get("palabra")
    username = session.get(
        "usuario_recuperacion"
    )
    if not username:
        return jsonify({
            "success":False,
            "message":"Sesión perdida"
        })
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT the_word
        FROM usuarios
        WHERE username = ?
    """,(username,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        palabra_real = resultado[0]
        if palabra_usuario == palabra_real:
            session["username"] = username
            return jsonify({

                "success":True
            })
    return jsonify({
        "success":False,
        "message":"Palabra incorrecta"
    })
@app.route('/autenticador')
def autenticador():
    return render_template('autenticador.html')
@app.route('/terminos')
def terminos():
    return render_template('terminos.html')
@app.route('/conoce_sistema')
def conoce_sistema():
    return render_template('conoce_sistema.html')
@app.route('/codigo_acceso')
def codigo_acceso():
    return render_template('codigo_acceso.html')
@app.route('/generar_codigo', methods=['POST'])
def generar_codigo_ruta():
    print("SESSION:", dict(session))
    username = session.get("usuario_2fa")
    if(username == None):
        username = session.get("usuario_recuperacion")
    if not username:
        return jsonify({
            "success":False,
            "message":
            "No hay usuario para verificar"
        })
    codigo = generar_codigo()
    session["codigo_acceso"] = codigo
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email, Numtelefono
        FROM usuarios
        WHERE username = ?
    """,(username,))
    usuario = cursor.fetchone()
    conn.close()
    if usuario:
        email = usuario[0]
        telefono = usuario[1]
        enviar_codigo(
            email,
            codigo
        )
        enviar_llave_wasap(
            telefono,
            codigo
        )
    print(
        "CODIGO GENERADO:",
        codigo
    )
    return jsonify({
        "success":True,
        "message":
        "Código enviado a correo y WhatsApp"
    })
@app.route('/verificar_codigo', methods=['POST'])
def verificar_codigo():
    data = request.get_json()
    codigo_usuario = data.get("codigo")
    codigo_real = session.get(
        "codigo_acceso"
    )
    if codigo_usuario == codigo_real:
        session["username"] = session.get("usuario_recuperacion" )
        session.pop("codigo_acceso", None)
        session.pop("usuario_recuperacion", None)
        return jsonify({
            "success": True

        })
    return jsonify({
        "success": False,
        "message":
        "Código incorrecto"
    })
if __name__ == "__main__":
    app.run(
        port=puerto_frontend,
        debug=status_debug
    )