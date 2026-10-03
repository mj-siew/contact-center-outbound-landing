"""ADK workflow for creating and revising a Customer Care reactivation page."""

import os
from pathlib import Path

# gpt-6-luna supports medium-reasoning tool calls through the Responses API.
os.environ.setdefault("LITELLM_ROUTE_ALL_CHAT_OPENAI_TO_RESPONSES", "true")

from google.adk.agents import Agent, SequentialAgent
from google.adk.apps import App
from google.adk.models.lite_llm import LiteLlm

from app.tools import generate_draft, generate_final, read_draft


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRAND_GUIDE_PATH = PROJECT_ROOT / "docs" / "brand_guide.md"
BRAND_GUIDE = (
    BRAND_GUIDE_PATH.read_text(encoding="utf-8")
    if BRAND_GUIDE_PATH.exists()
    else (
        "## Brand Language\n"
        "- Reactivation pages feel warm, human, and glad to have the customer back.\n"
        "- Use plain, friendly English; avoid jargon and sales pressure.\n"
        "- Personalise the message to the customer's cancellation reason; show we listened.\n"
        "- State the 40% first-box discount and its caveats accurately; no other promises.\n"
        "- Photography: appetising realistic food shots on a light wooden table, natural home settings; no text, packaging, hands, or faces in generated images (the page template's offer badge over the hero is the one accepted exception).\n"
        "- Visual look: vivid green shades, generous white space, clean consumer-product layout.\n"
    )
)
REACTIVATION_REFERENCE = """
Brand voice and CTA style
- Warm, glad-to-have-you-back tone: "You spoke. We listened" framing. The page
  shows the returning customer that their cancellation reason was heard and is
  directly answered with a concrete benefit.
- Plain, friendly English copy. No jargon, no sales pressure. One obvious next
  step: a prominent reactivation CTA with the offer named in it.
- Visual direction: vivid red, generous white space, appetising
  realistic food photography, clean consumer-product layout.
- Food-image style: each dish is
  photographed from a slight top-down or 45-degree angle on a light wooden
  table, with natural daylight, shallow depth of field, and appetising, modern
  plating. NEVER overlay titles, subtitles, badges,
  text, typography, watermarks, or logos on the images; the image is pure
  photography only.

Facts to represent faithfully on the page (English market)
- Offer: 40% discount on the first box. One-time comeback offer for former customers.
- Eligibility: the customer must be a former customer with a
  cancelled subscription. Redeeming the offer reactivates an auto-renewing
  subscription that can be cancelled or paused at any time; deliveries can be
  skipped or scheduled flexibly.
- Variety UVP: up to 100 recipes to choose from every week in the German market.
- Three plan categories to showcase with one appetising dish image each:
  Meat & Veggies (Fleisch & Gemuese, most popular plan), Veggie (vegetarian and
  plant-based meals), and Family Friendly (kid-tested, family-friendly recipes).
- How reactivation works: log into the account (app or desktop), follow the
  reactivation prompt or CTA, pick meals and preferences, and the box is
  delivered.
- Personalisation: address the customer by the first name Laura.
  and map at least one benefit directly to their stated cancellation reason.
  For a price-driven cancellation reason, lead with value: the 40% first-box
  discount, flexible weekly planning, and skipping weeks to control spend.

Do not invent other discounts, prices, or guarantees beyond the 40% first-box
offer. Do not imply the offer applies to more than the first box.
"""


MODEL = LiteLlm(
    model="openai/gpt-6-luna",
    reasoning_effort="medium",
    allowed_openai_params=["reasoning_effort"],
)

