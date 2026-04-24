# backend/app/recommendation_engine.py
from dataclasses import dataclass, field


@dataclass
class Recommendation:
    region_key: str
    region_name: str
    score: int
    priority: str   # "high" | "medium" | "ok"
    message: str
    details: str
    steps: list[str] = field(default_factory=list)


_ADVICE: dict[str, dict[str, dict]] = {
    "visual_cortex": {
        "high": {
            "message": "Strong visual appeal — your content is aesthetically engaging.",
            "details": "The visual cortex is well-activated. Composition, contrast, and visual hierarchy are working in your favor.",
            "steps": ["Maintain this visual standard across your ad variants", "A/B test with even bolder color contrast to see if you can push higher"],
        },
        "medium": {
            "message": "Visual impact is moderate — not grabbing attention fast enough.",
            "details": "The visual cortex processes images before conscious thought. Moderate scores mean viewers are registering the content but it's not creating a strong pull. You're competing with high-stimulus feeds.",
            "steps": [
                "Increase contrast ratio — pair one dominant color with a sharp accent (e.g. dark background + bright text)",
                "Use the rule of thirds: move the key subject off-center",
                "Add motion in the opening frame — a slow zoom, text reveal, or camera pull-in",
                "Crop tighter on the subject — remove visual clutter from the background",
            ],
        },
        "low": {
            "message": "Weak visual engagement — this will be scrolled past.",
            "details": "Low visual cortex activation means viewers' brains are not being grabbed. On high-velocity feeds (Instagram, TikTok) you have under 1 second to stop the scroll. Flat, low-contrast, or low-resolution content fails this test consistently.",
            "steps": [
                "Replace with a high-contrast hero image — dark/light split, vivid color, or dramatic lighting",
                "Use professional-grade imagery or footage (≥1080p, sharp focus)",
                "Design the first frame as a standalone attention hook — assume the rest won't be seen",
                "Add a bold text overlay in the first 0.5s to create visual anchor",
                "Remove competing visual elements — one focal point only",
            ],
        },
    },
    "face_social": {
        "high": {
            "message": "Excellent human connection — faces and social proof are landing well.",
            "details": "The fusiform face area is strongly activated. Human faces are the brain's highest-priority attention magnet.",
            "steps": ["Continue leading with faces", "Test direct eye contact vs. product-focused framing to optimize further"],
        },
        "medium": {
            "message": "Weak human presence — trust is harder to establish without faces.",
            "details": "The brain's face-detection system (fusiform face area) activates automatically and triggers trust, empathy, and social proof. Without a strong face signal, you're relying on copy alone to build connection — a significantly harder task.",
            "steps": [
                "Add a human face in the first 2 seconds — ideally looking directly at the camera",
                "Use a real customer testimonial with their photo, not an avatar or stock image",
                "If it's a product ad, show a hand using the product (hands trigger social mirroring)",
                "Overlay social proof numbers ('10,000+ customers') with a grid of real user photos",
            ],
        },
        "low": {
            "message": "No human connection — this content feels cold and untrustworthy.",
            "details": "Humans are wired to trust other humans. Content with no faces, hands, or human elements activates minimal social proof processing. Viewers don't feel connected and are unlikely to take action. This is one of the highest-ROI fixes in ad creative.",
            "steps": [
                "Lead with a face: founder, customer, or spokesperson — looking at camera",
                "Use direct eye contact — the brain treats it as being personally addressed",
                "Record a 3-5 second UGC-style clip of a real person talking about the product",
                "Add before/after testimonials with real photos (not illustrated avatars)",
                "If animation/product-only is required, overlay a real quote with a headshot",
            ],
        },
    },
    "amygdala": {
        "high": {
            "message": "High emotional impact — your content creates a strong feeling response.",
            "details": "The amygdala is strongly activated. Your content is triggering desire, urgency, fear of loss, or aspirational pull — all of which drive action.",
            "steps": ["Identify which specific emotion is driving this and double down on it in future creatives", "Test whether leaning into desire vs. fear of loss further increases conversion"],
        },
        "medium": {
            "message": "Emotional resonance is moderate — not creating enough urgency or desire.",
            "details": "The amygdala drives all emotional decision-making. Moderate activation means viewers feel something, but not strongly enough to override inertia. People buy on emotion and justify with logic — weak emotional signal = weak conversion.",
            "steps": [
                "Sharpen your hook around a specific pain point ('tired of X?') or strong desire ('imagine waking up and...')",
                "Use emotionally loaded words: 'finally', 'never again', 'breakthrough', 'before it's too late'",
                "Add a countdown or scarcity element ('48 hours left', 'only 12 remaining')",
                "Show the emotional outcome, not just the product feature — what does their life look like after?",
            ],
        },
        "low": {
            "message": "Low emotional impact — no feeling, no action.",
            "details": "The amygdala is barely engaged. This content is not creating a felt response — no desire, no urgency, no fear of missing out. Without emotional activation, even clear messaging and good visuals fail to drive action. Emotion is the catalyst that converts.",
            "steps": [
                "Rewrite your hook around a raw, specific pain: '3 years of bad sleep ended when...'",
                "Show a dramatic before/after — not just the product, but the person's emotional state",
                "Use music with emotional arc — builds tension then releases into the solution",
                "Add urgency language and time pressure ('doors close Sunday', 'sold out twice this year')",
                "Open with a question that hits a nerve: 'Why does this happen every time?'",
            ],
        },
    },
    "hippocampus": {
        "high": {
            "message": "Highly memorable — this content will stick.",
            "details": "The hippocampus is strongly activated, meaning this content is being encoded into memory. Viewers are more likely to recall your brand later.",
            "steps": ["Identify the memorable element (story, visual hook, phrase) and use it as the consistent anchor across your campaign"],
        },
        "medium": {
            "message": "Memorability is average — forgettable in a crowded feed.",
            "details": "The hippocampus encodes new memories when something is novel, emotionally salient, or narrative-driven. Average activation means you're registering but not sticking. In competitive markets, forgettable ads have zero carry-over effect.",
            "steps": [
                "Add one unexpected element — a pattern interrupt in the first 2 seconds (unexpected visual, sound, or statement)",
                "Use a memorable phrase or tagline that gets repeated at the end",
                "Structure as a micro-story: problem → moment of change → outcome (even in 15 seconds)",
                "Give the brand a distinctive visual signature that appears consistently",
            ],
        },
        "low": {
            "message": "Easily forgotten — zero recall value.",
            "details": "This content is not being encoded into long-term memory. Viewers may complete viewing it but won't recall the brand or message. Ad spend with low memorability has near-zero compounding effect — every impression starts from zero.",
            "steps": [
                "Open with a story: 'Six months ago, I couldn't afford rent. Now...' — narrative structure forces hippocampal encoding",
                "Use a surprising visual or sound hook in the first frame that creates a 'what was that?' response",
                "End with a memorable slogan or visual that repeats 2-3 times",
                "Create a brand character or mascot to anchor recall",
                "Use contrast: show what life looks like without your product vs. with it — the gap creates memory",
            ],
        },
    },
    "language_areas": {
        "high": {
            "message": "Clear, persuasive messaging — your language is working.",
            "details": "Broca's and Wernicke's areas are strongly activated. Your copy is being processed fluently and is compelling.",
            "steps": ["Preserve the headline structure in future variants", "Test whether adding one power word ('guaranteed', 'instantly', 'proven') can push conversion further"],
        },
        "medium": {
            "message": "Messaging clarity is moderate — your point isn't landing fast enough.",
            "details": "Language areas process verbal and written information. Moderate activation often means the message is understandable but not punchy — too long, too generic, or buried under jargon. On social media, copy needs to communicate value in under 3 seconds of reading.",
            "steps": [
                "Rewrite your headline to lead with the outcome, not the feature: 'Sleep in 8 minutes' not 'Advanced sleep formula'",
                "Cut word count by 40% — remove every word that doesn't add meaning",
                "Add a direct CTA in the first 5 words of body copy: 'Get X. Do Y. Feel Z.'",
                "Use plain language — a 7th-grade reading level converts better than sophisticated copy",
            ],
        },
        "low": {
            "message": "Weak messaging — viewers don't know what you're offering or why it matters.",
            "details": "Language areas are barely engaged. This typically means the copy is absent, confusing, generic, or too long to process during a scroll. If viewers can't answer 'what is this and why should I care?' in 2 seconds, they won't.",
            "steps": [
                "Write a single-sentence value proposition: '[Product] helps [target person] [get outcome] without [obstacle]'",
                "Move your headline above the fold — it should be the first thing seen, not buried",
                "Add closed captions/subtitles to video — 85% of social video is watched on mute",
                "Test three radically different headlines using your exact pain/desire/outcome formula",
                "Remove all filler: 'innovative', 'world-class', 'cutting-edge' — replace with specifics",
            ],
        },
    },
    "reward_circuit": {
        "high": {
            "message": "Strong desire — your content makes people want it.",
            "details": "The dopaminergic reward circuit is strongly activated. Viewers are experiencing anticipatory desire — the feeling of wanting the outcome your product promises.",
            "steps": ["Identify the specific desire trigger (status, pleasure, convenience, savings) and amplify it", "Test reward language ('unlock', 'claim', 'get your') against urgency language to see which converts better"],
        },
        "medium": {
            "message": "Moderate desire — the value isn't compelling enough yet.",
            "details": "The reward circuit activates when the brain anticipates gain. Moderate scores mean viewers understand the offer but aren't feeling strong pull. The transformation isn't vivid enough, the value isn't clear enough, or the offer isn't differentiated.",
            "steps": [
                "Make the transformation tangible: show the exact before/after numbers or visual change",
                "Add 'reward language' to your CTA: 'Claim your free X', 'Unlock your Y', 'Get instant access'",
                "Quantify the value: '3x your output in 30 days' is more activating than 'improve your productivity'",
                "Show the aspirational lifestyle outcome — not just the product, but what it enables",
            ],
        },
        "low": {
            "message": "No desire activation — viewers won't want this.",
            "details": "The reward circuit is barely firing. The offer is not creating anticipation or desire. This usually means the transformation isn't visible, the value is unclear, or the positioning is too generic. Without desire activation, even perfect copy and targeting won't convert.",
            "steps": [
                "Lead with the aspiration: show the outcome first, then reveal how you get there",
                "Use exclusivity and access language: 'Most people never discover...', 'This is only for...'",
                "Add testimonials with specific results: '$8,400 in 30 days', 'Lost 14 lbs in 6 weeks'",
                "Make the offer feel like a steal: show the original price crossed out, highlight what's included",
                "Create a 'reason why' — limited batch, founder story, or scarcity that justifies the purchase now",
            ],
        },
    },
    "prefrontal": {
        "high": {
            "message": "Strong rational justification — trust signals are well established.",
            "details": "The prefrontal cortex is helping viewers justify the decision to buy. Logic, credibility, and proof are registering well.",
            "steps": ["Continue stacking social proof — you can add more data points without overwhelming", "Test adding a money-back guarantee in the CTA area to reduce final purchase friction"],
        },
        "medium": {
            "message": "Rational justification is thin — viewers can't fully trust this yet.",
            "details": "The prefrontal cortex evaluates decisions for logic and risk. Moderate activation means some proof is landing but objections remain. Even emotionally engaged viewers will hesitate if rational trust signals are absent.",
            "steps": [
                "Add a specific proof stat: 'Used by 12,400+ customers', '4.9 stars from 830 reviews'",
                "Show a recognizable logo, press mention, or certification ('As seen in Forbes')",
                "Add a 30-day money-back guarantee — it eliminates perceived risk and doubles as a credibility signal",
                "Include 2-3 specific objection-busting facts near your CTA",
            ],
        },
        "low": {
            "message": "No credibility — viewers won't trust this enough to act.",
            "details": "The prefrontal cortex is not finding evidence to justify a decision. This content lacks proof, credentials, social validation, or risk-removal. Visitors may be emotionally interested but will talk themselves out of it without rational anchors.",
            "steps": [
                "Add a trust bar: 'X customers | Y stars | Z-day guarantee | Featured in [publication]'",
                "Include real, named testimonials with photos and specific results — not 'Great product! - J.D.'",
                "Show credentials: years in business, certifications, founder background, industry recognition",
                "Address the top objection directly in your copy: 'Still skeptical? Here's what happened when...'",
                "Add a money-back or satisfaction guarantee with clear terms — visible near the CTA",
            ],
        },
    },
    "motor_action": {
        "high": {
            "message": "Strong action drive — your content activates and moves people.",
            "details": "Motor cortex regions associated with action are well-activated. Your CTA and energy are creating behavioral momentum.",
            "steps": ["Ensure your landing page matches the energy level — a high-action ad to a static page creates friction", "Test verb variations in your CTA ('Start', 'Get', 'Grab') to optimize click-through"],
        },
        "medium": {
            "message": "Action drive is moderate — not enough momentum to push the click.",
            "details": "The motor action system activates when content creates urgency and behavioral momentum. Moderate scores often mean the CTA is present but passive, or the energy drops off before the viewer reaches it.",
            "steps": [
                "Use strong action verbs in your CTA: 'Start', 'Get', 'Grab', 'Join', 'Claim' — avoid 'Learn more' or 'Submit'",
                "Move your CTA earlier — don't wait until the end of a 30-second video",
                "Add directional cues pointing to your CTA (arrow, person gesturing, gaze direction)",
                "Create energy pacing: build in the middle, peak at the CTA, not fade out",
            ],
        },
        "low": {
            "message": "No action drive — this content is passive viewing, not a funnel.",
            "details": "Motor action circuits are barely firing. This content lacks the energy, urgency, or directional pull to move someone from watching to clicking. A passive ad is a brand-awareness tool at best — and only if your brand awareness budget is separate.",
            "steps": [
                "Add a visible, high-contrast CTA button overlay on video ('Shop Now', 'Get Yours', 'Claim Offer')",
                "Use time pressure language: 'This offer expires at midnight', 'Only 7 left at this price'",
                "Raise the energy of your voiceover, music, and pacing — match the action you want viewers to take",
                "End with a direct verbal ask: 'Click the link below right now and...'",
                "Create a two-step CTA: 'Comment READY below for the link' (lowers friction, increases commitment)",
            ],
        },
    },
}


def get_recommendations(scores: dict[str, int]) -> list[Recommendation]:
    from app.brain_mapper import REGIONS

    unknown = set(scores) - _ADVICE.keys()
    if unknown:
        raise ValueError(f"Unknown region keys: {unknown}")

    def level(s: int) -> tuple[str, str]:
        if s < 35:
            return "low", "high"
        if s < 65:
            return "medium", "medium"
        return "high", "ok"

    recs = []
    for key, score in scores.items():
        lvl, priority = level(score)
        advice = _ADVICE[key][lvl]
        recs.append(Recommendation(
            region_key=key,
            region_name=REGIONS[key]["name"],
            score=score,
            priority=priority,
            message=advice["message"],
            details=advice["details"],
            steps=advice["steps"],
        ))

    recs.sort(key=lambda r: ({"high": 0, "medium": 1, "ok": 2}[r.priority], r.score))
    return recs
