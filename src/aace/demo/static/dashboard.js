"use strict";

(() => {
  const byId = id => document.getElementById(id);
  const say = (id, value) => { byId(id).textContent = value; };
  const scenarioNames = {
    benign: "Everyday work", hazard: "Under pressure", degraded: "After damage",
    low_reserve: "Low reserves", deadline: "Almost out of time"
  };
  const planNames = {
    checked: "Work carefully", fast: "Move quickly", restore: "Restore capacity",
    defer: "Stop this task", process_checked: "Work carefully", process_fast: "Move quickly"
  };
  const outcomes = {
    running: "Work continues", completed: "Work completed", abandoned: "Task set aside",
    irreversible_outage: "Irreversible outage", deadline_missed: "Deadline missed",
    quota_depleted: "Resources exhausted", action_deadline: "Action timed out",
    external_stop: "Stopped by supervisor", stale_state: "State changed",
    abstained: "No action applied", step_budget: "Decision limit reached"
  };
  const candidateLabels = {
    selected: "Chosen", lower_score: "Lower score", constraint_rejected: "Outside policy",
    unexplored: "Not evaluated", forecast_invalid: "Forecast unavailable", discarded: "Discarded"
  };
  const policyReasons = {
    failure_limit: "Its forecast exceeds the allowed failure risk.",
    insufficient_recovery_reserve: "It would leave too little in reserve for recovery.",
    capability_floor: "It would leave the system below its required health.",
    mission_deadline: "It would take longer than the available time.",
    lower_score: "Another plan within policy scored higher.",
    best_admissible_score: "It scored highest among the plans that met the policy.",
    unqualified_forecast: "Its forecast could not support a decision.",
    unknown_consequences: "Some required consequences are unknown.",
    not_evaluated: "The engine reached its evaluation budget.",
    forecast_invalid: "Its forecast could not be used.",
    unknown_resource_requirements: "Its resource requirements are incomplete.",
    forecast_identity_mismatch: "Its forecast belongs to a different state or plan.",
    forecast_scope_mismatch: "Its forecast applies to a different task domain.",
    insufficient_forecast_horizon: "Its forecast does not cover the full required horizon."
  };
  const traceNames = { proposal: "Agent proposals", policy: "VALOR findings", outcome: "Observed result" };
  const instrumentLinks = {
    "studio-link": "simulation", "futures-link": "futures",
    "memory-link": "memory", "chamber-link": "chamber"
  };
  let run = null;
  let runHistory = [];
  let decisionIndex = 0;
  let trace = "policy";
  let requestVersion = 0;
  let submitting = false;

  const scenarioName = name => scenarioNames[name] || "Simulation";
  const planName = name => planNames[name] || (name ? name.replaceAll("_", " ") : "No supported action");
  const outcomeName = status => outcomes[status] || (status ? status.replaceAll("_", " ") : "Unavailable");
  const percent = value => Number.isFinite(value) ? `${(100 * value).toFixed(1)}%` : "Unavailable";
  const units = value => Number.isFinite(value) ? `${Number(value.toFixed(2))} units` : "Unavailable";
  const seconds = value => Number.isFinite(value) ? `${Number(value.toFixed(2))} s` : "Unavailable";
  const runKey = record => record.example ? "example" : record.study_id;
  const candidates = row => row?.decision?.candidates || [];
  const chosen = row => candidates(row).find(candidate => candidate.status === "selected");
  const choiceName = row => planName(chosen(row)?.candidate.identifier || row?.proposed_action?.name);
  const observedName = row => outcomeName(row.commit?.status === "applied" ? row.actual_outcome?.status : row.commit?.status);
  const beforeState = index => run.decisions[index - 1]?.actual_outcome || run.initial_state;
  const plural = (count, single, many = `${single}s`) => `${count} ${count === 1 ? single : many}`;

  function node(tag, className, content) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content !== undefined) element.textContent = content;
    return element;
  }

  function status(message = "", tone = "") {
    say("dashboard-status", message);
    byId("dashboard-status").dataset.tone = tone;
  }

  async function json(path, options = {}) {
    const response = await fetch(path, { signal: AbortSignal.timeout(15000), ...options });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || `Request failed (${response.status})`);
    }
    return response.json();
  }

  function median(values) {
    if (!values.length) return null;
    const ordered = values.slice().sort((a, b) => a - b);
    const middle = Math.floor(ordered.length / 2);
    return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
  }

  function classifyStep(row, index) {
    const result = row.actual_outcome;
    if (!result || row.commit?.status !== "applied") return "stopped";
    if (result.status === "completed") return "completed";
    if (result.status === "abandoned") return "stopped";
    if (result.status !== "running") return "disrupted";
    if (result.integrity > beforeState(index)?.integrity) return "recovery";
    return "progress";
  }

  function updateLinks() {
    for (const [id, view] of Object.entries(instrumentLinks)) {
      const query = new URLSearchParams({ view });
      if (run) {
        query.set("run", runKey(run));
        query.set("decision", decisionIndex + 1);
      }
      byId(id).href = `/studio?${query}`;
    }
  }

  function facts(entries) {
    const list = node("dl", "trace-facts");
    for (const [label, value] of entries) {
      const fact = node("div");
      fact.append(node("dt", "", label), node("dd", "", value));
      list.append(fact);
    }
    return list;
  }

  function candidateList(plans, includeReasons = false) {
    const list = node("ul", "trace-list");
    for (const candidate of plans) {
      const item = node("li", "trace-item");
      const label = node("span", "trace-item-copy");
      label.append(node("strong", "", planName(candidate.candidate.identifier)));
      if (includeReasons) {
        const reason = reasonText(candidate);
        if (reason) label.append(node("small", "", reason));
      }
      const badge = node(
        "span", "trace-badge",
        includeReasons && candidate.forecast
          ? `${percent(candidate.forecast.failure_probability)} risk`
          : candidateLabels[candidate.status] || candidate.status.replaceAll("_", " ")
      );
      badge.dataset.status = candidate.status;
      item.append(label, badge);
      list.append(item);
    }
    return list;
  }

  function reasonText(candidate) {
    return (candidate?.reason_codes || []).map(code => policyReasons[code]).filter(Boolean).join(" ");
  }

  function renderTrace(row) {
    const container = byId("trace-content");
    say("trace-source", traceNames[trace]);
    for (const button of document.querySelectorAll("[data-trace]")) {
      button.setAttribute("aria-pressed", String(button.dataset.trace === trace));
    }
    container.replaceChildren();
    if (!row) {
      container.append(node("p", "dashboard-empty", "Choose a simulation to see its decision and outcome."));
      return;
    }

    const plans = candidates(row);
    if (trace === "proposal") {
      container.append(
        node("h3", "trace-heading", plural(plans.length, "possible plan")),
        node("p", "trace-summary", "The simulated agent starts with these options."),
        candidateList(plans)
      );
      return;
    }

    if (trace === "policy") {
      const selected = chosen(row);
      const excluded = plans.filter(candidate => candidate.status === "constraint_rejected");
      const guard = row.commit?.status;
      const elapsed = row.decision.decision_ms;
      const summary = reasonText(selected) || "No plan met the evidence and policy requirements.";
      container.append(node("h3", "trace-heading", choiceName(row)), node("p", "trace-summary", summary));
      container.append(
        facts([
          ["Plan failure forecast", percent(selected?.forecast?.failure_probability)],
          ["Action", guard === "applied" ? "Applied in simulation" : outcomeName(guard)],
          ["Forecasts evaluated", row.decision.forecast_calls],
          ["Decision time", Number.isFinite(elapsed) ? `${elapsed.toFixed(2)} ms` : "Unavailable"],
        ])
      );
      if (excluded.length) {
        const details = node("details", "trace-disclosure");
        details.append(
          node("summary", "", `${plural(excluded.length, "plan")} outside policy`),
          candidateList(excluded, true)
        );
        container.append(details);
      }
      return;
    }

    const after = row.actual_outcome;
    const before = beforeState(decisionIndex);
    const work = state => `${state.progress} / ${run.goal} complete`;
    const changes = (format, key) => {
      const previous = before ? format(before[key]) : "";
      const next = format(after[key]);
      return previous && previous !== next ? `${previous} → ${next}` : next;
    };
    container.append(
      node("h3", "trace-heading", observedName(row)),
      node("p", "trace-summary", row.commit?.status === "applied"
        ? `${planName(row.commit.applied_action?.name || chosen(row)?.candidate.identifier)} was applied.`
        : "This step ended without applying an action."),
      facts([
        ["Work", before && before.progress !== after.progress ? `${before.progress} → ${work(after)}` : work(after)],
        ["System health", changes(percent, "integrity")],
        ["Reserve", changes(units, "quota")],
        ["Simulated time", changes(seconds, "elapsed_s")]
      ])
    );
  }

  function renderDecision() {
    const row = run?.decisions[decisionIndex];
    const count = run?.decisions.length || 0;
    say("trace-position", row ? `Decision ${decisionIndex + 1} of ${count}` : "No decision selected");
    say("agent-preview", row ? plural(candidates(row).length, "plan") : "Awaiting proposals");
    say("valor-preview", row ? choiceName(row) : "Awaiting decision");
    say("work-preview", row ? `${row.actual_outcome.progress} / ${run.goal} complete` : "Awaiting result");
    byId("valor-preview").dataset.status = row?.commit?.status || "idle";
    byId("work-preview").dataset.status = row?.actual_outcome?.status || "idle";
    byId("trace-prev").disabled = !row || decisionIndex === 0;
    byId("trace-next").disabled = !row || decisionIndex >= count - 1;
    for (const [index, button] of Array.from(byId("decision-strip").children).entries()) {
      if (index === decisionIndex) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    }
    updateLinks();
    renderTrace(row);
    renderProduct(row);
  }

  function selectDecision(index) {
    if (!run || index < 0 || index >= run.decisions.length) return;
    decisionIndex = index;
    renderDecision();
  }

  function renderRun(record, step = 1) {
    if (!record?.state || !Array.isArray(record.decisions) || !Number.isFinite(record.goal)) {
      throw new Error("The run record is incomplete.");
    }
    run = record;
    decisionIndex = Math.min(Math.max(step - 1, 0), Math.max(0, record.decisions.length - 1));
    say("run-title", scenarioName(record.scenario));
    say("run-source", record.example ? "Example replay" : "Session simulation");
    byId("run-source").dataset.source = record.example ? "example" : "simulation";
    say("run-outcome", outcomeName(record.status));
    byId("run-outcome").dataset.status = record.status;
    byId("run-outcome").hidden = false;
    say("run-reference", record.example ? `Seed ${record.seed}` : `Run ${record.study_id.slice(0, 8)} · Seed ${record.seed}`);
    say("metric-work", `${record.state.progress} / ${record.goal}`);
    say("metric-decisions", record.decisions.length);
    let excluded = 0;
    for (const row of record.decisions) {
      excluded += candidates(row).filter(candidate => candidate.status === "constraint_rejected").length;
    }
    say("metric-excluded", excluded);
    const latency = median(record.decisions.map(row => row.decision?.decision_ms).filter(Number.isFinite));
    say("metric-latency", latency === null ? "—" : `${latency.toFixed(2)} ms`);
    const completion = record.goal > 0 ? Math.max(0, Math.min(100, 100 * record.state.progress / record.goal)) : 0;
    byId("work-ring").setAttribute("stroke-dasharray", `${completion} 100`);
    byId("work-ring").dataset.status = record.status;
    byId("export-run").disabled = false;

    const strip = byId("decision-strip");
    strip.replaceChildren();
    for (const [index, row] of record.decisions.entries()) {
      const button = node("button", "decision-step", String(index + 1).padStart(2, "0"));
      button.type = "button";
      button.dataset.stage = classifyStep(row, index);
      button.setAttribute("aria-label", `Decision ${index + 1}. ${choiceName(row)}. ${observedName(row)}.`);
      button.title = `${choiceName(row)} · ${observedName(row)}`;
      button.addEventListener("click", () => selectDecision(index));
      strip.append(button);
    }
    renderDecision();
    renderRecent();
  }

  function renderRecent() {
    const list = byId("recent-runs");
    const focused = list.contains(document.activeElement) ? document.activeElement.dataset.runId : null;
    const isList = ["UL", "OL"].includes(list.tagName);
    list.replaceChildren();
    if (!runHistory.length) {
      list.append(node(isList ? "li" : "p", "dashboard-empty", "Runs you start appear here."));
      return;
    }
    for (const entry of runHistory) {
      const button = node("button", "recent-run");
      button.type = "button";
      button.dataset.status = entry.status;
      button.dataset.runId = entry.study_id;
      button.setAttribute("aria-pressed", String(!!run && runKey(run) === entry.study_id));
      const copy = node("span", "recent-run-copy");
      const time = new Date(entry.recorded_at);
      const timestamp = entry.recorded_at && Number.isFinite(time.getTime())
        ? time.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })
        : "";
      const line = [plural(entry.decision_count, "decision"), timestamp].filter(Boolean).join(" · ");
      copy.append(node("strong", "recent-run-title", scenarioName(entry.scenario)), node("small", "recent-run-meta", line));
      button.append(copy, node("span", "recent-run-result", outcomeName(entry.status)));
      button.addEventListener("click", () => selectRun(entry.study_id));
      if (isList) {
        const item = node("li");
        item.append(button);
        list.append(item);
      } else {
        list.append(button);
      }
      if (focused === entry.study_id) button.focus({ preventScroll: true });
    }
  }

  function loading(message) {
    status(message, "loading");
    return ++requestVersion;
  }

  function recordPath(key) {
    return `/api/studies/${encodeURIComponent(key)}`;
  }

  async function selectRun(key) {
    if (submitting) return;
    const token = loading(key === "example" ? "Opening the example replay…" : "Opening the run…");
    try {
      const record = await json(recordPath(key));
      if (token !== requestVersion) return;
      renderRun(record);
      status();
    } catch {
      if (token !== requestVersion) return;
      status("Could not open that run. It may have expired from this session.", "error");
    }
  }

  async function initialize() {
    const token = loading("Loading the latest run…");
    const params = new URLSearchParams(window.location.search);
    const requested = params.get("run");
    const step = Number(params.get("decision"));
    let historyUnavailable = false;

    try {
      const { runs } = await json("/api/studies");
      if (token !== requestVersion) return;
      runHistory = runs;
      renderRecent();
    } catch {
      if (token !== requestVersion) return;
      historyUnavailable = true;
    }

    let requestedUnavailable = false;
    if (requested) {
      if (/^(example|[a-f0-9]{32})$/.test(requested)) {
        try {
          const record = await json(recordPath(requested));
          if (token !== requestVersion) return;
          renderRun(record, Number.isSafeInteger(step) && step > 0 ? step : 1);
          status();
          return;
        } catch {
          if (token !== requestVersion) return;
        }
      }
      requestedUnavailable = true;
    }

    try {
      const latest = runHistory[0]?.study_id;
      let record;
      if (latest && latest !== requested) {
        record = await json(recordPath(latest)).catch(() => null);
      }
      if (token !== requestVersion) return;
      if (!record) record = await json(recordPath("example"));
      if (token !== requestVersion) return;
      renderRun(record);
      if (requestedUnavailable) {
        status(record.example ? "That run is no longer in this session. Showing the example replay." : "That run is no longer in this session. Showing the latest run.", "notice");
      } else if (historyUnavailable) {
        status("Session history is unavailable. Showing the example replay.", "notice");
      } else {
        status();
      }
    } catch {
      if (token !== requestVersion) return;
      status("Could not load a replay. Start a simulation or reopen VALOR and try again.", "error");
    }
  }

  async function submitRun(event) {
    event.preventDefault();
    if (submitting) return;
    submitting = true;
    byId("run-submit").disabled = true;
    const token = loading("Running the local simulation…");
    try {
      const record = await json("/api/study", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario: byId("scenario-select").value, seed: 42 }),
      });
      if (token !== requestVersion) return;
      runHistory = [{
        study_id: record.study_id, scenario: record.scenario, recorded_at: record.recorded_at,
        status: record.status, decision_count: record.decisions.length
      }, ...runHistory.filter(entry => entry.study_id !== record.study_id)].slice(0, 12);
      trace = "policy";
      renderRun(record);
      status("Simulation recorded.", "success");
      json("/api/studies").then(({ runs }) => {
        if (token !== requestVersion) return;
        runHistory = runs;
        renderRecent();
      }).catch(() => {
        // The run itself is already rendered and listed from the POST response.
      });
    } catch {
      if (token !== requestVersion) return;
      status("Could not run the simulation. Check that VALOR is running and try again.", "error");
    } finally {
      submitting = false;
      byId("run-submit").disabled = false;
    }
  }

  const pages = {
    overview: ["Command Center", "Every decision. In perspective.", "See what the agent proposed, what VALOR found, and what followed."],
    agents: ["Agents", "An agent. With oversight.", "Inspect the simulated worker and its recorded decisions."],
    runs: ["Runs", "Follow the work.", "Move through the recorded decisions, one step at a time."],
    evaluations: ["Evaluations", "The choice behind the action.", "Compare the plans VALOR evaluated for the selected decision."],
    evidence: ["Evidence", "From prediction to proof.", "Observed results, experimental signals, and original records."]
  };
  function showPage() {
    const page = location.hash.slice(1) || "overview";
    const active = Object.hasOwn(pages, page) ? page : "overview";
    document.querySelectorAll("[data-screen]").forEach(el => { el.hidden = !el.dataset.screen.split(" ").includes(active); });
    document.querySelectorAll("[data-page]").forEach(el => {
      if (el.dataset.page === active) el.setAttribute("aria-current", "page");
      else el.removeAttribute("aria-current");
    });
    say("page-kicker", pages[active][0].toUpperCase());
    say("page-title", pages[active][1]);
    say("page-subtitle", pages[active][2]);
    document.title = `VALOR · ${pages[active][0]}`;
  }
  function panel(title, className = "") {
    const box = node("article", "instrument-panel " + className);
    box.append(node("h2", "panel-title", title)); return box;
  }
  function jump(label, page) {
    const link = node("a", "panel-link", label + " ↗"); link.href = "#" + page; return link;
  }
  function chart(values, label) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 500 130"); svg.classList.add("signal-chart");
    svg.setAttribute("role", "img"); svg.setAttribute("aria-label", label);
    const max = Math.max(1, ...values);
    const line = document.createElementNS(svg.namespaceURI,"polyline");
    line.setAttribute("points",values.map((v,i)=>`${10+i*480/Math.max(1,values.length-1)},${120-v/max*105}`).join(" ")); svg.append(line);
    values.forEach((v,i)=>{const dot=document.createElementNS(svg.namespaceURI,"circle");dot.setAttribute("cx",10+i*480/Math.max(1,values.length-1));dot.setAttribute("cy",120-v/max*105);dot.setAttribute("r","3");svg.append(dot);});
    return svg;
  }
  function renderProduct(row) {
    if (!row) return;
    const selected = chosen(row), plans = candidates(row), forecast = selected?.forecast;
    const overview = byId("decision-overview"); overview.replaceChildren();
    const active = panel("Active decision", "active-panel");
    active.append(node("span","eyebrow",`DECISION ${decisionIndex+1} / ${run.decisions.length}`),node("h3","feature-title",choiceName(row)),node("p","muted","Simulated service agent"));
    const chain=node("div","mini-chain");
    ["Agent","VALOR","Work"].forEach((x,i)=>chain.append(node("span",i===1?"chain-gate":"",x)));
    active.append(chain,jump("Inspect trace","runs"));
    const futures=panel("Consequence forecast","forecast-panel");
    futures.append(node("p","muted","Chosen plan · predicted outcomes"));
    [["Completion",forecast?.success_probability,"green"],["Failure",forecast?.failure_probability,"red"]].forEach(([label,value,tone])=>{
      const line=node("div","forecast-row");line.append(node("span","",label),node("strong",tone,percent(value)));
      const bar=node("div","forecast-track"), fill=node("i",tone);fill.style.width=Number.isFinite(value)?`${Math.max(0,Math.min(1,value))*100}%`:"0%";bar.append(fill);line.append(bar);futures.append(line);
    });
    futures.append(jump("Compare alternatives","evaluations"));
    const result=panel("Observed result","result-panel");
    const health=row.actual_outcome.integrity;
    const dial=node("div","health-dial");dial.style.setProperty("--health",`${Math.max(0,Math.min(1,health))*100}%`);
    const inner=node("div");inner.append(node("strong","",percent(health)),node("span","muted","System health"));dial.append(inner);
    result.append(dial,node("p","result-caption",observedName(row)));
    const recommendation=panel("VALOR recommendation","recommendation-panel");
    recommendation.append(node("span","recommendation-mark","✓"),node("h3","feature-title",choiceName(row)),node("p","muted",reasonText(selected)||"No plan met the policy requirements."),jump("See decision evidence","evidence"));
    const signals=panel("System health across this run","signals-panel");
    signals.append(chart([run.initial_state.integrity,...run.decisions.map(d=>d.actual_outcome.integrity)],"Observed system health from start through end of run. Scale zero to one."),node("p","chart-legend","Start → final observation · 0–100% health"));
    overview.append(active,futures,result,recommendation,signals);
    const agent=byId("agent-screen");agent.replaceChildren();
    const identity=panel("Supervised agent");identity.append(node("span","eyebrow","SIMULATION · LOCAL"),node("h3","feature-title","Service worker"),node("p","muted","The worker proposes plans. VALOR checks forecasts against policy before an action is applied."),facts([["Current plan",choiceName(row)],["Available plans",plans.length],["Connection","Local simulator"],["Action",row.commit?.status === "applied" ? "Applied in simulation" : outcomeName(row.commit?.status)]]),jump("Review decisions","runs"));
    const activity=panel("Decision history");
    run.decisions.forEach((d,i)=>{const b=node("button","activity-row");b.type="button";b.setAttribute("aria-pressed",String(i===decisionIndex));b.append(node("span","activity-number",String(i+1).padStart(2,"0")),node("strong","",choiceName(d)),node("span","muted",observedName(d)));b.onclick=()=>selectDecision(i);activity.append(b);});agent.append(identity,activity);
    const evaluation=byId("evaluation-screen");evaluation.replaceChildren();
    const comparison=panel("Evaluated alternatives","comparison-panel");
    comparison.append(node("p","muted",`Decision ${decisionIndex+1} · predictions, not observed outcomes.`));
    const table=node("div","comparison-table");
    const head=node("div","comparison-row comparison-head");["Plan","Completion","Failure","Score","Decision"].forEach(t=>head.append(node("span","",t)));table.append(head);
    plans.forEach(c=>{const line=node("div","comparison-row");line.dataset.selected=String(c.status==="selected");[planName(c.candidate.identifier),percent(c.forecast?.success_probability),percent(c.forecast?.failure_probability),Number.isFinite(c.score)?c.score.toFixed(3):"—",candidateLabels[c.status]||c.status].forEach(t=>line.append(node("span","",t)));table.append(line);});comparison.append(table);
    const why=panel("Why this plan");why.append(node("h3","feature-title",choiceName(row)),node("p","muted",reasonText(selected)||"No plan met the policy requirements."),candidateList(plans.filter(c=>c.status!=="selected"),true));evaluation.append(comparison,why);
    const evidence=byId("record-screen");evidence.replaceChildren();
    const observed=panel("Observed outcome");observed.append(node("h3","feature-title",observedName(row)),facts([["Work completed",`${row.actual_outcome.progress} / ${run.goal}`],["System health",percent(health)],["Reserve",units(row.actual_outcome.quota)],["Applied action",row.commit?.status === "applied" ? planName(row.commit.applied_action?.name) : "None"]]));
    const memory=panel("Fear Memory");const history=run.decisions.slice(0,decisionIndex+1).map(d=>d.affect_observer?.after?.arousal).filter(Number.isFinite);
    memory.append(chart(history,"Experimental activation through the selected decision; raw values, not probabilities."),node("p","muted","Experimental observer only. This signal does not select actions or change forecasts in this demo."));
    const source=panel("Record provenance");source.append(facts([["Source",run.example?"Example simulation":"Session simulation"],["Seed",run.seed],["Selected decision",decisionIndex+1],["Execution scope","Local simulator"]]),node("p","muted","Export record downloads forecasts, policy reasons and observations for the complete run."));evidence.append(observed,memory,source);
  }
  window.addEventListener("hashchange", showPage);
  showPage();

  byId("run-form").addEventListener("submit", submitRun);
  byId("example-run").addEventListener("click", () => selectRun("example"));
  byId("trace-prev").addEventListener("click", () => selectDecision(decisionIndex - 1));
  byId("trace-next").addEventListener("click", () => selectDecision(decisionIndex + 1));
  for (const button of document.querySelectorAll("[data-trace]")) {
    button.addEventListener("click", () => {
      if (!Object.hasOwn(traceNames, button.dataset.trace)) return;
      trace = button.dataset.trace;
      renderTrace(run?.decisions[decisionIndex]);
      if (window.matchMedia("(max-width: 980px)").matches) {
        byId("trace-inspector").scrollIntoView({ block: "nearest", behavior: "instant" });
      }
    });
  }
  byId("export-run").addEventListener("click", () => {
    if (!run) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(run, null, 2)], { type: "application/json" }));
    const link = node("a");
    link.href = url;
    link.download = `valor-${runKey(run)}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  renderRecent();
  renderDecision();
  initialize();
})();
