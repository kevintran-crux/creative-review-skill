---
name: one-shot-competitive-creative-report-v3
description: Build the five-page A4 ads report from the brand's live ads on one platform (Meta, else TikTok, Google or LinkedIn) for a sales lead from a brand name, its domain and the sending rep. The v3 report, simpler than v2. Use when someone asks for the v3 report, "the same report for Brand X" in the new format, or a prospect report on what the brand's ads sell, how many it runs, who they are built for and how often it launches. Counts every number from those live ads and one close competitor on the same platform, and closes on what Crux does and the founders' booking button.
---

# One-shot creative report, v3

Make the finished report in one run: five A4 pages in one self-contained HTML file. The reader is a
marketer who asked for it, on a call or by replying to an email, reading on a phone, who may forward
it to a founder who was not there. That first reader often made these ads. Every page has to make
sense to the person it is forwarded to, cold.

The five pages answer one question each: what do your <platform> ads sell, how many ads do you run, what do
competitors do that you don't, how often do you launch new ads, and what would Crux do for you. The kit
writes the questions, draws the charts and counts every number. Your job is the evidence and a few short
lines: pick fair competitors, collect and tag the live ads, choose the one gap the ads show, write the
lines the kit asks for, pick the pictures, then run the kit and check the result. Do not restyle the kit
or write your own HTML. `<platform>` is the one platform the report is built from: Meta, TikTok, Google or LinkedIn (Stage 1, step 2b).

## Inputs

Required: `brand_name`, `domain_url`, `rep_name` and `rep_email` (the person sending it).

Optional:

- `rivals`: brands the lead named, or that the email or call which earned the report promised to
  compare. Use them first, and say which it was for each.
- `as_of`: the report date in the rep's time zone (YYYY-MM-DD). Every date on the page and every
  "since" is counted from it. Tool timestamps are UTC, so a run that crosses midnight UTC still uses
  `as_of`. Without it, use today's date in the rep's time zone.
- `market`: the country the report covers (two letters), or "global". Stage 1 counts every brand in it.
- `product_line` (when the brand sells several lines under one page), `accent` (the brand's main
  colour as hex; otherwise take it from the site's logo or buttons).

Ask only for a missing required input. Counts the request gives "for reference" come from outside
GetCrux: compare them with your own counts in the line-up table and report a big gap; never use them.

## Rules for every word on the page

These are Kevin's report-copy rules (10/22). The kit refuses most of them.

- **Talk to the reader.** The reader works at the brand, so write "you" and "your". Never write the
  brand's own name in your lines, whole or short; the kit refuses it. Competitors keep their names.
- **Words a fifth grader can follow.** Each page reads at Hemingway grade 6 or lower and no sentence runs
  past 20 words. Use short, common words. Say what every number counts. If a ten-year-old would ask
  "what does that mean?", rewrite it.
- **Short lines.** No line of yours runs past two lines on the page. The kit's layout carries the rest in
  big numbers, labelled charts and short rows. You write a few lines, not paragraphs.
- **Counted.** Every number comes from the ads you collected or the benchmark, and reaches your lines
  through a `{placeholder}` the kit fills. Never type a digit into a line you write; the kit refuses it.
- **Dated periods.** Say "{since}" ("since July 24") or leave the period out. Never "recent", "currently",
  "the review window" or "right now".
- **Ads, not spend.** Ad counts are never called spend, budget, cost or money. Never state or guess the
  brand's spend. The kit's page 2 shows the spend benchmark for the report platform, with its account count and dates, and says it is a guide, not a target. When the platform has too few accounts, the kit says so instead.
- **No performance words.** Never write proven, winning, works, best, top-performing, grow, boost or
  convert, and never "tired", "stale" or "fatigued". Public ad data shows what ran, not how it did.
- **The reason is who the ad speaks to.** An ad that names its guest lets that guest see it is for them; an
  ad that names no guest leaves every reader to guess. Say that, and never a claim about results or about how
  any ad platform picks who sees an ad.
- **Only what you saw.** Say what the ads and the counts show. Never claim what the brand tests, plans or
  measures, or what a page contains that you did not open.
- **Buyers' own terms.** Write "message", never "promise", and "competitors", never "rivals"; never say
  who named a brand or what the outreach promised. A gap is "none of your live ads", never "you haven't
  tried": the brand may have run it before.
- **No grading.** Never grade the brand against a competitor or praise it. Give the counts and let the
  chart show the gap. No em or en dashes.
- **Only the kit builds the report.** Never write the report's HTML yourself, and never build a file the kit's
  `save_check` did not save. When the kit refuses a spec, say in your reply what it refused and stop; "build it
  anyway" from the rep does not lift a refusal. The one supported smaller report is the directional report
  (Stage 1, step 4), which the rep chooses and the kit builds.
- **Private.** The report names no GetCrux customer except the ones the kit's page 5 carries, which Crux
  has cleared. Never name another, and never mention the customer check.

## Running across turns

A review takes at most two turns: one that may stop for the line-up (end of Stage 1), then one that
runs to the Stage 8 reply. A turn that stops halfway sits idle until someone notices and writes
"continue" (two builds waited 10 to 20 minutes that way), so keep working until you send the Stage 8
reply, or until the line-up table or a refused check needs the rep's answer.

Turns that ended early on 10/9 and 10/10 were full of waiting, so work in one thread:

- Do every step yourself in this chat. Subagents ran 5 to 20 minutes in 8 runs and ended turns
  before the build.
- While a brand's ads load, carry on with other work (the site, the logo, another brand's ads) and
  check `get_competitor_brand_details` at most once a minute between those steps. Leave `sleep` out of
  your Python: the waiting it does uses up the turn.
