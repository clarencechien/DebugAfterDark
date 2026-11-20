"""Privacy policy and terms pages for the site (/privacy/, /terms/), plus the footer that links to them.

Added 2026-11-20 for the YouTube API Services compliance audit: the upload and reporting tools (tools/yt_upload.py,
tools/yt_report.py) use YouTube API Services, so the site must publish a privacy policy that names them, links the
YouTube Terms of Service and the Google Privacy Policy, says how to revoke access and how data is deleted, and the
homepage must link to it with YouTube branding visible.

English first (reviewers read it), Traditional Chinese second. If what the tools do changes (new scope, new data
stored, longer retention), update the text here and bump UPDATED.
"""
import html

UPDATED = "2026-11-20"
YT_TOS = "https://www.youtube.com/t/terms"
GOOGLE_PRIVACY = "https://policies.google.com/privacy"
REVOKE = "https://security.google.com/settings/security/permissions"
YT_API_TOS = "https://developers.google.com/youtube/terms/api-services-terms-of-service"
REPO = "https://github.com/clarencechien/debugafterdark"

# The red rounded rectangle with a white play triangle, drawn inline so the badge needs no external asset.
YT_ICON = ('<svg class="yt-icon" viewBox="0 0 28 20" width="28" height="20" aria-hidden="true">'
           '<rect width="28" height="20" rx="5" fill="#FF0000"/><path d="M11 5.5v9l7.8-4.5z" fill="#fff"/></svg>')

LEGAL_STYLE = """
/* Footer links and the YouTube badge (2026-11-20, API audit). */
.legal-links { display:flex; flex-wrap:wrap; align-items:center; gap:8px 18px; margin:10px 0 0; font-size:14px; }
.legal-links a { font-weight:700; }
.yt-badge { display:inline-flex; align-items:center; gap:10px; padding:6px 12px 6px 8px; border:1px solid var(--line);
            border-radius:8px; background:var(--panel); color:var(--ink); text-decoration:none; font:500 13.5px/1.4 var(--f-body); }
.yt-badge:hover { border-color:var(--lamp); color:var(--ink); }
.yt-icon { flex:none; display:block; }
.legal { padding-block:28px 72px; }
.legal h1 { font:700 clamp(30px, 5vw, 44px)/1.25 var(--f-display); margin:0 0 6px; }
.legal h2 { font-size:22px; margin:36px 0 8px; }
.legal h3 { font:700 17px/1.5 var(--f-body); margin:22px 0 6px; }
.legal p, .legal li { max-width:40em; }
.legal ul { padding-left:1.3em; }
.legal li { margin:4px 0; }
.legal .meta { font:13px/1.6 var(--f-mono); color:var(--muted); margin:0 0 20px; }
.legal .lang { border-top:1px solid var(--line); margin-top:44px; padding-top:8px; }
.legal .key { border:1px solid var(--line); border-left:3px solid #FF0000; border-radius:8px; background:var(--panel); padding:12px 16px; margin:16px 0; }
.legal .key p { margin:4px 0; }
"""


def footer_links(prefix, show):
    """Privacy / terms links and the YouTube badge. prefix is '' on the homepage, '../' one level down."""
    yt = next((x["url"] for x in show.get("listen_on", []) if x["name"] == "YouTube"), "https://www.youtube.com/")
    return (f'<p class="legal-links"><a href="{prefix}privacy/">隱私權政策 Privacy Policy</a>'
            f'<a href="{prefix}terms/">服務條款 Terms of Service</a>'
            f'<a class="yt-badge" href="{html.escape(yt)}">{YT_ICON}<span>Developed with YouTube · 使用 YouTube API Services</span></a></p>')


