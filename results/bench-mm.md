# Millimetre benchmark of the shipped model, 30 set-aside discharges

Command: `python analysis/error_in_mm.py --model out/model/ipp1-ipn.npz --set locked` (AMD Ryzen 5 7535HS, Sat 24 Oct 2026, after the limiter point became the mean of the side network and the general network). The shipped model for clean inputs is `analysis/clean_model.py` (measurements divided by the plasma current, `results/ipp1-ipn.md`), trained on the 119 development discharges. Earlier shipped models on the same discharges: `cand` axis R 0.133 / Z 0.172 mm; `cand` plus a separate axis network 0.063 / 0.091 mm.

```
Odchylka od rekonstrukce ústavu (absolutní hodnota |model − rekonstrukce|)
====================================================================================================
model   out/model/ipp1-ipn.npz (119 discharges (34211 rows), seed 0, 150 epochs, Huber 0.2)
sada    locked: odložené výboje (30 v results/ipp1-locked-test-ids.txt); 30 výbojů, 8761 řádků

Rozdělení odchylky v mm (proud plazmatu v kA), na řádcích, kde rekonstrukce veličinu má
----------------------------------------------------------------------------------------------------
veličina             řádků výb.     MAE  medián    RMSE     p90     p95     p99   p99.9     max
osa R                 8761   30  0.0562  0.0316   0.184   0.121   0.164   0.364   0.836    11.8
osa Z                 8761   30  0.0647  0.0363   0.279   0.127   0.179   0.413    2.31    19.6
osa 2D vzdálenost     8761   30  0.0966  0.0631   0.334   0.175   0.251    0.57     2.4    22.9
X bod R               5207   30  0.0472   0.024   0.135  0.0902   0.124   0.479    2.08    3.26
X bod Z               5207   30  0.0526  0.0286   0.114    0.11   0.173   0.413    1.33    2.88
bod dopadu 1 R        5206   30  0.0744  0.0357     0.2    0.13   0.206   0.922    2.51     2.8
bod dopadu 1 Z        5206   30  0.0277  0.0148  0.0594  0.0575  0.0843   0.244   0.554    1.37
bod dopadu 2 R        5206   30  0.0518  0.0272   0.168  0.0999   0.164   0.375    1.72     7.1
bod dopadu 2 Z        5206   30  0.0116 0.00673  0.0401  0.0218  0.0343  0.0783   0.266    2.12
bod limiteru R        3554   30    2.85   0.331    18.4    2.68    6.01    35.2     281     352
bod limiteru Z        3554   30    4.49     1.3    17.1    7.54    14.5    52.3     233     439
proud plazmatu kA     8760   30  0.0343  0.0255  0.0466  0.0761  0.0961    0.14   0.185   0.384

Podíl řádků s odchylkou pod prahem (%) a 95% interval (bootstrap po výbojích, 1000×)
----------------------------------------------------------------------------------------------------
veličina              <0.1   <0.5     <1     <2     <5  MAE [95% interval]    pod 1 mm % [95% int.]
osa R                87.07  99.37  99.93  99.97  99.98  0.0562 [0.0476, 0.0658] 99.93 [99.87, 99.99]
osa Z                84.86  99.28  99.71  99.87  99.97  0.0647 [0.0541, 0.0778] 99.71 [99.49, 99.87]
osa 2D vzdálenost    74.03  98.70  99.66  99.87  99.97  0.0966 [0.0825, 0.112] 99.66 [99.43, 99.82]
X bod R              91.90  99.06  99.79  99.88 100.00  0.0472 [0.0352, 0.0617] 99.79 [99.43, 99.98]
X bod Z              88.34  99.29  99.83  99.98 100.00  0.0526 [0.0401, 0.0672] 99.83 [99.62, 99.96]
bod dopadu 1 R       83.52  98.33  99.08  99.71 100.00  0.0744 [0.0546, 0.0976] 99.08 [98.07, 99.89]
bod dopadu 1 Z       96.29  99.75  99.98 100.00 100.00  0.0277 [0.0211, 0.0352] 99.98 [99.94, 100.00]
bod dopadu 2 R       90.01  99.44  99.71  99.92  99.98  0.0518 [0.039, 0.0678] 99.71 [99.35, 99.92]
bod dopadu 2 Z       99.33  99.94  99.96  99.98 100.00  0.0116 [0.00964, 0.0141] 99.96 [99.87, 100.00]
bod limiteru R       26.20  58.67  71.83  85.73  94.23  2.85 [1.69, 4.44]     71.83 [67.12, 76.17]
bod limiteru Z        6.53  28.11  44.12  60.61  83.01  4.49 [3.73, 5.38]     44.12 [40.68, 47.68]
proud plazmatu kA        –      –      –      –      –  0.0343 [0.0306, 0.0379] –

Konfigurace limitovaná / divertorová (model: is_limited > 0.5)
----------------------------------------------------------------------------------------------------
shoda s rekonstrukcí 99.20 % z 8761 řádků; výbojů s aspoň jedním rozdílem: 22
                            model limitovaná  model divertorová
rekonstrukce limitovaná                 3512                 42
rekonstrukce divertorová                  28               5179

10 řádků s největší odchylkou (řádek jednou, podle jeho největší odchylky polohy)
----------------------------------------------------------------------------------------------------
  #     výboj  rel. čas  veličina            odchylka mm  osa 2D mm
  1       129     0.205  bod limiteru Z              439      0.232
  2       104     0.263  bod limiteru Z              411       1.12
  3        88     0.011  bod limiteru R              352      0.178
  4       129     0.000  bod limiteru R              349      0.153
  5       104     0.260  bod limiteru R              313       1.59
  6        44     0.205  bod limiteru Z              292       0.17
  7       104     0.257  bod limiteru R              283       1.03
  8       104     0.248  bod limiteru R              279       0.34
  9       104     0.245  bod limiteru R              279      0.467
 10        52     0.003  bod limiteru R              258     0.0781

Čísla jsou shoda s rekonstrukcí ústavu, ne odchylka od plazmatu samotného.
```
