# flicker check [81, 84), 3 frames, 1672x941

Mean absolute change of a 1.5 px blurred grey image between adjacent frames (0-255).
"ratio" = change of (redraw - orig) / orig change.  Anomaly locator only (screen coordinates; camera
motion, gain, sharpening and the removed watermark all count), not a pass mark: judge by eye.
crop for crop_1to1.mp4: x=374 y=620 w=480 h=270

| pair | orig change | redraw change | change of (redraw - orig) | ratio | worst 1% of (redraw - orig) change |
|---|---|---|---|---|---|
| n81->82 | 3.83 | 4.82 | 1.81 | 0.47 | 19.5 |
| n82->83 | 3.76 | 4.25 | 1.45 | 0.39 | 19.5 |
