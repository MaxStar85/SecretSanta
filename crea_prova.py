"""
Crea la pagina di PROVA (nomi e abbinamenti finti) in prova/index.html,
partendo da modello.html. Serve solo per guardare la grafica sul telefono.
Si rilancia ogni volta che si cambia modello.html:  python crea_prova.py
"""
import os

cartella = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(cartella, "modello.html"), encoding="utf-8") as f:
    s = f.read()

# Nomi lunghi apposta, per mettere sotto stress il layout
s = s.replace("__NOME__", "Maria Elena")
s = s.replace("async function destinatario(){", 'async function destinatario(){return "Cristiana";')

os.makedirs(os.path.join(cartella, "prova"), exist_ok=True)
with open(os.path.join(cartella, "prova", "index.html"), "w", encoding="utf-8") as f:
    f.write(s)
print("Creata prova/index.html")
