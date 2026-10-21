# Golden tree: notes

## Method

Source: `data/union/strategies.csv`, the strategy list the dashboard reads (9,918 strategies, 45
countries). Only the strategy names were read, not their stage 3 rows.

1. Ten agents split each name into an objective, a target and an instrument (one row per
   strategy, the main aim where a name joins several).
2. Exact duplicates were dropped: 5,687 distinct objective phrases, 1,128 target phrases, 34
   instrument phrases.
3. Phrases were merged on meaning into labels within families. Objectives went in two passes:
   four sector blocks (677 labels), then one pass across blocks (456). Targets in one pass (197).
   Instruments by hand (19).
4. Each label got a definition saying what is in and what is out.

`buckets.py` joins it all; the phrase-to-label maps are in `names/`.

## List sizes

- **Objectives**: 456 in 19 families. The 18 seeded families plus Regional and rural
  development.
- **Targets**: 197 in 8 families. The 7 seeded plus Civil society and external partners.
  3,566 strategies (36%) name no target.
- **Instruments**: 19 in 9 families. The 10 seeded, less Direct service provision and
  Institutional and governance reform (no name stated one), plus Financing vehicles (fund, bond,
  public-private partnership).
- **Golden table**: 3,269 observed objective × target × instrument combinations.

## Instruments

2,023 strategies (20%) name an instrument; the country range is 0% (Uzbekistan, 7 strategies) to
48% (Brunei). This is a floor: the lever is often in a strategy's detail rather than its name, and
the names were the only source. Infrastructure strategies are uneven: the agent for the
security, justice and infrastructure block left a build without a named facility blank where
others counted it.

## Worked example: health insurance

18 strategy names contain "health insurance". 16 land on the objective Extend health financial
protection and 17 on the instrument Health insurance. Iran's "health insurance governance and
purchasing" sits under Reform health financing; Iran's "electronic health records and integrated
digital health insurance services" sits under digital health, with an information system as its
instrument.

## RHDR category

No RHDR decision was made here. The viewer shows the amended category where the rhdr_2026_10
`from` map gives exactly one; the 2,906 strategies published as Joined-up Thinking or Fostering
the Spirit of Change, and 44 with no published category, read "Not decided".

## Merges to check by hand

- Objectives: universal health coverage sits with access to services, not financial
  protection; climate resilience and disaster risk are kept apart; price and market stabilisation
  sits with monetary policy; food safety sits in Health; population growth and demographic change
  are one label.
- Targets: Bumiputera maps to Indigenous peoples; Sabah and Sarawak, Papua, Aceh and Bangsamoro
  map to Special and autonomous regions; farmers sit in Workers while producers sit in Firms;
  girls merge into Women and girls; mental illness merges into Persons with disabilities.
- Instruments: feed-in tariffs merge into Subsidy; scholarships are a Transfer.