PRIVACY_EN = f"""
<h1>Privacy Policy</h1>
<p class="meta">深夜 Debug｜Debug After Dark · Last updated {UPDATED}</p>

<div class="key">
<p><strong>This podcast and its publishing tools use YouTube API Services.</strong></p>
<p>By using them you agree to the <a href="{YT_TOS}">YouTube Terms of Service</a>, and Google's handling of data is described in the <a href="{GOOGLE_PRIVACY}">Google Privacy Policy</a>.</p>
<p>You can revoke this app's access to a Google account at any time at <a href="{REVOKE}">{REVOKE}</a>.</p>
</div>

<h2>1. Who we are</h2>
<p>深夜 Debug (Debug After Dark) is an independent podcast produced by a single person. This website (podcast.ai-apps.work) hosts the show's RSS feed and episode pages. The same producer runs a small, internal set of publishing tools for the show's own YouTube channel, <a href="https://www.youtube.com/@debugafterdark-podcast">@debugafterdark-podcast</a>.</p>

<h2>2. Our use of YouTube API Services</h2>
<p>The publishing tools are an internal, single-user application. They are not offered to the public, and the only Google account that ever signs in is the channel owner's own. Through YouTube API Services they:</p>
<ul>
<li>upload the show's own episode videos and Shorts to its own channel, and set their title, description, tags, thumbnail, captions, playlist, scheduled publish time and the "altered or synthetic content" disclosure (YouTube Data API v3);</li>
<li>read the channel's own video list and statistics (YouTube Data API v3);</li>
<li>read the channel's own aggregated performance reports, such as views, watch time, traffic sources, impressions and click-through rate (YouTube Analytics API and YouTube Reporting API).</li>
</ul>
<p>The tools do not access any other channel's private data, and they do not collect personal data about viewers. YouTube Analytics data is aggregated by YouTube and does not identify individual viewers.</p>

<h3>Google OAuth scopes requested</h3>
<ul>
<li><code>https://www.googleapis.com/auth/youtube.upload</code>: upload videos to the channel.</li>
<li><code>https://www.googleapis.com/auth/youtube</code>: set thumbnails, captions and playlists, and read the channel's videos.</li>
<li><code>https://www.googleapis.com/auth/yt-analytics.readonly</code>: read the channel's aggregated analytics.</li>
</ul>

<h2>3. What data is stored, where, and for how long</h2>
<ul>
<li><strong>OAuth credentials.</strong> One OAuth refresh token for the channel owner's account, stored as an encrypted secret in the GitHub Actions settings of the show's repository and in the producer's own cloud work environment. It is never published, logged or shared. Short-lived access tokens are kept in memory only for the duration of a run.</li>
<li><strong>Upload records.</strong> The YouTube video IDs of the show's own uploads, kept in the show's repository so the same episode is never uploaded twice.</li>
<li><strong>Analytics reports.</strong> Aggregated numbers about the channel's own videos (per video and per day), saved as JSON and an HTML report in the producer's private project storage, used only to decide titles, thumbnails and publishing times. They are not sold, shared, or combined with data from other sources about individuals.</li>
</ul>
<p>Data obtained from YouTube API Services is not shared with any third party and is not used for advertising.</p>

<h2>4. Data deletion</h2>
<ul>
<li>Stored API data (analytics reports and video statistics) is refreshed or deleted at least every 30 days. Reports older than that are removed, except numbers the channel owner has chosen to keep about their own channel.</li>
<li>If access is revoked (see below), the refresh token stops working immediately; we delete the stored token and all stored API data within 7 days.</li>
<li>You can ask us to delete data at any time by contacting us (section 7). We will confirm deletion within 7 days.</li>
</ul>

<h2>5. How to revoke access</h2>
<p>Visit the Google security settings page at <a href="{REVOKE}">{REVOKE}</a>, find this app, and choose "Remove access". After that the tools can no longer access the account.</p>

<h2>6. This website</h2>
<ul>
<li>The site has no accounts, no forms, no comments and no advertising cookies.</li>
<li>It is hosted on GitHub Pages; GitHub may keep standard server logs (such as IP address) under the <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">GitHub Privacy Statement</a>.</li>
<li>It uses Cloudflare Web Analytics, a cookieless page-view counter that does not track individuals across sites.</li>
<li>Audio downloads requested through the RSS feed pass through SoundOn's download counter before reaching the file, so podcast apps can be counted; the website's own player does not use it.</li>
<li>Links to YouTube, Apple Podcasts, Spotify and Portaly lead to services with their own privacy policies.</li>
</ul>

<h2>7. Contact</h2>
<p>Email <a href="mailto:podcast@ai-apps.work">podcast@ai-apps.work</a>, or open an issue at <a href="{REPO}/issues">{REPO}/issues</a>.</p>

<h2>8. Changes</h2>
<p>When this policy changes, the date at the top changes too. Material changes are noted on this page.</p>
"""

