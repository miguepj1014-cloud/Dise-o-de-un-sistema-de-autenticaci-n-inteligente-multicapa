from flask import json
import requests
import security
import sqlite3
from dotenv import load_dotenv
import os
load_dotenv()
token_whataspp = os.getenv("TOKEN_WHATSAPP")
numero_whatsapp = os.getenv("NUMERO_WHATSAPP")
TOKEN = token_whataspp
PHONE_ID = numero_whatsapp
codigo = security.generar_codigo()
def enviar_mensaje_wasap(texto, Numtefono):
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": Numtefono,
        "type": "text",
        "text": {"body": texto}
    }
    respuesta = requests.post(url, headers=headers, json=data)
    print("Status:", respuesta.status_code)
    print("Respuesta:", respuesta.text)
def enviar_llave_wasap(telefono, llave):
    mensaje = f"Tu llave maestra es: {llave}"
    enviar_mensaje_wasap(
        mensaje,
        telefono
    )
def enviar_llave_wasap_desde_bd(username):
    with sqlite3.connect("usuarios.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Numtelefono, llave_maestra
            FROM usuarios
            WHERE username = ?
        """, (username,))
        resultado = cursor.fetchone()
        if not resultado:
            print("Usuario no encontrado")
            return None
        telefono, llaves_json = resultado
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
        mensaje = f"Tu llave maestra es: {llave}"
        enviar_mensaje_wasap(mensaje, telefono)
        print("Llave enviada por WhatsApp ")
        return llave