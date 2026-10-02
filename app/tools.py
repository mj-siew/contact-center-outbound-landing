"""Small file-producing tools used by the reactivation-page ADK workflow."""

import base64
import html
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from google.adk.tools import ToolContext
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "tmp"
OUTPUT_DIR.mkdir(exist_ok=True)


IMAGE_STYLE = (
    " Photographic style: realistic editorial food photography, natural soft window"
    " daylight from the left, light oak or pale linen surface, fresh herbs and raw"
    " ingredients scattered naturally, shallow depth of field, warm true-to-life"
    " colours, appetising modern home plating. Absolutely no text, letters,"
    " numbers, logos, packaging, badges, watermarks, hands, or faces."
)


def _write_image(filename: str, prompt: str) -> None:
    """Create one image with the OpenAI Image API."""
    is_hero = filename.startswith("hero")
    framing = (
        " Wide landscape composition, 45-degree angle, hero dish placed right of"
        " centre with generous margin on every side so a tall crop keeps the whole"
        " plate; keep the lower-left corner plain for a small badge."
        if is_hero
        else " Landscape 3:2, slight top-down angle, single plated dish centred,"
        " matte white plate, same oak table for every dish."
    )
    response = OpenAI().images.generate(
        model="gpt-image-2.5-sunburst",
        prompt=prompt + framing + IMAGE_STYLE,
        size="1536x1024",
        quality="medium",
    )
    image_data = response.data[0].b64_json
    if not image_data:
        raise RuntimeError("The OpenAI Image API returned no image data.")
    (OUTPUT_DIR / filename).write_bytes(base64.b64decode(image_data))


def _write_images(jobs: list[tuple[str, str]]) -> None:
    """Create several images in parallel (one image call's wall time)."""
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        for result in pool.map(lambda job: _write_image(*job), jobs):
            pass


LOGO_FILE = "HelloFresh_Logo_2020.png"
CTA_HREF = "#reactivate-placeholder"


def _copy_logo() -> None:
    """Copy the user-supplied logo next to the generated HTML."""
    src = PROJECT_ROOT / "assets" / LOGO_FILE
    if src.exists():
        (OUTPUT_DIR / LOGO_FILE).write_bytes(src.read_bytes())


def _split_benefits(benefits: str) -> list[tuple[str, str]]:
    """Parse three 'Title: body' lines."""
    out = []
    for line in benefits.splitlines():
        line = line.strip().lstrip("-•* ").strip()
        if not line:
            continue
        title, _, body = line.partition(":")
        out.append((title.strip(), body.strip()))
    return out[:3]


def _split_faq(faq: str) -> list[tuple[str, str]]:
    """Parse 'Question? | Answer' lines."""
    out = []
    for line in faq.splitlines():
        line = line.strip()
        if not line:
            continue
        q, _, a = line.partition("?")
        out.append((q.strip() + "?", a.strip().lstrip("|").strip()))
    return out[:3]


