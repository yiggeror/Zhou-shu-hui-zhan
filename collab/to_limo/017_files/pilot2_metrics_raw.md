# flicker check [81, 84), 3 frames, 1672x941

Mean absolute change of a 1.5 px blurred grey image between adjacent frames (0-255).
"ratio" = change of (redraw - orig) / orig change.  Anomaly locator only (screen coordinates; camera
motion, gain, sharpening and the removed watermark all count), not a pass mark: judge by eye.
crop for crop_1to1.mp4: x=464 y=621 w=480 h=270

| pair | orig change | redraw change | change of (redraw - orig) | ratio | worst 1% of (redraw - orig) change |
|---|---|---|---|---|---|
| n81->82 | 3.83 | 6.45 | 3.42 | 0.89 | 35.8 |
| n82->83 | 3.76 | 4.56 | 3.24 | 0.86 | 34.1 |
