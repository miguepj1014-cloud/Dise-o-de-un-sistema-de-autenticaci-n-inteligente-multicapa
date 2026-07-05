import sqlite3
import bcrypt
import json
import requests
import platform
from datetime import datetime
from wasap import enviar_llave_wasap_desde_bd, enviar_mensaje_wasap
from email_service import enviar_codigo
from security import generar_codigo
from security import generar_llaves_maestras
def obtener_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "Desconocida"
def obtener_ubicacion(ip):
    try:
        data = requests.get(f"http://ip-api.com/json/{ip}").json()
        return f"{data.get('city', 'Desconocida')}, {data.get('country', 'Desconocido')}"
    except:
        return "Ubicación desconocida"
def obtener_fecha():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def obtener_dispositivo():
    return platform.system() + " " + platform.release()
def registrar_usuario(username, password,Categoria, the_word, email, Numtelefono):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    ip = obtener_ip()
    ubicacion = obtener_ubicacion(ip)
    fecha = obtener_fecha()
    dispositivo = obtener_dispositivo()
    llave_maestra = json.dumps(generar_llaves_maestras())
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        cursor.execute("""
            INSERT INTO usuarios
            (username, password_hash, llave_maestra,Categoria, the_word, email, Numtelefono,ip,ubicacion,fecha_registro,dispositivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            password_hash,
            llave_maestra,
            Categoria,
            the_word,
            email,
            Numtelefono,
            ip,
            ubicacion,
            fecha,
            dispositivo
        ))
        conn.commit()
        return "Usuario registrado correctamente"
    except sqlite3.IntegrityError:
        return "El usuario ya existe"
    except Exception as e:
        print(" ERROR:", e)
        return False
    finally:
        conn.close()
def verificar_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode()), "ok"
    except:
        return False, "error"
def login_total(username):
    from email_service import enviar_llave_desde_bd
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT password_hash, llave_maestra, email, the_word, categoria,Numtelefono, ip, ubicacion, dispositivo
        FROM usuarios
        WHERE username = ?
    """, (username,))
    resultado = cursor.fetchone()
    ip_actual = obtener_ip()
    ubicacion_actual = obtener_ubicacion(ip_actual)
    dispositivo_actual = obtener_dispositivo()
    if not resultado:
        return "Usuario no encontrado"
    password_hash, llaves_json, correo, palabra_seguridad, categoria, Numtelefono, ip, ubicacion, dispositivo = resultado
    llaves = json.loads(llaves_json)
    intentos_password = 0
    while intentos_password < 2:
        credencial = input("Contraseña: ")
        if bcrypt.checkpw(credencial.encode(), password_hash.encode()):
            codigo = generar_codigo()
            print(" Acceso correcto")
            if (ip_actual == ip and 
                ubicacion_actual == ubicacion and 
                dispositivo_actual == dispositivo):
                print(" Acceso seguro confirmado")
            elif (ip_actual == ip and 
                ubicacion_actual == ubicacion and 
                dispositivo_actual != dispositivo):
                print(" Nuevo dispositivo detectado (misma red)")
            elif (ip_actual != ip and 
                dispositivo_actual != dispositivo):
                print(" Acceso bloqueado: entorno desconocido")
                return
            else:
                print(" Comportamiento sospechoso")
            enviar_mensaje_wasap(f"Tu código de acceso es: {codigo}", Numtelefono)
            enviar_codigo(correo, codigo)
            intento = input("Código enviado al correo: ")
            if intento == codigo:
                print(" Acceso total concedido")
                return
            else:
                print(" Código incorrecto")
                return
        else:
            intentos_password += 1
            print(f" Contraseña incorrecta ({intentos_password}/2)")
    while True:
        print(" Probrar otra opción para recuperar acceso:")
        print("1. Reintentar contraseña")
        print("2. Llave maestra (correo & whatsapp)")
        print("3. Palabra de seguridad")
        print("4. Salir")
        opcion = input("Elige opción: ")
        if opcion == "1":
            intentos_reintento = 0
            while intentos_reintento < 2:
                credencial = input("Contraseña: ")
                if bcrypt.checkpw(credencial.encode(), password_hash.encode()):
                    print(" Acceso concedido")
                    return
                else:
                    intentos_reintento += 1
                    print(f" Incorrecto ({intentos_reintento}/2)")
            print(" Límite alcanzado en contraseña")
        elif opcion == "2":
            intentos_llave = 0
            while intentos_llave < 2:
                llave = enviar_llave_desde_bd(username)
                llave= enviar_llave_wasap_desde_bd(username)
                if not llave:
                    return
                intento = input("Ingresa la llave enviada: ")
                if intento == llave:
                    print(" Acceso concedido")
                    return
                else:
                    intentos_llave += 1
                    print(f" Llave incorrecta ({intentos_llave}/2)")
            print(" Límite de llaves alcanzado")
        elif opcion == "3":
            import random
            intentos_palabra = 0
            categorias_base = {
                "A": ["rojo", "azul", "verde","amarillo", "negro", "blanco","gris", "rosado", "morado"],
                "B": ["perro", "gato", "ratón","jirafa", "león", "tigre","elefante", "conejo", "oso"],
                "C": ["pizza", "hamburguesa", "arroz","pollo", "sopa", "pan","queso", "ensalada", "pasta"]
            }
            while intentos_palabra < 2:
                print(" Selecciona la categoría:")
                print("A. Colores ")
                print("B. Animales ")
                print("C. Comida ")
                cat_user = input("Categoría: ").upper()
                if cat_user != categoria:
                    intentos_palabra += 1
                    print(f" Categoría incorrecta ({intentos_palabra}/2)")
                    continue
                base = categorias_base[categoria].copy()
                if palabra_seguridad not in base:
                    base.append(palabra_seguridad)
                random.shuffle(base)
                print("Elige tu palabra:")
                for i, palabra in enumerate(base, 1):
                    print(f"{i}. {palabra}")
                try:
                    op = int(input("Opción: "))
                    if base[op - 1] == palabra_seguridad:
                        print(" Acceso concedido")
                        return
                    else:
                        intentos_palabra += 1
                        print(f" Palabra incorrecta ({intentos_palabra}/2)")
                except:
                    print(" Opción inválida")
            print(" Límite en palabra de seguridad")
        elif opcion == "4":
            print(" Saliendo...")
            return
        else:
            print(" Opción inválida")
def registrar_usuario_logica(username, password,Categoria, the_word, email, Numtelefono):
    return registrar_usuario(
            username,
            password,
            Categoria,
            the_word,
            email,
            Numtelefono,
    )