PRIVACY_ZH = f"""
<div class="lang">
<h2>隱私權政策（中文）</h2>
<p class="meta">最後更新 {UPDATED}。中英文內容相同，有出入時以英文版為準。</p>
<div class="key">
<p><strong>本節目與發佈工具使用 YouTube API Services。</strong></p>
<p>使用即表示同意 <a href="{YT_TOS}">YouTube 服務條款</a>；Google 如何處理資料，見 <a href="{GOOGLE_PRIVACY}">Google 隱私權政策</a>。</p>
<p>隨時可以在 <a href="{REVOKE}">{REVOKE}</a> 撤銷這個應用程式對 Google 帳戶的存取權。</p>
</div>
<h3>我們是誰</h3>
<p>深夜 Debug 是由一個人製作的獨立 podcast。本站（podcast.ai-apps.work）放節目的 RSS 和單集頁面。製作者另有一套內部用的發佈工具，只管理節目自己的 YouTube 頻道 <a href="https://www.youtube.com/@debugafterdark-podcast">@debugafterdark-podcast</a>。</p>
<h3>怎麼使用 YouTube API Services</h3>
<p>發佈工具是內部、單一使用者的應用程式，不對外提供，唯一登入的 Google 帳戶是頻道擁有者自己的。透過 YouTube API Services，工具會：</p>
<ul>
<li>把節目自己的影片和 Shorts 上傳到自己的頻道，並設定標題、說明、標籤、縮圖、字幕、播放清單、排程公開時間，以及「變造或合成內容」的揭露（YouTube Data API v3）；</li>
<li>讀取頻道自己的影片清單與統計（YouTube Data API v3）；</li>
<li>讀取頻道自己的彙總成效報表，例如觀看次數、觀看時間、流量來源、曝光與點閱率（YouTube Analytics API、YouTube Reporting API）。</li>
</ul>
<p>工具不存取其他頻道的非公開資料，也不蒐集觀眾的個人資料。YouTube Analytics 的數字是 YouTube 彙總過的，無法識別個別觀眾。</p>
<p>要求的 OAuth 範圍：<code>youtube.upload</code>（上傳）、<code>youtube</code>（縮圖、字幕、播放清單、讀取影片）、<code>yt-analytics.readonly</code>（讀取彙總數據）。</p>
<h3>儲存哪些資料、放在哪裡、放多久</h3>
<ul>
<li><strong>OAuth 憑證</strong>：頻道擁有者帳戶的一組 refresh token，以加密 secret 存在節目 repository 的 GitHub Actions 設定，以及製作者自己的雲端工作環境。不公開、不寫進紀錄、不分享。短效的 access token 只在執行期間存在記憶體中。</li>
<li><strong>上傳紀錄</strong>：節目自己上傳的影片 ID，存在節目的 repository，避免同一集重複上傳。</li>
<li><strong>成效報表</strong>：頻道自己影片的彙總數字（每支影片、每天），以 JSON 和 HTML 報表存在製作者的私人專案空間，只用來決定標題、縮圖和上架時間。不出售、不分享，也不與其他來源的個人資料合併。</li>
</ul>
<p>從 YouTube API Services 取得的資料不提供給任何第三方，也不用於廣告。</p>
<h3>資料刪除</h3>
<ul>
<li>儲存的 API 資料（成效報表、影片統計）至少每 30 天更新或刪除一次；超過的報表會刪除，頻道擁有者選擇保留的自己頻道數字除外。</li>
<li>撤銷存取權後，refresh token 立即失效；我們會在 7 天內刪除儲存的 token 與所有 API 資料。</li>
<li>隨時可以透過下方聯絡方式要求刪除資料，我們會在 7 天內確認刪除。</li>
</ul>
<h3>如何撤銷存取權</h3>
<p>到 Google 安全性設定 <a href="{REVOKE}">{REVOKE}</a>，找到這個應用程式，選「移除存取權」。之後工具就無法再存取該帳戶。</p>
<h3>本網站</h3>
<p>本站沒有帳號、表單、留言或廣告 cookie。網站放在 GitHub Pages（GitHub 可能保留一般伺服器紀錄，例如 IP，見 GitHub 隱私權聲明）；使用 Cloudflare Web Analytics 計算瀏覽數，不用 cookie、不跨站追蹤個人。RSS 的音檔下載會先經過 SoundOn 的下載計數再導回音檔，網站上的播放器不經過。連到 YouTube、Apple Podcasts、Spotify、Portaly 的連結，適用各自的隱私權政策。</p>
<h3>聯絡</h3>
<p>Email <a href="mailto:podcast@ai-apps.work">podcast@ai-apps.work</a>，或在 <a href="{REPO}/issues">GitHub issues</a> 留言。</p>
</div>
"""

