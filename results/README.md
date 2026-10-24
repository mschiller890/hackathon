# Výsledky (results/)

Agregované výsledky a grafy, které čtou notebooky. Žádná surová data ÚFP. Soubory jsou ploché, protože na ně odkazují
cesty v notebookech a skriptech; tady jsou seřazené podle tématu.

## Nasazený model
| Soubor | Co v něm je |
|---|---|
| `clean-model.md` | model pro čistá měření: recept, co se zkoušelo a nepomohlo |
| `noise-window.md` | model pro zašuměná měření (časové okno 5 okamžiků) |
| `final-evaluation.md`, `final-evaluation-seeds.md` | porovnání receptur na 30 odložených výbojích, rozptyl přes semínka |
| `error-in-mm.md` | chyby v milimetrech s intervaly spolehlivosti |
| `locked-test-ids.txt` | čísla 30 odložených výbojů |
| `accuracy-{overall,outputs,ladder}-{cs,en}.png` | grafy přesnosti |

## Data a základní modely
| Soubor | Co v něm je |
|---|---|
| `data-checks.md` | rozptyly cílů, struktura šumu, model z pěti hlavních komponent |
| `baseline.md`, `baseline.json` | ridge a malá síť, křížová validace po výbojích |
| `distribution.md`, `unusual-shapes.*`, `unusual-heldout.md` | nerovnoměrné rozdělení dat a neobvyklé tvary |

## Vstupy, čas a rychlost
| Soubor | Co v něm je |
|---|---|
| `input-importance*.md/.json` | kolik vstupů stačí a které jsou důležité |
| `stability-over-time.*` | chování chyby během výboje |
| `latency.*`, `latency-shipped.md` | doba jednoho odhadu |

## Robustnost a další pokusy
| Soubor | Co v něm je |
|---|---|
| `robustness-findings.md` | šum, drift, množství dat, časový kontext |
| `signcanon.md`, `limiter-swap.md` | pokusy, které se nenasadily |

## Kamera a syntetická data
| Soubor | Co v něm je |
|---|---|
| `cloud-camera-*.md/.json`, `camera-v2*.{md,png}` | modely z kamery |
| `synthetic-validation.*` | uzavřený test na simulovaných rovnováhách se známou pravdou |