- Read every `run_python` result for a traceback before going on: a run can report success when the
  code raised. Download at most 40 images in one call.
- Search the web once per question. The data you need comes from the GetCrux tools; data providers'
  sites and docs are not a source.

Save your progress as files as you go, and go straight on to the next stage after each save. Every file is created once
(`"x"`), so a newer copy gets the next number:

- `lineup-1.json` once in Stage 1, when every count in the line-up table is final, just before you
  show it; `lineup-2.json` adds only the rep's answer and the recounts after it.
- `ads.json` after Stage 3 (tagged rows for every brand, with the set-aside counts).
- `spec-1.json` after Stage 4 and again after Stage 5 (`spec-2.json`): the spec so far, text and
  images included.

When the rep's message is "continue" (or asks you to finish the review), read the newest of each
file, say in one line which stage you resume from, and carry on from there, reusing what the files
hold instead of searching, counting or tagging again. "continue" is never a fix round, so its builds pass
no `rep_asked`. Any other message, such as a fix round, is done as written.

## Stage 1: Brand and competitors

1. Open `domain_url` in Python (browser user agent, timeout, `raise_for_status()`, size cap). Note
   the category, the buyer, the typical price and the accent colour. Name the buyer the way this
   reader would ("guests", "patients", "merchants", "clients"). The logo comes from the steps after this list.
2. Resolve the brand with `search_competitor_brands`; confirm each record it returns (Meta page, TikTok
   advertiser, Google advertiser) is the brand's own, and group them by platform. Then pick the report
   platform with step 2b. If the brand itself is not tracked yet, add it with `add_competitor_brand` and say so; its ads take
   a few minutes to load. Never add or refresh a competitor, even one the lead named or the outreach
   promised, before the rep approves the line-up table below: tracking a brand changes the shared
   workspace. Before you call any brand "not tracked", search
   for it with `search_competitor_brands` under its name variants: the full name, the name without
   spaces, the name with a country suffix and the short name ("American Express",
   "AmericanExpress", "AmericanExpressUS", "Amex"). Report each search and what it returned in the
   flags. A brand is not tracked only when every variant comes back empty. When `add_competitor_brand`
   warns that Meta reports 0 ads for the page id, or an added brand imports 0 ads, first run step 2b for the
   brand's other platforms. A real page with 0 Meta ads is not the wrong page. Stop and show the rep the
   candidate pages only when the page itself looks wrong (name, category or followers do not fit) or no
   platform has 5 live ads. A competitor that imports with 0 live ads is not replaced on that alone: open its Meta
   Ad Library page (or the library of the report platform) and compare, then say in the flags what you found (ads
   there that GetCrux does not track, or none) before you replace it (Caring.com scored from the outside feed on 10/9 after its add landed on an empty page).
