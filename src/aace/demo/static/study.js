"use strict";
const byId=id=>document.getElementById(id);
const say=(id,value)=>{byId(id).textContent=value;};
const reducedMotion=window.matchMedia("(prefers-reduced-motion: reduce)");
const inspectionIds=["study-options","study-internals","study-records","study-metrics-help","study-settings"];
const scenarios={
  benign:["Room to move.","Finish eight units of simulated work with a light workload, enough resources and time.",20,1,30],
  hazard:["Under pressure.","Finish eight units of simulated work under high load, while keeping resources and system health.",20,1,30],
  degraded:["Starting after damage.","System health starts at 20%. Should VALOR spend resources and time recovering before it works?",20,.2,30],
  low_reserve:["Less left to spend.","Resources are scarce. Finishing the work may leave too little in reserve for recovery.",9,1,30],
  deadline:["Time is running short.","Eight units of work, five simulated seconds left. A quicker plan may still carry too much risk.",20,1,5]
};
const plans={checked:"Work carefully",fast:"Move quickly",restore:"Restore capacity",defer:"Stop this task"};
const states={running:"Work continues",completed:"Work completed",abandoned:"Task set aside",irreversible_outage:"Irreversible outage",deadline_missed:"Deadline missed",quota_depleted:"Resources exhausted"};
const reasons={failure_limit:"The forecast exceeds the permitted failure risk.",insufficient_recovery_reserve:"The full plan would leave less than the required resource reserve.",capability_floor:"Projected capability is below the required minimum.",mission_deadline:"The full plan exceeds the available task time.",lower_score:"Another admissible plan has a higher score under the same objective.",best_admissible_score:"This plan has the highest score among the supported options that meet the fixed policy.",unqualified_forecast:"The forecast evidence is not qualified for a decision.",unknown_consequences:"Some required consequences are unknown.",not_evaluated:"This option was not evaluated within the budget.",forecast_invalid:"The forecaster did not return usable evidence.",unknown_resource_requirements:"The resource or recovery requirements are incomplete.",forecast_identity_mismatch:"The forecast belongs to a different state or continuation.",forecast_scope_mismatch:"The forecast applies to a different domain.",insufficient_forecast_horizon:"The forecast does not cover the required horizon."};
let selectedScenario="hazard",run=null,index=0,selectedCandidate=null,busy=false,timer=null,toastTimer=null,guideReturn=null,failureMessage="";
const number=(v,d=1)=>Number.isFinite(v)?Number(v).toFixed(d):"Not estimated";
const percent=v=>Number.isFinite(v)?number(100*v,1)+"%":"Not estimated";
const pretty=v=>JSON.stringify(v,null,2);
function toast(message){clearTimeout(toastTimer);say("study-toast",message);byId("study-toast").hidden=false;toastTimer=setTimeout(()=>{byId("study-toast").hidden=true;},6500);}
function stopPlayback(){clearInterval(timer);timer=null;stopFlow();}
function controls(){
  byId("study-start").disabled=busy;
  byId("study-run").disabled=busy;
  byId("study").setAttribute("aria-busy",String(busy));
  say("study-start",busy?"Running…":"New run ↗");
  say("study-run",busy?"Running…":run?"Run again ↗":"Run simulation ↗");
  byId("study-play").disabled=busy || !run;
  byId("study-next").disabled=busy || !run || index>=run.decisions.length-1;
  byId("study-export").disabled=busy || !run;
  byId("study-seed").disabled=busy;
  document.querySelectorAll("[data-scenario]").forEach(b=>{b.disabled=busy;b.setAttribute("aria-pressed",String(b.dataset.scenario===selectedScenario));});
  say("study-play",timer?"Pause":run && index===run.decisions.length-1?"Replay record":"Play record");
}
function fields(target,entries){
  const container=byId(target);container.replaceChildren();
  for(const [label,value] of entries){const div=document.createElement("div"),dt=document.createElement("dt"),dd=document.createElement("dd");dt.textContent=label;dd.textContent=value;div.append(dt,dd);container.append(div);}
}
function candidateDetail(candidate){
  byId("study-candidate-detail").hidden=!candidate;
  if(!candidate)return;
  const f=candidate.forecast;
  const status={selected:"CHOSEN",lower_score:"LOWER SCORE",constraint_rejected:"OUTSIDE THE POLICY",unexplored:"NOT EVALUATED",forecast_invalid:"EVIDENCE UNAVAILABLE",discarded:"RESULT DISCARDED"};
  say("study-candidate-status",status[candidate.status] || candidate.status.toUpperCase());
  say("study-candidate-title",plans[candidate.candidate.identifier] || candidate.candidate.identifier);
  say("study-candidate-reason",candidate.reason_codes.map(code=>reasons[code] || code.replaceAll("_"," ")).join(" "));
  fields("study-forecast-values",f?[["Completion forecast",percent(f.success_probability)],["Failure forecast",percent(f.failure_probability)],["Plan duration",number(f.duration_s)+" seconds"],["Resources required",number(Object.fromEntries(f.resource_costs).processing_quota)+" units"],["Score",number(candidate.score,3)],["Evidence",f.evidence.kind==="analytic"?"Known simulation equations":f.evidence.kind]]:[["Forecast","Not available"]]);
}
function renderScene(state, row, config) {
  for (const [id, value, maximum, label] of [
    ["resources",state.quota,config[2],number(state.quota,0)+" units"],
    ["health",state.integrity,1,percent(state.integrity)],
    ["time",Math.max(0,config[4]-state.elapsed_s),config[4],number(Math.max(0,config[4]-state.elapsed_s),0)+" seconds"]
  ]) {
    byId("scene-"+id).value=value;
    byId("scene-"+id).setAttribute("max",String(maximum));
    say("scene-"+id+"-text",label);
  }
  say("scene-progress",state.progress+" / 8");
  say("scene-state",row ? states[state.status] || state.status : "Ready to begin");
  say("scene-position",row ? "Recorded decision "+(index+1)+" of "+run.decisions.length : "Awaiting a run");
  const work=byId("scene-work");
  work.replaceChildren();
  for(let i=0;i<8;i++){
    const unit=document.createElement("span");
    unit.textContent=String(i+1);
    unit.classList.toggle("complete",i<state.progress);
    unit.setAttribute("aria-label","Work unit "+(i+1)+(i<state.progress?" completed":" pending"));
    work.append(unit);
  }
  const options=byId("scene-options");
  options.replaceChildren();
  const candidates=row?.decision.candidates || [];
  for(const candidate of candidates){
    const button=document.createElement("button");
    const label=({selected:"Chosen",constraint_rejected:"Outside policy",lower_score:"Lower score"})[candidate.status] || candidate.status.replaceAll("_"," ");
    button.textContent=plans[candidate.candidate.identifier]+" · "+label;
    button.setAttribute("data-status",candidate.status);
    button.setAttribute("aria-pressed",String(selectedCandidate ? candidate.candidate.identifier===selectedCandidate : candidate.status==="selected"));
    button.addEventListener("click",()=>{
      stopPlayback();selectedCandidate=candidate.candidate.identifier;
      byId("study-options").open=true;render();byId("inspector-close").focus();
    });
    options.append(button);
  }
  const inspected=candidates.find(c=>c.candidate.identifier===selectedCandidate) || candidates.find(c=>c.status==="selected");
  say("scene-inspection-label",inspected ? "PLAN FORECAST / "+plans[inspected.candidate.identifier].toUpperCase() : "YOUR MISSION");
  say("scene-inspection-copy",inspected ? (inspected.forecast ? percent(inspected.forecast.success_probability)+" completion forecast. " : "")+
    inspected.reason_codes.map(code=>reasons[code] || code.replaceAll("_"," ")).join(" ")
    : "Complete the eight work units. Each action spends time and resources. Run a situation to reveal the evaluated plans.");
}
let tourStep=0;
const tourSteps=[
  "Choose a situation above. Start with Under pressure to see why faster work can be rejected.",
  "Run the simulation. The meters and eight work markers show the observed state at the displayed decision.",
  "Select a plan on the right. Its forecast and recorded selection reason appear below the scene. Red marks a policy rejection.",
  "Use Next decision or the numbered timeline below to follow the outcome. Open the complete record to verify or download the evidence."
];
byId("tour-next").addEventListener("click",()=>{
  stopPlayback();tourStep=(tourStep+1)%tourSteps.length;
  say("tour-count","GUIDE 0"+(tourStep+1)+" / 04");say("tour-copy",tourSteps[tourStep]);
  say("tour-next",tourStep===3?"Restart guide ↺":"Next tip →");
  render();
});
let flowTimer=null, flowPhase=0;
function stopFlow(){
  clearInterval(flowTimer);flowTimer=null;
  say("flow-play","Animate flow ▷");
}
function renderFlow(){
  const row=run?.decisions[index],chosen=row?.decision.candidates.find(c=>c.status==="selected");
  byId("gateway-flow").setAttribute("data-phase",String(flowPhase));
  const work=byId("command-work");work.replaceChildren();
  for(let i=0;i<8;i++){
    const unit=document.createElement("span");
    const completed=!!row && i<row.actual_outcome.progress;
    unit.classList.toggle("complete",completed);
    unit.setAttribute("aria-label","Work unit "+(i+1)+(completed?" completed":" pending"));
    unit.textContent=completed?"✓":String(i+1);work.append(unit);
  }
  const stages=["Proposal","Logic + signal","Policy decision","Observed result"];
  say("flow-step-label","0"+(flowPhase+1)+" · "+stages[flowPhase]);
  say("flow-proposal",row ? row.decision.candidates.length+" candidate plans" : "Candidate plans arrive here.");
  say("flow-logic",chosen ? plans[chosen.candidate.identifier] : "Awaiting plans");
  say("flow-fear",row ? number(row.affect_observer.before.arousal,3)+" · observer only" : "Observer only");
  say("flow-outcome",row ? states[row.actual_outcome.status] || row.actual_outcome.status : "The observed result appears here.");
  const captions=row ? [
    "The simulator proposed "+row.decision.candidates.length+" plans for the current state.",
    "VALOR compared their forecasts with the fixed policy. The fear signal was recorded separately.",
    chosen ? plans[chosen.candidate.identifier]+" was selected. Permission status · "+row.commit.status : "No supported plan was selected.",
    row.actual_outcome.progress+" of 8 work units completed after this action."
  ] : ["Run a scenario to trace a proposal through the simulation."];
  say("flow-caption",captions[flowPhase] || captions[0]);
  byId("flow-play").disabled=!row;
  byId("flow-step").disabled=!row;
}
byId("flow-step").addEventListener("click",()=>{
  stopPlayback();flowPhase=(flowPhase+1)%4;renderFlow();controls();
});
byId("flow-play").addEventListener("click",()=>{
  if(flowTimer){stopFlow();return;}
  stopPlayback();flowPhase=0;renderFlow();controls();
  if(reducedMotion.matches){toast("Use Next stage to explore the flow with reduced motion.");return;}
  say("flow-play","Pause flow Ⅱ");
  flowTimer=setInterval(()=>{
    flowPhase++;renderFlow();
    if(flowPhase===3)stopFlow();
  },1700);
});
function renderInstruments(row){
  renderFlow();
  say("instrument-position",row ? "Decision "+(index+1)+" / "+run.decisions.length : "Run a scenario in Command");
  byId("instrument-previous").disabled=!row || index===0;
  byId("instrument-next").disabled=!row || index>=run.decisions.length-1;
  const candidates=row?.decision.candidates || [];
  const chosen=candidates.find(c=>c.status==="selected");
  const inspected=candidates.find(c=>c.candidate.identifier===selectedCandidate) || chosen;
  say("future-origin",row ? "Decision "+(index+1) : "Awaiting a decision");
  const branches=byId("future-branches");
  branches.replaceChildren();
  for(const candidate of candidates){
    const button=document.createElement("button");
    button.setAttribute("data-status",candidate.status);
    button.setAttribute("aria-pressed",String(candidate===inspected));
    const title=document.createElement("strong"),metric=document.createElement("span");
    title.textContent=plans[candidate.candidate.identifier];
    metric.textContent=candidate.forecast ? percent(candidate.forecast.failure_probability)+" failure forecast · "+candidate.status.replaceAll("_"," ") : "Forecast unavailable";
    button.append(title,metric);
    button.addEventListener("click",()=>{
      stopPlayback();selectedCandidate=candidate.candidate.identifier;render();
      byId("future-name").focus();
    });
    branches.append(button);
  }
  say("future-label",inspected ? inspected.status.replaceAll("_"," ").toUpperCase() : "SELECT A BRANCH");
  say("future-name",inspected ? plans[inspected.candidate.identifier] : "Run a scenario to begin.");
  say("future-reason",inspected ? inspected.reason_codes.map(code=>reasons[code] || code.replaceAll("_"," ")).join(" ") : "");
  const forecast=inspected?.forecast;
  fields("future-metrics",forecast ? [["Completion",percent(forecast.success_probability)],["Failure",percent(forecast.failure_probability)],["Duration",number(forecast.duration_s)+" s"],["Score",number(inspected.score,3)]] : []);
  const trace=byId("memory-trace");trace.replaceChildren();
  const history=run ? run.decisions.slice(0,index+1) : [];
  say("memory-summary",row ? history.length+" recorded steps · "+number(row.affect_observer.after.arousal,3)+" current activation" : "Run a scenario to inspect the signal history.");
  const ceiling=Math.max(1,...history.flatMap(entry=>[entry.affect_observer.after.arousal,entry.affect_observer.after.observed_harm]));
  for(const [position,entry] of history.entries()){
    const event=document.createElement("div"),label=document.createElement("button");
    label.textContent="Decision "+(position+1);
    label.setAttribute("aria-current",position===index?"step":"false");
    label.addEventListener("click",()=>{stopPlayback();index=position;selectedCandidate=null;render();byId("memory-title").focus();});
    event.append(label);
    for(const [key,name] of [["observed_harm","Observed harm"],["arousal","Activation"]]){
      const cell=document.createElement("label"),bar=document.createElement("meter"),value=document.createElement("span");
      bar.setAttribute("aria-label",name+" at decision "+(position+1));bar.setAttribute("max",String(ceiling));
      bar.value=entry.affect_observer.after[key];
      value.textContent=number(bar.value,3);
      cell.append(bar,value);event.append(cell);
    }
    trace.append(event);
  }
  say("chamber-status",row ? "POLICY DECISION / "+row.commit.status.toUpperCase() : "AWAITING A RUN");
  say("chamber-action",chosen ? plans[chosen.candidate.identifier] : "No selected plan");
  say("chamber-reason",chosen ? chosen.reason_codes.map(code=>reasons[code] || code.replaceAll("_"," ")).join(" ") : "Run a scenario from Command.");
  const f=chosen?.forecast;
  fields("chamber-metrics",f ? [["Expected score",number(chosen.score,3)],["Failure forecast",percent(f.failure_probability)],["Time required",number(f.duration_s)+" s"],["Fear influence","Observer only"]] : []);
  const alternative=candidates.filter(c=>c!==chosen && Number.isFinite(c.score)).sort((a,b)=>b.score-a.score)[0];
  say("chamber-alternative",alternative ? plans[alternative.candidate.identifier]+" · score "+number(alternative.score,3)+" · "+alternative.status.replaceAll("_"," ") : "No other scored plan.");
  say("chamber-outcome",row ? row.actual_outcome.progress+" / 8 completed · "+percent(row.actual_outcome.integrity)+" health · "+(states[row.actual_outcome.status] || row.actual_outcome.status) : "No outcome yet.");
}
function render(){
  const config=scenarios[selectedScenario],row=run?.decisions[index],state=row?.actual_outcome || {quota:config[2],integrity:config[3],progress:0,elapsed_s:0,status:"running"};
  renderScene(state,row,config);
  renderInstruments(row);
  say("study-title",config[0]);say("study-description",config[1]);
  say("work-count",state.progress);say("quota-value",number(state.quota,0)+" units");say("integrity-value",number(state.integrity*100,1)+"%");say("time-value",number(Math.max(0,config[4]-state.elapsed_s),0)+" seconds");
  [...byId("work-track").children].forEach((point,i)=>point.classList.toggle("done",i<state.progress));
  say("study-phase",row?(states[state.status] || state.status).toUpperCase():"READY WHEN YOU ARE");
  const status=row?"Decision "+(index+1)+" of "+run.decisions.length:"Ready to begin";
  say("study-playback-status",busy?"The local engine is computing your run…":failureMessage || (timer?"Playing · "+status.toLowerCase():status));
  const timeline=byId("study-timeline");
  if(!row){
    say("step-label","BEFORE THE FIRST MOVE");say("chosen-title","Four options. One next move.");
    say("chosen-reason","Work carefully, move quickly, recover, or stop. VALOR compares the proposed plans against the same limits before choosing.");
    say("study-story","Run the experiment to see what VALOR chooses and how the situation changes.");
    say("choice-prediction","What the full plan is expected to achieve.");say("choice-result","What actually happened after the next action.");
    say("lens-danger","Outage, a missed deadline, or resources running out.");
    say("lens-belief","Forecasts use the starting conditions and the rules of this simulation.");
    say("lens-choice","Run a scenario to see which action the simulator applies.");
    say("record-caption","The engine computes a complete run locally. Playback reveals its recorded decisions.");
    say("study-provenance","The complete record includes policy, alternatives, forecasts, guarded actions, outcomes and source identity.");
    say("study-raw","Run an experiment to inspect its record.");
    timeline.replaceChildren();byId("study-candidates").replaceChildren();byId("study-candidate-detail").hidden=true;
    fields("study-affect-values",[["Awaiting an observation","Not yet available"]]);controls();return;
  }
  const candidates=row.decision.candidates,chosen=candidates.find(c=>c.status==="selected"),f=chosen?.forecast;
  say("step-label","DECISION "+(index+1)+" / ACTUAL ENGINE RECORD");
  say("chosen-title",chosen?plans[chosen.candidate.identifier]:"No supported action.");
  say("chosen-reason",chosen?(chosen.candidate.identifier==="defer"?"Stop this task and preserve the remaining resources. Setting work aside is recorded separately from finishing it.":chosen.candidate.identifier==="restore"?"Recover first, then propose careful work. This plan includes the time and resources recovery needs.":chosen.candidate.identifier==="checked"?"Careful work ranks highest among the plans that pass the risk, resource and capability limits. The forecast covers its full proposed plan.":"The quicker plan ranks highest while passing the same risk, resource and capability limits."):"None of the evaluated plans had enough support to act. VALOR did not apply a proposal.");
  say("study-story",state.status==="running"?state.progress+" of 8 work units completed. The next decision uses the updated state.":state.status==="completed"?"All eight units were completed in this simulated run.":state.status==="abandoned"?"The task was abandoned. Preserving a reserve does not count as completing the work.":"The observed outcome was "+(states[state.status] || state.status).toLowerCase()+". A permitted nonzero risk can still produce failure.");
  say("choice-prediction",f?"Before acting: "+percent(f.success_probability)+" completion and "+percent(f.failure_probability)+" failure forecast for this full continuation.":"No qualified consequence forecast was available.");
  say("choice-result",row.commit.status==="applied"?"After the next action: "+state.progress+" of 8 completed, "+number(state.integrity*100,1)+"% system health. "+(states[state.status] || state.status)+".":"The final permission check did not apply this proposal: "+row.commit.status.replaceAll("_"," ")+".");
  const rejected = candidates.filter(candidate=>candidate.status==="constraint_rejected");
  const limits = [...new Set(rejected.flatMap(candidate=>candidate.reason_codes))];
  say("lens-danger",limits.length ? limits.map(code=>reasons[code] || code.replaceAll("_"," ")).join(" ")
    : "No evaluated plan was rejected by the policy limits at this step.");
  say("lens-belief",f ? percent(f.success_probability)+" completion forecast for the chosen plan, using the simulation rules."
    : "There is no qualified forecast for an applied plan at this step.");
  say("lens-choice",row.commit.status==="applied" && chosen ? plans[chosen.candidate.identifier]+". The simulator applied its next action."
    : "The simulator did not apply a proposed action at this step.");
  say("record-caption","Recorded simulation · "+number(row.decision.decision_ms,2)+" ms to decide · "+row.decision.forecast_calls+" forecasts · Playback changes the view, not the decisions.");
  if(timeline.dataset.study!==run.study_id){
    timeline.replaceChildren();timeline.dataset.study=run.study_id;
    run.decisions.forEach((decision,i)=>{const li=document.createElement("li"),button=document.createElement("button");button.textContent=String(i+1).padStart(2,"0");button.setAttribute("aria-label","Inspect decision "+(i+1));button.addEventListener("click",()=>{stopPlayback();index=i;selectedCandidate=null;render();});li.append(button);timeline.append(li);});
  }
  [...timeline.children].forEach((li,i)=>{if(i===index)li.firstChild.setAttribute("aria-current","step");else li.firstChild.removeAttribute("aria-current");});
  const list=byId("study-candidates");
  if(!list.children.length){
    candidates.forEach(c=>{const button=document.createElement("button"),name=document.createElement("span"),badge=document.createElement("span");button.dataset.plan=c.candidate.identifier;name.textContent=plans[c.candidate.identifier];badge.className="study-option-badge";button.append(name,badge);button.addEventListener("click",()=>{stopPlayback();selectedCandidate=button.dataset.plan;render();});list.append(button);});
  }
  const selected=candidates.find(c=>c.candidate.identifier===selectedCandidate) || chosen || candidates[0];
  [...list.children].forEach(button=>{const c=candidates.find(c=>c.candidate.identifier===button.dataset.plan);button.dataset.status=c.status;button.setAttribute("aria-pressed",String(c===selected));button.lastChild.textContent=({selected:"Chosen",lower_score:"Lower score",constraint_rejected:"Outside policy",unexplored:"Not evaluated",forecast_invalid:"No evidence",discarded:"Discarded"})[c.status] || c.status;});
  candidateDetail(selected);
  const affect=row.affect_observer;
  fields("study-affect-values",[["Observed integrity loss",number(affect.after.observed_harm,4)],["Activation before → after",number(affect.before.arousal,3)+" → "+number(affect.after.arousal,3)],["Slower sensitization trace",number(affect.after.sensitization,3)],["Current cue association",number(affect.after.current_cue_activation,3)],["Influence on this decision","Observer only"]]);
  say("study-provenance","Analytic service benchmark · seed "+run.seed+" · source "+run.git_revision.slice(0,7)+(run.git_dirty?" with local edits":"")+" · No real service controlled. Raw activations are experimental.");
  say("study-raw",pretty(row));controls();
}
async function begin(){
  if(busy)return;
  showWorkspace("simulation");
  const seed=Number(byId("study-seed").value);
  if(!Number.isInteger(seed)||seed<0||seed>=2147483648){byId("study-settings").open=true;byId("study-seed").focus();toast("Use a whole starting number from 0 to 2147483647.");return;}
  stopPlayback();failureMessage="";busy=true;render();
  try{
    const response=await fetch("/api/study",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({scenario:selectedScenario,seed}),signal:AbortSignal.timeout(10000)});
    const data=await response.json();if(!response.ok)throw new Error(data.error || "The study could not start.");
    flowPhase=0;run=data;index=0;selectedCandidate=null;byId("study-timeline").dataset.study="";byId("study-candidates").replaceChildren();
    if(run.decisions.length>1 && !reducedMotion.matches && !inspectionIds.some(id=>byId(id).open))startPlayback();
    byId("study").scrollIntoView({behavior:reducedMotion.matches?"instant":"smooth",block:"start"});byId("study").focus({preventScroll:true});
  }catch(error){toast(error instanceof TypeError || error.name==="TimeoutError"?"The local engine is not responding. Reopen Start VALOR, then refresh this page.":error.message);failureMessage=run?"The new study could not start. The previous record is still available.":"The study could not start. Reopen Start VALOR, then try again.";}
  finally{busy=false;render();}
}
function startPlayback(){
  stopPlayback();timer=setInterval(()=>{if(index>=run.decisions.length-1){stopPlayback();}else{index++;selectedCandidate=null;if(index===run.decisions.length-1)stopPlayback();}render();},1400);
}
byId("study-start").addEventListener("click",begin);
byId("study-run").addEventListener("click",begin);
function showWorkspace(view){
  stopPlayback();
  byId("instrument-navigation").hidden=!["futures","memory","chamber"].includes(view);
  for(const [name,panel] of [["simulation","study"],["futures","futures"],["memory","memory"],["chamber","chamber"],["execution","execution"],["research","research"]]){
    byId(panel).hidden=name!==view;
    byId("nav-"+name).setAttribute("aria-pressed",String(name===view));
  }
}
for(const name of ["simulation","futures","memory","chamber","execution","research"]){
  byId("nav-"+name).addEventListener("click",()=>{showWorkspace(name);render();});
}
byId("instrument-command").addEventListener("click",()=>{showWorkspace("simulation");render();});
for(const [id,delta] of [["instrument-previous",-1],["instrument-next",1]]){
  byId(id).addEventListener("click",()=>{
    if(!run)return;
    stopPlayback();index=Math.max(0,Math.min(run.decisions.length-1,index+delta));selectedCandidate=null;flowPhase=0;render();
  });
}
byId("inspector-close").addEventListener("click",()=>{byId("study-options").open=false;byId("study-run").focus();});
for (const [link, panel] of [["mission-futures","study-options"],["mission-memory","study-internals"]]) {
  byId(link).addEventListener("click",()=>{
    showWorkspace("simulation");byId(panel).open=true;render();
    if(panel==="study-options")byId("inspector-close").focus();
    else byId(panel).scrollIntoView({block:"center",behavior:"instant"});
  });
}
byId("study-next").addEventListener("click",()=>{stopPlayback();if(run && index<run.decisions.length-1){index++;selectedCandidate=null;}render();});
byId("study-play").addEventListener("click",()=>{if(!run)return;if(timer)stopPlayback();else{if(index>=run.decisions.length-1){index=0;selectedCandidate=null;}startPlayback();}render();});
document.querySelectorAll("[data-scenario]").forEach(button=>button.addEventListener("click",()=>{if(busy)return;stopPlayback();selectedScenario=button.dataset.scenario;run=null;index=0;selectedCandidate=null;failureMessage="";render();}));
for(const id of inspectionIds)byId(id).addEventListener("toggle",()=>{if(byId(id).open){stopPlayback();render();}});
reducedMotion.addEventListener?.("change",()=>{if(reducedMotion.matches){stopPlayback();render();}});
document.addEventListener("visibilitychange",()=>{if(document.hidden){stopPlayback();render();}});
byId("study-export").addEventListener("click",()=>{if(!run)return;const url=URL.createObjectURL(new Blob([pretty(run)],{type:"application/json"})),link=document.createElement("a");link.href=url;link.download="valor-study-"+run.study_id+".json";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast("The complete run was sent to your browser’s downloads.");});
byId("study-help").addEventListener("click",()=>{stopPlayback();render();guideReturn=document.activeElement;byId("study-guide").showModal();});
for(const id of ["study-guide-close","study-guide-done"])byId(id).addEventListener("click",()=>byId("study-guide").close());
byId("study-guide").addEventListener("close",()=>guideReturn?.focus());
render();
