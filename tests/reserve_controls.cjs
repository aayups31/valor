const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const records = JSON.parse(fs.readFileSync(0, "utf8"));
const ids = new Map();
function element() {
  return {children: [], events: {}, attributes: {}, value: "", textContent: "", hidden: false,
    append(e){this.children.push(e);}, replaceChildren(){this.children=[];},
    addEventListener(name, fn){this.events[name]=fn;},
    setAttribute(name, value){this.attributes[name]=value;}};
}
const get = id => {if (!ids.has(id)) ids.set(id,element()); return ids.get(id);};
let download, evidence, revoked;
const context = vm.createContext({
  document: {getElementById:get, createElement:() => ({...element(), click(){download=this.download;}})},
  Blob: class {constructor(parts){evidence = JSON.parse(parts[0]);}},
  URL: {createObjectURL:()=> "blob:replay", revokeObjectURL:url=>{revoked=url;}},
  setTimeout: fn=>fn(),
  fetch: async url => ({ok: !!records[url.split("/").at(-1)], json: async () => records[url.split("/").at(-1)]})
});
vm.runInContext(fs.readFileSync(process.argv[2],"utf8"),context);
(async()=>{
  get("scenario").value = "damaged";
  await vm.runInContext("load()",context);
  assert.equal(get("replay").hidden,false);
  assert.match(get("screen-text").textContent,/Lookahead selected/);
  assert.equal(get("screen-checks").children.length,3);
  assert.ok(get("screen-checks").children.every(item=>item.textContent.startsWith("Passed")));
  assert.match(get("step").textContent,/DECISION 1/);
  assert.equal(get("previous").attributes["aria-disabled"],"true");
  get("previous").events.click();
  assert.match(get("step").textContent,/DECISION 1/);
  get("next").events.click();
  assert.match(get("step").textContent,/DECISION 2/);
  assert.equal(get("jump").value,"1");
  const end = records.damaged.guarded.decisions.length;
  get("jump").value = String(end-1);
  get("jump").events.change();
  assert.equal(get("next").attributes["aria-disabled"],"true");
  get("next").events.click();
  assert.match(get("step").textContent,new RegExp(`DECISION ${end} OF ${end}`));
  get("download").events.click();
  assert.equal(download,`valor-reserve-${records.damaged.seed}.json`);
  assert.deepEqual(evidence,records.damaged);
  assert.equal(revoked,"blob:replay");
  get("policy").value = "baseline";
  get("policy").events.change();
  assert.match(get("step").textContent,/DECISION 1/);
  assert.equal(get("jump").children.length,records.damaged.baseline.decisions.length);
  const fetchRecord = context.fetch;
  let resolveOld;
  context.fetch = () => new Promise(resolve=>{resolveOld=resolve;});
  const oldLoad = vm.runInContext("load()",context);
  get("scenario").value = "nominal";
  get("scenario").events.change();
  assert.equal(get("replay").hidden,true);
  context.fetch = fetchRecord;
  await vm.runInContext("load()",context);
  resolveOld(await fetchRecord("/api/reserve/damaged"));
  await oldLoad;
  assert.match(get("screen-text").textContent,/One-release planning retained/);
  assert.ok(get("screen-checks").children.some(item=>item.textContent.startsWith("Missed")));
  const legacy = {...records.damaged};
  delete legacy.screen_checks;
  records.legacy = legacy;
  get("scenario").value = "legacy";
  await vm.runInContext("load()",context);
  assert.equal(get("replay").hidden,true);
  assert.equal(get("run").disabled,false);
  assert.match(get("status").textContent,/Stop VALOR, then Start VALOR/);
  get("scenario").value = "unknown";
  await vm.runInContext("load()",context);
  assert.equal(get("replay").hidden,true);
  assert.equal(get("run").disabled,false);
  assert.match(get("status").textContent,/couldn’t load/);
})().catch(error=>{console.error(error);process.exitCode=1;});
