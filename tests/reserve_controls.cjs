const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const records = JSON.parse(fs.readFileSync(0, "utf8"));
const ids = new Map();
function element() {
  return {children: [], events: {}, value: "", textContent: "", hidden: false,
    append(e){this.children.push(e);}, replaceChildren(){this.children=[];},
    addEventListener(name, fn){this.events[name]=fn;}};
}
const get = id => {if (!ids.has(id)) ids.set(id,element()); return ids.get(id);};
const context = vm.createContext({
  document: {getElementById:get, createElement:element},
  fetch: async url => ({ok: !!records[url.split("/").at(-1)], json: async () => records[url.split("/").at(-1)]})
});
vm.runInContext(fs.readFileSync(process.argv[2],"utf8"),context);
(async()=>{
  get("scenario").value = "damaged";
  await vm.runInContext("load()",context);
  assert.equal(get("replay").hidden,false);
  assert.match(get("screen-text").textContent,/Lookahead selected/);
  assert.match(get("step").textContent,/DECISION 1/);
  get("next").events.click();
  assert.match(get("step").textContent,/DECISION 2/);
  get("policy").value = "baseline";
  get("policy").events.change();
  assert.match(get("step").textContent,/DECISION 1/);
  get("scenario").value = "nominal";
  get("scenario").events.change();
  assert.equal(get("replay").hidden,true);
  await vm.runInContext("load()",context);
  assert.match(get("screen-text").textContent,/One-release planning retained/);
  get("scenario").value = "unknown";
  await vm.runInContext("load()",context);
  assert.equal(get("replay").hidden,true);
  assert.equal(get("run").disabled,false);
  assert.match(get("status").textContent,/couldn’t load/);
})().catch(error=>{console.error(error);process.exitCode=1;});
