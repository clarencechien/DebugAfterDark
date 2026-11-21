// node --test cron-worker/worker.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import worker, { SCHEDULE, dispatch } from "./worker.js";

const toml = fs.readFileSync(new URL("./wrangler.toml", import.meta.url), "utf8");

test("wrangler.toml 的 crons 跟 SCHEDULE 一致", () => {
  const crons = JSON.parse(toml.match(/crons = (\[.*\])/)[1]);
  assert.deepEqual(crons.sort(), Object.keys(SCHEDULE).sort());
});

test("SCHEDULE 裡的 workflow 檔都存在而且有 workflow_dispatch", () => {
  for (const files of Object.values(SCHEDULE))
    for (const f of files) {
      const y = fs.readFileSync(new URL(`../.github/workflows/${f}`, import.meta.url), "utf8");
      assert.match(y, /workflow_dispatch:/, f);
    }
});

test("dispatch 打對的網址、帶 token、ref=main", async () => {
  let seen;
  const r = await dispatch("pages.yml", "tok", async (url, init) => {
    seen = { url, init };
    return new Response(null, { status: 204 });
  });
  assert.equal(r.ok, true);
  assert.equal(seen.url, "https://api.github.com/repos/clarencechien/debugafterdark/actions/workflows/pages.yml/dispatches");
  assert.equal(seen.init.headers.Authorization, "Bearer tok");
  assert.deepEqual(JSON.parse(seen.init.body), { ref: "main" });
});

test("401 不重試，回報錯誤", async () => {
  let n = 0;
  const r = await dispatch("pages.yml", "bad", async () => { n++; return new Response("Bad credentials", { status: 401 }); });
  assert.equal(r.ok, false);
  assert.equal(n, 1);
  assert.match(r.error, /401/);
});

test("500 會重試，第二次成功", async () => {
  let n = 0;
  const r = await dispatch("pages.yml", "tok", async () => new Response(null, { status: ++n === 1 ? 500 : 204 }));
  assert.equal(r.ok, true);
  assert.equal(r.attempts, 2);
});

test("scheduled：沒 token 會丟錯", async () => {
  await assert.rejects(worker.scheduled({ cron: "17 * * * *" }, {}, {}), /GH_TOKEN/);
});
