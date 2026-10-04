# shot 0 camera check on left-out frames [80, 84, 88] (reference n86, 1672x941 px)

For each feature: its position in frame n found by template matching from n86, then mapped back to n86 by the camera; the error is the distance to where the feature really is in n86.  Correlation < 0.6: the match itself is doubtful.

| feature | n80 error (corr) | n84 error (corr) | n88 error (corr) | n82 error (corr) | n90 error (corr) |
|---|---|---|---|---|---|
| A speed line, upper | 12.4 (0.98) | 4.1 (0.99) | 2.6 (0.97) | 7.4 (0.99) | 4.3 (0.90) |
| B speed line, lower | 27.1 (0.91) | 8.4 (0.96) | 6.9 (0.92) | 17.0 (0.93) | 13.2 (0.71) |
| C sleeve seam cross | 85.5 (0.80) | 11.0 (0.93) | 9.5 (0.93) | 41.2 (0.73) | 17.8 (0.83) |
| D sleeve fold (ambiguous) | 3.3 (0.95) | 0.3 (0.99) | 1.4 (0.99) | 0.8 (0.97) | 6.8 (0.98) |
| E thumb nail | 3.0 (0.97) | 0.9 (0.98) | 1.2 (0.98) | 1.9 (0.98) | 1.6 (0.98) |
| F finger corner | 3.1 (0.96) | 1.0 (0.98) | 0.2 (0.99) | 2.1 (0.98) | 0.8 (0.97) |
| G right white region bend | 6.2 (0.78) | 1.9 (0.88) | 1.7 (0.90) | 3.8 (0.85) | 1.6 (0.85) |
| H pale block, top | 19.2 (0.98) | 3.2 (1.00) | 1.0 (0.99) | 9.8 (0.99) | 1.3 (0.98) |
| I right vertical lines | 5.4 (0.83) | 1.4 (0.96) | 1.4 (0.96) | 3.5 (0.89) | 2.3 (0.86) |
