import { useEffect, useMemo, useRef, useState } from 'react';
import OpenSeadragon from 'openseadragon';
import {
  Button,
  Disclosure,
  DisclosurePanel,
  Heading,
  Input,
  Label,
  Radio,
  RadioGroup,
  TextArea,
  TextField
} from 'react-aria-components';
import {
  loadRuntimeManifest,
  manifestMatchesSnapshot,
  snapshot,
  type DecisionOutcome,
  type RuntimeManifest
} from './cew/model';
import { buildDecisionProposal, type DecisionProposal } from './cew/decision';

const outcomeLabels: Record<DecisionOutcome, { title: string; detail: string }> = {
  UNBOUND: {
    title: 'Associazione non determinabile',
    detail: 'La fonte è leggibile ma non consente un legame strutturale affidabile.'
  },
  UNREADABLE: {
    title: 'Fonte non leggibile',
    detail: 'Il dettaglio non è interpretabile con affidabilità sufficiente.'
  },
  NEEDS_BETTER_SOURCE: {
    title: 'Serve una fonte migliore',
    detail: 'Occorre una scansione, tavola o dettaglio documentale di qualità superiore.'
  },
  NEEDS_SITE_SURVEY: {
    title: 'Serve verifica in sito',
    detail: 'La decisione richiede un rilievo o una verifica diretta.'
  },
  DEFER: {
    title: 'Rinvia la decisione',
    detail: 'Mantiene il caso aperto senza introdurre una conclusione tecnica.'
  }
};

export function HumanDecisionPanel({
  decisionEnabled,
  onProposal
}: {
  decisionEnabled: boolean;
  onProposal: (proposal: DecisionProposal) => void;
}) {
  const [outcome, setOutcome] = useState<DecisionOutcome | null>(null);
  const [reviewer, setReviewer] = useState('');
  const [observation, setObservation] = useState('');
  const [error, setError] = useState('');

  function prepareProposal() {
    setError('');
    if (!outcome) {
      setError('Seleziona un esito tecnico prima di preparare la ricevuta.');
      return;
    }
    try {
      onProposal(buildDecisionProposal(reviewer, outcome, observation));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Dati di revisione non validi.');
    }
  }

  return (
    <section className="decision-panel" aria-labelledby="decision-heading">
      <div className="panel-kicker">Decisione professionale</div>
      <Heading id="decision-heading" level={2}>Come deve essere trattata questa evidenza?</Heading>
      <p className="quiet">
        Nessuna opzione è preselezionata. Questa schermata produce solo una proposta recepita:
        non scrive nel modello canonico.
      </p>

      <RadioGroup
        aria-label="Esito della revisione"
        value={outcome ?? ''}
        onChange={(value) => setOutcome(value as DecisionOutcome)}
        isDisabled={!decisionEnabled}
        className="decision-options"
      >
        {(Object.keys(outcomeLabels) as DecisionOutcome[]).map((value) => (
          <Radio key={value} value={value} className="decision-option">
            <span className="radio-dot" aria-hidden="true" />
            <span>
              <strong>{outcomeLabels[value].title}</strong>
              <small>{outcomeLabels[value].detail}</small>
            </span>
          </Radio>
        ))}
      </RadioGroup>

      <div className="confirmed-disabled" aria-disabled="true">
        <strong>Associazione confermata</strong>
        <span>Non disponibile: manca un target strutturale registrato e verificato.</span>
      </div>

      <div className="decision-fields">
        <TextField isDisabled={!decisionEnabled} value={reviewer} onChange={setReviewer}>
          <Label>Revisore</Label>
          <Input placeholder="Nome del tecnico revisore" />
        </TextField>
        <TextField isDisabled={!decisionEnabled} value={observation} onChange={setObservation}>
          <Label>Osservazione tecnica</Label>
          <TextArea rows={4} placeholder="Descrivi soltanto ciò che è supportato dalla fonte primaria." />
        </TextField>
      </div>

      {error && <div role="alert" className="validation-message">{error}</div>}
      <Button className="primary-action" isDisabled={!decisionEnabled} onPress={prepareProposal}>
        Prepara ricevuta di decisione
      </Button>
    </section>
  );
}

