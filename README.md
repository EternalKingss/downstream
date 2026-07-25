# Downstream

An EMR study site built around causal chains: anatomy → what breaks it → what happens next → what interrupts it.

## Open it

Open `out/index.html` in any browser. No server needed, works from `file://`.

## Rebuild after editing content

```
python3 build.py
```

Nothing to install. Standard library only.

## How it's put together

You never edit HTML. You edit JSON, and the generator wires up every cross-link.

```
data/structures*.json  body systems and anatomical structures, each with a failure mode
data/conditions*.json  conditions, their cascades, and what interrupts each link
data/nodes*.json       shared physiological states reused across every cascade
data/meds*.json        medications: mechanism, dosing, timing, cautions
data/skills.json       procedures, with the reason behind every step
data/signs.json        reverse lookup: sign -> the cascades that produce it
data/questions.json    hand-written quiz items (optional; everything else is generated)
assets/img/<system>.*  anatomy image for a body system, named after its id
                       (png/jpg/webp/svg). Drop one in and it appears on the
                       landing tile and the system page. No wiring needed.
assets/style.css       design system, including the per-system colour palette
assets/app.js          ECG preloader, anatomy picker, structure expanders, search
assets/quiz.js         quiz runner and spaced-repetition scheduling
build.py               generator (validates every cross-reference, fails on a broken link)
out/                   the site (regenerated from scratch each build; don't edit)
```

Any file matching `conditions*.json`, `nodes*.json`, `structures*.json`, or
`meds*.json` is merged automatically, so you can split content into as many
files as you like. The build refuses to run if any reference points at
something that does not exist.

### Adding a condition

Add an object to `conditions.json` with `status: "built"`. It automatically appears:

- under every structure listed in its `structures` array
- on every medication page listed in that med's `used_in`
- on every shared node its cascade references

### Cascade steps

```json
{
  "id": "three-hit",
  "label": "Airway narrows three ways",
  "sub": "Spasm, swelling, mucus",
  "severity": "normal | warn | crit",
  "structure": "bronchioles",
  "shared": "hypoxia",
  "detail": "..."
}
```

`structure` links back to the anatomy page. `shared` links to a node in the node
library — use it whenever a step is a state that other conditions also reach, so
it gets written once instead of eleven times.

### Interventions

Attach each one to the cascade step it breaks:

```json
{ "med": "salbutamol", "breaks_at": "three-hit", "scope": "EMR", "note": "..." }
```

`scope` on the intervention overrides the drug's default, because scope is
contextual — an epinephrine auto-injector for anaphylaxis is EMR, epinephrine
for severe asthma is not.

## Questions

The quiz bank is generated from the data layer, so it grows on its own as
content is added. Nothing is copied from a commercial question bank. Types:

```
Where it breaks the chain  from interventions[].breaks_at
What happens next          from consecutive cascade steps and node leads_to
Order the cascade          rebuild the first five steps in sequence
Failure modes              structure <-> failure_mode, both directions
Start from a sign          the clue that separates one cause from another
Drug timing and scope      onset, duration, Alberta scope tag
Shared nodes               identify the state, and what it runs into next
Telling it apart           the real discriminator vs plausible distractors
Skills                     the reason behind a given step
```

Add your own in `data/questions.json` for anything the structure cannot
express — scene management, legal, documentation, judgement calls:

```json
{ "topic": "Scene size-up", "stem": "...",
  "choices": ["...", "...", "...", "..."], "answer": 0,
  "why": "...", "page": "skill/primary-survey.html",
  "ref": "EMR ch. 6, Scene Size-Up (p. 120)" }
```

`answer` takes an index or the exact text of the right choice. `page` is the
site page to reread; `ref` is a textbook pointer shown after answering.

Scheduling is per-question in `localStorage` under `ds-srs`: correct answers
push the next appearance out (10 min, 1, 3, 7, 16, 35 days), a miss resets it.
Progress never leaves the browser, and clearing site data clears it.

## Hosting

Push `out/` to GitHub Pages, Netlify, or Cloudflare Pages. It's fully static.

## Sources

Built with reference to openly licensed material: WisTech Open *Emergency
Medical Responder* (CC BY 4.0), OpenStax *Anatomy and Physiology 2e*, the Oregon
EMS Psychomotor Skills Lab Manual (CC BY-NC-SA), and Alberta Health Services EMS
Medical Control Protocols. All prose is written fresh rather than reproduced.

Study tool, not a field reference. Protocols are the authority of record.
