from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import bcrypt
import random
app = Flask(__name__)
CORS(app)
ultimo_codigo = None
def verificar_usuario(username, password):
    try:
        conn = sqlite3.connect("usuarios.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT password_hash
            FROM usuarios
            WHERE username = ?
            """,
            (username,)
        )
        resultado = cursor.fetchone()
        conn.close()
        if resultado is None:
            print("Usuario no encontrado")
            return False
        password_hash = resultado[0]
        return bcrypt.checkpw(
            password.encode(),
            password_hash.encode()
        )
    except Exception as e:
        print("ERROR verificando usuario:", e)
        return False
@app.route("/")
def home():
    return "Servidor Flask funcionando"
@app.route("/api/login", methods=["POST"])
def login():
    global ultimo_codigo
    print("\n==============================")
    print("PETICION RECIBIDA")
    print("==============================")
    data = request.get_json(silent=True)
    print("JSON recibido:", data)
    if not data:
        return jsonify({
            "status": "error",
            "message": "No JSON"
        }), 400
    username = data.get("username")
    password = data.get("password")
    print("Usuario:", username)
    user = verificar_usuario(username, password)
    if user:
        codigo = random.randint(10, 99)
        ultimo_codigo = codigo
        print("Login correcto")
        print("Codigo generado:", codigo)
        return jsonify({
            "status": "success",
            "message": "Login correcto",
            "codigo": codigo
        })
    print("Credenciales incorrectas")
    return jsonify({
        "status": "error",
        "message": "Credenciales incorrectas"
    }), 401
@app.route("/obtener_codigo")
def obtener_codigo():
    return jsonify({
        "codigo": ultimo_codigo
    })
if __name__ == "__main__":
    print("===================================")
    print("SERVIDOR INICIADO")
    print("Base de datos: usuarios.db")
    print("Puerto: 5000")
    print("===================================")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )