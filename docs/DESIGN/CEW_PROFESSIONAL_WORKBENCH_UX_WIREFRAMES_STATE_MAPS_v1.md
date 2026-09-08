# CEW Professional Evidence Workbench — UX Wireframes & State Maps v1

**Status:** `DESIGN_BASELINE_PROPOSED`  
**Authority effect:** `NONE`  
**Canonical write:** `false`

## 1. Design objective

Define the spatial hierarchy and principal UI states before implementation. The workbench must look and behave like a drawing tool first, not like an audit form.

## 2. Desktop default — SPLIT

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Project › Drawing › Context     SOURCE  TECHNICAL  [SPLIT]  OVERLAY          │
│ Pan  Area zoom  Fit  100%  Rotate | Sync: SEMANTIC | Layers | Issues | ⋯    │
├───────────────────────────────────────┬──────────────────────────────────────┤
│                                       │                                      │
│           VERIFIED SOURCE             │        TECHNICAL REPRESENTATION      │
│          F3 DEEP-ZOOM VIEW            │          VECTOR SCENE                │
│                                       │                                      │
│        [Evidence highlight]           │      [Selectable objects/text]       │
│                                       │                                      │
│                                       │                                      │
├───────────────────────────────────────┴───────────────────────────┬──────────┤
│ Source verified · Registration: unavailable · 3 open issues      │ Inspector│
└──────────────────────────────────────────────────────────────────┴──────────┘
```

The inspector is collapsed by default unless an object/issue is selected.

## 3. Desktop selected-object state

```text
Technical viewport                        Inspector
┌──────────────────────────┐             ┌───────────────────────────────┐
│                          │             │ Armatura inferiore            │
│      [ 2 Φ12 ? ] ◀───────┼─────────────│ Stato: DA VERIFICARE          │
│                          │             │ Lettura riconosciuta: ?       │
└──────────────────────────┘             │ Proposta: 2 Φ12               │
                                         │ [Conferma] [Modifica]          │
                                         │ [Non leggibile]                │
                                         │ [Apri evidenza]                │
                                         │ Evidence ▸   Provenienza ▸     │
                                         └───────────────────────────────┘
```

Internal SourceVersion/EvidenceRegion ids are hidden until `Provenienza` is expanded.

## 4. SOURCE mode

Source occupies the full central canvas. Technical selection remains available through search/issues but does not consume half the viewport.

Primary controls:

- deep zoom;
- navigator/minimap;
- EvidenceRegion markers toggle;
- context jump;
- rotate/fit/100%;
- issue/evidence selection.

## 5. TECHNICAL mode

Technical scene occupies full canvas.

Primary controls:

- pan/zoom;
- layer visibility;
- selection;
- search/locate;
- working edit;
- issue navigation;
- evidence reveal command.

## 6. OVERLAY mode

```text
┌──────────────────────────────────────────────────────────┐
│ Overlay · Registration VERIFIED      Source 70%  Tech 100%│
├──────────────────────────────────────────────────────────┤
│                                                          │
│     source raster + registered vector technical scene    │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ Layers ▾   Alignment VERIFIED · Details ▸                │
└──────────────────────────────────────────────────────────┘
```

If registration is not VERIFIED, OVERLAY is disabled and its tooltip/explanation states the missing prerequisite.

## 7. Registration states

### UNAVAILABLE

- Sync spatial disabled;
- Overlay disabled;
- semantic selection may remain available;
- status: `Positional alignment not established`.

### PROPOSED

- preview/alignment review allowed only in explicit registration workflow;
- normal professional overlay remains disabled;
- cannot be mistaken for verified alignment.

### VERIFIED

- spatial sync available;
- overlay available;
- inspector can expose control points/residuals.

### STALE

- spatial sync immediately disabled;
- prior registration retained for audit/history;
- reason explains source/scene revision mismatch.

### REJECTED

- no spatial sync/overlay;
- registration proposal remains inspectable as rejected evidence.

## 8. ReadingIssue visual states

Issue marker always includes icon/shape + textual state in inspector/list, not colour alone.

- OPEN — question marker;
- IN_REVIEW — review marker;
- RESOLVED — resolved check;
- NOT_RESOLVABLE_FROM_CURRENT_SOURCES — explicit terminal unresolved marker.

Selecting from issue list centres the relevant viewport/objects only through explicit anchors/links.

## 9. WorkingEdit states

### No edit
Base recognized/source value visible.

### Editing
Inline or inspector editor active; source/base value remains available.

### Draft
Technical scene previews the working value with a non-canonical indicator.

### Ready for review
Working edit is frozen enough for review/handoff; still not canonical.

### Withdrawn
Base representation restored; audit/session history may preserve the withdrawn edit.

### Handed off
Proposal/receipt sent to governed workflow; Workbench does not show it as promoted unless authority state later confirms promotion.

## 10. Progressive disclosure states

### Work
Default:
- object name/type;
- value/state;
- issue/question;
- direct actions.

### Evidence expanded
Adds:
- source preview/region;
- recognition literal;
- alternatives;
- context navigation.

### Provenance expanded
Adds:
- SourceVersion/Page/Transform/EvidenceRegion/Observation ids;
- hashes;
- epistemic/binding/promotion states;
- adapter/extractor versions.

## 11. Layer manager

Compact drawer:

```text
Layers
☑ Source
☑ Extracted linework
☑ Recognized text
☑ Dimensions
☑ Technical candidates
☑ Governed structural objects
☑ Reinforcement
☑ Reading issues
☑ Engineer annotations
☑ Validation state
```

Unavailable layers are disabled with reason; they are not silently empty if data failed to load.

## 12. Tablet landscape

Default can remain SPLIT when viewport permits.

Inspector becomes slide-over drawer. Layer/issues panels are overlays. One-tap Source/Technical full-screen mode available without losing selection/location.

## 13. Narrow/mobile

```text
┌──────────────────────────┐
│ Drawing · [Source][Tech] │
├──────────────────────────┤
│                          │
│       active view        │
│                          │
├──────────────────────────┤
│ Selection / issue summary│
│ [Open inspector]         │
└──────────────────────────┘
```

No forced side-by-side miniature drawings. Overlay/complex editing may be review-only or unavailable if reliable interaction cannot be guaranteed.

## 14. Empty/failure states

### Technical scene unavailable
Source remains fully usable. Message: technical representation unavailable for this source/revision; no fallback geometry invented.

### Source tiles unavailable
Technical representation may remain viewable only if its own provenance state is valid, but user is clearly warned that primary evidence cannot currently be inspected.

### No object binding
Object can be displayed as candidate; structural identity remains unbound.

### No issues
No empty governance panel; issue control shows `0 open`.

## 15. Focus and keyboard state

Visible focus ring on toolbar, viewport, selectable object proxy/list, inspector controls and layer controls.

Viewport must have a keyboard-operable focus mode with equivalent pan/zoom commands.

## 16. HVA-observable interactions

The UI must make these naturally observable without exposing test telemetry:

- source navigation;
- mode switching;
- technical selection;
- evidence reveal;
- issue selection/resolution;
- edit/cancel/recovery;
- registration/sync understanding;
- provenance access when needed.

## 17. Design rejection criteria

Reject implementation if:

- the drawing occupies less visual priority than governance metadata during normal work;
- technical view is still a page-region box/list instead of a technical scene;
- edits are global/unanchored;
- Source/Technical/Split/Overlay use inconsistent navigation semantics;
- overlay can appear without verified registration;
- internal ids dominate the default screen;
- narrow mode merely compresses desktop split view.
