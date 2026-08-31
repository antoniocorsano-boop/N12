# CEW Enterprise UX — Professional AEC System Pattern Decoding v1

**Status:** `RESEARCH_BASELINE_COMPLETE`  
**Authority effect:** `NONE`  
**Canonical engineering write:** `false`

## 1. Purpose

This document decodes interaction and information-architecture patterns from mature AEC/CAD/BIM review systems in order to define CEW as a professional evidence-first work operating system rather than as a viewer with accumulated panels.

The comparison is about workflow logic, not feature parity.

## 2. Systems reviewed and decoded patterns

### Autodesk Construction Cloud / Autodesk Build Sheets
Official documentation shows version-aware sheet comparison in both overlay and side-by-side modes, with explicit alignment and visibility controls. The important pattern is that comparison is a **temporary review mode entered from a stable sheet context**, not the default layout of the entire product.

Pattern for CEW: `COMPARE` is a task mode, not a permanent screen topology.

Source: https://help.autodesk.com/cloudhelp/ENU/Build-Sheets/files/Compare_Sheets.html

### Bluebeam Revu
Revu separates a dominant document canvas from dockable panels. Tool Chest stores reusable project/workflow-specific tools. Compare Documents and Overlay Pages are explicit operations; differences become trackable markups/list items instead of transient pixels only.

Patterns for CEW:
- canvas first;
- side/bottom panels are dockable and independent;
- project-specific reusable object/family library;
- comparison result becomes reviewable evidence objects;
- scanned and vector sources may require different review strategies.

Sources:
- https://support.bluebeam.com/revu/features/tool-chest-guide.html
- https://support.bluebeam.com/revu/features/compare-documents-vs-overlay-pages.html
- https://support.bluebeam.com/user-manual/menus/document/overlay-pages.html

### AutoCAD Smart Blocks — Detect and Convert
Object detection groups results into **sets of similar objects**, exposes a primary instance, supports next/previous review and removal of wrong instances, and requires an explicit conversion step. Autodesk also blocks unrelated commands during detection review, reducing mode ambiguity.

Patterns for CEW:
- detector output is a review set, not accepted truth;
- representative/prototype instance is explicit;
- set review is bounded and navigable;
- erroneous instances can be removed without accepting/rejecting the entire drawing;
- review mode can deliberately restrict unrelated actions;
- conversion/promotion is a separate step from detection.

Sources:
- https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-WhatsNew/files/GUID-25BD5FB7-119A-42A8-B1C1-62BB812A3F4F.htm
- https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Core/files/GUID-6BAE51A3-075E-4665-8C5D-4DD94940DC1B.htm

### Revizto
Revizto unifies 2D and 3D but does not force split view continuously. Splitview and overlay are deliberate tools entered when cross-context is useful. Issues preserve context and can carry a source sheet/viewpoint.

Patterns for CEW:
- one project context, multiple coordinated surfaces;
- 2D/technical split only on demand;
- issue/topic is durable and reopens the relevant visual context;
- spatial context must be recoverable, not rediscovered manually.

Sources:
- https://revizto.com/product/unified-2d-3d-environment
- https://help.revizto.com/hc/en-us/articles/15986310925199-Viewing-projects-with-splitview
- https://help.revizto.com/hc/en-us/articles/4404217613967-Viewing-sheets

### Dalux
Comments are created from drawing/document/model context and retain the relation to the place where they were made. The workflow is effectively `select context → annotate → fill structured issue`. Comment types and channels can be configured by project.

Patterns for CEW:
- issue creation starts from context, not from a detached form;
- the same issue model can bind to 2D, documents or 3D;
- project configuration controls issue types/workflows;
- history and responsibility remain attached to the topic.

Sources:
- https://support.dalux.com/hc/en-us/articles/12727090183708-How-to-use-Comments
- https://support.dalux.com/hc/en-us/articles/360020417020-How-to-set-up-Comments

### Procore Drawings / Coordination Issues
Creating a coordination issue on a drawing automatically carries a snapshot and link back to the original drawing. Pins use state coloring.

Patterns for CEW:
- a review issue must reopen exact evidence context;
- snapshot/context is a convenience artifact, while the source link remains authoritative;
- state is legible spatially without opening every record.

Source: https://support.procore.com/products/online/user-guide/project-level/drawings/tutorials/create-or-link-coordination-issues-on-a-drawing

### Navisworks
Viewpoints capture camera/context and can carry markups/comments. Clash review focuses the selected result in the scene and can isolate related items. Navigation and markup modes are mutually exclusive while annotating.

