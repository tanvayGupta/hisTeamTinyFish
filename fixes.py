"""Small, evidence-led fix templates for report findings."""

import json
from html import escape


def fix_for(finding_id: str, fetch, url: str) -> tuple[str, str | None]:
    title = (fetch.raw_title or "Page title").strip()
    description = fetch.meta_description or "A concise description of this page's main topic and value."
    if finding_id in {"no_title", "weak_title"}:
        suggested = title if 20 <= len(title) <= 65 else "Clear page title | Main topic and audience"
        return ("Add a concise, descriptive title between 20 and 65 characters.",
                f"<title>{escape(suggested)}</title>")
    if finding_id == "no_meta_description":
        return ("Add a unique 70–160 character summary in the document head.",
                f'<meta name="description" content="{escape(description, quote=True)}">')
    if finding_id == "no_json_ld":
        data = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": url}
        return ("Add accurate structured data that describes this page.",
                '<script type="application/ld+json">\n' + json.dumps(data, indent=2) + "\n</script>")
    if finding_id == "image_alt":
        return ("Write meaningful alt text for informative images; use empty alt for decorative images.",
                '<img src="image.jpg" alt="Describe the information this image conveys">')
    if finding_id in {"extraction_gap", "js_dependent"}:
        return ("Render the main page text and headings in the initial HTML, or provide reliable server-side/pre-rendered HTML to crawlers.",
                None)
    if finding_id == "not_ranking":
        return ("Align the page title, headings, and introductory copy with the target query, then ensure the page is crawlable and internally linked.", None)
    if finding_id == "outranked":
        return ("Make the page's distinct answer to the target query explicit in its title, headings, and opening paragraph.", None)
    return ("Review the evidence and update the page content or metadata accordingly.", None)
