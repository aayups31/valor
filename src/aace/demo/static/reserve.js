"use strict";
const el = id => document.getElementById(id);
const titles = {fast:"Work quickly",careful:"Work carefully",repair:"Repair the damage",stop:"Defer this release"};
const outcomes = {completed:"Release completed",stopped:"Release deferred",release_failure:"Release failed",outage:"System outage",running:"Work continues"};
const number = value => value.toLocaleString("en-US",{maximumFractionDigits:2});
let record, step = 0, request = 0;
function line(parent, tag, value, className) {
  const child = document.createElement(tag);
  child.textContent = value;
  if (className) child.className = className;
  parent.append(child);
  return child;
}
function renderSummary() {
  const band = el("outcomes");
  band.replaceChildren();
  for (const [key, label] of [["guarded","Guarded planning"],["baseline","One release at a time"]]) {
    const run = record[key], item = line(band,"div","");
    line(item,"p",label,"label");
    line(item,"strong",`${run.completed} of 2 completed`);
    line(item,"span",`${number(run.score)} score · ${run.outage + run.release_failure} terminal failures`);
  }
  const screen = record.guarded.forecast_screen;
  el("screen-text").textContent = screen.accepted
    ? "Lookahead selected. It passed all three checks against the simpler plan."
    : "One-release planning retained. Lookahead missed at least one of the checks below.";
  const checks = el("screen-checks");
  checks.replaceChildren();
  for (const [key, description] of [
    ["higher_score", "Predict a higher score"],
    ["completion_within_limit", "Predict at most 0.04 fewer completed releases"],
    ["failures_within_limit", "Predict at most 0.02 more terminal failures"],
  ]) {
    const result = record.screen_checks[key] ? "Passed" : "Missed";
    line(checks,"li",`${result} · ${description}`);
  }
  const details = el("screen-values");
  details.replaceChildren();
  for (const [key, name] of [["lookahead","Lookahead"],["myopic","One-release"]]) {
    const [score, failures, completed] = screen[key];
    line(details,"p",`${name} forecast across both releases: ${number(score)} score, ${number(completed)} expected completions, ${number(failures)} expected terminal failures.`);
  }
}
function resetPath() {
  step = 0;
  const jump = el("jump");
  jump.replaceChildren();
  record[el("policy").value].decisions.forEach((decision, index) => {
    const option = line(jump,"option",`Decision ${index+1} · Release ${decision.task+1}`);
    option.value = String(index);
  });
  renderStep();
}
function renderStep() {
  const run = record[el("policy").value], decision = run.decisions[step], after = decision.after;
  el("step").textContent = `RELEASE ${decision.task+1} OF 2 · DECISION ${step+1} OF ${run.decisions.length}`;
  el("action").textContent = titles[decision.selected];
  const shock = decision.observed_shock === null ? "" : decision.observed_shock ? " A shock occurred." : " No shock occurred.";
  el("observed").textContent = `Observed: ${outcomes[after.status]}.${shock}`;
  const state = el("state");
  state.replaceChildren();
  for (const [key,name] of [["resources","Reserve"],["integrity","Integrity (out of 3)"],["faults","Open faults"]]) {
    const item = line(state,"div","");
    line(item,"dt",name);
    line(item,"dd",`${decision.before[key]} → ${after[key]}`);
  }
  el("forecast-scope").textContent = run.executed_policy === "horizon_markov" && decision.task === 0
    ? "Forecasts cover both releases. The highest expected score in the selected policy wins this step."
    : "Forecasts cover this release. The highest expected score in the selected policy wins this step.";
  el("forecast-scope").textContent += ` This release is worth ${decision.stakes} points before time and cost adjustments. The model estimates a ${number(100*decision.shock_probability)}% shock chance if working quickly.`;
  const options = el("options");
  options.replaceChildren();
  for (const [action, forecast] of Object.entries(decision.alternatives)) {
    const row = line(options,"div","","option");
    line(row,"strong",titles[action] + (action === decision.selected ? " · Selected" : ""));
    line(row,"span",`Expected score ${number(forecast.expected_score)} · expected terminal failures ${number(forecast.expected_failure_count)}`);
  }
  el("jump").value = String(step);
  el("previous").setAttribute("aria-disabled", String(step === 0));
  el("next").setAttribute("aria-disabled", String(step+1 >= run.decisions.length));
  el("status").textContent = `Replay ready. ${el("step").textContent.toLowerCase()}.`;
}
async function load() {
  const current = ++request;
  el("run").disabled = true;
  el("status").textContent = "Loading the recorded comparison…";
  el("replay").hidden = true;
  try {
    const response = await fetch(`/api/reserve/${encodeURIComponent(el("scenario").value)}`);
    if (!response.ok) throw new Error("Replay unavailable.");
    const data = await response.json();
    if (current !== request) return;
    if (data.schema === "shared-reserve-replay-v1" && !data.screen_checks) {
      el("status").textContent = "An older VALOR is still open. Double-click Stop VALOR, then Start VALOR and reopen the replay.";
      return;
    }
    if (data.schema !== "shared-reserve-replay-v1") throw new Error("Unexpected replay format.");
    record = data;
    el("policy").value = "guarded";
    el("screen").open = false; el("alternatives").open = false;
    renderSummary(); resetPath();
    el("replay").hidden = false;
  } catch {
    if (current === request) el("status").textContent = "The replay couldn’t load. Check the local server and try again.";
  } finally {
    if (current === request) el("run").disabled = false;
  }
}
el("controls").addEventListener("submit",event=>{event.preventDefault();load();});
el("scenario").addEventListener("change",()=>{request++;record=null;el("run").disabled=false;el("replay").hidden=true;el("status").textContent="Load this situation to start its replay.";});
el("policy").addEventListener("change",resetPath);
el("jump").addEventListener("change",()=>{step=Number(el("jump").value);renderStep();});
el("previous").addEventListener("click",()=>{if(step>0){step--;renderStep();}});
el("next").addEventListener("click",()=>{if(record && step+1<record[el("policy").value].decisions.length){step++;renderStep();}});
el("download").addEventListener("click",()=>{
  const url = URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:"application/json"}));
  const link = document.createElement("a");
  link.href=url;link.download=`valor-reserve-${record.seed}.json`;link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});
