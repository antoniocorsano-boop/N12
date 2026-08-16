# Inventario artefatti storici

Gli artefatti binari originali devono essere conservati senza modificarli. Questo inventario registra ciò che è stato verificato nei pacchetti storici.

## Pacchetto DXF strutturale v25

Artefatti verificati come presenti:

- `TAV5_CARPENTERIA.dxf`
- `TAV6_TRAVI.dxf`
- `TAV7_PILASTRI.dxf`
- `ABACO_TOPOLOGICO_TAV5_v11.csv`
- `ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv`
- `MATRICE_PILASTRI_27x5_v22.csv`
- `ABACO_TRAVI_TAV6_v23.csv`
- `ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv`
- ulteriori DXF di controllo relativi a catene verticali, tipi di pilastro e famiglie di travi.

## Interpretazione

L'abaco topologico contiene ID e coordinate X,Y. La presenza nei registri di riferimenti a ID superiori a N057 impedisce di assumere che i 57 nodi costituiscano automaticamente l'intero universo geometrico della carpenteria.

Le associazioni geometriche delle travi provenienti dal v25 restano proposte geometriche finché non ricevono un secondo riscontro documentale.

## Politica archivio

Gli ZIP storici sono evidenza immutabile. I dati utilizzati dal modello devono essere estratti in `data/canonical/` con provenienza esplicita e stato di evidenza.