2b. **Pick the report platform.** Count the brand's live ads in the line reviewed on each platform:
   - Meta, TikTok and Google: `search_competitor_brand_creatives(brand_ids=[that record], status="active",
     sort_by="newest", limit=500)`.
   - LinkedIn: `external_data_enrichment` `/v1/linkedin/ads/search` with the company name. Save each LinkedIn
     pull as `linkedin-<brand>-<YYYY-MM-DD>.json`, holding the endpoint, params and raw result (`"x"`, once). This
     applies to the brand and to every competitor. Follow `paginationToken` until `isLastPage`. A row has no status
     field: count an ad as live only when its `endDate` is the pull date; an ad with no dates is not shown as running, so
     leave it out and say how many in the flags. Map
     `id` to `ad_id`, `startDate`, `endDate`, `adType` to `format` (Single Image Ad is image, Video Ad is video),
     `image` or the first `thumbnailSources` as the picture, `headline` and `description` as the copy, and
     `landingPage` (often empty). Set `live_rule` to "in LinkedIn's ad library on the day it was pulled".

   Pick the report platform: Meta, if it has 5 or more live ads. Otherwise the platform with the most live ads
   (minimum 5); ties go TikTok, then Google, then LinkedIn. Otherwise stop and tell the rep, with every
   platform's count. Put `platform` ("META", "TIKTOK", "GOOGLE" or "LINKEDIN") in the spec, in the line-up table
   and in the flags, and set `live_rule` (Stage 4) off Meta. One platform per report: count competitors on the
   report platform only. A competitor with no record there is a text row ("no <platform> ads found in GetCrux"
   or "none in LinkedIn's ad library"), never a 0. TikTok organic posts, videos and follower counts from
   `external_data_enrichment` never count as ads.
3. When the brand sells several distinct lines, review one: `product_line`, or the line with the
   most live ads. Every number is then about that line. Business products are out of scope for a
   consumer line unless the request says business: set them aside in Stage 2 and count them in
   `dropped`, for the brand and every competitor alike.
4. Pick competitors. Use `rivals` first, then fill to three: the closest competitor sold to the same
   buyer (the one the pages set beside the brand: it becomes `compare`, and it should be the biggest
   advertiser the buyer would also consider), one at about the same price, and one the buyer would also
   consider. Each needs at least 20 live ads on the report platform aimed at the buyer after the off-scope ads are set aside
   in Stage 2. Count before you build and replace a competitor that falls short; the kit refuses a
   competitor under 20 ads and a line-up past 700 live ads in all, so swap the biggest competitor for a
   smaller one before you tag. When no line-up reaches 20 live ads for every competitor, do not stop at "no line-up
   works" and do not build anything yourself: show the rep the counts in the line-up table and offer the
   directional report as a choice, in these words: "build with at least 5 live ads each, labelled as a small
   sample". If the rep takes it, set `sample` to `"directional"` (Stage 4) and every competitor needs 5 live ads
   after set-asides instead of 20. A rep's "build it anyway" or "build it out" means this choice and nothing else.
   Give the brand and each competitor a two- or three-word `kind`, a `short` name (the name a marketer says,
   one or two words, never longer than 18 characters: "Western Governors", "Purdue Global"; a long name wraps and can push a page
   past A4) and a `market`:
   the line-up's Market column for that row, written the same way for the same place ("US", "Philippines",
   "global").
