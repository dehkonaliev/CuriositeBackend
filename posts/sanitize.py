import bleach
from bleach.css_sanitizer import CSSSanitizer

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "h1", "h2", "h3", "h4",
    "ul", "ol", "li", "a", "img", "blockquote", "code", "pre", "span",
]
ALLOWED_ATTRS = {
    "a": ["href", "target", "rel"],
    "img": ["src", "alt", "width", "height"],
    "*": ["style", "class"],
}
CSS_SANITIZER = CSSSanitizer(
    allowed_css_properties=["font-size", "font-weight", "text-align", "color", "text-decoration"]
)


def sanitize_html(html: str) -> str:
    return bleach.clean(
        html or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        css_sanitizer=CSS_SANITIZER,
        strip=True,
    )