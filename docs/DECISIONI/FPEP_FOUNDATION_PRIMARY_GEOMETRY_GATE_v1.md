# Decisione FPEP — geometria primaria fondazioni prima di M1-F

Data: 2026-08-24

## Decisione

`M1F-FOUNDATION-MODEL` non può più iniziare dalla riconciliazione con PT/M0-G. È preceduto dal work item obbligatorio `M1F-PRIMARY-GEOMETRY-REVALIDATION`, eseguito tramite `N12_FPEP_FOUNDATION_PRIMARY_EVIDENCE_PIPELINE`.

## Motivazione

La carpenteria fondazioni `TAV-01S` è l'autorità geometrica primaria. TAV-01A documenta armature/sezioni; PT Master, M0-G e topologia M1-F preesistente sono derivati o cross-check. Fornirli ai reader prima della lettura primaria creerebbe rischio di conferma del risultato atteso.

## Checkpoint preservato

La topologia M1-F preesistente (38 supporti / 58 membri / una componente) non viene cancellata né degradata. È congelata come `REGRESSION_CHECKPOINT` e diventa visibile solo dopo `FPEP-P07-PRIMARY-GEOMETRY-GATE`.

## Regola di conflitto

Una differenza emersa da TAV-01S non riapre automaticamente M0-G. Si riapre il claim fondale minimo; soltanto un claim primario `CROSS_VALIDATED` che incida sull'identità/posizione globale dei sostegni può generare una richiesta formale `M0G-REOPEN`.

## Effetto sulla coda

`M1L-LOAD-MODEL -> M1F-PRIMARY-GEOMETRY-REVALIDATION -> M1F-FOUNDATION-MODEL -> M1E-CALCULATION-MODEL-HANDOFF`.

La sotto-coda FPEP P00-P12 applica letture cieche indipendenti, metric/topology gate, adjudication e cross-check downstream.
