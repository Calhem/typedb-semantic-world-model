# Domain modules and World Ontology Profiles

## Modules (what gets defined) vs profiles (what an application installs)
- A **module** is a versioned set of TypeQL schema files (and functions) for one topic: `core`, `spatial`,
  `temporal-functions`, `physical`, `social`, `memory`, `robotics`, `vision`.
- A **profile** is a manifest that names a core version, the modules it needs, the optional ones, and the competency
  questions it must answer. It is not a separate database and not a type.

The brief's six families stay as a **documentation index**, not a module tree: time, identity and evidence are in
`core`, so no family re-implements them.

### Proposed v1 modules
| Module | Contents | Needed by |
|---|---|---|
| `core` | The ~20 types in upper-ontology-proposal.md | all |
| `spatial` | place hierarchy, topological claims (in, on, near, adjacent), frame references, pose summaries | ROS 2, VWE |
| `physical` | part-of extensions, system, substance, measurements with units | ROS 2, explorer, lunar |
| `social` | person roles, communication events, social relations, attributed affect and intention | social robot, GUPI, VWE |
| `memory` | conversation sources, mentions, conversational context (from GUPI) | GUPI |
| `robotics` | robot, sensor, task, navigation goal, map version, track | ROS 2 |
| `vision` | video, segment, detection, track | VWE |

### Proposed profiles
| Profile | Modules |
|---|---|
| `wop-robotics-1` | core, spatial, physical, robotics |
| `wop-visual-1` | core, spatial, social, vision |
| `wop-memory-1` | core, social, memory |

## How profiles would be implemented and validated in TypeDB
1. **Install** = load `core`, then each module's files in dependency order, in schema transactions (probe 1).
2. **Naming:** every module-owned type carries no prefix but must be registered in a single names index across all
   published modules; a test fails on any collision (probe 4 shows TypeDB will otherwise reject the second definition
   at install time, which is late).
3. **Core protection:** modules may add subtypes and `plays` to core types (probe 10) but may not redefine,
   undefine or retype them. A test loads each profile and checks the core's own competency questions still give the
   same answers on the core fixtures.
4. **Conformance:** introspection queries (probe 8) compare the installed schema with the manifest.
5. **Versioning:** semantic versions per module; a profile pins exact versions. A minor version may only add.
   Migrations are numbered files, as in GUPI.
6. **Exchange:** two profiles can exchange the claims whose types they share; anything else is dropped and *counted*
   (Experiment 7 measures loss).

## Complexity this introduces (be honest)
- A compatibility matrix (core × module × profile versions) to test.
- Module dependency order and diamond dependencies (two modules extending the same core type).
- Every exchange needs an export format and a loss report.
- Applications must handle "this database has a profile I don't know".

**Recommendation for v1:** one repository, one version number for everything, three profiles as manifests, and
collision and core-protection tests. Independent module versioning only once a second team publishes a module.
