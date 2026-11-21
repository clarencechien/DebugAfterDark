// 準時觸發 GitHub Actions 的 Cloudflare Worker。
//
// 為什麼：GitHub 的 schedule 在尖峰時段會延遲幾小時，甚至整次跳過（2026-11 實測 20:07 的建置拖到 04:04，
// yt-autofix 18 小時只跑 2 次），上架時間實驗需要準時。Cloudflare 的 Cron Trigger 準時得多，
// 這裡在指定時間呼叫 GitHub 的 workflow_dispatch API。workflow 裡原本的 schedule 留著當備援，
// 重複觸發沒關係：兩個 workflow 都有 concurrency group 排隊，而且重跑結果一樣。
//
// 需要一個 secret：GH_TOKEN，fine-grained personal access token，只給 clarencechien/debugafterdark，
// 權限只開 Actions: Read and write。設定步驟見 README.md。
//
// cron 是 UTC。台北 = UTC+8。

const REPO = "clarencechien/debugafterdark";
const REF = "main";

// cron 字串（要跟 wrangler.toml / 後台 Trigger events 一字不差）→ 要觸發的 workflow 檔名
export const SCHEDULE = {
  "2 0 * * *": ["pages.yml"],   // 08:02 台北：08:00、08:01 上架的集數進 feed
  "2 12 * * *": ["pages.yml"],  // 20:02 台北
  "17 * * * *": ["yt-autofix.yml"], // 每小時 :17，RSS 匯入的新影片標 AI、改公開
};

export async function dispatch(workflow, token, fetchImpl = fetch) {
  const url = `https://api.github.com/repos/${REPO}/actions/workflows/${workflow}/dispatches`;
  // 網路偶爾失敗，重試 3 次（1s、4s 間隔）。204 = 成功。
  let last = "";
  for (let attempt = 0; attempt < 3; attempt++) {
    if (attempt) await new Promise((r) => setTimeout(r, attempt * attempt * 1000));
    try {
      const res = await fetchImpl(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "debugafterdark-cron-worker",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ref: REF }),
      });
      if (res.status === 204) return { workflow, ok: true, attempts: attempt + 1 };
      last = `HTTP ${res.status} ${(await res.text()).slice(0, 300)}`;
      // 401/403/404/422 重試也沒用（token 錯、權限不夠、檔名錯）
      if ([401, 403, 404, 422].includes(res.status)) break;
    } catch (e) {
      last = String(e);
    }
  }
  return { workflow, ok: false, error: last };
}

export default {
  async scheduled(event, env, ctx) {
    const workflows = SCHEDULE[event.cron];
    if (!workflows) {
      console.error(`不認得的 cron：${event.cron}`);
      return;
    }
    if (!env.GH_TOKEN) throw new Error("沒有設定 GH_TOKEN secret");
    const results = await Promise.all(workflows.map((w) => dispatch(w, env.GH_TOKEN)));
    console.log(JSON.stringify({ cron: event.cron, results }));
    const failed = results.filter((r) => !r.ok);
    // 丟錯讓這次 cron 在 Cloudflare 後台顯示失敗，方便查
    if (failed.length) throw new Error(`觸發失敗：${JSON.stringify(failed)}`);
  },

  // 沒有對外功能。
  async fetch() {
    return new Response("not found", { status: 404 });
  },
};