Patterns for CEW:
- persisted `ViewState` is a first-class object;
- selecting a result focuses context rather than growing a detail page;
- mode exclusivity prevents accidental operations;
- review result + viewpoint + comments form an audit trail independent of changing base geometry.

Sources:
- https://help.autodesk.com/cloudhelp/2025/ENU/Navisworks/files/GUID-BD49E564-502F-4D57-9F9F-8761E09DF8D9.htm
- https://help.autodesk.com/cloudhelp/2026/ENU/Navisworks-Clash-Detective/files/GUID-807A6516-CD83-453E-B2A0-5572D84D89FE.htm
- https://help.autodesk.com/cloudhelp/2022/ENU/Navisworks/files/GUID-7FDFB8F2-B361-4234-B67B-263B8DC2D361.htm

### BIMcollab / BCF
BCF issues carry structured topic fields and viewpoint information such as camera, section planes and component identifiers. Good issue management depends on a clear viewpoint and direct relation to relevant model components.

Patterns for CEW:
- `Issue` and `ViewState` are related but separate entities;
- visual state must be portable/recoverable;
- issue records need status/priority/type/assignee/history independent of viewport implementation;
- open interchange should remain possible downstream.

Sources:
- https://helpcenter.bimcollab.com/en/articles/351697-how-bcf-files-work-in-bimcollab
- https://helpcenter.bimcollab.com/en/articles/359090-create-the-best-viewpoints

### Trimble Connect
Saved Views retain 2D or 3D context including zoom/camera, visibility, measurements, markups, clipping and other display state. BCF Topics provide model-based issue communication but can also exist with document references without requiring a BIM model.

Patterns for CEW:
- `SavedView` is a reusable project object;
- issue communication must not depend on a complete structural model;
- the CDE/project context owns views/topics independently of a single application surface.

Sources:
- https://help.trimble.com/doc/trimble-connect/trimble-connect/connect-for-browser/views
- https://help.trimble.com/doc/trimble-connect/trimble-connect/connect-for-browser/bcf-topics

### Solibri
Checking results are split into a summary view and detailed results, including severity-based organization. This avoids showing all findings at full detail simultaneously.

Pattern for CEW: result review must be **summary → filtered set → active item**, never a full-height unvirtualized list beside the drawing.

Source: https://help.solibri.com/hc/en-us/articles/1500004886382-Viewing-Checking-Results

## 3. Convergent enterprise patterns

Across the systems above, the strongest recurring patterns are:

1. **Canvas dominance** — the drawing/model remains the stable primary work surface.
2. **Context panels, not page growth** — inspectors/issue lists scroll independently from the canvas.
3. **Task/mode explicitness** — compare, markup, detect, review and edit are entered deliberately.
4. **Persistent visual context** — viewpoint/view state is saveable and recoverable.
5. **Issue/topic as durable work object** — questions and findings carry state/history/context.
6. **Reusable project grammar** — tools, families, sets or blocks can be reused.
7. **Review sets, not automatic truth** — detection/checking outputs are grouped and reviewed before conversion/promotion.
8. **Summary before detail** — aggregate counts and filters precede individual findings.
9. **Cross-view only when useful** — split/overlay is on-demand, not universal default.
10. **Explicit promotion boundary** — detection/markup/issue resolution is not equivalent to canonical engineering acceptance.

## 4. Patterns CEW must deliberately reject

- permanent split view when one side has no actionable content;
- entire-page scrolling caused by a long inspector/result list;
- technical IDs and governance internals as primary operator language;
- automatic acceptance of a detected set because a score is high;
- visual proximity creating identity/evidence links;
- transient screenshot as replacement for immutable source evidence;
- mixing navigation, annotation, classification and acceptance actions without an explicit work mode;
- requiring a complete BIM/model before evidence/issues can be managed.

## 5. CEW synthesis

The enterprise target is not a clone of any one product. CEW combines:

- Bluebeam-style document/canvas ergonomics;
- AutoCAD-style set/prototype review;
- Revizto-style context switching without forced split;
- Navisworks/BCF-style persistent viewpoints;
- Dalux/Procore-style context-bound issues;
- Solibri-style summary-to-result review;
- CEW-specific evidence provenance and authority boundaries.

The resulting product model is defined in `docs/DESIGN/CEW_ENTERPRISE_PROFESSIONAL_WORKSPACE_MODEL_v1.md`.
