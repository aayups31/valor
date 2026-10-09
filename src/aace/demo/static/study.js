"use strict";
const byId=id=>document.getElementById(id);
const say=(id,value)=>{byId(id).textContent=value;};
const scenarios={
  benign:["Room to move.","Complete eight units of work under light load, with enough resources and time.",20,1,30],
  hazard:["A little pressure.","Process eight units of work under high load, while preserving resources and integrity.",20,1,30],
  degraded:["Starting after damage.","Capacity is already reduced. Does restoration deserve the time and resources it takes?",20,.2,30],
  low_reserve:["Less left to spend.","There may not be enough resources to finish while keeping the required reserve.",9,1,30],
  deadline:["Time is running short.","Eight units of work, five seconds available. A faster plan can still exceed the permitted risk.",20,1,5]
};
const plans={checked:"Work carefully",fast:"Move quickly",restore:"Restore capacity",defer:"Stop this task"};
const states={running:"Work continues",completed:"Work completed",abandoned:"Task set aside",irreversible_outage:"Irreversible outage",deadline_missed:"Deadline missed",quota_depleted:"Resources exhausted"};
const reasons={failure_limit:"The forecast exceeds the permitted failure risk.",insufficient_recovery_reserve:"The full plan would leave less than the required resource reserve.",capability_floor:"Projected capability is below the required minimum.",mission_deadline:"The full plan exceeds the available task time.",lower_score:"Another admissible plan has a higher score under the same objective.",best_admissible_score:"This plan has the highest score among the supported options that meet the fixed policy.",unqualified_forecast:"The forecast evidence is not qualified for a decision.",unknown_consequences:"Some required consequences are unknown.",not_evaluated:"This option was not evaluated within the budget.",forecast_invalid:"The forecaster did not return usable evidence.",unknown_resource_requirements:"The resource or recovery requirements are incomplete.",forecast_identity_mismatch:"The forecast belongs to a different state or continuation.",forecast_scope_mismatch:"The forecast applies to a different domain.",insufficient_forecast_horizon:"The forecast does not cover the required horizon."};
let selectedScenario="hazard",run=null,index=0,selectedCandidate=null,busy=false,timer=null,toastTimer=null,guideReturn=null,failureMessage="";
const number=(v,d=1)=>Number.isFinite(v)?Number(v).toFixed(d):"Not estimated";
const percent=v=>Number.isFinite(v)?number(100*v,1)+"%":"Not estimated";
const pretty=v=>JSON.stringify(v,null,2);
function toast(message){clearTimeout(toastTimer);say("study-toast",message);byId("study-toast").hidden=false;toastTimer=setTimeout(()=>{byId("study-toast").hidden=true;},6500);}
function stopPlayback(){clearInterval(timer);timer=null;}
function controls(){
  byId("study-start").disabled=busy;
  say("study-start",busy?"Computing the study…":run?"Run the study again →":"Begin the study →");
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
function render(){
  const config=scenarios[selectedScenario],row=run?.decisions[index],state=row?.actual_outcome || {quota:config[2],integrity:config[3],progress:0,elapsed_s:0,status:"running"};
  say("study-title",config[0]);say("study-description",config[1]);
  say("work-count",state.progress);say("quota-value",number(state.quota,0)+" units");say("integrity-value",number(state.integrity*100,1)+"%");say("time-value",number(Math.max(0,config[4]-state.elapsed_s),0)+" seconds");
  [...byId("work-track").children].forEach((point,i)=>point.classList.toggle("done",i<state.progress));
  say("study-phase",row?(states[state.status] || state.status).toUpperCase():"READY WHEN YOU ARE");
  const status=row?"Decision "+(index+1)+" of "+run.decisions.length:"Ready to begin";
  say("study-playback-status",busy?"The local engine is computing your run…":failureMessage || (timer?"Playing · "+status.toLowerCase():status));
  const timeline=byId("study-timeline");
  if(!row){
    say("step-label","BEFORE THE FIRST MOVE");say("chosen-title","Four options. One decision to make.");
    say("chosen-reason","VALOR can work carefully, move quickly, restore capacity, or stop the task. The next choice depends on the whole plan, not just the first move.");
    say("study-story","Begin the study to see a choice, its forecast and the observed result.");
    say("choice-prediction","The forecast will appear here.");say("choice-result","Then check what actually happened.");
    say("record-caption","A run is computed locally. Playback then lets you inspect each recorded decision.");
    say("study-provenance","The complete record includes policy, alternatives, forecasts, guarded actions, outcomes and source identity.");
    say("study-raw","Begin a study to inspect its record.");
    timeline.replaceChildren();byId("study-candidates").replaceChildren();byId("study-candidate-detail").hidden=true;
    fields("study-affect-values",[["Awaiting an observation","—"]]);controls();return;
  }
  const candidates=row.decision.candidates,chosen=candidates.find(c=>c.status==="selected"),f=chosen?.forecast;
  say("step-label","DECISION "+(index+1)+" / ACTUAL ENGINE RECORD");
  say("chosen-title",chosen?plans[chosen.candidate.identifier]:"No supported action.");
  say("chosen-reason",chosen?(chosen.candidate.identifier==="defer"?"The task is set aside while resources are preserved. Abandonment is recorded separately from completion.":chosen.candidate.identifier==="restore"?"Restore capacity first. The score includes the proposed careful continuation after restoration.":chosen.candidate.identifier==="checked"?"Careful work has the highest admissible score for this state. The comparison covers the whole proposed continuation.":"The quicker plan has the highest admissible score while meeting the fixed risk, resource and capability policy."):"No evaluated option could be supported under the fixed policy. The core abstained.");
  say("study-story",state.status==="running"?state.progress+" of 8 work units completed. The next decision uses the updated state.":state.status==="completed"?"All eight units were completed in this simulated run.":state.status==="abandoned"?"The task was abandoned. Preserving a reserve does not count as completing the work.":"The observed outcome was "+(states[state.status] || state.status).toLowerCase()+". A permitted nonzero risk can still produce failure.");
  say("choice-prediction",f?"Before acting: "+percent(f.success_probability)+" completion and "+percent(f.failure_probability)+" failure forecast for this full continuation.":"No qualified consequence forecast was available.");
  say("choice-result",row.commit.status==="applied"?"After acting: "+state.progress+" of 8 completed, "+number(state.integrity*100,1)+"% integrity. "+(states[state.status] || state.status)+".":"The authority gate did not apply this proposal: "+row.commit.status.replaceAll("_"," ")+".");
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
  [...list.children].forEach(button=>{const c=candidates.find(c=>c.candidate.identifier===button.dataset.plan);button.setAttribute("aria-pressed",String(c===selected));button.lastChild.textContent=({selected:"Chosen",lower_score:"Lower score",constraint_rejected:"Outside policy",unexplored:"Not evaluated",forecast_invalid:"No evidence",discarded:"Discarded"})[c.status] || c.status;});
  candidateDetail(selected);
  const affect=row.affect_observer;
  fields("study-affect-values",[["Observed integrity loss",number(affect.after.observed_harm,4)],["Activation before → after",number(affect.before.arousal,3)+" → "+number(affect.after.arousal,3)],["Slower sensitization trace",number(affect.after.sensitization,3)],["Current cue association",number(affect.after.current_cue_activation,3)],["Influence on this decision","Observer only"]]);
  say("study-provenance","Analytic service benchmark · seed "+run.seed+" · source "+run.git_revision.slice(0,7)+(run.git_dirty?" with local edits":"")+" · No real service controlled. Raw activations are experimental.");
  say("study-raw",pretty(row));controls();
}
async function begin(){
  if(busy)return;
  const seed=Number(byId("study-seed").value);
  if(!Number.isInteger(seed)||seed<0||seed>=2147483648){byId("study-settings").open=true;byId("study-seed").focus();toast("Use a whole starting number from 0 to 2147483647.");return;}
  stopPlayback();failureMessage="";busy=true;render();
  try{
    const response=await fetch("/api/study",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({scenario:selectedScenario,seed}),signal:AbortSignal.timeout(10000)});
    const data=await response.json();if(!response.ok)throw new Error(data.error || "The study could not start.");
    run=data;index=0;selectedCandidate=null;byId("study-timeline").dataset.study="";byId("study-candidates").replaceChildren();
    if(run.decisions.length>1)startPlayback();
    byId("study").scrollIntoView({behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches?"instant":"smooth",block:"start"});byId("study").focus({preventScroll:true});
  }catch(error){toast(error instanceof TypeError || error.name==="TimeoutError"?"The local engine is not responding. Reopen Start VALOR, then refresh this page.":error.message);failureMessage=run?"The new study could not start. The previous record is still available.":"The study could not start. Reopen Start VALOR, then try again.";}
  finally{busy=false;render();}
}
function startPlayback(){
  stopPlayback();timer=setInterval(()=>{if(index>=run.decisions.length-1){stopPlayback();}else{index++;selectedCandidate=null;if(index===run.decisions.length-1)stopPlayback();}render();},1400);
}
byId("study-start").addEventListener("click",begin);
byId("study-next").addEventListener("click",()=>{stopPlayback();if(run && index<run.decisions.length-1){index++;selectedCandidate=null;}render();});
byId("study-play").addEventListener("click",()=>{if(!run)return;if(timer)stopPlayback();else{if(index>=run.decisions.length-1){index=0;selectedCandidate=null;}startPlayback();}render();});
document.querySelectorAll("[data-scenario]").forEach(button=>button.addEventListener("click",()=>{if(busy)return;stopPlayback();selectedScenario=button.dataset.scenario;run=null;index=0;selectedCandidate=null;failureMessage="";render();}));
for(const id of ["study-options","study-internals","study-records"])byId(id).addEventListener("toggle",()=>{if(byId(id).open){stopPlayback();render();}});
document.addEventListener("visibilitychange",()=>{if(document.hidden){stopPlayback();controls();}});
byId("study-export").addEventListener("click",()=>{if(!run)return;const url=URL.createObjectURL(new Blob([pretty(run)],{type:"application/json"})),link=document.createElement("a");link.href=url;link.download="valor-study-"+run.study_id+".json";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast("The complete run was sent to your browser’s downloads.");});
byId("study-help").addEventListener("click",()=>{stopPlayback();render();guideReturn=document.activeElement;byId("study-guide").showModal();});
for(const id of ["study-guide-close","study-guide-done"])byId(id).addEventListener("click",()=>byId("study-guide").close());
byId("study-guide").addEventListener("close",()=>guideReturn?.focus());
render();
