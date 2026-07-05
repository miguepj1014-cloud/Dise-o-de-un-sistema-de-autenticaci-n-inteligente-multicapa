import random
import string
import json
def generar_codigo():
    return str(random.randint(100000, 999999))
def generar_llaves_maestras(cantidad=10):
    llaves = []
    for _ in range(cantidad):
        llave = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        llaves.append(llave)
    return json.dumps(llaves)