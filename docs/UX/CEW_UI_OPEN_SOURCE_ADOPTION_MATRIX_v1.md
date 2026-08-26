# CEW UI Open-Source Adoption Matrix v1

Status: `RESEARCHED FOUNDATION — implementation pinning deferred to UX1`

| Technology | CEW role | Decision | Guard |
|---|---|---|---|
| React Aria Components | accessible unstyled interaction primitives | ADOPT_FOR_UX1 | CEW owns styling and semantics |
| shadcn registry model | component distribution/source ownership pattern | ADOPT_PATTERN | no generic visual identity |
| TanStack Table | dense technical tables | ADOPT_STABLE_MAJOR | no beta major at production gate |
| Apache ECharts | engineering charts/results | ADOPT | chart is projection, not authority |
| React Flow / xyflow | provenance/dependency/knowledge graph | ADOPT | visualization does not establish edges |
| OpenSeadragon | HiRes source drawings | ADOPT_EXISTING_DIRECTION | F2 geometry remains authority |
| That Open Components | browser BIM/3D tools | BENCHMARK_FOR_UX1 | CEW stable IDs/adapters remain authority |
| web-ifc | IFC browser I/O | BENCHMARK/ADOPT_ADAPTER | IFC remains projection |
| Speckle Viewer | AEC UX/interop reference | REFERENCE | not canonical CEW backend |
| PatternFly | dense enterprise interaction benchmark | REFERENCE | not CEW identity |
| Carbon | tokens/consistency benchmark | REFERENCE | not CEW identity |
| Storybook | component catalog | MANDATORY_WHEN_WORKBENCH_EXISTS | engineering fixtures |
| Playwright | workflow/visual regression | MANDATORY_WHEN_WORKBENCH_EXISTS | source/model/decision paths |
| axe-core | automated accessibility | MANDATORY_WHEN_WORKBENCH_EXISTS | manual review still required |

Evaluation: maintenance, license, accessibility, composability, data density, AEC relevance, authority-boundary compatibility, performance and replaceability.

Research refresh 2026-08-26: TanStack Table v9 has reached a stable line; UX1 must pin a stable release instead of the earlier beta series. Apache ECharts 6.1.0 is a current stable release. That Open `engine_components` 3.4.0 is MIT and provides BIM primitives including measures, clipping, navigation and picking; it remains an engine candidate rather than a CEW data model.
