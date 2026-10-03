"use strict";
const $ = id => document.getElementById(id);
const labels = {heuristic_direct:"Direct heuristic",heuristic_detour:"Detour heuristic",oracle_planner:"Oracle planner"};
let sessionId = null, latest = null, inspectSide = "right", selectedPlan = null, busy = false;
const pretty = value => JSON.stringify(value, null, 2);
const fmt = (value, places=2) => Number(value).toFixed(places);
async function api(path, payload) {
  const response = await fetch(path, payload ? {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)} : {});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
function failure(error) { $("status").textContent = error.message; $("status").className = "error"; }
async function create() {
  const seed = Number($("seed").value);
  if (!Number.isInteger(seed) || seed < 0 || seed >= 2147483648) return failure(new Error("Use an integer seed between 0 and 2147483647."));
  try {
    if (sessionId) await api(`/api/session/${sessionId}/control`, {action:"pause"});
    latest = await api("/api/session", {scenario:$("scenario").value,seed,reference:"heuristic_direct",comparison:$("comparison").value});
    sessionId = latest.session_id; selectedPlan = null; render();
  } catch(error) { failure(error); }
}
async function control(action) {
  if (!sessionId) return;
  try { await api(`/api/session/${sessionId}/control`, {action,speed:Number($("speed").value)}); }
  catch(error) { failure(error); }
}
function addMetric(root, name, value) {
  const item = document.createElement("div"); item.className = "metric";
  const label = document.createElement("span"); label.textContent = name;
  const strong = document.createElement("strong"); strong.textContent = value;
  item.append(label, strong); root.append(item);
}
function map(side, run) {
  const canvas = $(`${side}-map`), ctx = canvas.getContext("2d"), o = run.observation, s = o.state;
  const pad = 45, w = canvas.width-2*pad, h = canvas.height-2*pad;
  const xy = p => [pad+p[0]/o.bounds[0]*w, canvas.height-pad-p[1]/o.bounds[1]*h];
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.strokeStyle = "#223236"; ctx.lineWidth = 1;
  for(let i=0;i<=10;i++) { let [x,y] = xy([i,i]); ctx.beginPath();ctx.moveTo(x,pad);ctx.lineTo(x,canvas.height-pad);ctx.stroke();ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(canvas.width-pad,y);ctx.stroke(); }
  for(const p of o.patches) {
    const a = xy([p.x0,p.y1]), b = xy([p.x1,p.y0]);
    ctx.fillStyle = "#f4b76d22";ctx.strokeStyle = "#c38b50";ctx.setLineDash([4,4]);
    ctx.fillRect(a[0],a[1],b[0]-a[0],b[1]-a[1]);ctx.strokeRect(a[0],a[1],b[0]-a[0],b[1]-a[1]);ctx.setLineDash([]);
    ctx.fillStyle = "#cda571";ctx.font = "10px monospace";ctx.fillText("TERRAIN", a[0]+7,a[1]+16);
  }
  function line(points, color, width, dashed=false) {
    if(points.length<2) return;ctx.strokeStyle=color;ctx.lineWidth=width;ctx.setLineDash(dashed?[4,5]:[]);ctx.beginPath();
    points.forEach((p,i)=>{const q=xy(p);i?ctx.lineTo(...q):ctx.moveTo(...q);});ctx.stroke();ctx.setLineDash([]);
  }
  if($("branches").checked && run.latest_decision) {
    for(const c of run.latest_decision.candidates) if(c.forecast) line(c.forecast.sample_path,c.status.startsWith("selected")?"#b9f38388":c.status==="constraint_rejected"?"#f58f843c":"#82bdff30",1.5,true);
  }
  line(run.path, side==="right"?"#b9f383":"#82bdff",2.5);
  function point(p,color,label) { const q=xy(p);ctx.fillStyle=color;ctx.beginPath();ctx.arc(...q,5,0,2*Math.PI);ctx.fill();ctx.font="10px monospace";ctx.fillText(label,q[0]+10,q[1]-10); }
  point(o.depot,"#82bdff","DEPOT");point(o.waypoint,"#b9f383",s.inspected?"INSPECTED":"WAYPOINT");
  const rover=xy([s.x,s.y]);ctx.fillStyle=s.status==="actuator_loss"||s.status==="battery_depleted"?"#f58f84":"#f1eee0";ctx.beginPath();ctx.arc(...rover,7,0,2*Math.PI);ctx.fill();
  ctx.strokeStyle="#0c1214";ctx.lineWidth=2;ctx.stroke();
  const metrics=$(`${side}-metrics`);metrics.replaceChildren();
  addMetric(metrics,"BATTERY",fmt(s.battery,1));addMetric(metrics,"HEALTH",`${fmt(s.health*100,0)}%`);addMetric(metrics,"SIM TIME",`${fmt(s.step*o.dt,1)}s`);addMetric(metrics,"STEP",s.step);
  const pill=$(`${side}-status`);pill.textContent=s.status.replaceAll("_"," ");pill.className="pill"+(s.status==="completed"?" good":s.status!=="running"?" bad":"");
}
function inspect() {
  const decision = latest[inspectSide].latest_decision;
  $("inspect-left").classList.toggle("active",inspectSide==="left");$("inspect-right").classList.toggle("active",inspectSide==="right");
  $("candidates").replaceChildren();
  if(!decision) { $("decision-meta").textContent="Step a controller to inspect its decision.";$("outcome").textContent="No action applied yet.";$("explanation").textContent="No candidates evaluated yet.";$("forecast-detail").textContent="";return; }
  $("decision-meta").textContent=`STEP ${decision.step}  ·  SELECTED ${decision.selected_plan}  ·  ${decision.forecast_source}  ·  ${fmt(decision.decision_ms)} ms  ·  ${decision.branch_transitions} branch transitions`;
  $("outcome").textContent=pretty({proposed_action:decision.proposed_action,applied_action:decision.applied_action,controller_bypassed:decision.controller_bypassed,guard_reason:decision.guard_reason,events:decision.actual_outcome.events,state:decision.actual_outcome.state});
  let current=decision.candidates.find(c=>c.plan===selectedPlan) || decision.candidates.find(c=>c.status.startsWith("selected")) || decision.candidates[0];
  for(const c of decision.candidates) {
    const row=document.createElement("tr");row.tabIndex=0;if(c===current)row.className="chosenrow";
    const f=c.forecast;
    const values=[c.plan.replaceAll("_"," "),c.status.replaceAll("_"," "),f?`${f.failure_count}/${f.particles} · 95% [${fmt(f.sampling_interval_95[0])}, ${fmt(f.sampling_interval_95[1])}]`:"not forecast",f?fmt(f.score):"—",f?`${fmt(f.mean_health*100,0)}%`:"—",f?fmt(f.mean_battery):"—"];
    values.forEach((v,i)=>{const cell=document.createElement("td");cell.textContent=v;if(i===1)cell.className=c.status;row.append(cell);});
    const choose=()=>{selectedPlan=c.plan;inspect();};row.addEventListener("click",choose);row.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();choose();}});$("candidates").append(row);
  }
  $("explanation").textContent=current.explanations.join(" ");
  $("forecast-detail").textContent=current.forecast?pretty({reason_codes:current.reason_codes,horizon_s:current.forecast.horizon_s,continuation:current.forecast.continuation,particles:current.forecast.particles,risk_estimate_kind:current.forecast.risk_estimate_kind,terminal_approximation:current.forecast.terminal_approximation,model_version:current.forecast.model_version,warning:current.forecast.warning}):"This controller did not run a forecast for this candidate.";
}
function render() {
  if(!latest)return;
  $("right-title").textContent=labels[latest.right.controller];
  $("status").className="";$("status").textContent=latest.error || `${latest.running?"Running":"Paused"} · ${latest.left.scenario.replaceAll("_"," ")} · seed ${latest.left.seed} · same initial state and disturbance seed`;
  map("left",latest.left);map("right",latest.right);inspect();
}
async function poll() {
  if(!sessionId||busy)return;busy=true;
  try {latest=await api(`/api/session/${sessionId}`);render();}catch(error){failure(error);}finally{busy=false;}
}
$("reset").addEventListener("click",create);
for(const action of ["run","pause","step","stop"])$(action).addEventListener("click",()=>control(action));
$("branches").addEventListener("change",render);
$("inspect-left").addEventListener("click",()=>{inspectSide="left";selectedPlan=null;inspect();});
$("inspect-right").addEventListener("click",()=>{inspectSide="right";selectedPlan=null;inspect();});
$("export").addEventListener("click",async()=>{
  if(!sessionId)return;
  try{const data=await api(`/api/session/${sessionId}/export`);const url=URL.createObjectURL(new Blob([pretty(data)],{type:"application/json"}));const a=document.createElement("a");a.href=url;a.download=`valor-${sessionId}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){failure(error);}
});
api("/api/scenarios").then(data=>{for(const name of data.scenarios){const option=document.createElement("option");option.value=name;option.textContent=name.replaceAll("_"," ");$("scenario").append(option);}$("scenario").value="shortcut";return create();}).catch(failure);
setInterval(poll,200);

