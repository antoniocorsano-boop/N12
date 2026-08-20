# Protocollo permanente di aggiornamento dei file Master

## Regola vincolante
Ogni nuova informazione utile prodotta da una qualunque elaborazione deve essere registrata nello stesso passaggio anche nel relativo file Master corrente del dominio interessato.

I file specialistici di analisi restano come evidenza e tracciabilità, ma non costituiscono da soli lo stato canonico corrente.

## Stato canonico PT
Per il piano terra il file Master corrente è:

`data/canonical/PT_MASTER_CURRENT.csv`

Deve contenere, per ogni pilastro/nodo pertinente:
- identificativo;
- tipologia;
- coordinate globali X,Y;
- stato delle coordinate;
- sezione;
- orientamento;
- identificativo del dettaglio TAV.7;
- stato dell'assegnazione;
- provenienza/evidenza;
- residui e note.

## Procedura obbligatoria ad ogni nuova elaborazione
1. leggere il Master corrente prima di iniziare;
2. produrre il file specialistico dell'elaborazione, se necessario;
3. aggiornare immediatamente il Master con i nuovi dati confermati;
4. non cancellare le incertezze: marcarle come ND, CONFLICT, RESIDUAL o SUPERSEDED secondo il caso;
5. non promuovere inferenze a DOC;
6. mantenere nei campi di evidenza il riferimento alla tavola, quota o elaborazione da cui deriva il dato;
7. considerare il Master come unico punto di ripresa operativa per le elaborazioni successive.

## Principio di continuità
La chat e i file intermedi sono strumenti di elaborazione. Il repository, attraverso i file Master correnti, è la memoria tecnica persistente e canonica del progetto.

Questa regola si applica anche ai domini successivi: fondazioni, travi, solai, livelli, materiali, armature, carichi, degrado e verifiche. Per ogni dominio va mantenuto un file Master corrente oppure, quando il modello sarà maturo, una vista Master unica derivata in modo controllato dai Master di dominio.