TERMS_EN = f"""
<h1>Terms of Service</h1>
<p class="meta">深夜 Debug｜Debug After Dark · Last updated {UPDATED}</p>

<div class="key">
<p><strong>This podcast and its publishing tools use YouTube API Services.</strong></p>
<p>By using any part of them that interacts with YouTube, you agree to be bound by the <a href="{YT_TOS}">YouTube Terms of Service</a> ({YT_TOS}). See also the <a href="{GOOGLE_PRIVACY}">Google Privacy Policy</a> and our <a href="../privacy/">Privacy Policy</a>.</p>
</div>

<h2>1. What these terms cover</h2>
<p>These terms cover this website (podcast.ai-apps.work), the show's RSS feed, and the internal publishing tools in the show's repository (<a href="{REPO}">{REPO}</a>) that upload the show's videos to its own YouTube channel and read that channel's analytics.</p>

<h2>2. The publishing tools</h2>
<ul>
<li>The tools are an internal, single-user application operated by the show's producer for the show's own YouTube channel. They are not a service offered to other users.</li>
<li>They use YouTube API Services in accordance with the <a href="{YT_API_TOS}">YouTube API Services Terms of Service</a> and the YouTube API Services Developer Policies.</li>
<li>Anyone who runs a copy of the source code with their own Google account must agree to the <a href="{YT_TOS}">YouTube Terms of Service</a>, is responsible for their own credentials and uploads, and can revoke access at <a href="{REVOKE}">{REVOKE}</a>.</li>
<li>Videos uploaded by the tools are disclosed on YouTube as altered or synthetic content where applicable, because the show's host voice is AI-generated.</li>
</ul>

<h2>3. The podcast and its content</h2>
<ul>
<li>Episodes are free to listen to for personal use. The audio, artwork, scripts and show notes are © 2026 深夜 Debug; please don't re-upload or redistribute them without permission. Sharing links is welcome.</li>
<li>The host, Ping, is an AI-generated voice that does not imitate any real person. Each episode is adapted from an article on <a href="https://imitator.ai-apps.work/">imitator.ai-apps.work</a> and is reviewed and listened to by a human before release.</li>
<li>Content is for general information and discussion only. It is not financial, investment, legal, medical or professional advice. Check the original sources linked in each episode before acting on anything.</li>
</ul>

<h2>4. Third-party services</h2>
<p>The site links to YouTube, Apple Podcasts, Spotify, SoundOn and Portaly. Your use of those services is governed by their own terms; in particular, use of YouTube is governed by the <a href="{YT_TOS}">YouTube Terms of Service</a>.</p>

<h2>5. No warranty and limitation of liability</h2>
<p>The site, the feed and the tools are provided "as is", without warranty of any kind. To the extent permitted by law, the producer is not liable for any loss arising from their use.</p>

<h2>6. Changes and contact</h2>
<p>These terms may change; the date at the top shows the latest version. Questions: <a href="mailto:podcast@ai-apps.work">podcast@ai-apps.work</a> or <a href="{REPO}/issues">GitHub issues</a>.</p>
"""

