# Four decision instruments — November 13, 2026

## Delivered

The home application now organizes one simulation record into four views:

- **Command:** proposed plans pass through an illustrated Agent → VALOR → Work sequence. Four selectable stages explain proposal, anticipation, permission and observation. A finite animation stops at the observed result. Selecting a proposed plan opens its forecast. Work markers, health and resources come from the actual record.
- **Futures:** a branch diagram exposes each evaluated continuation, its failure probability, policy status and selection reason. The detail view includes completion forecast, duration and score. Forecast bars use native meters so they respect the existing content-security policy.
- **Fear Memory:** a shared-scale plot displays observed harm and lingering activation through the inspected decision. Individual readings remain available below the plot. Selecting an earlier observation changes the shared decision. Starting a new scenario clears the old history.
- **Decision Chamber:** selected action, expected score, failure forecast, duration, strongest scored alternative, its rejection reason and the observed result. An explicit link opens that alternative in Futures.

The interface uses black, gold and muted red, open diagrams, restrained type and fine connections. Evidence tools are collapsed in the navigation. Tutorials describe the current four-view workflow. Desktop navigation remains available beside the work; phone navigation stays above the active screen while scrolling.

The owner's supplied screenshots and [Foundry](https://www.palantir.com/platforms/foundry/), [Yutori](https://yutori.com/), [Composio](https://composio.dev/) and [Phoenix](https://arize.com/phoenix/) informed the visual direction. Their product capabilities are not VALOR capability claims.

## Verification

Command:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_study.py tests/test_demo.py tests/test_reserve_controls.py --basetemp artifacts/pytest-ui-verified-nov13
21 passed in 8.91s
```

These checks include actual engine/API records and a Node DOM double for shared navigation, branch selection, forecast bars, chart history, empty-state clearing, manual stages, finite animation, reduced-motion handling, alternative links and playback stopping. The DOM double is not a rendering test.

Separately reviewed the application through the in-app browser at the default desktop size and a 390 × 844 viewport override. Reviewed all four views, recovery and abandonment examples, selected a rejected branch, paused at a policy decision and checked persistent mobile navigation. Browser review exposed and resolved:

1. A stale Playing label after switching to flow animation.
2. View navigation preserving an inappropriate scroll position.
3. Inline forecast-bar widths rejected by the existing content-security policy; replaced them with native meters.

The final browser error log was empty. Command and Futures had matching document and viewport widths in the checked layouts. JavaScript syntax and Git whitespace checks passed. A local screenshot is saved at `artifacts/valor-command-nov13.jpg`; artifacts are excluded from Git. The full Python/model-training suite was not rerun for this interface-only change.

## Scope and limitations

- This demo computes a simulation locally, then reveals its record. The flow is an illustration of that record, not a live external agent/tool connection.
- Fear activation is an experimental observer in this service study. It does not influence forecasts, permission or action selection. Neither a number nor a visualization establishes subjective fear.
- Only the applied action has an observed outcome. The branch diagram shows a finite set of evaluated alternatives, not all possible futures.
- The policy still chooses the highest-scoring supported plan within fixed limits. This UI work does not establish a research advantage or broaden production qualification.
- No external assets, paid APIs or new services were added. External spend: $0.

## Version control and next steps

Implementation milestones `e635b2e`, `135f95d` and `a9fc535` are pushed to `origin/main`. The report and progress entry are committed separately as the closeout. The earlier automatic approval quota interruption was resolved on resumption; the pending implementation commit and subsequent push succeeded.

Open Start VALOR, or refresh http://127.0.0.1:8765/. Run **After damage**, select **Animate flow**, then visit Futures, Fear Memory and Decision Chamber. The server is running locally.

Next product work should bind these instruments to qualified live supervisor receipts while preserving the distinction between recorded simulation, actual tool operations and measured research. Changes to fear's influence require separate implementation and matched evaluation; the UI should only claim that influence once supported.