function SourceEvidenceViewer({ manifest }: { manifest: RuntimeManifest | null }) {
  const hostRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!manifest || !manifestMatchesSnapshot(manifest) || !hostRef.current) return;
    const viewer = OpenSeadragon({
      element: hostRef.current,
      showNavigator: false,
      showNavigationControl: false,
      animationTime: 0.35,
      blendTime: 0.1,
      minZoomImageRatio: 0.7,
      visibilityRatio: 0.6,
      tileSources: { type: 'image', url: manifest.image_url }
    });

    viewer.addHandler('open', () => {
      const { bbox } = snapshot.evidence_region;
      const imageRect = viewer.viewport.imageToViewportRectangle(
        bbox.x * manifest.render_width_px,
        bbox.y * manifest.render_height_px,
        bbox.w * manifest.render_width_px,
        bbox.h * manifest.render_height_px
      );
      const overlay = document.createElement('div');
      overlay.className = 'evidence-overlay';
      overlay.setAttribute('aria-hidden', 'true');
      viewer.addOverlay({ element: overlay, location: imageRect });
      viewer.viewport.fitBounds(imageRect, true);
    });

    return () => viewer.destroy();
  }, [manifest]);

  return (
    <section className="source-pane" aria-labelledby="source-heading">
      <div className="workspace-title-row">
        <div>
          <div className="panel-kicker">Fonte primaria · vista derivata 300 dpi</div>
          <Heading id="source-heading" level={2}>{snapshot.source.drawing_label}</Heading>
        </div>
        <span className="state-chip epistemic-doc">DOC · documentato</span>
      </div>
      <div className="viewer-shell">
        <div ref={hostRef} className="osd-viewer" data-testid="source-viewer" />
        {!manifest && (
          <div className="viewer-fallback" role="status">
            <strong>Raster non staged</strong>
            <span>La decisione resta disabilitata finché la fonte primaria pin-nata non viene ricostruita e verificata.</span>
          </div>
        )}
      </div>
      <div className="evidence-caption">
        <span className="evidence-swatch" aria-hidden="true" />
        Regione documentale verificata · {snapshot.evidence_region.evidence_unit}
      </div>
    </section>
  );
}

function EngineeringInspector({ sourceVerified }: { sourceVerified: boolean }) {
  return (
    <aside className="inspector" aria-labelledby="inspector-heading">
      <div className="panel-kicker">Contesto strutturale</div>
      <Heading id="inspector-heading" level={2}>Schema armatura copertura</Heading>
      <p className="entity-subtitle">Associazione strutturale da determinare</p>

      <dl className="property-grid">
        <div><dt>Stato della fonte</dt><dd><span className="state-chip epistemic-doc">DOC</span> Documentato</dd></div>
        <div><dt>Regione</dt><dd><span className="state-chip workflow-ready">READY</span> Geometria verificata</dd></div>
        <div><dt>Binding strutturale</dt><dd><span className="state-chip neutral">UNBOUND</span> Non determinato</dd></div>
        <div><dt>Valutazione</dt><dd><span className="state-chip neutral">N/A</span> Non valutata</dd></div>
      </dl>

      <div className={`source-integrity ${sourceVerified ? 'verified' : 'blocked'}`}>
        <strong>{sourceVerified ? 'Fonte verificata' : 'Verifica sorgente necessaria'}</strong>
        <span>{sourceVerified
          ? 'Il raster deriva dal PDF primario pin-nato; la revisione può essere preparata.'
          : 'La UI resta in sola lettura e non accetta decisioni.'}</span>
      </div>

      <Disclosure>
        <Button slot="trigger" className="disclosure-trigger">Provenienza tecnica</Button>
        <DisclosurePanel className="provenance">
          <dl>
            <div><dt>EvidenceRegion</dt><dd>{snapshot.evidence_region.id}</dd></div>
            <div><dt>SourceVersion</dt><dd>{snapshot.source.source_version_id}</dd></div>
            <div><dt>Page</dt><dd>{snapshot.source.page_id}</dd></div>
            <div><dt>Canonical snapshot</dt><dd>{snapshot.canonical_commit}</dd></div>
            <div><dt>Archive blob</dt><dd>{snapshot.source.archive_blob_sha}</dd></div>
          </dl>
        </DisclosurePanel>
      </Disclosure>
    </aside>
  );
}

