# Manual Video Trace Protocol

Manual video traces are human-created replay JSON files for validating the simulator against observed gameplay axes.

This directory is offline-only. Do not scrape, download, OCR, or parse videos in this protocol. A human should record the observed actors, skills, targets, RNG outcomes, HP/energy/SP/current AV checkpoints, and assumptions into JSON.

Every trusted manual trace should pass both:

```bash
python -m hsr_axis_sim.sim.replay_lint hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
```

Use `templates/manual_video_trace_template.json` for future Bilibili or other video transcriptions. Empty URLs are allowed for synthetic fixtures.