def _page_html(
    *,
    customer_context: str,
    headline: str,
    subheadline: str,
    message: str,
    offer: str,
    benefits: str,
    pricing: str,
    cta: str,
    faq: str,
    hero_image: str,
    food_image_1: str,
    food_image_2: str,
    food_image_3: str,
) -> str:
    """Render the self-contained English reactivation landing page."""
    e = html.escape
    benefit_rows = "".join(
        f'<li><span class="icon">{ICONS[i % 3]}</span><div>'
        + (f"<h3>{e(t)}</h3>" if t else "")
        + f"<p>{e(b)}</p></div></li>"
        for i, (t, b) in enumerate(_split_benefits(benefits))
    )
    faq_items = "".join(
        f"<details><summary>{e(q or a[:60])}</summary><p>{e(a)}</p></details>"
        for q, a in _split_faq(faq)
    )
    food = [food_image_1, food_image_2, food_image_3]
    plan_cards = "".join(
        f'<article class="plan">'
        + f'<img src="{e(food[i])}" alt="Sample dish {name}" loading="lazy">'
        + f"<h3>{name}</h3><p class=\"tag\">{tag}</p><p>{desc}</p></article>"
        for i, (name, tag, desc) in enumerate(PLANS)
    )
    cta_html = f'<a class="cta" href="{CTA_HREF}">{e(cta)}</a>'
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>HelloFresh — {e(headline)}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
      :root {{
        --leaf: #106b36; --leaf-dark: #0a4f27; --lime: #96dc14; --lime-soft: #eef8d9;
        --ink: #1d2a21; --muted: #4a5a4f; --line: #dfe8d6; --white: #fff;
        --display: "Figtree", "Segoe UI", system-ui, sans-serif;
        --body: "Figtree", "Segoe UI", system-ui, sans-serif;
        --radius: 20px; --wrap: min(1160px, 100% - 48px);
      }}
      * {{ box-sizing: border-box; }}
      html {{ scroll-behavior: smooth; }}
      body {{ margin: 0; background: var(--white); color: var(--ink); font: 17px/1.6 var(--body); -webkit-font-smoothing: antialiased; }}
      ::selection {{ background: var(--lime); color: var(--ink); }}
      :focus-visible {{ outline: 3px solid var(--lime); outline-offset: 3px; border-radius: 6px; }}
      .skip {{ position: absolute; left: -999px; }} .skip:focus {{ left: 16px; top: 16px; background: var(--white); padding: 8px 14px; z-index: 9; }}
      .wrap {{ width: var(--wrap); margin-inline: auto; }}
      h1, h2, h3 {{ font-family: var(--display); letter-spacing: -0.025em; text-wrap: balance; margin: 0; }}
      h1 {{ font-size: clamp(2.35rem, 5vw, 4.1rem); line-height: 1.04; font-weight: 700; }}
      h2 {{ font-size: clamp(1.9rem, 3.3vw, 2.75rem); line-height: 1.08; font-weight: 700; }}
      h3 {{ font-size: 1.3rem; line-height: 1.2; font-weight: 600; }}
      p {{ margin: 0; }}

      .site-header {{ border-bottom: 1px solid var(--line); background: var(--white); position: sticky; top: 0; z-index: 5; }}
      .site-header .wrap {{ display: flex; align-items: center; justify-content: space-between; height: 72px; }}
      .site-header img {{ height: 38px; width: auto; display: block; }}
      .login {{ color: var(--ink); font-weight: 700; text-decoration: none; padding: 8px 18px; border: 2px solid var(--ink); border-radius: 999px; }}
      .login:hover {{ background: var(--ink); color: var(--white); }}

      .cta {{ display: inline-flex; align-items: center; gap: 10px; background: var(--leaf); color: var(--white); font-weight: 700; font-size: 1.1rem; line-height: 1.3; text-decoration: none; padding: 17px 30px; border-radius: 999px; box-shadow: 0 8px 20px -8px #0a4f2799; transition: background .2s, transform .2s cubic-bezier(.2,.8,.2,1); }}
      .cta::after {{ content: ""; width: 18px; height: 18px; flex: none; background: currentColor; mask: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>') center/contain no-repeat; transition: transform .2s; }}
      .cta:hover {{ background: var(--leaf-dark); transform: translateY(-2px); }} .cta:hover::after {{ transform: translateX(3px); }}

      .hero {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.05fr); min-height: min(680px, 86vh); background: var(--lime-soft); }}
      .hero-copy {{ align-self: center; padding: 64px 56px 64px max(24px, calc((100vw - 1160px) / 2)); display: grid; gap: 22px; justify-items: start; }}
      .hello {{ font-size: 1.15rem; color: var(--muted); max-width: 34ch; }}
      .hero .sub {{ font-size: 1.25rem; max-width: 30ch; }}
      .hero-media {{ position: relative; overflow: hidden; }}
      .hero-media img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
      .badge {{ position: absolute; left: 28px; bottom: 28px; width: 156px; aspect-ratio: 1.18; display: grid; place-content: center; text-align: center; background: var(--lime); color: var(--ink); border-radius: 58% 42% 55% 45% / 52% 48% 52% 48%; transform: rotate(-12deg); box-shadow: 0 14px 30px -12px #1d2a2166; font-family: var(--display); }}
      .badge b {{ font-size: 2.7rem; line-height: .9; font-weight: 800; letter-spacing: -0.04em; }}
      .badge span {{ font-size: .95rem; font-weight: 600; }}
      .fine-hint {{ font-size: .9rem; color: var(--muted); }}

      section.block {{ padding: clamp(72px, 9vw, 120px) 0; }}
      .listened .wrap {{ display: grid; grid-template-columns: 0.9fr 1.1fr; gap: clamp(40px, 6vw, 96px); align-items: start; }}
      .listened .lead {{ display: grid; gap: 18px; position: sticky; top: 110px; }}
      .listened .lead p {{ color: var(--muted); font-size: 1.15rem; max-width: 36ch; }}
      .benefits {{ list-style: none; margin: 0; padding: 0; display: grid; }}
      .benefits li {{ display: grid; grid-template-columns: 56px 1fr; gap: 20px; padding: 28px 0; border-top: 1px solid var(--line); }}
      .benefits li:last-child {{ border-bottom: 1px solid var(--line); }}
      .benefits h3 {{ margin-bottom: 6px; }}
      .benefits p {{ color: var(--muted); max-width: 60ch; }}
      .icon {{ width: 56px; height: 56px; border-radius: 50%; background: var(--lime-soft); display: grid; place-items: center; }}
      .icon svg {{ width: 28px; height: 28px; fill: none; stroke: var(--leaf); stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }}
      .icon .fill {{ fill: var(--leaf); stroke: none; }}

      .variety {{ background: var(--leaf); color: var(--white); }}
      .variety-head {{ display: flex; justify-content: space-between; align-items: end; gap: 32px; flex-wrap: wrap; margin-bottom: 48px; }}
      .variety-head p {{ max-width: 38ch; color: #d9ecd0; font-size: 1.15rem; }}
      .big-num {{ color: var(--lime); }}
      .plans {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }}
      .plan {{ background: var(--white); color: var(--ink); border-radius: var(--radius); padding: 28px 18px 30px; display: grid; gap: 8px; align-content: start; }}
      .plan img, .plan-art {{ width: 100%; aspect-ratio: 4 / 3; object-fit: cover; border-radius: 12px; margin-bottom: 10px; }}
      .plan h3, .plan p {{ padding-inline: 10px; }}
      .plan .tag {{ font-size: .85rem; font-weight: 700; color: var(--leaf); text-transform: uppercase; letter-spacing: .06em; }}
      .plan p:last-child {{ color: var(--muted); }}
      .plan .icon {{ margin: 0 10px 12px; }}

      .steps {{ list-style: none; margin: 48px 0 0; padding: 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; counter-reset: s; position: relative; }}
      .steps::before {{ content: ""; position: absolute; top: 28px; left: 28px; right: 16%; border-top: 2px dashed var(--line); }}
      .steps li {{ counter-increment: s; display: grid; gap: 10px; position: relative; }}
      .steps li::before {{ content: counter(s); width: 56px; height: 56px; border-radius: 50%; background: var(--lime); display: grid; place-items: center; font: 800 1.4rem var(--display); margin-bottom: 8px; }}
      .steps p {{ color: var(--muted); max-width: 32ch; }}

      .terms {{ background: var(--lime-soft); }}
      .terms .wrap {{ display: grid; grid-template-columns: 0.9fr 1.1fr; gap: clamp(40px, 6vw, 96px); }}
      .terms-box {{ display: grid; gap: 28px; }}
      .terms-box > p {{ font-size: 1.1rem; }}
      details {{ background: var(--white); border-radius: 14px; padding: 4px 22px; }}
      details + details {{ margin-top: 10px; }}
      summary {{ cursor: pointer; font-weight: 700; padding: 16px 28px 16px 0; list-style: none; position: relative; }}
      summary::-webkit-details-marker {{ display: none; }}
      summary::after {{ content: "+"; position: absolute; right: 0; top: 12px; font: 600 1.5rem var(--display); color: var(--leaf); transition: transform .2s; }}
      details[open] summary::after {{ transform: rotate(45deg); }}
      details p {{ padding-bottom: 18px; color: var(--muted); }}

      .closing {{ text-align: center; }}
      .closing .wrap {{ display: grid; justify-items: center; gap: 22px; }}
      .closing p {{ font-size: 1.2rem; color: var(--muted); max-width: 44ch; }}

      footer {{ border-top: 1px solid var(--line); padding: 36px 0 48px; }}
      footer .wrap {{ display: grid; gap: 18px; }}
      footer img {{ height: 28px; width: auto; }}
      footer small {{ color: var(--muted); font-size: .82rem; line-height: 1.55; max-width: 110ch; }}

      @media (max-width: 860px) {{
        .hero {{ grid-template-columns: 1fr; min-height: 0; }}
        .hero-media {{ order: -1; aspect-ratio: 4 / 3; }}
        .hero-copy {{ padding: 40px 24px 56px; }}
        .badge {{ width: 104px; left: auto; right: 16px; bottom: 16px; }}
        .badge b {{ font-size: 2rem; }}
        .listened .wrap, .terms .wrap {{ grid-template-columns: 1fr; }}
        .listened .lead {{ position: static; }}
        .plans, .steps {{ grid-template-columns: 1fr; }}
        .steps::before {{ display: none; }}
        .cta {{ width: 100%; justify-content: center; }}
        .site-header img {{ height: 30px; }}
      }}
      @media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; scroll-behavior: auto !important; }} }}
    </style>
  </head>
  <body>
    <a class="skip" href="#main">Skip to main content</a>
    <header class="site-header">
      <div class="wrap">
        <img src="{LOGO_FILE}" alt="HelloFresh" width="117" height="38">
        <a class="login" href="{CTA_HREF}">Log in</a>
      </div>
    </header>
    <main id="main">
      <section class="hero">
        <div class="hero-copy">
          <h1>{e(headline)}</h1>
          <p class="sub">{e(subheadline)}</p>
          <p class="hello">{e(message)}</p>
          {cta_html}
          <p class="fine-hint">One-time, on your first box. Pause or cancel any time.*</p>
        </div>
        <div class="hero-media">
          <img src="{e(hero_image)}" alt="A freshly cooked HelloFresh meal on a light wooden table">
          <div class="badge" aria-hidden="true"><b>40%</b><span>off box 1</span></div>
        </div>
      </section>

      <section class="block listened">
        <div class="wrap">
          <div class="lead">
            <h2>You told us. We listened.</h2>
            <p>{e(offer)}</p>
          </div>
          <ul class="benefits">{benefit_rows}</ul>
        </div>
      </section>

      <section class="block variety">
        <div class="wrap">
          <div class="variety-head">
            <h2>Up to <span class="big-num">100 recipes</span><br>every week</h2>
            <p>Pick your meals after reactivating, to match your taste and your budget.</p>
          </div>
          <div class="plans">{plan_cards}</div>
        </div>
      </section>

      <section class="block how">
        <div class="wrap">
          <h2>How easy it is to come back</h2>
          <ol class="steps">
            <li><h3>Reactivate</h3><p>Log in on the app or desktop and follow the comeback offer.</p></li>
            <li><h3>Pick your meals</h3><p>Choose your favourite recipes and set your delivery schedule.</p></li>
            <li><h3>Cook &amp; enjoy</h3><p>Your box arrives at your door. Recipe card out, get cooking.</p></li>
          </ol>
        </div>
      </section>

      <section class="block terms">
        <div class="wrap">
          <h2>Good to know</h2>
          <div class="terms-box">
            <p>{e(pricing)}</p>
            <div>{faq_items}</div>
          </div>
        </div>
      </section>

      <section class="block closing" id="reactivate">
        <div class="wrap">
          <h2>Let's get cooking again.</h2>
          <p>Your comeback offer is waiting: 40% off your first box.</p>
          {cta_html}
        </div>
      </section>
    </main>
    <footer>
      <div class="wrap">
        <img src="{LOGO_FILE}" alt="HelloFresh" width="86" height="28">
        <small>*40% Rabatt gilt einmalig für die erste Box nach der Reaktivierung. Angebot nur für ehemalige HelloFresh-Kundinnen und -Kunden mit einem gekündigten Abo. Mit der Einlösung wird ein automatisch verlängerndes Abo aktiviert, das jederzeit pausiert oder gekündigt werden kann. Nicht mit anderen Aktionen kombinierbar.</small>
      </div>
    </footer>
  </body>
</html>
"""


def generate_draft(
    customer_context: str,
    headline: str,
    subheadline: str,
    message: str,
    offer: str,
    benefits: str,
    pricing: str,
    cta: str,
    faq: str,
    hero_image_prompt: str,
    food_image_prompt_1: str,
    food_image_prompt_2: str,
    food_image_prompt_3: str,
    tool_context: ToolContext,
) -> dict:
    """Generates the draft images and draft.html for the reactivation page."""
    jobs = [
        ("hero.png", hero_image_prompt),
        ("food_meat_veg.png", food_image_prompt_1),
        ("food_veggie.png", food_image_prompt_2),
        ("food_family.png", food_image_prompt_3),
    ]
    _write_images(jobs)
    _copy_logo()
    (OUTPUT_DIR / "draft.html").write_text(
        _page_html(
            customer_context=customer_context,
            headline=headline,
            subheadline=subheadline,
            message=message,
            offer=offer,
            benefits=benefits,
            pricing=pricing,
            cta=cta,
            faq=faq,
            hero_image="hero.png",
            food_image_1="food_meat_veg.png",
            food_image_2="food_veggie.png",
            food_image_3="food_family.png",
        ),
        encoding="utf-8",
    )
    tool_context.state["customer_context"] = customer_context
    tool_context.state["draft_path"] = "tmp/draft.html"
    tool_context.state["image_prompts"] = {
        "hero": hero_image_prompt,
        "meat_veg": food_image_prompt_1,
        "veggie": food_image_prompt_2,
        "family": food_image_prompt_3,
    }
    files = [
        "tmp/hero.png",
        "tmp/food_meat_veg.png",
        "tmp/food_veggie.png",
        "tmp/food_family.png",
        "tmp/draft.html",
    ]
    return {"status": "created", "files": files}


def read_draft(tool_context: ToolContext) -> dict:
    """Reads draft.html so it can be assessed before revision."""
    draft = OUTPUT_DIR / "draft.html"
    if not draft.exists():
        return {"status": "error", "message": "draft.html does not exist yet."}
    return {
        "status": "success",
        "html": draft.read_text(encoding="utf-8"),
        "image_prompts": tool_context.state.get("image_prompts", {}),
    }


def generate_final(
    headline: str,
    subheadline: str,
    message: str,
    offer: str,
    benefits: str,
    pricing: str,
    cta: str,
    faq: str,
    hero_image_prompt: str,
    food_image_prompt_1: str,
    food_image_prompt_2: str,
    food_image_prompt_3: str,
    tool_context: ToolContext,
) -> dict:
    """Generates the four final images and final.html from the critique-informed revision."""
    customer_context = str(
        tool_context.state.get("customer_context", "ehemaliger Kunde")
    )
    _write_images([
        ("hero_final.png", hero_image_prompt),
        ("food_meat_veg_final.png", food_image_prompt_1),
        ("food_veggie_final.png", food_image_prompt_2),
        ("food_family_final.png", food_image_prompt_3),
    ])
    _copy_logo()
    (OUTPUT_DIR / "final.html").write_text(
        _page_html(
            customer_context=customer_context,
            headline=headline,
            subheadline=subheadline,
            message=message,
            offer=offer,
            benefits=benefits,
            pricing=pricing,
            cta=cta,
            faq=faq,
            hero_image="hero_final.png",
            food_image_1="food_meat_veg_final.png",
            food_image_2="food_veggie_final.png",
            food_image_3="food_family_final.png",
        ),
        encoding="utf-8",
    )
    tool_context.state["final_path"] = "tmp/final.html"
    return {
        "status": "created",
        "files": [
            "tmp/hero_final.png",
            "tmp/food_meat_veg_final.png",
            "tmp/food_veggie_final.png",
            "tmp/food_family_final.png",
            "tmp/final.html",
        ],
    }
