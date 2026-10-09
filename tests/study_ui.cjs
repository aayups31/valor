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
const intervals=new Map();let timerId=0,reply=studies.hazard,fail=false;
const context=vm.createContext({
  document:{getElementById:id=>{assert(elements.has(id),"missing HTML id "+id);return elements.get(id);},createElement:()=>new Element(),querySelectorAll:selector=>{assert.equal(selector,"[data-scenario]");return conditions;},addEventListener(){},hidden:false,activeElement:new Element()},
  window:{matchMedia:()=>({matches:false})},
  fetch:async(path,request)=>{assert.equal(path,"/api/study");assert.equal(request.method,"POST");if(fail)throw new TypeError("offline");return {ok:true,json:async()=>reply};},
  setInterval:fn=>{const id=++timerId;intervals.set(id,fn);return id;},clearInterval:id=>intervals.delete(id),
  setTimeout:()=>0,clearTimeout(){},AbortSignal:{timeout:()=>({})},Blob,URL:{createObjectURL:()=>"blob:unit-test",revokeObjectURL(){}},TypeError
});
vm.runInContext(fs.readFileSync(root+"study.js","utf8"),context);
const get=id=>elements.get(id);
(async()=>{
  assert.equal(get("study-play").disabled,true);
  await get("study-start").emit("click");
  assert.equal(get("work-count").textContent,studies.hazard.decisions[0].actual_outcome.progress);
  assert.equal(get("study-export").disabled,false);
  assert.equal(intervals.size,1,"playback runs after a multi-step record");
  get("study-options").open=true;get("study-options").emit("toggle");
  assert.equal(intervals.size,0,"opening evidence pauses playback");
  get("study-candidates").children.find(b=>b.dataset.plan==="fast").emit("click");
  assert.match(get("study-candidate-reason").textContent,/permitted failure risk/);
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
  get("study-internals").open=true;get("study-internals").emit("toggle");
  assert.equal(intervals.size,0,"internal state inspection also pauses playback");
  get("study-timeline").lastChild.firstChild.emit("click");
  assert.equal(get("study-phase").textContent,"IRREVERSIBLE OUTAGE");
  assert.match(get("study-story").textContent,/nonzero risk can still produce failure/);
  assert.equal(get("study-next").disabled,true);
  get("study-seed").value="-1";await get("study-start").emit("click");
  assert.equal(get("study-settings").open,true);
  assert.match(get("study-toast").textContent,/whole starting number/);
  console.log("Study record semantics, pause, scenario reset, retained error evidence and input handling passed.");
})().catch(error=>{console.error(error);process.exitCode=1;});
