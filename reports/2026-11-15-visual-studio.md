# VALOR visual supervision studio · November 15, 2026

## Delivered

Command opens on rendered hardware with a scenario picker and Run simulation. The scene follows a recorded proposal from the agent intake to the VALOR gate. The downstream signal plays when the record shows an applied action. Eight lights show completed units. Health, resources and time use the action's starting state until Observe reveals the recorded result. Animation stops on the first observation, and the complete run can be played or stepped separately.

Select Agent to open proposed plans, VALOR to inspect the decision, and Work to see the detailed state. Run evidence retains export, seed and reading controls. Futures presents estimated failure bars with the selected forecast beside them. Fear Memory highlights the observed signal through the current decision. Decision Chamber shows the chosen action and outcome, with reasons available on demand.

The original scene is served locally as an 84 KB WebP. The application ships without external asset or runtime dependencies for the visuals. The local launcher now requires interface version 7 so the new asset routes are available. No external service was provisioned.

## Verification

- 21 targeted checks passed in 13.59 seconds across `tests/test_study.py`, `tests/test_demo.py` and `tests/test_reserve_controls.py`. These cover the local WebP response, simulation records, trace transitions, and replay behavior. JavaScript syntax and Git whitespace checks passed.
- Isolated Chrome review at 1440 × 940 and 390 × 844 verified the visual loading, automatically illustrated first decision, plan selection, evidence navigation and phone layout. Escape closed the plan list and restored focus. Reduced motion kept the trace under manual control and disabled its visual animation. No application JavaScript or content security errors were reported.
- One local After damage replay showed health moving from 20% to 50% after the recovery action. A separate low-reserve replay showed the task being set aside. These are examples from the simulator. Existing trial and research evidence remain accessible separately.

## Scope and handoff

The hardware is an illustration. The local engine provides the decision and outcome data, and the fear signal is observer-only. The studio does not extend the validated tool workflow or production qualification. The next integration milestone is to use the same view with supervised receipts from a qualified live workflow.

Open Start VALOR or refresh http://127.0.0.1:8765/. Choose **After damage** and select **Run simulation** to see the full sequence. The local build was left running. Browser previews are saved in `artifacts`, including `valor-command-studio.png` and `valor-studio-phone.png`.

The initial visual studio commit `c137a89` was pushed before the final cleanup and this report. External service spend was $0.
