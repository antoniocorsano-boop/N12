# N12 — Sistema editoriale definitivo degli elaborati

Versione: `ED-TAV-0001` — 2026-08-16

## 1. Principio

Tutte le tavole devono appartenere a un unico sistema grafico, con numerazione stabile, riferimenti incrociati e cartiglio identico. Il contenuto tecnico resta subordinato al Registro Master: un dato ND/INC non viene trasformato in dato certo per esigenze grafiche.

## 2. Famiglie e codifica

- `TAV-00` — copertina e indice generale.
- `TAV-Axx` — stato di fatto architettonico, prospetti, sezioni e inquadramento.
- `TAV-S01..S06` — carpenterie strutturali dei livelli, dalle fondazioni alla copertura.
- `TAV-Rxx` — armature di travi/pilastri e particolari costruttivi.
- `TAV-Fxx` — fondazioni, sezioni e armature.
- `TAV-Mxx` — modello strutturale, viste 3D, telai, nomenclatura e corrispondenze EdiLus-EE.
- `TAV-Dxx` — degrado, rilievo, mappature e interventi, quando disponibili.

Ogni richiamo deve usare la forma `TAV-<famiglia><numero> / DET-<numero>` o `SEZ-<lettera>`; i nodi e gli elementi strutturali devono mantenere gli ID canonici del modello.

## 3. Cartiglio unico

Posizione: fascia verticale destra per tavole A1/A0; variante orizzontale inferiore ammessa solo quando necessaria, senza cambiare campi o gerarchia.

Campi obbligatori, nello stesso ordine:

1. **COMUNE DI ARIANO IRPINO (AV)** — eventuale stemma solo da fonte ufficiale.
2. **EDIFICIO ESISTENTE IN C.A. — Via Villa Caracciolo 30**.
3. **Fascicolo:** `N12 — Conoscenza, analisi e recupero dell'esistente`.
4. **Fase:** Conoscenza / Modellazione / Verifica / Recupero, secondo elaborato.
5. **Oggetto della tavola**.
6. **Titolo esteso dell'elaborato**.
7. **Codice tavola** in corpo dominante.
8. **Scala/e**; `NTS` per schemi non in scala.
9. **Data** e **revisione**.
10. **Fonte dati:** DOC / MIS / RIF / INF / ND, con rinvio al Registro Master quando necessario.
11. **Redazione / verifica / responsabile**: campi lasciati vuoti finché non documentati.
12. **Nome file canonico** e identificativo revisione.

## 4. Regole di riferimento

Ogni tavola strutturale deve riportare:

- assi/fili fissi e orientamento;
- quota/livello e corrispondenza con livello superiore/inferiore;
- identificativo di pilastri, travi, solai e fondazioni;
- sezioni solo quando documentate;
- freccia Nord sulle piante;
- rimando a sezioni e dettagli;
- legenda grafica uniforme;
- nota di provenienza dei dati;
- evidenza grafica distinta per `DOC`, `MIS`, `INF`, `ND` senza confondere dato certo e dato da verificare.

## 5. Copertina

Titolo principale:

**RECUPERO E VALORIZZAZIONE DELL'EDIFICIO ESISTENTE IN C.A.**

Sottotitolo:

**Dalla conoscenza della struttura alla sicurezza, dalla cura dell'esistente al futuro.**

Concetto visuale: edificio esistente reale/evocativo che transita dalla materia degradata alla struttura ricostruita digitalmente; la metà materica comunica memoria e vulnerabilità, la metà strutturale trasparente comunica conoscenza, diagnosi e progetto. Evitare l'immagine di una demolizione o di un edificio completamente nuovo: il messaggio deve essere il valore del recupero.

Parole chiave in copertina: **Conoscenza · Sicurezza · Durabilità · Recupero · Valorizzazione**.

## 6. Stato tecnico delle tavole

Le tavole possono essere completate editorialmente, ma la chiusura tecnica deve rispettare i residui M0: quote Z definitive, attribuzione puntuale delle famiglie di pilastri, Telaio 1 G2, materiali/LC/FC e raccordo globale dei nodi restano da congelare soltanto quando supportati da fonte. Il pacchetto EdiLus v18 qualifica infatti il modello come `M0-G/PRE-M0-S` e vieta di completare ND/INC per analogia.

## 7. Criterio di emissione

Una tavola passa a `EMESSA` soltanto dopo: controllo geometrico → controllo ID/riferimenti → controllo fonti → controllo scale/quote → controllo cartiglio → controllo incrociato con Registro Master → esportazione PDF.
