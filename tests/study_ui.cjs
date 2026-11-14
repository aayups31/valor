// Source-level state/record checks with a minimal DOM double. No browser or rendering.
const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const studies=JSON.parse(fs.readFileSync(0,"utf8"));
class Element {
  constructor(){this.children=[];this.attributes={};this.listeners={};this.dataset={};this.textContent="";this.hidden=false;this.disabled=false;this.value="";this.open=false;this.classes=new Set();this.classList={toggle:(name,enabled)=>{if(enabled)this.classes.add(name);else this.classes.delete(name);}};}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=[...children];}
  get firstChild(){return this.children[0];} get lastChild(){return this.children.at(-1);}
  setAttribute(key,value){this.attributes[key]=value;}
  removeAttribute(key){delete this.attributes[key];}
  addEventListener(event,callback){this.listeners[event]=callback;}
  emit(event){return this.listeners[event]?.();}
  scrollIntoView(){} focus(){} click(){} showModal(){this.open=true;} close(){this.open=false;this.emit("close");}
}
const root="src/aace/demo/static/",html=fs.readFileSync(root+"index.html","utf8"),elements=new Map();
for(const [,id] of html.matchAll(/\bid="([^"]+)"/g)){assert(!elements.has(id),"duplicate HTML id");elements.set(id,new Element());}
const conditions=[...html.matchAll(/data-scenario="([^"]+)"/g)].map(([,scenario])=>{const e=new Element();e.dataset.scenario=scenario;return e;});
elements.get("study-seed").value="42";
elements.get("work-track").append(...Array.from({length:8},()=>new Element()));
const intervals=new Map();let timerId=0,reply=studies.hazard,fail=false,requests=0;
const motion={matches:false,addEventListener(event,callback){assert.equal(event,"change");this.changed=callback;}};
const context=vm.createContext({
  document:{getElementById:id=>{assert(elements.has(id),"missing HTML id "+id);return elements.get(id);},createElement:()=>new Element(),querySelectorAll:selector=>{assert.equal(selector,"[data-scenario]");return conditions;},addEventListener(){},hidden:false,activeElement:new Element()},
  window:{matchMedia:()=>motion},
  fetch:async(path,request)=>{assert.equal(path,"/api/study");assert.equal(request.method,"POST");requests++;if(fail)throw new TypeError("offline");return {ok:true,json:async()=>reply};},
  setInterval:fn=>{const id=++timerId;intervals.set(id,fn);return id;},clearInterval:id=>intervals.delete(id),
  setTimeout:()=>0,clearTimeout(){},AbortSignal:{timeout:()=>({})},Blob,URL:{createObjectURL:()=>"blob:unit-test",revokeObjectURL(){}},TypeError
});
vm.runInContext(fs.readFileSync(root+"study.js","utf8"),context);
const get=id=>elements.get(id);
(async()=>{
  assert.equal(get("study-play").disabled,true);
  get("nav-research").emit("click");
  assert.equal(get("study").hidden,true);
  assert.equal(get("research").hidden,false);
  assert.equal(get("nav-research").attributes["aria-pressed"],"true");
  get("nav-simulation").emit("click");
  assert.equal(get("study").hidden,false);
  assert.equal(get("research").hidden,true);
  await get("study-start").emit("click");
  assert.equal(get("work-count").textContent,studies.hazard.decisions[0].actual_outcome.progress);
  assert.match(get("lens-danger").textContent,/permitted failure risk/);
  assert.match(get("lens-belief").textContent,/completion forecast for the chosen plan/);
  assert.match(get("lens-choice").textContent,/simulator applied its next action/);
  assert.equal(get("scene-work").children.length,8);
  assert.equal(get("scene-options").children.length,studies.hazard.decisions[0].decision.candidates.length);
  assert.equal(get("scene-health").value,studies.hazard.decisions[0].actual_outcome.integrity);
  assert.match(get("scene-position").textContent,/Recorded decision 1/);
  assert.equal(get("study-export").disabled,false);
  assert.equal(intervals.size,1,"playback runs after a multi-step record");
  get("mission-futures").emit("click");
  assert.equal(get("study-options").open,true);
  get("inspector-close").emit("click");
  assert.equal(get("study-options").open,false);
  get("mission-futures").emit("click");
  get("study-options").emit("toggle");
  assert.equal(intervals.size,0,"opening evidence pauses playback");
  get("study-candidates").children.find(b=>b.dataset.plan==="fast").emit("click");
  assert.match(get("study-candidate-reason").textContent,/permitted failure risk/);
  assert.match(get("scene-inspection-copy").textContent,/permitted failure risk/);
  get("tour-next").emit("click");
  assert.match(get("tour-count").textContent,/02/);
  assert.equal(intervals.size,0);
  get("study-timeline").lastChild.firstChild.emit("click");
  assert.equal(get("work-count").textContent,8);
  assert.equal(get("study-phase").textContent,"WORK COMPLETED");
  fail=true;await get("study-start").emit("click");
  assert.match(get("study-playback-status").textContent,/previous record is still available/);
  assert.equal(get("study-export").disabled,false);
  fail=false;conditions.find(b=>b.dataset.scenario==="low_reserve").emit("click");
  assert.equal(get("work-count").textContent,0);
  assert.equal(get("study-export").disabled,true,"changing conditions clears old evidence");
  reply=studies.low_reserve;await get("study-start").emit("click");
  assert.equal(get("study-phase").textContent,"TASK SET ASIDE");
  assert.match(get("study-story").textContent,/does not count as completing/);
  assert.equal(intervals.size,0,"single-step abandonment does not auto-play");
  conditions.find(b=>b.dataset.scenario==="hazard").emit("click");
  reply=studies.outage;await get("study-start").emit("click");
  get("mission-memory").emit("click");
  assert.equal(get("study-internals").open,true);
  get("study-internals").emit("toggle");
  assert.equal(intervals.size,0,"internal state inspection also pauses playback");
  get("study-timeline").lastChild.firstChild.emit("click");
  assert.equal(get("study-phase").textContent,"IRREVERSIBLE OUTAGE");
  assert.match(get("study-story").textContent,/nonzero risk can still produce failure/);
  assert.equal(get("study-next").disabled,true);
  get("study-seed").value="-1";await get("study-start").emit("click");
  assert.equal(get("study-settings").open,true);
  assert.match(get("study-toast").textContent,/whole starting number/);
  get("study-seed").value="42";
  for(const id of ["study-options","study-internals","study-records","study-metrics-help","study-settings"])get(id).open=false;
  reply=studies.hazard;motion.matches=true;
  await get("study-run").emit("click");
  assert.equal(intervals.size,0,"reduced motion starts with an inspectable paused record");
  assert.equal(get("study-export").disabled,false,"reduced motion still runs the real engine");
  motion.matches=false;
  const previousRequests=requests;
  const pending=get("study-run").emit("click");
  assert.equal(get("study-run").disabled,true);
  assert.equal(get("study-start").disabled,true);
  assert.equal(get("study").attributes["aria-busy"],"true");
  await get("study-start").emit("click");
  await pending;
  assert.equal(requests,previousRequests+1,"both entry points share the same request guard");
  assert.equal(get("study").attributes["aria-busy"],"false");
  assert.equal(intervals.size,1);
  get("study-metrics-help").open=true;get("study-metrics-help").emit("toggle");
  assert.equal(intervals.size,0,"reading metric explanations pauses the record");
  await get("study-run").emit("click");
  assert.equal(intervals.size,0,"rerunning with evidence already open stays paused");
  get("study-metrics-help").open=false;
  get("study-play").emit("click");
  assert.equal(intervals.size,1);
  motion.matches=true;motion.changed();
  assert.equal(intervals.size,0,"enabling reduced motion pauses active playback");
  assert.doesNotMatch(get("study-playback-status").textContent,/Playing/);
  // Every instrument reads the same current record; forecasts never become outcomes.
  const row=studies.hazard.decisions[0];
  get("nav-futures").emit("click");
  assert.equal(get("study").hidden,true);
  assert.equal(get("futures").hidden,false);
  assert.equal(get("instrument-navigation").hidden,false);
  assert.equal(get("future-branches").children.length,row.decision.candidates.length);
  const fastIndex=row.decision.candidates.findIndex(c=>c.candidate.identifier==="fast");
  assert.equal(get("future-branches").children[fastIndex].lastChild.value,row.decision.candidates[fastIndex].forecast.failure_probability,"risk bar uses the forecast probability directly");
  get("future-branches").children[fastIndex].emit("click");
  assert.equal(get("future-name").textContent,"Move quickly");
  assert.match(get("future-reason").textContent,/permitted failure risk/);
  assert.equal(get("future-metrics").children[1].lastChild.textContent,(row.decision.candidates[fastIndex].forecast.failure_probability*100).toFixed(1)+"%");
  get("nav-memory").emit("click");
  assert.equal(get("futures").hidden,true);
  assert.equal(get("memory").hidden,false);
  assert.equal(get("memory-trace").children.length,1,"memory excludes unseen decisions");
  assert.equal(get("memory-trace").firstChild.children[2].firstChild.value,row.affect_observer.after.arousal);
  assert.match(get("memory-scale").textContent,/not probabilities/);
  get("instrument-next").emit("click");
  assert.equal(get("memory-trace").children.length,2);
  assert.equal(get("memory-activation-line").attributes.points.split(" ").length,2,"plot excludes future observations");
  assert.equal(get("memory-current-point").attributes.cx,"865");
  get("memory-trace").firstChild.firstChild.emit("click");
  assert.equal(get("memory-trace").children.length,1);
  get("nav-chamber").emit("click");
  assert.equal(get("memory").hidden,true);
  assert.equal(get("chamber").hidden,false);
  assert.equal(get("chamber-action").textContent,"Work carefully");
  assert.equal(get("chamber-metrics").lastChild.lastChild.textContent,"Observer only");
  assert.match(get("chamber-outcome").textContent,new RegExp(row.actual_outcome.progress+" / 8 completed"));
  assert.equal(get("chamber-inspect").disabled,false);
  get("chamber-inspect").emit("click");
  assert.equal(get("futures").hidden,false);
  assert.equal(get("future-name").textContent,"Restore capacity");
  get("instrument-command").emit("click");
  assert.equal(get("study").hidden,false);
  assert.equal(get("chamber").hidden,true);
  assert.equal(get("instrument-navigation").hidden,true);
  get("flow-play").emit("click");
  assert.equal(intervals.size,0,"reduced motion leaves the flow under manual control");
  get("flow-step").emit("click");
  assert.equal(get("gateway-flow").attributes["data-phase"],"1");
  assert.match(get("flow-caption").textContent,/fear signal was recorded separately/);
  assert.doesNotMatch(get("study-playback-status").textContent,/Playing/);
  get("flow-phase-2").emit("click");
  assert.equal(get("gateway-flow").attributes["data-phase"],"2");
  assert.equal(get("flow-phase-2").attributes["aria-pressed"],"true");
  assert.match(get("flow-caption").textContent,/Permission status/);
  get("flow-plans").children[fastIndex].emit("click");
  assert.equal(get("futures").hidden,false,"proposal links open the matching forecast");
  assert.equal(get("future-name").textContent,"Move quickly");
  get("instrument-command").emit("click");
  motion.matches=false;
  get("flow-play").emit("click");
  assert.equal(intervals.size,1);
  for(let phase=1;phase<=3;phase++){
    [...intervals.values()][0]();
    assert.equal(get("gateway-flow").attributes["data-phase"],String(phase));
  }
  assert.equal(intervals.size,0,"illustrated flow stops after the observed result");
  assert.equal(get("command-work").children.filter(e=>e.classes.has("complete")).length,row.actual_outcome.progress);
  get("flow-play").emit("click");
  get("nav-memory").emit("click");
  assert.equal(intervals.size,0,"leaving Command stops animation");
  get("nav-simulation").emit("click");
  conditions.find(b=>b.dataset.scenario==="degraded").emit("click");
  assert.equal(get("memory-trace").children.length,0);
  assert.equal(get("memory-activation-line").attributes.points,"");
  assert.equal(get("memory-current-point").attributes.hidden,"");
  assert.equal(get("future-branches").children.length,0);
  assert.equal(get("flow-play").disabled,true);
  assert.equal(get("instrument-next").disabled,true);
  assert.equal(get("chamber-outcome").textContent,"No outcome yet.");
  assert.equal(get("chamber-inspect").disabled,true);
  console.log("Study records, failure/abandonment, both launch controls, request guard, help pause and reduced motion passed (DOM double; no rendering).");
})().catch(error=>{console.error(error);process.exitCode=1;});