TERMS_ZH = f"""
<div class="lang">
<h2>服務條款（中文）</h2>
<p class="meta">最後更新 {UPDATED}。中英文內容相同，有出入時以英文版為準。</p>
<div class="key">
<p><strong>本節目與發佈工具使用 YouTube API Services。</strong></p>
<p>使用其中與 YouTube 互動的任何部分，即表示同意遵守 <a href="{YT_TOS}">YouTube 服務條款</a>。另見 <a href="{GOOGLE_PRIVACY}">Google 隱私權政策</a> 與本站的<a href="../privacy/">隱私權政策</a>。</p>
</div>
<h3>適用範圍</h3>
<p>本條款適用於本網站（podcast.ai-apps.work）、節目的 RSS，以及節目 repository（<a href="{REPO}">{REPO}</a>）裡把影片上傳到節目自己 YouTube 頻道、讀取該頻道數據的內部發佈工具。</p>
<h3>發佈工具</h3>
<ul>
<li>工具是節目製作者為節目自己的 YouTube 頻道使用的內部、單一使用者應用程式，不對其他使用者提供服務。</li>
<li>工具依照 <a href="{YT_API_TOS}">YouTube API Services 服務條款</a>與 YouTube API Services 開發者政策使用 YouTube API Services。</li>
<li>任何人用自己的 Google 帳戶執行這份原始碼，都必須同意 <a href="{YT_TOS}">YouTube 服務條款</a>，自行負責憑證與上傳內容，並可在 <a href="{REVOKE}">{REVOKE}</a> 撤銷存取權。</li>
<li>主持人的聲音由 AI 合成，工具上傳的影片會在 YouTube 標示為變造或合成內容。</li>
</ul>
<h3>節目與內容</h3>
<ul>
<li>節目可免費收聽，供個人使用。音檔、圖像、稿子與說明欄 © 2026 深夜 Debug，未經同意請勿重新上傳或散布；歡迎分享連結。</li>
<li>主持人 Ping 是 AI 合成聲音，不模仿任何真人。每一集改寫自 <a href="https://imitator.ai-apps.work/">imitator.ai-apps.work</a> 的文章，上架前都經過真人審稿與試聽。</li>
<li>內容僅供一般資訊與討論，不構成財務、投資、法律、醫療或其他專業建議。行動前請查閱每集附的原始來源。</li>
</ul>
<h3>第三方服務</h3>
<p>本站連到 YouTube、Apple Podcasts、Spotify、SoundOn、Portaly，使用這些服務適用各自的條款；使用 YouTube 適用 <a href="{YT_TOS}">YouTube 服務條款</a>。</p>
<h3>不保證與責任限制</h3>
<p>網站、RSS 與工具依「現狀」提供，不做任何保證。在法律允許範圍內，製作者不對使用所生的損失負責。</p>
<h3>變更與聯絡</h3>
<p>條款可能變更，以頁首日期為準。問題請寄 <a href="mailto:podcast@ai-apps.work">podcast@ai-apps.work</a> 或到 <a href="{REPO}/issues">GitHub issues</a>。</p>
</div>
"""


def legal_page(show, style, kind, beacon=""):
    """kind is 'privacy' or 'terms'. style is build_site.STYLE (banner path fixed by the caller)."""
    title, body = {"privacy": ("Privacy Policy 隱私權政策", PRIVACY_EN + PRIVACY_ZH),
                   "terms": ("Terms of Service 服務條款", TERMS_EN + TERMS_ZH)}[kind]
    site = show["site_url"].rstrip("/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}｜深夜 Debug</title>
<meta name="description" content="{title} for 深夜 Debug｜Debug After Dark and its YouTube publishing tools.">
<meta name="theme-color" content="#0b0e1a">
<link rel="canonical" href="{site}/{kind}/">
<link rel="icon" href="../cover-512.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=LXGW+WenKai+TC:wght@400;700&family=Noto+Sans+TC:wght@400;500;700&display=swap">
<style>
{style}
</style>
</head>
<body>
<main class="wrap legal">
<p class="back meta"><a href="../">← 深夜 Debug｜Debug After Dark</a></p>
{body}
<footer>{footer_links("../", show)}</footer>
</main>
{beacon}
</body>
</html>
"""
