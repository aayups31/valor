"use strict";
const $ = id => document.getElementById(id);
const E = window.ValorEvidence;
let sessionId=null, latest=null, inspectSide="right", selectedPlan=null;
let polling=false, creating=false, commanding=false, lastRevision="", connectionFailed=false;
let requestVersion=0;
let toastTimer, guideMode="tour", guideStep=0, guideReturn=null;
const pretty=value=>JSON.stringify(value,null,2);
const fmt=(value,places=1)=>Number(value).toFixed(places);
const text=(id,value)=>{if($(id).textContent!==String(value)) $(id).textContent=value;};
const reducedMotion=()=>window.matchMedia("(prefers-reduced-motion: reduce)").matches;

async function api(path,payload) {
  const response=await fetch(path,{...(payload?{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}:{}),signal:AbortSignal.timeout(10000)});
  const data=await response.json();
  if(!response.ok) {const error=new Error(data.error || "The local engine could not complete that request.");error.status=response.status;throw error;}
  return data;
}
function toast(message) {
  clearTimeout(toastTimer); text("toast",message); $("toast").hidden=false;
  toastTimer=setTimeout(()=>{$("toast").hidden=true;},7000);
}
function failure(error) {
  connectionFailed=true;
  text("status","Connection interrupted");
  $("state-dot").className="error";
  text("playback-hint","Use the Start VALOR launcher to reopen the local engine. Your saved downloads remain on your computer.");
  toast(error.name==="TimeoutError" || error instanceof TypeError ? "The local engine is not responding. Reopen Start VALOR, then refresh this page." : error.message);
}
function setControls() {
  const unavailable=!latest || creating || commanding;
  for(const id of ["hero-start","run","restart","reset"]) $(id).disabled=unavailable;
  for(const id of ["step","stop"]) $(id).disabled=unavailable || (latest.left.ended && latest.right.ended);
  $("export").disabled=!latest || creating;
  $("scenario").disabled=creating || commanding || !latest;
  $("comparison").disabled=creating || commanding;
  $("seed").disabled=creating || commanding;
  $("speed").disabled=unavailable;
}
async function create({useSettings=true}={}) {
  if(creating || commanding) return false;
  const seed=useSettings ? Number($("seed").value) : latest.left.seed;
  if(!Number.isInteger(seed) || seed<0 || seed>=2147483648) {
    $("settings").open=true; $("seed").focus();
    toast("Use a whole number from 0 to 2147483647 for repeatable conditions."); return false;
  }
  const payload=useSettings ? {scenario:$("scenario").value,seed,reference:"heuristic_direct",comparison:$("comparison").value} :
    {scenario:latest.left.scenario,seed,reference:latest.left.controller,comparison:latest.right.controller};
  creating=true; requestVersion++; setControls();
  const previousId=sessionId;
  try {
    if(previousId) {
      try {await api("/api/session/"+previousId+"/control",{action:"pause"});}
      catch(error) {if(error.status!==404 && !error.message.includes("expired"))throw error;}
    }
    latest=await api("/api/session",payload); sessionId=latest.session_id;
    selectedPlan=null; lastRevision=""; connectionFailed=false;
    $("scenario").value=latest.left.scenario;
    render(true); return true;
  } catch(error) {
    if(latest) $("scenario").value=latest.left.scenario;
    failure(error); return false;
  } finally {creating=false;setControls();}
}
async function control(action) {
  if(!sessionId || creating || commanding) return;
  commanding=true; requestVersion++; setControls();
  const queriedId=sessionId;
  try {
    await api("/api/session/"+queriedId+"/control",{action,speed:Number($("speed").value)});
    // Fetch the worker's published state; avoid pretending a requested move already happened.
    const data=await api("/api/session/"+queriedId);
    if(sessionId===queriedId){latest=data;connectionFailed=false;render(true);}return true;
  } catch(error){failure(error);return false;} finally {commanding=false;setControls();}
}
async function toggleRun() {
  if(!latest || creating || commanding) return;
  if(latest.left.ended && latest.right.ended) {
    if(!await create({useSettings:false})) return;
  }
  await control(latest.running?"pause":"run");
}
function addMetric(root,label,value,note,ratio) {
  const item=document.createElement("div");
  const caption=document.createElement("span");caption.className="metric-label";caption.textContent=label;
  const strong=document.createElement("span");strong.className="metric-value";strong.textContent=value;
  item.append(caption,strong);
  if(ratio!==undefined) {
    const meter=document.createElement("div");meter.className="meter";
    const fill=document.createElement("span");fill.className="meter-fill";
    fill.style.transform="scaleX("+Math.max(0,Math.min(1,ratio))+")";
    meter.append(fill);item.append(meter);
  }
  const detail=document.createElement("span");detail.className="metric-note";detail.textContent=note;item.append(detail);
  root.append(item);
}
function drawMap(side,run) {
  const canvas=$(side+"-map"), ctx=canvas.getContext("2d"), o=run.observation, s=o.state;
  // Device pixel ratio keeps the same semantic drawing coordinates crisp on high-density screens.
  const W=720,H=460,dpr=Math.min(window.devicePixelRatio || 1,3);
  if(canvas.width!==W*dpr || canvas.height!==H*dpr){canvas.width=W*dpr;canvas.height=H*dpr;}
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);
  const padX=60,padY=46,w=W-2*padX,h=H-2*padY;
  const xy=p=>[padX+p[0]/o.bounds[0]*w,H-padY-p[1]/o.bounds[1]*h];
  ctx.fillStyle="#bccac2";
  for(let x=0;x<=o.bounds[0];x++) for(let y=0;y<=o.bounds[1];y++) {
    const q=xy([x,y]);ctx.beginPath();ctx.arc(q[0],q[1],.85,0,Math.PI*2);ctx.fill();
  }
  for(const p of o.patches) {
    const a=xy([p.x0,p.y1]), b=xy([p.x1,p.y0]);
    ctx.fillStyle="#bc905322";ctx.beginPath();ctx.roundRect(a[0],a[1],b[0]-a[0],b[1]-a[1],16);ctx.fill();
    ctx.save();ctx.clip();ctx.strokeStyle="#a87e4820";ctx.lineWidth=1;
    for(let n=-H;n<W;n+=12){ctx.beginPath();ctx.moveTo(n,0);ctx.lineTo(n+H,H);ctx.stroke();}
    ctx.restore();ctx.fillStyle="#886b44";ctx.font="11px -apple-system, Segoe UI, sans-serif";ctx.textAlign="center";
    ctx.fillText("Rough ground",(a[0]+b[0])/2,a[1]+22);
  }
  function line(points,color,width,dashed=false) {
    if(points.length<2)return;
    ctx.strokeStyle=color;ctx.lineWidth=width;ctx.lineCap="round";ctx.lineJoin="round";ctx.setLineDash(dashed?[4,7]:[]);
    ctx.beginPath();points.forEach((p,i)=>{const q=xy(p);i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]);});
    ctx.stroke();ctx.setLineDash([]);
  }
  if($("branches").checked && run.latest_decision) {
    for(const c of run.latest_decision.candidates) if(c.forecast) {
      line(c.forecast.sample_path,c.status.startsWith("selected")?"#357f7095":c.status==="constraint_rejected"?"#a45d4948":"#78899b40",1.8,true);
    }
  }
  line(run.path,side==="right"?"#367f72":"#697d8a",3.5);
  function landmark(p,color,label,inspected=false) {
    const q=xy(p);
    ctx.beginPath();ctx.fillStyle=color+"12";ctx.arc(q[0],q[1],17,0,Math.PI*2);ctx.fill();
    ctx.beginPath();ctx.fillStyle=color;ctx.arc(q[0],q[1],5,0,Math.PI*2);ctx.fill();
    ctx.font="12px -apple-system, Segoe UI, sans-serif";ctx.textAlign="center";ctx.fillStyle=color;ctx.fillText(label,q[0],q[1]+35);
    if(inspected){ctx.font="12px sans-serif";ctx.fillText("✓",q[0],q[1]-25);}
  }
  landmark(o.depot,"#566c85","Home");landmark(o.waypoint,"#2b8276",s.inspected?"Site inspected":"Inspection site",s.inspected);
  const rover=xy([s.x,s.y]), failed=s.status==="actuator_loss" || s.status==="battery_depleted";
  ctx.beginPath();ctx.fillStyle=failed?"#ac675327":"#fff";ctx.arc(rover[0],rover[1],13,0,Math.PI*2);ctx.fill();
  ctx.shadowColor="#21352b28";ctx.shadowBlur=12;ctx.shadowOffsetY=3;
  ctx.beginPath();ctx.fillStyle=failed?"#ad5d48":"#253b33";ctx.arc(rover[0],rover[1],8,0,Math.PI*2);ctx.fill();
  ctx.shadowBlur=0;ctx.shadowOffsetY=0;
  const angle=Math.atan2(-s.vy,s.vx);
  ctx.save();ctx.translate(rover[0],rover[1]);ctx.rotate(angle);
  ctx.fillStyle="#fff";ctx.beginPath();ctx.moveTo(4,0);ctx.lineTo(-2,-2.5);ctx.lineTo(-2,2.5);ctx.closePath();ctx.fill();ctx.restore();
  const remaining=Math.max(0,o.mission.deadline_s-s.step*o.dt);
  const metrics=$(side+"-metrics");metrics.replaceChildren();
  addMetric(metrics,"Battery",fmt(s.battery)+"%","Energy remaining",s.battery/100);
  addMetric(metrics,"Movement",Math.round(s.health*100)+"%","Damage reduces capacity",s.health);
  addMetric(metrics,"Time left",fmt(remaining)+"s","To inspect & return",remaining/o.mission.deadline_s);
  const status=$(side+"-status");
  status.textContent=!s.step?"Ready":E.statuses[s.status] || s.status;
  status.className="status-tag"+(s.status==="completed"?" good":s.status!=="running"?" bad":"");
  text(side+"-story",E.runStory(run));
  canvas.setAttribute("aria-label",(side==="left"?"Simple approach. ":"Comparison approach. ")+E.runStory(run)+" Battery "+fmt(s.battery)+" percent. Movement "+Math.round(s.health*100)+" percent. Time left "+fmt(remaining)+" seconds.");
}
function candidateDetail(candidate) {
  $("candidate-detail").hidden=!candidate;
  $("forecast-metrics").replaceChildren();
  if(!candidate){text("forecast-detail","No forecast yet.");return;}
  text("candidate-status",E.candidateStatuses[candidate.status] || candidate.status);
  text("candidate-title",E.plan(candidate.plan)[0]);
  text("explanation",E.reason(candidate));
  const f=candidate.forecast;
  if(f) {
    const values=[["Failures in sampled futures",f.failure_count+" of "+f.particles],["Movement after lookahead",Math.round(f.mean_health*100)+"%"],["Battery after lookahead",fmt(f.mean_battery)+"%"],["Mission score",fmt(f.score,2)]];
    for(const [name,value] of values){const item=document.createElement("div");item.className="forecast-stat";const label=document.createElement("span");label.textContent=name;const number=document.createElement("strong");number.textContent=value;item.append(label,number);$("forecast-metrics").append(item);}
    text("forecast-note","Up to "+f.horizon_s+" seconds ahead, using known simulator physics. The "+f.particles+" samples are coarse estimates. Zero sampled failures does not mean a plan is safe. Scores combine reward and a declared estimate of what remains beyond the forecast.");
    text("forecast-detail",pretty({reason_codes:candidate.reason_codes,...f}));
  } else {
    text("forecast-note","This option was not forecast. No predicted outcome or confidence is available.");
    text("forecast-detail",pretty({reason_codes:candidate.reason_codes,forecast:null}));
  }
}
function inspect() {
  if(!latest)return;
  for(const side of ["left","right"]){const button=$("inspect-"+side);button.classList.toggle("active",inspectSide===side);button.setAttribute("aria-pressed",String(inspectSide===side));}
  const decision=latest[inspectSide].latest_decision, story=E.describe(decision);
  text("decision-label",decision?"DECISION "+(decision.step+1)+" · "+E.controllers[decision.controller].short.toUpperCase():"READY WHEN YOU ARE");
  for(const [id,value] of [["decision-title",story.title],["decision-summary",story.summary],["choice",story.choice],["reason",story.reason],["outcome-summary",story.outcome]])text(id,value);
  const candidates=decision?decision.candidates:[];
  let current=candidates.find(c=>c.plan===selectedPlan) || candidates.find(c=>c.status.startsWith("selected")) || candidates[0];
  text("option-count",candidates.length?candidates.length+" listed":"");
  const list=$("candidates");
  // Keep candidate button nodes stable so polling does not steal keyboard focus.
  const signature=candidates.map(c=>c.plan).join("|");
  if(list.dataset.signature!==signature) {
    list.replaceChildren();list.dataset.signature=signature;
    for(const c of candidates) {
      const button=document.createElement("button");button.className="candidate-button";button.dataset.plan=c.plan;
      const icon=document.createElement("span");icon.className="candidate-icon";icon.setAttribute("aria-hidden","true");icon.textContent=E.plan(c.plan)[2];
      const wording=document.createElement("span"),name=document.createElement("span"),subtitle=document.createElement("span");
      name.className="candidate-name";name.textContent=E.plan(c.plan)[0];subtitle.className="candidate-subtitle";wording.append(name,subtitle);
      const badge=document.createElement("span");badge.className="candidate-badge";button.append(icon,wording,badge);
      button.addEventListener("click",()=>{selectedPlan=c.plan;inspect();});list.append(button);
    }
  }
  for(const button of list.children) {
    const c=candidates.find(c=>c.plan===button.dataset.plan),f=c.forecast;
    button.setAttribute("aria-pressed",String(c===current));
    button.querySelector(".candidate-subtitle").textContent=f?f.failure_count+" of "+f.particles+" sampled futures failed":E.plan(c.plan)[1];
    const badge=button.querySelector(".candidate-badge");badge.className="candidate-badge "+c.status;badge.textContent=E.candidateStatuses[c.status] || c.status;
  }
  candidateDetail(current);
  if(!decision){text("decision-meta","Waiting for the first decision.");text("outcome","No action applied yet.");return;}
  text("decision-meta","Decision "+(decision.step+1)+" · "+fmt(decision.decision_ms,2)+" ms to compute · "+decision.branch_transitions+" simulated transitions · "+(decision.forecast_source==="oracle_dynamics"?"Known simulator physics":"No model forecast"));
  text("outcome",pretty({proposed_action:decision.proposed_action,applied_action:decision.applied_action,controller_bypassed:decision.controller_bypassed,guard_reason:decision.guard_reason,events:decision.actual_outcome.events,state:decision.actual_outcome.state}));
}
function render(force=false) {
  if(!latest)return;
  const revision=[latest.session_id,latest.running,latest.speed,latest.error,latest.left.observation.state.step,latest.right.observation.state.step,inspectSide].join("|");
  if(!force && revision===lastRevision)return;
  lastRevision=revision;
  const mission=E.missions[latest.left.scenario];
  text("mission-title",mission[0]);text("mission-description",mission[1]);
  const controller=E.controllers[latest.right.controller];
  text("right-title",controller.title);text("right-description",controller.description);text("right-eyebrow",controller.eyebrow);text("inspect-right",controller.short);
  const bothEnded=latest.left.ended && latest.right.ended, started=latest.left.observation.state.step>0;
  const status=latest.error?"The engine paused with an error":bothEnded?"Both runs have finished":latest.running?"Mission in motion":started?"Paused · take your time":"Ready when you are";
  text("status",status);$("state-dot").className=latest.error?"error":latest.running?"running":"";
  text("run",bothEnded?"Run again":latest.running?"Pause":started?"Continue":"Start mission");
  text("hero-start",bothEnded?"Watch again ↗":latest.running?"Pause the demo":started?"Continue the demo ↗":"Start the demo ↗");
  text("playback-hint",bothEnded?"Compare the results above. Explore the options below, or run the same mission again.":latest.running?"Both rovers share the same starting conditions. Pause to examine a decision.":started?"One decision advances each unfinished rover by one move. Continue resumes the mission.":"Press Start mission. Pause whenever you want to explore a choice.");
  drawMap("left",latest.left);drawMap("right",latest.right);inspect();setControls();
  if(latest.error)toast("The engine paused: "+latest.error);
}
async function poll() {
  if(!sessionId || polling || creating || commanding || document.hidden)return;
  polling=true;const queriedId=sessionId,queriedVersion=requestVersion;
  try {
    const data=await api("/api/session/"+queriedId);
    if(queriedId===sessionId && queriedVersion===requestVersion && !creating && !commanding){const recovered=connectionFailed;latest=data;connectionFailed=false;render(recovered);}
  } catch(error){if(queriedVersion===requestVersion && !connectionFailed)failure(error);} finally {polling=false;}
}
const guideSteps=[
  {title:"A small mission. A bigger question.",copy:"The rover leaves home, inspects a site, and must get back before time runs out. Its energy and ability to move are limited. The risky shortcut puts rough ground in its path.",extra:"Start with the defaults. Everything runs on this computer."},
  {title:"Watch two approaches.",copy:"The left rover follows a fixed rule toward its goal. The right planner simulates six plans before moving. Both begin with the same state and disturbance sequence.",extra:"The solid line is the route actually taken. Dashed lines are sampled future routes, not promises."},
  {title:"Follow a real decision.",copy:"Pause whenever something interests you. “One decision” advances each unfinished rover once. Below the maps, see what was chosen, why it was chosen, and what happened after the action.",extra:"Explore the other options to find rejected plans and untested choices. A low failure count from three samples is still uncertain."},
  {title:"Explore at your own pace.",copy:"Try a different mission. Watch the battery, movement capacity and time remaining. You can restart the same conditions, apply brakes, or download both complete decision records.",extra:"This is an early research demo. The planner uses known simulator physics; learned predictions and AACE memory are upcoming work."}
];
function renderGuide() {
  const info=guideMode==="help"?{title:"What am I watching?",copy:"A simulated rover makes real, recorded control decisions. Its mission is to inspect a site and return home. The comparison shows how fixed rules and limited planning affect the outcome.",extra:"Battery is remaining energy. Movement is the rover’s remaining capacity after damage. Time left is the deadline for the complete round trip. The planner scores only its six listed plans with three sampled futures each; it does not evaluate every possibility."}:guideSteps[guideStep];
  text("guide-title",info.title);text("guide-copy",info.copy);
  $("guide-extra").replaceChildren();const p=document.createElement("p");p.textContent=info.extra;$("guide-extra").append(p);
  text("guide-eyebrow",guideMode==="help"?"HOW IT WORKS":"A QUICK WALKTHROUGH");
  text("guide-progress",guideMode==="help"?"Local research preview":(guideStep+1)+" / "+guideSteps.length);
  $("guide-back").hidden=guideMode==="help" || guideStep===0;
  text("guide-next",guideMode==="help"?"Got it":guideStep===guideSteps.length-1?"Explore the demo":"Next →");
}
async function openGuide(mode) {
  if(latest && latest.running)await control("pause");
  guideMode=mode;guideStep=0;guideReturn=document.activeElement;renderGuide();
  if(!$("guide-dialog").open)$("guide-dialog").showModal();
}
function closeGuide(){$("guide-dialog").close();}
$("help").addEventListener("click",()=>openGuide("help"));
$("tour").addEventListener("click",()=>openGuide("tour"));
$("guide-close").addEventListener("click",closeGuide);
$("guide-next").addEventListener("click",()=>{if(guideMode==="help" || guideStep===guideSteps.length-1)closeGuide();else{guideStep++;renderGuide();}});
$("guide-back").addEventListener("click",()=>{guideStep=Math.max(0,guideStep-1);renderGuide();});
$("guide-dialog").addEventListener("close",()=>{if(guideReturn)guideReturn.focus();});
$("hero-start").addEventListener("click",async()=>{await toggleRun();$("mission").scrollIntoView({behavior:reducedMotion()?"instant":"smooth",block:"start"});$("mission").focus({preventScroll:true});});
$("run").addEventListener("click",toggleRun);
$("step").addEventListener("click",()=>control("step"));
$("stop").addEventListener("click",async()=>{if(await control("stop"))toast("One braking action requested. The demo is paused.");});
$("restart").addEventListener("click",()=>create({useSettings:false}));
$("reset").addEventListener("click",()=>create());
$("scenario").addEventListener("change",()=>create());
$("speed").addEventListener("change",()=>{if(latest && latest.running)control("run");});
$("branches").addEventListener("change",()=>render(true));
for(const side of ["left","right"])$("inspect-"+side).addEventListener("click",()=>{inspectSide=side;selectedPlan=null;inspect();});
$("export").addEventListener("click",async()=>{
  if(!sessionId)return;
  try {
    const data=await api("/api/session/"+sessionId+"/export"),url=URL.createObjectURL(new Blob([pretty(data)],{type:"application/json"}));
    const link=document.createElement("a");link.href=url;link.download="valor-"+sessionId+".json";link.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);toast("Your full decision record was sent to your browser’s downloads.");
  } catch(error){failure(error);}
});
window.addEventListener("resize",()=>{if(latest){drawMap("left",latest.left);drawMap("right",latest.right);}});
document.addEventListener("visibilitychange",()=>{if(!document.hidden)poll();});
api("/api/scenarios").then(async data=>{
  for(const name of data.scenarios){const option=document.createElement("option");option.value=name;option.textContent=(E.missions[name] || [name,name,name])[2];$("scenario").append(option);}
  $("scenario").value="shortcut";await create();
}).catch(failure);
setInterval(poll,200);