creator = Agent(
    name="creator",
    model=MODEL,
    description="Creates the first draft of a personalised reactivation page.",
    instruction=f"""
You are the Creator in a Customer Care reactivation workflow. The user message
is a short context from a care agent about a former customer: their cancellation
reason and that they want the current comeback offer in writing. Recognise the
cancellation reason from the agent's own words. Use the customer first name
"Laura" for personalisation. Write concise, warm, plain English landing-page copy
for that customer.

Call generate_draft exactly once with: the recognised customer context
(cancellation reason in short English form), a English headline, a English
subheadline, a personalised English greeting message, the English offer text
(40% discount on the first box), English benefit lines mapped to the
cancellation reason, English pricing/eligibility text, a English CTA, three
English FAQ items, and four image prompts: one appetising hero image prompt and
three dish image prompts (one meat-and-veggies dish, one veggie dish, one
family-friendly dish). Do not invent other discounts or make unsupported
promises.
Output format rules (the page template parses these):
- benefits: exactly three lines, each "Short title: one-sentence body". The
  first benefit answers the cancellation reason directly.
- faq: exactly three lines, each "Question? | Answer".
- headline: max 8 words. subheadline: one sentence naming the offer.
  message: 1-2 warm sentences acknowledging the cancellation reason; do not
  repeat the offer there. offer: one short sentence. cta: max 6 words.
- Image prompts describe only the dish and ingredients; framing and photo style
  are appended automatically.
- Dish image prompts, one per plan, each visibly different in colour and shape:
  meat_veg shows a clearly visible meat portion with roasted vegetables;
  veggie contains no meat or fish at all; family is a kid-friendly classic
  (e.g. pasta, tacos, mild curry). Hero shows one generous plated dish.
Your final response should briefly confirm that draft.html and the
four draft images were created.

Brand guide:
{BRAND_GUIDE}

Reactivation reference:
{REACTIVATION_REFERENCE}
""",
    tools=[generate_draft],
    output_key="creator_summary",
)


critic = Agent(
    name="critic",
    model=MODEL,
    description="Checks the reactivation draft against brand guidance.",
    instruction=f"""
You are the Critic. Read draft.html by calling read_draft exactly once. Then
give specific, useful feedback on the reactivation page for this customer
context: {{customer_context}}. Identify at least two major weaknesses,
including one about the call to action and one about brand identity. Also
check: whether the benefits directly address the stated cancellation reason,
whether the 40% first-box offer and its eligibility terms are stated clearly
and accurately, whether the "up to 100 recipes" variety message and the three
plan categories (Meat & Veggies, Veggie, Family Friendly) are present, and
whether the English copy is plain and warm, whether the customer is addressed
as Laura, and whether the copy follows the length and format rules (three
"Title: body" benefits, three "Question? | Answer" FAQs). Also review the four
image prompts returned by read_draft: veggie has no meat or fish, meat_veg shows
meat and vegetables, family is kid-friendly, the three dishes look distinct,
and no prompt asks for text or logos. Only give feedback the Revisor can act on:
copy fields and image prompts (layout and the offer badge are fixed). Do not
rewrite the page.

The following brand guide is loaded into your runtime instructions and is the
source of truth for your critique:
{BRAND_GUIDE}

Also evaluate whether the draft faithfully applies this reactivation reference.
Flag missing, misleading, or unsupported offer, pricing, eligibility, or
variety details, as well as a weak brand voice, visual direction, or CTA:
{REACTIVATION_REFERENCE}
""",
    tools=[read_draft],
    output_key="critique",
)


revisor = Agent(
    name="revisor",
    model=MODEL,
    description="Applies the critique to produce the final reactivation page.",
    instruction=f"""
You are the Revisor. Improve the draft for this customer context:
{{customer_context}} using this critique:
{{critique}}

Call generate_final exactly once with improved English copy: headline,
subheadline, personalised message, offer text, benefit lines, pricing and
eligibility text, CTA, FAQ items, and four improved image prompts (one hero,
three dishes: meat-and-veggies, veggie, family-friendly). Apply the critique
while keeping the copy plain, warm, human, and specific, and keeping the offer
facts accurate (40% off the first box only).
Output format rules (the page template parses these):
- benefits: exactly three lines, each "Short title: one-sentence body". The
  first benefit answers the cancellation reason directly.
- faq: exactly three lines, each "Question? | Answer".
- headline: max 8 words. subheadline: one sentence naming the offer.
  message: 1-2 warm sentences acknowledging the cancellation reason; do not
  repeat the offer there. offer: one short sentence. cta: max 6 words.
- Image prompts describe only the dish and ingredients; framing and photo style
  are appended automatically.
- Dish image prompts, one per plan, each visibly different in colour and shape:
  meat_veg shows a clearly visible meat portion with roasted vegetables;
  veggie contains no meat or fish at all; family is a kid-friendly classic
  (e.g. pasta, tacos, mild curry). Hero shows one generous plated dish.
Your final response must say that
final.html and the four final images are ready.

Brand guide:
{BRAND_GUIDE}

Reactivation reference:
{REACTIVATION_REFERENCE}
""",
    tools=[generate_final],
    output_key="revision_summary",
)


root_agent = SequentialAgent(
    name="reactivation_page",
    description="Creates, critiques, and revises a personalised reactivation page.",
        sub_agents=[creator, critic, revisor],
)

app = App(name="app", root_agent=root_agent)
