from database import crear_bd
from auth import registrar_usuario, login_total
from database import obtener_usuario
from auth import verificar_password
def login_usuario(username, password):
    datos = obtener_usuario(username)
    if not datos:
        return False
    password_hash, categoria, palabra = datos
    ok, msg = verificar_password(password, password_hash)
    return ok
def menu():
    while True:
        print("--- MENÚ ---")
        print("1. Registrarse")
        print("2. Iniciar sesión")
        print("3. Salir")
        opcion = input("Elige una opción: ")
        if opcion == "1":
            user = input("Usuario: ")
            password = input("Contraseña: ")
            email = input("Ingresa tu gmail: ")
            Numtelefono = input("Número de teléfono: ")
            the_word = ("Selección de palabra secreta")
            print("Categorías:")
            print("A - Colores")
            print("B - Animales")
            print("C - Comida")
            Categoria = input("Elige categoría: ").upper()
            Categorias = {
                "A": ["vino","malva","oliva","caoba","granate","aguamarina","maiz","añil","fandango","turquesa"],
                "B": ["krill","urraca","Star-noseDmole","Aye aye","tarsius tarsier","Uakarí","Macrocelidea","MYxini","Bata eniceps Rex","Kiwa hirsuta",],
                "C": ["escamoles","criadillas","Pizzushi","tequeños","Cachapas","schnitzel","Saverbraten","Eisbein","spatzle",]
            }
            if Categoria not in Categorias:
                print(" Categoría inválida")
                return
            print("Opciones:")
            for i, palabra in enumerate(Categorias[Categoria]):
                print(f"{i+1}. {palabra}")
            try:
                eleccion = int(input("Elige una opción: ")) - 1
                the_word = Categorias[Categoria][eleccion]
            except:
                print(" Opción inválida")
                return
            respuesta = registrar_usuario(user,password,Categoria,the_word,email,Numtelefono,)
            print(respuesta)
        elif opcion == "2":
            user = input("Usuario: ")
            login_total(user)
        elif opcion == "3":
            print("Saliendo...")
            break
        else:
            print("Opción inválida")
crear_bd()
if __name__ == "__main__":
 menu()