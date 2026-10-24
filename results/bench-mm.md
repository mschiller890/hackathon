# Millimetre benchmark of the selected model, 30 set-aside discharges

Command: `python analysis/bench_mm.py --model model/ipp1-selected.npz --set locked` (Apple M5, Sat 24 Oct 2026). The numbers match `results/ipp1-final.md` (candidate, plain, clean inputs).

```
Odchylka od rekonstrukce ústavu (absolutní hodnota |model − rekonstrukce|)
====================================================================================================
model   model/ipp1-selected.npz (the 119 development discharges (34211 rows), seed 0, recipe cand of
        analysis/ipp1_final.py (150 epochs, Huber 0.5))
sada    locked: odložené výboje (30 v results/ipp1-locked-test-ids.txt); 30 výbojů, 8761 řádků

Rozdělení odchylky v mm (proud plazmatu v kA), na řádcích, kde rekonstrukce veličinu má
----------------------------------------------------------------------------------------------------
veličina             řádků výb.     MAE  medián    RMSE     p90     p95     p99   p99.9     max
osa R                 8761   30   0.133  0.0614   0.374   0.254   0.403    1.39    4.42    15.1
osa Z                 8761   30   0.172  0.0785   0.741   0.307    0.47    1.59    5.46    37.2
osa 2D vzdálenost     8761   30    0.24   0.122    0.83     0.4   0.646    2.16    6.12    37.3
X bod R               5207   30   0.115  0.0558   0.454   0.178   0.277    1.01    9.28    10.1
X bod Z               5207   30  0.0969  0.0417   0.257   0.222   0.349   0.716    2.91    7.25
bod dopadu 1 R        5206   30   0.108  0.0546   0.219   0.219    0.39    1.03    1.81    2.77
bod dopadu 1 Z        5206   30  0.0459  0.0211    0.11  0.0838   0.161   0.461    1.01     2.9
bod dopadu 2 R        5206   30   0.136  0.0522   0.638   0.202   0.357     1.2    10.8    15.2
bod dopadu 2 Z        5206   30  0.0264  0.0117     0.1  0.0478  0.0772    0.22    1.63    2.83
bod limiteru R        3554   30    4.55   0.733    19.4    9.22    17.2    77.5     308     357
bod limiteru Z        3554   30    8.35    2.96    20.9      19    35.2    92.2     210     485
proud plazmatu kA     8760   30  0.0347  0.0258   0.047  0.0765  0.0982   0.143   0.185   0.398

Podíl řádků s odchylkou pod prahem (%) a 95% interval (bootstrap po výbojích, 1000×)
----------------------------------------------------------------------------------------------------
veličina              <0.1   <0.5     <1     <2     <5  MAE [95% interval]    pod 1 mm % [95% int.]
osa R                67.44  96.15  98.23  99.50  99.91  0.133 [0.099, 0.177]  98.23 [96.75, 99.26]
osa Z                58.04  95.43  98.04  99.37  99.83  0.172 [0.128, 0.223]  98.04 [96.39, 99.14]
osa 2D vzdálenost    41.59  92.98  96.93  98.84  99.79  0.24 [0.178, 0.311]   96.93 [94.73, 98.64]
X bod R              72.71  97.83  98.96  99.37  99.85  0.115 [0.0756, 0.168] 98.96 [97.62, 99.82]
X bod Z              77.78  97.23  99.42  99.67  99.96  0.0969 [0.0673, 0.13] 99.42 [98.72, 99.90]
bod dopadu 1 R       72.13  96.10  98.91  99.96 100.00  0.108 [0.0768, 0.144] 98.91 [97.75, 99.75]
bod dopadu 1 Z       91.97  99.02  99.88  99.96 100.00  0.0459 [0.0344, 0.0607] 99.88 [99.63, 100.00]
bod dopadu 2 R       72.76  97.35  98.83  99.23  99.65  0.136 [0.0836, 0.205] 98.83 [97.42, 99.77]
bod dopadu 2 Z       96.58  99.69  99.79  99.92 100.00  0.0264 [0.019, 0.0358] 99.79 [99.52, 99.96]
bod limiteru R        8.61  39.20  57.09  71.27  84.95  4.55 [3.3, 6.16]      57.09 [51.21, 62.50]
bod limiteru Z        2.50  11.51  22.20  39.08  66.01  8.35 [6.81, 10.2]     22.20 [19.06, 25.13]
proud plazmatu kA        –      –      –      –      –  0.0347 [0.0311, 0.0382] –

Konfigurace limitovaná / divertorová (model: is_limited > 0.5)
----------------------------------------------------------------------------------------------------
shoda s rekonstrukcí 99.16 % z 8761 řádků; výbojů s aspoň jedním rozdílem: 23
                            model limitovaná  model divertorová
rekonstrukce limitovaná                 3511                 43
rekonstrukce divertorová                  31               5176

10 řádků s největší odchylkou (řádek jednou, podle jeho největší odchylky polohy)
----------------------------------------------------------------------------------------------------
  #     výboj  rel. čas  veličina            odchylka mm  osa 2D mm
  1       104     0.263  bod limiteru Z              485      0.734
  2       104     0.251  bod limiteru R              357      0.722
  3       104     0.245  bod limiteru R              355      0.414
  4       104     0.248  bod limiteru R              352      0.484
  5       104     0.254  bod limiteru R              322      0.808
  6       104     0.257  bod limiteru R              295      0.543
  7        52     0.003  bod limiteru R              251       0.35
  8       129     0.000  bod limiteru R              247      0.484
  9         1     0.335  bod limiteru Z              235      0.617
 10       104     0.260  bod limiteru Z              234      0.502

Čísla jsou shoda s rekonstrukcí ústavu, ne odchylka od plazmatu samotného.
```
