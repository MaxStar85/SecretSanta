"""
Secret Santa: fa l'estrazione e crea una pagina per ogni persona.

Si lancia UNA SOLA VOLTA:  python genera.py
- Non stampa mai gli abbinamenti.
- Se la cartella "pagine" esiste già si rifiuta di rifare l'estrazione
  (altrimenti i link già inviati smetterebbero di funzionare).
- Crea la cartella "pagine" con un file HTML per persona (nome casuale)
  e il file LINK_DA_INVIARE.txt (nome -> file, senza abbinamenti).
"""
import base64
import os
import secrets
import sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CARTELLA = os.path.dirname(os.path.abspath(__file__))
USCITA = os.path.join(CARTELLA, "pagine")

# Indirizzo del sito (GitHub Pages): serve per i link e per l'anteprima su WhatsApp
BASE_URL = "https://maxstar85.github.io/SecretSanta"

NOMI = ["Massimo", "Cristiana", "Giorgia", "Lorenzo", "Luca",
        "Laura", "Ivo", "Maria Elena", "Francesca"]

# Coppie che non possono regalarsi a vicenda (in entrambe le direzioni)
VIETATE = [("Massimo", "Giorgia"), ("Cristiana", "Lorenzo"),
           ("Luca", "Laura"), ("Ivo", "Maria Elena")]
PROIBITO = {(a, b) for a, b in VIETATE} | {(b, a) for a, b in VIETATE}


def b64url(dati: bytes) -> str:
    return base64.urlsafe_b64encode(dati).decode().rstrip("=")


def estrai():
    """Estrazione simultanea: una permutazione valida di tutti i nomi."""
    rng = secrets.SystemRandom()
    for _ in range(100000):
        riceventi = NOMI[:]
        rng.shuffle(riceventi)
        if all(d != r and (d, r) not in PROIBITO for d, r in zip(NOMI, riceventi)):
            return dict(zip(NOMI, riceventi))
    raise SystemExit("Nessuna estrazione valida trovata (regole impossibili?)")


def main():
    if os.path.exists(USCITA):
        print("La cartella 'pagine' esiste già: estrazione GIÀ fatta.")
        print("Non la rifaccio, altrimenti i link già inviati non andrebbero più bene.")
        print("Se vuoi davvero rifarla, cancella tu la cartella 'pagine' a mano.")
        sys.exit(1)

    for n in NOMI:   # le card dell'anteprima devono esistere (python crea_card.py)
        if not os.path.exists(os.path.join(CARTELLA, "assets", "card-" + n.lower().replace(" ", "-") + ".jpg")):
            print("Manca la card di", n, "-> lancia prima: python crea_card.py")
            sys.exit(1)

    with open(os.path.join(CARTELLA, "modello.html"), encoding="utf-8") as f:
        modello = f.read()

    abbinamenti = estrai()

    # Controllo finale (non stampa nulla): ognuno dà e riceve una sola volta, regole rispettate
    assert sorted(abbinamenti.keys()) == sorted(NOMI)
    assert sorted(abbinamenti.values()) == sorted(NOMI)
    assert all(d != r and (d, r) not in PROIBITO for d, r in abbinamenti.items())

    os.makedirs(USCITA)
    righe = []
    for nome in NOMI:
        chiave = AESGCM.generate_key(bit_length=128)
        iv = secrets.token_bytes(12)
        cifrato = AESGCM(chiave).encrypt(iv, abbinamenti[nome].encode("utf-8"), None)
        pagina = (modello.replace("__NOME__", nome)
                         .replace("__SLUG__", nome.lower().replace(" ", "-"))
                         .replace("__BASE__", BASE_URL)
                         .replace("__CIFRATO__", b64url(cifrato))
                         .replace("__IV__", b64url(iv)))
        nome_file = secrets.token_urlsafe(12) + ".html"   # non indovinabile
        with open(os.path.join(USCITA, nome_file), "w", encoding="utf-8") as f:
            f.write(pagina)
        # La chiave sta nella parte dopo il # del link: non viene mai inviata al server
        righe.append(f"{nome}: {BASE_URL}/pagine/{nome_file}#{b64url(chiave)}")

    with open(os.path.join(CARTELLA, "LINK_DA_INVIARE.txt"), "w", encoding="utf-8") as f:
        f.write("Ogni riga e' il link COMPLETO di UNA persona (comprese le lettere dopo il #).\n"
                "Copialo per intero e mandalo solo a quella persona.\n\n")
        f.write("\n".join(righe) + "\n")

    print(f"Fatto: create {len(NOMI)} pagine nella cartella 'pagine'.")
    print("I link sono in LINK_DA_INVIARE.txt (gli abbinamenti non sono scritti da nessuna parte).")


if __name__ == "__main__":
    main()
