# Secret Santa di famiglia (9 persone)

Leggi prima `C:\Users\massi\.claude\CLAUDE.md`. Questo file vale per questo progetto.
Creato l'11 novembre 2026.

## Cos'è
Estrazione dei regali di Natale per 9 persone (Massimo, Cristiana, Giorgia, Lorenzo, Luca, Laura, Ivo, Maria Elena, Francesca). Ognuno riceve un LINK PERSONALE: pagina web animata (copertina con i 9 ritratti → regolamento con budget 50 € → busta con sigillo di ceralacca da tenere premuto → fuochi d'artificio → nome del destinatario). Massimo non deve conoscere gli abbinamenti degli altri.

## ATTENZIONE: l'estrazione è già stata fatta (11 novembre 2026)
- **MAI rilanciare `genera.py` e MAI cancellare la cartella `pagine/`**: rifarebbe l'estrazione e i link già inviati smetterebbero di funzionare (lo script si rifiuta se `pagine/` esiste).
- Regole: ognuno regala a una persona sola e riceve da una sola; nessuno a se stesso; vietate le coppie Massimo↔Giorgia, Cristiana↔Lorenzo, Luca↔Laura, Ivo↔Maria Elena (in entrambe le direzioni); lo scambio reciproco A→B e B→A è permesso.
- Gli abbinamenti non sono scritti in chiaro da nessuna parte: ogni pagina in `pagine/<codice>.html` contiene il nome del destinatario cifrato (AES-GCM); la chiave sta nel link, dopo il `#`, e non va mai al server.
- `LINK_DA_INVIARE.txt` contiene i 9 link completi: è in `.gitignore`, mai su GitHub, mai in chat (salvo il link di Massimo su sua richiesta). Non leggere né riassumere gli abbinamenti.
- Se serve cambiare qualcosa nelle pagine dopo l'estrazione si fa un cambio di testo nei 9 file di `pagine/` (come fatto per `og:description`), senza toccare `CIFRATO`/`IV`; poi si controlla che si decifrino ancora.

## Dove sta
- Cartella `D:\Progetti\SecretSanta`, repo `MaxStar85/SecretSanta` (PUBBLICO, GitHub Pages dal ramo `main`, radice). Indirizzo: `https://maxstar85.github.io/SecretSanta/`. Account personale scelto da Massimo: il nome compare nel link.
- Niente Flask, database o Render: sito statico.
- Il push lo fa Massimo con GitHub Desktop. Nei commit NIENTE riga `Co-Authored-By` (regola globale: GitHub mostrerebbe Claude tra i contributori).

## File
- `modello.html`: la pagina (un solo file con CSS e JS; segnaposto `__NOME__`, `__SLUG__`, `__BASE__`, `__CIFRATO__`, `__IV__`). Soglie responsive: telefono in verticale; in orizzontale compare l'invito a girare il telefono.
- `genera.py` (estrazione + pagine), `crea_prova.py` (pagina di prova con dati finti in `prova/index.html`, link `.../prova/`), `mockup.html` (vecchio, dati finti).
- `crea_asset.py` (busta e ceralacca), `crea_asset_natale.py` (ghirlanda, lucine, palline, pupazzi, suolo di neve), `crea_card.py` (card 1200×630 per l'anteprima WhatsApp, una per persona): immagini calcolate con numpy/PIL in `assets/`. Si rilanciano solo se si cambia la grafica.
- `foto/<nome>.jpg`: i ritratti (illustrazioni natalizie), con `maria-elena.jpg` col trattino.
- Le pagine caricano `../assets/...` e `../foto/...`: devono stare un livello sotto la radice (`pagine/`, `prova/`).
- Anteprima WhatsApp: tag Open Graph nel `<head>`; la card e il testo ("Anche quest'anno c'è il Secret Santa di famiglia! …") sono già dentro il link. WhatsApp tiene in memoria le anteprime: per riprovare un indirizzo già visto aggiungere `?v=2`.

## Effetto di apertura
Tenere premuto il sigillo ~1,5 s (energia, onde dorate, calore) → sigillo che si spezza + fuochi d'artificio su canvas (`Fuochi`) + lampo → compare il destinatario.

## Cornice Android per la mamma (Francesca)
Nel repo privato `StarLoad`, cartella `SecretSanta/android/` (vedi il suo CLAUDE.md, sezione 5). Telefono: OnePlus Nord 2 con Starnova. Il link di Francesca sta dentro `MainActivity.kt`: non stamparlo.

## Cose da non rifare
- Non usare box-shadow animati su elementi rotondi (sui telefoni compare un riquadro quadrato attorno): usare sfumature radiali con opacità/scala.
- I comandi lunghi in shell con apostrofi rompono lo script: scrivere uno script in file (scratchpad) e lanciarlo.