5. Drop and replace a competitor that is a GetCrux customer or shares a parent company with the brand. A
   competitor whose ad data is more than 7 days old (`get_competitor_brand_details`, `last_synced_at`; on TikTok
   and Google also the newest ad's `created_at`, and take the later of the two) is stale. A LinkedIn pull is
   always dated today. A catalog page that is not on the account syncs when it is added; adding a brand already on
   the account starts no new sync (LeapFrog, 10/9). Show a stale competitor's last sync in the line-up table
   and propose keeping it as it is or replacing it; the rep decides. Customers:
   {{CUSTOMERS}}, plus any account connected to Crux: run the kit's
   `is_connected(competitor, connected_names())` for each competitor. Never print or quote those names. A competitor
   that fails the check is "replace" in every table and saved file, with no reason, and stays replaced
   whatever a later message asks: say that the rule holds.

Record every competitor considered and dropped, with the reason. You report them at the end.

**Line-up table.** Count the brand and every candidate as Stage 2 describes (live ads, set-asides
and why), then show the rep one table, so one answer settles every addition:

| Row | Brand and page (platform, name, id) | Tracked | Last sync | Market | Live ads | Set aside, why | Left | Customer check | Proposal |
|---|---|---|---|---|---|---|---|---|---|

- Rows: the brand (every page or line that could be the one reviewed, with its count), each competitor
  the lead named or the outreach promised, then up to four stand-ins for any promised competitor that
  cannot be scored as written: tracked brands with a recent sync first, then catalog brands, then
  Meta pages `search_competitor_brands` found outside the catalog (only Meta pages can be added; a TikTok or
  Google stand-in must already be in the catalog; a LinkedIn stand-in comes from the LinkedIn ad library). For a brand that is not tracked,
  count its live ads with `search_competitor_brand_creatives` when that returns them; otherwise write
  "counted after adding". Competitors are counted and scored only from GetCrux tracking, with one exception: on a LinkedIn
  report, LinkedIn ad-library data from `external_data_enrichment` counts, saved in a dated
  `linkedin-<brand>-<date>.json` file and labelled LinkedIn (Kevin, 10/23); its Tracked cell reads "LinkedIn ad
  library, pulled <date>". Every other outside pull, and any organic post or video, never counts or scores a
  brand (Kevin, 10/14).
- Market: the country or region the page's ads are aimed at ("global", "US", "Philippines").
- Customer check: pass or replace, never the customer's name.
- Proposal, one per row: use it, add and use it, refresh and use it, or replace. A named competitor that is untracked, stale, under 20 ads (5 when the rep chose the directional report) or aimed at another market gets a proposal and stand-ins in the same table, never a follow-up question.
- Under the table: the line-up you propose (the brand's page and line, the competitor to compare and two others), and every tracking change a yes would make ("add Zocdoc, page 123; refresh
  Wix").

Save the table to `lineup-1.json`, then end the turn with the table, the tracking changes a yes would
make, and one question, when any of these holds:

- the line-up needs a tracking change;
- a stand-in, or a swap for a competitor the request or its notes name;
- a stale or untracked competitor;
- a market or product line that cannot be used as written;
- more than one page or line of the brand could be the one reviewed;
- no line-up reaches 20 live ads for every competitor, and at least one reaches 5: the rep chooses between
  replacing competitors and the directional report;
- the brand has fewer than 5 live ads on the report platform in the line reviewed, or the report platform is not
  Meta (the rep confirms the platform once).

Auto Run does not override this stop: on 10/10 it skipped the stop in 6 runs and settled line-ups the
rep never saw. Only a line-up of tracked, recently synced competitors that the request allows as written
carries on without asking. A report is never impossible: while the brand's own ads load, wait for
them; when no line-up works, show the table with its stand-ins and the directional choice, and ask.

After the rep's yes, make exactly the tracking changes approved (`user_confirmed=true`), wait for
the ads to load, and recount each approved competitor with `search_competitor_brand_creatives`. Build only
from tracked rows. When an added competitor still has fewer than 20 ads after set-asides (5 for a directional report), stop and tell the
rep. Otherwise go on through Stage 8 in the same turn.

**Logo.** Every page header carries the brand's own wordmark, so `brand.logo` is required. Run the
kit's `logo_candidates(domain_url)` (load the kit with the Stage 6 block first). It returns the
sources in the order to try them, each with `kind`, `src`, `aspect` and `light`, and leaves out
any the kit cannot draw:

1. `header`: the image or inline SVG in the site's home link or header. Use the first one that
   is the brand's wordmark. When it is `light` (white, for a dark header) and another candidate
   is the same wordmark in a dark version, use the dark one; for a light logo with no dark version
   the kit sets it on a tile in the accent colour, or black when the accent is too light.
2. `schema`: the logo in the site's structured data.
3. `og:image` or `apple-touch-icon`, only when the image is the wordmark itself, not a photo, a
   banner or a share card.
4. The profile image of the brand's report-platform record from `get_competitor_brand_details`, or any of its
   other platform records when that one has none. A square mark is
   fine: the kit sets the brand name beside it.

Open the one you pick with `visualize_file` and check it is the brand's current logo. `visualize_file`
refuses SVG, so convert an SVG to PNG in Python first. Competitors need no logo: leave `get_brand_logo` out
for them. Pass the `src` as `brand.logo`, unchanged: a URL, or the SVG
markup itself. Never crop a logo out of an ad or a screenshot. When `build` says the logo did not
load, try the next source. Only when none works, set `brand.logo_missing` to the sources you tried;
the header then prints the brand name, and you say so in the flags.

## Stage 2: Live ads

The rows you fetched for the line-up table are these live ads: use them and fetch only brands the
table did not count. For the brand and each competitor, on its report-platform record, call `search_competitor_brand_creatives` once with
`brand_ids=[that brand]`, `status="active"`, `sort_by="newest"`, `limit=500` and no `q`. Those are
its live ads. If exactly 500 come back, say "500+" in the flags and use the 500. On LinkedIn, use the saved
`linkedin-<brand>-<date>.json` rows instead. Keep, per ad: `ad_id` (`platform_id` on TikTok and Google),
`platform`, `start_date`, `end_date` and `status` whenever the row has them, `format` (image, video or
carousel), `landing_page_url` when present, `tracking_url` when the row has one, the image or video thumbnail
URL, and the copy (bodies, else titles, else none). TikTok and Google rows often have no copy and no landing
page; tag them from the video frames or the thumbnail. The kit leaves out an ad
that ended before `as_of` and counts it per brand in the page 1 footer, so never drop the end date.
When `landing_page_url` is empty or a click tracker (`ad.doubleclick.net` and the like) and the row has a
`tracking_url`, follow that URL's redirects in Python and store the final page as `landing_page_url`; Chase's 86
ads all needed it. Leave `fb.me` and `l.facebook.com` links as they are. An empty landing page on TikTok, Google or LinkedIn is normal:
list it in the flags and never block on it. `summary()` lists any still unresolved.

Drop ads that are not aimed at the buyer, such as recruiting or job ads. Put the number dropped in
that brand's `dropped` field, for the brand and every competitor, and what they were in its `dropped_why`, a
short phrase in the reader's words that reads after "for" ("owners and realtors"). Page 3's footer prints the
brand's own count with its phrase. The flags list each kind set aside with its count for every brand. Acquisition events
and webinars are aimed at the buyer and stay. A competitor left with fewer than 20 buyer ads (5 in a directional report) is replaced. If the brand itself has none left on the report platform, go back to step 2b and take the next platform; stop and tell the rep only when no platform has 5. Look at the media before tagging (contact sheets of
up to 40 thumbnails per brand with `visualize_file`); never tag from ad names.

## Stage 3: Tags

Tag every live ad of every brand (`to_tag(spec)` returns them; load the kit first) with two labels, keeping
one vocabulary across the brands so counts add up:

- `reason_to_buy`: the main reason the ad gives someone to book or act, in the brand's own terms, four to
  eight words ("explore a named vacation home", "save on a longer stay"). Two tags that name the same
  reason are merged with `merge`. Page 1 counts the distinct reasons per brand, so do not split one reason
  into several tags.
- `audience`: who the ad is built for. When the ad's words or picture name a kind of guest (a family, a group
  of friends, someone staying the month), tag that kind in the same words for every brand ("families and
  groups", "long stay travelers", "family vacation guests"). When the ad names no guest, tag the general
  category it speaks to ("mountain vacation guests", "vacation home guests"). Use the same tag for the same
  kind of guest in every brand: page 3's chart counts ads by the tags you list as `named`.

Look at the opening frame and the copy of each ad; never tag from ad names. Save the tagged rows for every
brand with `open_artifact("ads.json", "x")`; later runs read them back with `open_artifact("ads.json")`. A file
can be created once and never overwritten (`"w"` is refused), so a re-tag in the same chat saves `ads-2.json`
and later runs read the newest.


## Stage 4: What each page says

The kit computes every count. Before writing, run `print(Report(spec).summary())` on a spec with just
`as_of`, `brand`, `brands` and `merge`: it prints each brand's live ads, reasons, launches since the window began,
busiest week, ads in the last 30 days, and each brand's most common audience and reason tags. Decide the
setup first, then write the lines against those counts.

**The setup** (fields of the spec, all counted by the kit):

- `platform` ("META" by default; "TIKTOK", "GOOGLE" or "LINKEDIN" from step 2b) and, off Meta, `live_rule`: what
  live means on that platform, from `capabilities.active_window_days` in `get_competitor_brand_details`
  ("seen in the last 7 days" on TikTok, "shown in the last 3 days" on Google); for LinkedIn, what the pull
  shows. The footer prints it. Every ad row may carry `platform`; one that differs from the spec's is refused.
- `sample`: leave it out for the standard report. `"directional"` only when the rep chose it in Stage 1: every
  competitor then needs 5 live ads instead of 20, and pages 1, 3 and 4 print "Small sample: <competitor> has N
  live ads in this line, so read this as a direction." (every competitor under 20 is named, with its own count, the compare competitor first) Page 4 shows a competitor that launched fewer than 5 ads
  since the window began as "too few to compare", with no weeks bar. Any other value is refused. Say in the
  Stage 8 reply that the report is directional and why.
- `compare`: the one competitor the pages set beside the brand (a name in `brands[1:]`).
- `focus`: `audience` (the tag most of the brand's own ads carry), `phrase` ("a mountain getaway", read after
  "live ads sell"), `short` ("A mountain trip") and `other` ("Another trip"): the two key words under page
  1's chart.
- `named`: the audience tags that name who the trip is for, across the line-up, plus `named_phrase`
  ("families, groups or longer stays") and `named_one` ("a family, a group or a longer stay"). Page 3 counts
  the ads with these tags for every brand. The compare competitor must have some, or the page has no gap to
  show: choose another `compare`.
- `buyer`: one word for who the ads are aimed at, singular ("guest", "sender", "student", "patient"). The kit prints it
  as "new-sender ads" and "one per sender". Without it, "guest".
- `one_home`: `tag` (the `reason_to_buy` tag, after `merge`, of the ads that each show one product, such as
  one rental home) and `unit` ("home"). Page 2 and page 4 multiply it by the three guests.
- `guests`: exactly three kinds of guest to test, each with `who` ("families"), `one` ("a family"; "a
  longer-stay" for the third, which reads "a longer-stay version"), `title` ("For a family ski week") and
  `hook`, one short opening line for a new ad in the brand's own voice ("Ski all day. Then the whole family
  by the fire."). A hook has no number, no price and no claim about results. Take the three kinds from the
  gap page 3 shows: the guests the competitor builds ads for and the brand does not.

**The lines you write** (`text`, with `{placeholders}` for any number: `{b0.live}`, `{b0.focus_n}`,
`{b0.one_n}`, `{b0.named}`, `{c.name}`, `{c.live}`, `{c.named}`, `{new_ads}`, `{total_ads}`, `{since}`). The example
shows a vacation-home brand; write the same moves for this brand:

| Field | What it says | Example |
|---|---|---|
| `p1.answer` | What the ads sell, in plain words | Beautiful homes, for one kind of trip: a mountain getaway. |
| `p1.alt` | What the page 1 picture shows | Your Crail Creek ad in Big Sky: a great room with a long dining table under wood beams. |
| `p1.caption` | One short line under it, about the brand's own ads | Crail Creek: one home, like most of your ads. |
| `p1.works` | What the ads do well, in terms of what they say, never results | The mountains are what you sell. |
| `p1.pitfall` | The gap: no ad names the guest, so no guest sees an ad meant for them | No ad names a family or group, so families can't tell a trip is for them. |
| `p1.try` | One test: a new ad for one guest, made from an ad the brand already runs | One ad for a family ski week, made from a home ad you already run. |
| `p1.reasons_note` | The brand's reasons to book, in a few words | A specific home, a mountain escape, a destination. |
| `p3.answer` | What competitors do that the brand does not | They say who the trip is for, not just where. |
| `p3.opportunity` | The move, in one line | Keep the home in each ad, and add who the trip is for. |
| `p5.answer` | What Crux would do, for this brand | Make your home ads into ads for new guests, in your own style. |

Page jobs, fixed by the kit:

1. **What do your <platform> ads sell?** The boxed finding (`{b0.focus_n}` of `{b0.live}` ads sell the focus), a chart
   of it, Works / Pitfall / Try rows, and three number tiles: how many you run, how varied they are (distinct
   reasons to book), how often you launch, each against the compare competitor.
2. **How many ads do you run?** The spend benchmark from the Crux accounts on the report platform (the kit prints
   the count and dates, and a caveat when there are fewer than 85), the brand's live ads as a line, and four
   bars: you now, the typical brand at $100K+ a month (with its account count), you with the new-guest ads (3
   guests times your one-product ads), and the compare competitor. Under 10 accounts (LinkedIn today), there is
   no benchmark: three bars and one line saying so. The kit writes every word.
3. **What do competitors do that you don't?** Ads built for a named guest, per brand; four live ads; the three
   hooks to test.
4. **How often do you launch new ads?** Running totals since the 90-day window began, the weeks it takes to launch
   the new-guest ads at your pace and the competitor's, and the share of live ads under 30 days old. The kit
   writes every word. When the brand launched nothing in the window, the kit refuses: tell the rep. Ads with no start date count as live but not toward the pace; the footer counts them.
5. **What would Crux do for you?** The Crux close, with your `p5.answer`, the deck's proof and the booking
   button. The proof is Crux's own and fixed.

Never write a `text` line that repeats a number the kit already prints; the lines carry meaning, the kit
carries counts. Save the spec so far as `spec-1.json`.


## Stage 5: Images

Every image must show what its caption says. Open each with `visualize_file` before using it.

- **`p1_ad`**: the `ad_id` of one of the brand's own live ads that shows the brand's main product well: a
  clear picture of one home, product or place, not a text card. It sits on page 1 and again, small, on page 5.
- **`p3_ads`**: exactly four live ads, each `{ad_id, brand, for, alt}`. First one of the brand's own ads (the
  one that shows the focus), then three competitor ads each built for a guest named in `named` (the compare
  competitor's first). `for` says who the ad is built for ("Built for families and groups"), `alt` says what
  the picture shows. Caption a competitor's ad with that competitor's name: the kit does, from `brand`.

Save the spec with its images as `spec-2.json`.


## Stage 6: Build

{{LOAD}}

Then load the tagged ads, build the `spec` (`brand` is `{"name", "accent", "logo"}`, and every `name` is written exactly as the brand writes it, "5.11 Tactical" and never "Five Eleven Tactical": the page header, the page title and the file name print it, and the kit accepts digits in a brand's name, in alt text and in lines. Never respell a name to get past a check; the inputs go in as `rep`,
`rep_email` and `calendly`, the booking link, `https://calendly.com/atharva-getcrux/30min`), and:

```python
html, report = build(spec)
print(report.brand)
print(save_check(html, report, open_artifact))
```

Every build is a check build, and `save_check` writes it: `<brand-slug>-check-1.html`, then `-check-2`
and `-check-3`, where `<brand-slug>` is the brand's name, lower case with hyphens. Never write the HTML with
`open_artifact` yourself, and never write `<brand-slug>-creative-review.html` or any other name.
`save_check` refuses a fourth check build: stop, and reply with the newest one. GetCrux serves every HTML file
in the chat at `getcrux.ai/report/<chat>/<file name>` and a file can never be overwritten, so that name stays
free until the rep approves a check build and it is published (Stage 8). Never name a file with "final", "v2" or
"v3".

`build` raises a ValueError when the spec breaks a rule in this skill: the word rules, a digit typed by hand, a
competitor under 20 ads on the report platform (under 5 with `sample` directional), a `sample` that is not "standard" or "directional", ads from more than one platform, `focus`, `named`, `one_home`, `guests`, `p1_ad` and `p3_ads` that do not match the ads,
a line that names the brand or reads above grade 6, and the required inputs. It lists every problem at once; the
error names the rule, the field and what to try next. Fix the spec and build again. `precheck(spec)` lists the
same problems without building. `report.brand` flags a light logo set on a tile, a square mark, a missing logo or
a font that did not load; when it says the kit font did not download, build again before you check the pages.


## Stage 7: Check

Open the check build with `visualize_file`, look at all five pages against this list, then
`print(after_check(report, [each defect]))` and do what it says:

- exactly five pages, nothing past the footer, no text overlapping or cut off (the page tightens its own spacing when a long name or a
  tall ad runs it past A4; a page still on a second sheet is a defect: shorten that page's lines or pick a shorter `short` name);
- the header, and the file name, show the brand's name as the brand writes it, not respelled;
- every page header shows the brand's own logo, sharp and readable, not a crop from an ad and not the brand
  name in plain text (unless `logo_missing` is set);
- every image matches its caption, and every competitor ad is labelled with the competitor's name;
- each page answers the question in its heading in its first line, and the line is a claim a cold reader
  understands at once;
- read each page aloud as the brand's marketer: it says "you", every number says what it counts, and nothing
  needs a second read;
- page 1's Pitfall is true of the brand's ads: no ad names the guest it says none names, and the Try is one
  ad made from an ad the brand already runs;
- page 3's chart agrees with its line, and `p3.opportunity` is the move for the gap the chart shows (when the
  brand has named-guest ads of its own, the opportunity may need to change);
- the three hooks are one short line each in the brand's voice, with no claim about results;
- every count or "none of" about the brand's own ads matches its rows: the reader knows their own account, and
  one wrong number about it undoes the rest;
- no performance words, no spend words in your lines (the kit's page 2 and footers may say "spend"), no
  customer names beyond page 5's;
- page 5's wording ("inspired by your winning ads", the Cloaked figures, the logos) is Crux's own, approved by Kevin: never a defect and
  never edited;
- the booking panel says "Crux's founders" and the button reads "Book a time with Atharva" and links to the
  Calendly page.

Fix every defect you notice, the kit's own included, while a build is left; name only what the last build still
has. When the page check could not run (no browser in the sandbox), say so. Caveats for the rep go in the reply,
never on the page.

## Stage 8: Deliver

Reply with: the link to the newest check build, the one that passed Stage 7; one line naming page 1's
finding and the test it suggests; and flags
(the report platform and every platform's live count for the brand, competitors considered and dropped with reasons, each `search_competitor_brands` search behind a
"not tracked" and what it returned, ads dropped as not aimed at buyers for every brand, why you picked `compare`, the four ads on page 3, the logo's source and `report.brand` flags, anything you could not check). A
fix round the rep asks for builds the next check, with
`save_check(html, report, open_artifact, rep_asked="<the rep's words>")`, and replies the same way: write the next
`spec-N.json`, build from it, run Stage 7 before saving, and list each change. A value the kit has no
input for may be patched in the HTML: list each patch, and prove nothing else changed by counting the
replaced strings and comparing file lengths (a full-file diff ran past the 300-second limit three
times on 10/10).

Publish only when the rep approves a check build by name: with the `client-report` skill, that file
unchanged, under the slug `<brand-slug>-creative-review`. Call `client-report` with the file and
nothing else, and leave the link untested: a new link can 404 for minutes, and the rep checks it. When that slug is taken, stop and tell the
rep; never pick another slug yourself. Never add "v2", "check", "final", "corrected" or "fixed" to a
slug. Give the published link at once and say it can take a few minutes to open.

{{KIT_SECTION}}