export default function App() {
  const [manifest, setManifest] = useState<RuntimeManifest | null>(null);
  const [proposal, setProposal] = useState<DecisionProposal | null>(null);

  useEffect(() => {
    loadRuntimeManifest().then(setManifest);
  }, []);

  const sourceVerified = useMemo(
    () => Boolean(manifest && manifestMatchesSnapshot(manifest)),
    [manifest]
  );

  return (
    <main className="app-shell">
      <header className="context-bar">
        <div className="brand-mark" aria-label="Civil Existing Workflow">CEW</div>
        <div className="breadcrumbs">
          <span>{snapshot.project.label}</span>
          <span>Stato esistente</span>
          <strong>Copertura · revisione evidenza</strong>
        </div>
        <div className="context-status">
          <span className="context-label">Workflow</span>
          <span className="state-chip workflow-review">IN REVIEW</span>
        </div>
      </header>

      <nav className="project-nav" aria-label="Navigazione progetto">
        <div className="nav-section-title">Progetto</div>
        {['Quadro progetto','Fonti e tavole','Modello strutturale','Materiali e armature','Carichi','Analisi','Stato e degrado','Indagini','Interventi','Quantità e costi','Fascicolo'].map((label) => (
          <button key={label} className={label === 'Fonti e tavole' ? 'nav-item active' : 'nav-item'}>{label}</button>
        ))}
      </nav>

      <section className="work-area">
        <div className="review-banner">
          <div>
            <div className="panel-kicker">Revisione tecnica sperimentale · {snapshot.decision.work_item}</div>
            <h1>Verifica associazione schema di armatura</h1>
            <p>
              Confronta la fonte primaria con il contesto strutturale. La regione è documentata,
              ma il legame a un elemento del modello non è ancora stabilito. Questa superficie legge
              il contesto canonico {snapshot.decision.canonical_context} senza modificarne lo stato.
            </p>
          </div>
          <div className="banner-state">
            <span>Decisione</span>
            <strong>{proposal ? 'PROPOSTA PREPARATA' : 'NON ESPRESSA'}</strong>
          </div>
        </div>

        <div className="workspace-grid">
          <SourceEvidenceViewer manifest={manifest} />
          <EngineeringInspector sourceVerified={sourceVerified} />
        </div>

        <div className="trail" aria-label="Percorso evidenza e decisione">
          {['Fonte primaria','Pagina misurata','EvidenceRegion READY','Binding UNBOUND','Decisione umana','Eventuale promozione governata'].map((step, index) => (
            <div className={index < 4 ? 'trail-step complete' : 'trail-step'} key={step}>
              <span>{index + 1}</span><strong>{step}</strong>
            </div>
          ))}
        </div>

        <div className="decision-layout">
          <HumanDecisionPanel decisionEnabled={sourceVerified} onProposal={setProposal} />
          <section className="receipt-preview" aria-labelledby="receipt-heading">
            <div className="panel-kicker">Receipt preview</div>
            <Heading id="receipt-heading" level={2}>Proposta non promotiva</Heading>
            {proposal ? (
              <pre data-testid="proposal-preview">{JSON.stringify(proposal, null, 2)}</pre>
            ) : (
              <div className="empty-receipt">
                <strong>Nessuna decisione registrata</strong>
                <span>La preview compare solo dopo una scelta esplicita del revisore.</span>
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}
