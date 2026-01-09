# How I DT! — CPH50 6 AM Extension (Teacher/Student Pack)

A short guide for high school design thinking classes to storyboard a 45–60s "How I DT!" reel, using the CPH50 charging project as a model.

## Phase-by-Phase Story Beats

- **Discovery (Problem + Context)**  
  - Visuals: clip of frost on car, two EVs in driveway, ChargePoint app showing charge ending at 6:00 AM.  
  - Line: "Our EV stops charging at 6 AM because of the utility price window—winter range is short."

- **Interpretation (Reframe + Constraints)**  
  - Visuals: sticky note or overlay listing constraints.  
  - Line: "Keep the smart rate scheduling, add a 6 AM push. No new hardware, zero cost, must work with daylight saving."

- **Ideation (Options Tour)**  
  - Visuals: rapid icons/logos—Home Assistant, ESP32, Raspberry Pi, GitHub Actions, Cloudflare Workers.  
  - Line: "We brainstormed hosts. Picked serverless—no hardware to buy, handles time zones for free."

- **Experimentation (Prototype + Test)**  
  - Visuals: quick code snippet (login → start_session), retry/backoff note, MailChannels alert.  
  - Line: "Prototyped a Cloudflare Worker: login, start charge at 6, retry 3×, alert on failure."

- **Iteration (Fixes + Learnings)**  
  - Visuals: highlight quirks—User-Agent header, `1:` station ID prefix, `%23` for `#` in passwords.  
  - Line: "Debugged API quirks with community docs; refined until it ran clean."

- **Result (Impact)**  
  - Visuals: charging past 6 AM, Energy Price Plan screen still enabled.  
  - Line: "Kept the rate-aware schedule, just added one smart nudge. No new gear."

- **CTA (Class Activity)**  
  - Visuals: title card "Your Turn".  
  - Line: "Find a daily friction. Run Discovery → Interpretation → Ideation → Experimentation → Iteration. Share your 60s ‘How I DT!’ clip."

## Suggested Reel Structure (45–60s)

1. Hook (3–5s): Statement of the problem with a visual.  
2. Phase beats (5–7s each): One sentence + one clear visual per phase.  
3. Result (5s): Before/after.  
4. CTA (5s): Invite students to run the cycle on their own problem.

## Classroom Use

- **Warm-up:** Students list a friction on campus/home in 2 minutes.  
- **Map to phases:** Each student writes one sentence per phase for their idea.  
- **Prototype fast:** Storyboard frames on paper; optional: record a 30–60s clip.  
- **Share/iterate:** Play reels, gather one insight per viewer, refine.

## Tips for Students

- Keep jargon light; explain constraints plainly.  
- Show one "unexpected learning" to prove iteration.  
- Use real artifacts (screenshots, notes) over stock visuals.  
- Timebox ideation; pick a direction quickly and prototype.

## Tips for Teachers

- Set a hard 60s limit to force prioritization.  
- Encourage evidence: every claim paired with a visual.  
- Reward iteration: show the fix, not just the win.  
- Offer a rubric: clarity of problem, fit to constraints, evidence of testing, reflection on iteration.
