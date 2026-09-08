# CEW Panel Maturity Reference v1

## Purpose

This note records the external interface research used to refine the **internal quality** of the CEW Professional Document Workbench without changing its canonical topology or any evidence/engineering authority boundary.

The goal is not to imitate a product visually. The goal is to adopt interaction patterns that have proved durable in mature editor, notebook, technical-PDF and engineering-viewer products.

## Sources reviewed

### Microsoft VS Code — Custom Layout

Official documentation:

- https://code.visualstudio.com/docs/configure/custom-layout

Relevant mature patterns:

- the **Activity Bar** switches views in the Primary Side Bar;
- the **Primary Side Bar** and **Secondary Side Bar** are distinct persistent workbench parts;
- the central editor remains the dominant flexible surface;
- layout can be compacted without changing feature ownership;
- secondary content can coexist with primary navigation instead of replacing the document/editor.

CEW adoption:

- Activity Rail remains a view switcher only;
- left and right sidebars remain independently collapsible/resizable;
- the drawing canvas absorbs reclaimed space;
- compact density is the default for panel chrome.

### JupyterLab — Application shell and sidebars

Official documentation:

- https://jupyterlab.readthedocs.io/en/stable/user/interface.html
- https://jupyterlab.readthedocs.io/en/stable/user/interface_customization.html
- https://jupyterlab.readthedocs.io/en/stable/user/commands_list.html

Relevant mature patterns:

- stable `left`, `right`, `main`, `down`, `top` and `bottom` shell areas;
- left/right sidebars contain persistent tools while the main work area contains the document/activity;
- clicking the active sidebar tab can collapse the sidebar;
- layout state includes side areas and relative sizes;
- standard keyboard commands expose/hide left and right sidebars (`Ctrl+B` and `Ctrl+J` in current JupyterLab command documentation).

CEW adoption:

- active Activity Rail item toggles the Primary Sidebar;
- `Ctrl+B` toggles the Primary Sidebar;
- `Ctrl+J` toggles the Auxiliary Sidebar;
- panel sizes and visibility remain presentation-only persisted state.

### Bluebeam Revu — Technical PDF workspace

Official documentation:

- https://support.bluebeam.com/user-manual/welcome/revu-interface.html
- https://support.bluebeam.com/user-manual/menus/window/window-panel.html
- https://support.bluebeam.com/revu/how-to/customize-panels.html

Relevant mature patterns:

- the **main workspace** occupies the bulk of the interface;
- panel access bars open specialized panels at the left/right/bottom;
- panels are distinct from toolbars;
- panels can be hidden to recover drawing space;
- the status bar and navigation controls stay compact and separate from document properties;
- workspace arrangements are saved and restored.

CEW adoption:

- drawing inspection remains visually dominant;
- document navigation/evidence belongs to panels, viewport movement belongs to the editor toolbar;
- status stays in the bottom status bar;
- no permanent training form occupies the inspector when training is blocked.

Bluebeam is a proprietary product reference. **No source code, icons, branding, or protected visual assets are copied.** Only interaction principles are used.

### Autodesk Viewer — Contextual properties and viewer tools

Official documentation:

- https://help.autodesk.com/cloudhelp/2025/ENU/Vault-Essentials/files/GUID-EA5CF17C-B218-49FE-8466-C64D883794AF.htm
- https://help.autodesk.com/cloudhelp/ENU/ADSKVIEWER-Help/files/AutodeskViewerTools/ADSKVIEWER_Help_AutodeskViewerTools_ViewerSettings_html.html

Relevant mature patterns:

- navigation tools belong to the viewer surface;
- model/document browser and Properties are separate concerns;
- properties are contextual to the selected object;
- selection can cause properties to become the active inspection surface.

CEW adoption:

- fit/zoom/pan/rotation remain editor-anchored;
- cluster selection drives the contextual Inspector;
- Properties and Provenance remain separate inspector views.

### OpenHands Agent Canvas

Inspectable source/documentation:

- https://github.com/OpenHands/OpenHands/blob/main/docs/architecture.md

Relevant mature pattern:

- one frontend shell coordinates conversation/files/browser/terminal-like surfaces while UI state remains distinct from execution authority.

CEW adoption:

- workbench layout state is not evidence state;
- panel actions do not alter semantic, structural or canonical authority.

## Consolidated CEW panel-quality rules

The topology remains:

`TITLE_BAR + COMMAND_BAR + ACTIVITY_RAIL + PRIMARY_SIDEBAR + FLEXIBLE_EDITOR_CANVAS + AUXILIARY_SIDEBAR + STATUS_BAR`.

Internal panel quality is governed by these rules:

1. **One visible title per panel level.** Do not repeat the active view title inside the same sidebar body.
2. **Human-readable operational labels.** Machine tokens may remain in logs/status diagnostics, but ordinary panel copy uses readable Italian labels.
3. **Compact chrome.** Panel headers, tabs, counts and action icons consume as little drawing area as practical.
4. **Context before forms.** Properties/Provenance are default inspector surfaces; Decision exists only when governed teaching is enabled.
5. **Document-first space allocation.** Sidebars may collapse independently and the editor absorbs the released width.
6. **Stable navigation semantics.** Activity Rail changes the Primary Sidebar view; it does not perform document-domain actions.
7. **Keyboard parity.** `Ctrl+B` toggles Primary Sidebar; `Ctrl+J` toggles Auxiliary Sidebar. Sashes remain keyboard adjustable.
8. **Accessible state.** Activity items expose pressed/current state, inspector tabs expose selected state, sashes expose values and bounds, editor panel toggles expose expanded/collapsed state.
9. **No decorative controls.** A visible action must perform a real current operation; unavailable governed actions stay absent/disabled rather than decorative.
10. **Status separation.** Execution completion, graphic-evidence result, source authority and training authority remain separate states.

## Explicitly not adopted

The following mature-product capabilities are intentionally **not** added in this tranche:

- arbitrary panel detaching/floating;
- user-defined panel docking topology;
- multi-document split editor groups;
- bottom Markups/console panel;
- automatic semantic labeling;
- automatic selection-to-training;
- any change to SourceVersion/Page governance or canonical write.

Those capabilities would expand topology or authority and require separate governance.

## Acceptance consequence

A panel-quality change is acceptable only when:

- the mounted FastAPI route materializes in Chromium;
- sidebars still collapse/restore and persist correctly;
- the document/editor retains the flexible central role;
- keyboard and accessibility state are functional;
- blocked training remains absent from ordinary inspector use;
- no acquisition/semantic/canonical boundary changes.
