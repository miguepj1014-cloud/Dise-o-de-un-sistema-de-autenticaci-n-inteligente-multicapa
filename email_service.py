import smtplib
import sqlite3
import json
from dotenv import load_dotenv
import os
load_dotenv()
correo_servicio_smtp = os.getenv("CORREO_SERVICIO_SMTP")
contrasena_servicio_smtp = os.getenv("CONTRASENA_SERVICIO_SMTP")
def enviar_codigo(destinatario, codigo):
    remitente = correo_servicio_smtp
    password = contrasena_servicio_smtp
    mensaje = f"Subject: Codigo de verificacion\n\nTu codigo es: {codigo}"
    servidor = smtplib.SMTP("smtp.gmail.com", 587)
    servidor.starttls()
    servidor.login(remitente, password)
    servidor.sendmail(remitente, destinatario, mensaje)
    servidor.quit()
def enviar_llave_desde_bd(username):
    with sqlite3.connect("usuarios.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email, llave_maestra FROM usuarios WHERE username = ?", (username,))
        resultado = cursor.fetchone()
        if not resultado:
            print("Usuario no encontrado")
            return None
        correo, llaves_json = resultado
        if not llaves_json:
            print("No hay llaves guardadas")
            return None
        try:
            llaves = json.loads(llaves_json)
            if isinstance(llaves, str): 
                llaves = json.loads(llaves)
        except json.JSONDecodeError:
            print("Error al leer las llaves")
            return None
        if not isinstance(llaves, list) or not llaves:
            print("No tienes llaves disponibles")
            return None
        llave = llaves.pop(0)
        cursor.execute(
            "UPDATE usuarios SET llave_maestra = ? WHERE username = ?",
            (json.dumps(llaves), username)
        )
        conn.commit()
        enviar_codigo(correo, llave)
        print("Se envió una llave maestra a tu correo")
        return llave