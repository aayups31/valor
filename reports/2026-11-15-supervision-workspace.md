# VALOR supervision workspace · November 15, 2026

## Delivered

- **Command** opens with a scenario picker and one primary run button. Its workspace shows projected options, the VALOR policy decision, and the state of the simulated work. The timeline, run player, and decision inspector use the same decision record. The first decision stays available until the reader chooses to advance. Raw evidence, export and seed controls sit under Run evidence.
- **Futures** displays evaluated branches and risk bars alongside the selected plan's forecast and policy reason. A proposal in Command opens its corresponding branch.
- **Fear Memory** plots observed damage and activation through the current decision, with exact values under a disclosure. The experiment records this signal separately from policy logic.
- **Decision Chamber** brings together the action, risk, score, strongest alternative and observed result. The alternative links to its forecast. Research and tool trial evidence has its own navigation.

The animation follows the recorded state through four stages. Work starts from the prior observed state. The Observe stage reveals the result, such as health moving from 20% to 50% in the local After damage recovery example. The stages remain selectable on their own and respect reduced motion.

The supplied screenshots and [Composio](https://composio.dev/), [Phoenix](https://arize.com/phoenix/), [Foundry](https://www.palantir.com/platforms/foundry/) and [Yutori](https://yutori.com/) guided the compact product navigation, mediation diagram and trace inspection. The delivered interface uses original VALOR styling and local assets.

## Verification

- 21 targeted checks passed in 8.36 seconds: `tests/test_study.py`, `tests/test_demo.py` and `tests/test_reserve_controls.py`. The tests cover the local simulator records, stage changes and controls. JavaScript syntax and Git whitespace checks passed.
- Tested the served app in an isolated Chrome profile at 1440 × 940 and 390 × 844. The browser opened the scenario picker, ran the recovery case, played the trace through observation, inspected a rejected plan, stepped the fear history and opened Decision Chamber. At 390 pixels, all six workspace views fit without horizontal overflow. A separate low-reserve run correctly reported that the task was set aside. The browser reported no application JavaScript or content security errors in these checks.
- Preview images are saved under `artifacts/`, including `valor-command-nov15.png` and `valor-phone-nov15.png`. External spend was $0.

## Boundaries and next step

The canvas illustrates simulated agent proposals and work. Logic applies the fixed policy, and fear activation is an experimental observer. The observed examples demonstrate how to inspect the simulation. Claims about real tool use and improvements belong to the separately recorded trials and research.

Implementation commits `3c5772b` and `4ca4c5d` contain the workspace and browser-reviewed refinements. Open Start VALOR or refresh http://127.0.0.1:8765/ to try it. The next integration milestone is to use the same inspection flow with supervised tool receipts from a qualified live workflow.
