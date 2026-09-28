# Extension guide — add feeds, sectors, states, geographies, clients

Everything below is a config change. Commit it, and the next scheduled run picks it up.
To check a change locally first: `python -m tracker sources check`, then `python -m tracker run`.

## Add a news feed

Append to `config/sources/feeds.yaml`:

```yaml
  - {id: deccan-education, name: "Deccan Herald — Education", type: national_media, language: en, prior: 20,
     url: "https://www.deccanherald.com/education/feed"}
```

- `prior` is 0 for general feeds, about 20 for feeds that are already on-topic, and 10–15 for official ones.
- Test the feed with `python -m tracker sources check --only deccan-education`.

## Add a Google News query or language

In `config/sources/google_news.yaml`:
- **Add a query:** add a line under a pack's `queries:` (for example `kn: 'ಶಾಲಾ ಶಿಕ್ಷಣ'`).
- **Add a language:** enable it under `languages:`.

A new pack (for example `id: scholarships`) becomes one feed per language automatically.

## Watch another government page

Add to `config/sources/watch.yaml`:

```yaml
  - id: upsec
    name: UP State Election Commission
    url: "https://sec.up.nic.in/"
    include: "\\.pdf|notification|election"
    stream: election
    state: UP
```

Run `python -m tracker watch --only upsec` twice: the first run records a baseline, the second shows new items. Only plain-HTML pages work, so check that the links appear in the page source.

## Add or fix vocabulary

| To change | Edit |
|---|---|
| Sector words (any language) | `config/taxonomy/sectors.yaml`: `strong` (unambiguous) or `terms` (supporting) |
| Things to ignore | `negative` in `sectors.yaml` (off-topic) or `noise_terms` in `scoring.yaml` (round-ups/SEO) |
| Category words | `config/taxonomy/categories.yaml` |
| Bodies, courts, parties | `config/taxonomy/actors.yaml`. Give a High Court its `state:` so rulings are placed correctly |

Matching rules:
- ALL-CAPS acronyms match case-sensitively as whole words.
- Other English terms match whole words, case-insensitively.
- Indian-language terms match at the start of a word, allowing inflections.

Add a test in `tests/test_tagger.py` for anything important.

## Add a sector (e.g. healthcare)

1. Add a block to `config/taxonomy/sectors.yaml`:

   ```yaml
     healthcare:
       label: Healthcare
       strong: {en: [NMC, "health ministry", AIIMS, "Ayushman Bharat", "NEET-PG", "medical college"],
                hi: ["स्वास्थ्य मंत्रालय", "आयुष्मान भारत"]}
       terms:  {en: [hospital, hospitals, doctor, doctors, patients, health], hi: ["अस्पताल", "डॉक्टर", "स्वास्थ्य"]}
   ```

2. Add a query pack to `google_news.yaml` (`sector: healthcare`), and health feeds or pages if you want them.
3. Add a paragraph to `config/engine/ai_interests.txt` for the AI filter.
4. Add a few 👍/👎 seed examples to `config/training/seed_labels.yaml`, then run `python -m tracker train`.

The sector then appears in tags, filters, reports and Excel automatically.

## Add a state, district or city

In `config/geography/india.yaml`, add names to the state's `names` (strong signals, in any
script) or `cities` (district headquarters, towns). Add ambiguous words, like city names that
are also common words, only if they are unambiguous in news headlines.

## Add a country or geography

Create `config/geography/<country>.yaml` with the same structure: `country`, `country_names`,
`national_terms`, `municipal_terms`, `district_terms`, `foreign_terms`, `states`. Then add that
country's feeds and Google News editions (`gl`/`ceid` in `google_news.yaml`).

## Serve another client (resale)

The whole client profile is the `config/` folder:

1. Copy it: `cp -r config config-healthcare-client`.
2. Edit its sectors, sources, interests and seed labels.
3. Run with `python -m tracker --config config-healthcare-client run`, or set `TRACKER_CONFIG_DIR`.

For a fully separate deployment, fork the repository with the new `config/` and that client's
own secrets. Nothing in the code is specific to this client.

## Tune scores

`config/taxonomy/scoring.yaml` holds every weight. The band limits are in
`config/settings.yaml` → `relevance.bands`.

After a change, run `python -m tracker process` and compare bands on the dashboard. Each item's
"Why this score" shows the effect.
