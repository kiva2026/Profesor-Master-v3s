"""
modules/ui/svg_renderer.py — Procesarea și randarea SVG.

Funcții mutate din app.py:
  - repair_unclosed_tags()
  - repair_svg()
  - validate_svg()
  - sanitize_svg()
  - render_message_with_svg()
"""
import re
import streamlit as st
import streamlit.components.v1 as components

# lxml pentru parsare robustă — fallback la regex dacă nu e disponibil
try:
    from lxml import etree as _lxml_etree
    _LXML_AVAILABLE = True
except ImportError:
    _LXML_AVAILABLE = False


# ──────────────────────────────────────────────────────────────────
# Reparare SVG
# ──────────────────────────────────────────────────────────────────

def repair_unclosed_tags(svg_content: str) -> str:
    """Repară tag-uri SVG comune care nu sunt închise corect."""
    self_closing_tags = [
        'path', 'rect', 'circle', 'ellipse', 'line',
        'polyline', 'polygon', 'image', 'use'
    ]

    for tag in self_closing_tags:
        pattern = rf'<{tag}(\s[^>]*)?>(?!</{tag}>)'

        def fix_tag(match, _tag=tag):
            attrs = match.group(1) or ""
            if attrs.rstrip().endswith('/'):
                return match.group(0)
            return f'<{_tag}{attrs}/>'

        svg_content = re.sub(pattern, fix_tag, svg_content)

    text_opens  = len(re.findall(r'<text[^>]*>', svg_content))
    text_closes = len(re.findall(r'</text>', svg_content))
    if text_opens > text_closes:
        for _ in range(text_opens - text_closes):
            svg_content = svg_content.replace('</svg>', '</text></svg>')

    g_opens  = len(re.findall(r'<g[^>]*>', svg_content))
    g_closes = len(re.findall(r'</g>', svg_content))
    if g_opens > g_closes:
        for _ in range(g_opens - g_closes):
            svg_content = svg_content.replace('</svg>', '</g></svg>')

    return svg_content


def repair_svg(svg_content: str) -> str | None:
    """Repară SVG incomplet sau malformat.

    Încearcă mai întâi cu lxml (parser XML tolerant),
    fallback la regex dacă lxml eșuează sau nu e disponibil.
    """
    if not svg_content:
        return None

    svg_content = svg_content.strip()

    # Asigură tag-uri <svg> deschis/închis
    has_svg_open  = bool(re.search(r'<svg[^>]*>', svg_content, re.IGNORECASE))
    has_svg_close = '</svg>' in svg_content.lower()

    if not has_svg_open:
        svg_content = (
            '<svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg" '
            'style="max-width:100%;height:auto;">\n'
            + svg_content + '\n</svg>'
        )
    elif has_svg_open and not has_svg_close:
        svg_content += '\n</svg>'

    if 'xmlns=' not in svg_content:
        svg_content = svg_content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    if 'viewBox=' not in svg_content.lower():
        svg_content = svg_content.replace('<svg', '<svg viewBox="0 0 800 600"', 1)

    # Încearcă repararea cu lxml
    if _LXML_AVAILABLE:
        try:
            parser = _lxml_etree.XMLParser(
                recover=True,
                remove_comments=False,
                resolve_entities=False,
                ns_clean=True,
            )
            root    = _lxml_etree.fromstring(svg_content.encode("utf-8"), parser)
            repaired = _lxml_etree.tostring(
                root,
                pretty_print=True,
                encoding="unicode",
                xml_declaration=False,
            )
            return repaired
        except Exception:
            pass

    # Fallback regex
    return repair_unclosed_tags(svg_content)


# ──────────────────────────────────────────────────────────────────
# Validare SVG
# ──────────────────────────────────────────────────────────────────

def validate_svg(svg_content: str) -> tuple[bool, str]:
    """Validează SVG și returnează (is_valid, error_message)."""
    if not svg_content:
        return False, "SVG gol"

    visual_elements = [
        'path', 'rect', 'circle', 'ellipse', 'line',
        'text', 'polygon', 'polyline', 'image'
    ]

    if _LXML_AVAILABLE:
        try:
            parser = _lxml_etree.XMLParser(recover=True)
            _lxml_etree.fromstring(svg_content.encode("utf-8"), parser)
            has_content = any(f'<{el}' in svg_content.lower() for el in visual_elements)
            if not has_content:
                return False, "SVG fără elemente vizuale"
            return True, "OK"
        except Exception:
            pass

    # Fallback validare simplă
    if '<svg' not in svg_content.lower():
        return False, "Lipsește tag-ul <svg>"
    if '</svg>' not in svg_content.lower():
        return False, "Lipsește tag-ul </svg>"
    if not any(f'<{el}' in svg_content.lower() for el in visual_elements):
        return False, "SVG fără elemente vizuale"
    return True, "OK"


# ──────────────────────────────────────────────────────────────────
# Sanitizare SVG (XSS prevention)
# ──────────────────────────────────────────────────────────────────

def sanitize_svg(svg_content: str) -> str:
    """Sanitizează SVG — elimină scripturi și event handlers (XSS prevention)."""
    if not svg_content:
        return svg_content

    # Elimină <script> complet
    svg_content = re.sub(
        r'<script\b[^>]*>.*?</script\s*>', '', svg_content,
        flags=re.DOTALL | re.IGNORECASE
    )
    # Elimină event handlers on* cu ghilimele duble
    svg_content = re.sub(r'\s+on[a-zA-Z]+\s*=\s*"[^"]*"', '', svg_content)
    # Elimină event handlers on* cu ghilimele simple
    svg_content = re.sub(r"\s+on[a-zA-Z]+\s*=\s*'[^']*'", '', svg_content)
    # Elimină event handlers on* cu backtick
    svg_content = re.sub(r'\s+on[a-zA-Z]+\s*=\s*`[^`]*`', '', svg_content)
    # Elimină href=javascript:
    svg_content = re.sub(
        r'(xlink:)?href\s*=\s*["\']?\s*javascript:[^"\'>\s]*["\']?', '',
        svg_content, flags=re.IGNORECASE
    )
    # Elimină <use href="data:...">
    svg_content = re.sub(
        r'<use\b[^>]*href\s*=\s*["\']data:[^"\']*["\'][^>]*>', '',
        svg_content, flags=re.IGNORECASE
    )
    # Elimină style cu behavior: sau expression(
    svg_content = re.sub(
        r'style\s*=\s*["\'][^"\']*(?:behavior|expression)\s*:[^"\']*["\']', '',
        svg_content, flags=re.IGNORECASE
    )
    # Elimină <foreignObject>
    svg_content = re.sub(
        r'<foreignObject\b.*?</foreignObject\s*>', '', svg_content,
        flags=re.DOTALL | re.IGNORECASE
    )
    return svg_content


# ──────────────────────────────────────────────────────────────────
# Randare mesaj cu suport SVG
# ──────────────────────────────────────────────────────────────────

def render_message_with_svg(content: str):
    """Randează mesajul cu suport îmbunătățit pentru SVG."""
    has_svg_markers   = '[[DESEN_SVG]]' in content
    has_svg_elements  = bool(re.search(r'<svg\b[^>]*>.*?</svg\s*>', content, re.DOTALL | re.IGNORECASE))
    has_svg_sub       = any(tag in content.lower() for tag in ['<path', '<rect', '<circle', '<line', '<polygon'])

    if has_svg_markers or has_svg_elements or (has_svg_sub and 'stroke=' in content):
        svg_code   = None
        before_text = ""
        after_text  = ""

        if '[[DESEN_SVG]]' in content:
            parts = content.split('[[DESEN_SVG]]')
            before_text = parts[0]
            if len(parts) > 1 and '[[/DESEN_SVG]]' in parts[1]:
                inner = parts[1].split('[[/DESEN_SVG]]')
                svg_code   = inner[0]
                after_text = inner[1] if len(inner) > 1 else ""
            elif len(parts) > 1:
                svg_code = parts[1]
        elif '<svg' in content.lower():
            svg_match = re.search(r'<svg.*?</svg>', content, re.DOTALL | re.IGNORECASE)
            if svg_match:
                svg_code   = svg_match.group(0)
                before_text = content[:svg_match.start()]
                after_text  = content[svg_match.end():]
            else:
                svg_start = content.lower().find('<svg')
                if svg_start != -1:
                    before_text = content[:svg_start]
                    svg_code    = content[svg_start:]

        if svg_code:
            svg_code = sanitize_svg(svg_code)
            svg_code = repair_svg(svg_code)

            # Injectăm <style> direct în SVG
            _dark_svg     = st.session_state.get("dark_mode", False)
            _style_inject = (
                "<style>"
                "svg{background:transparent!important}"
                "rect[id='bg'],rect[id='background'],rect.bg,rect.background{display:none!important}"
                + ("text{fill:#e0e0e0!important}" if _dark_svg else "")
                + "</style>"
            )
            svg_code = re.sub(r'(<svg[^>]*>)', r'\1' + _style_inject, svg_code, count=1)
            is_valid, error = validate_svg(svg_code)

            if is_valid:
                if before_text.strip():
                    st.markdown(before_text.strip())

                _is_dark = st.session_state.get("dark_mode", False)
                _bg      = "#0e1117" if _is_dark else "#ffffff"
                _text    = "#fafafa" if _is_dark else "#1a1a1a"
                components.html(
                    f'''<style>
                    html,body{{margin:0;padding:0;background:{_bg};}}
                    .svg-wrap{{background:{_bg};width:100%;padding:10px 4px;box-sizing:border-box;border-radius:8px;}}
                    svg{{background:transparent!important;max-width:100%;height:auto;}}
                    svg text{{fill:{_text}!important;}}
                    svg rect[fill="white"],svg rect[fill="#fff"],svg rect[fill="#ffffff"]{{fill:{_bg}!important;}}
                    </style>
                    <div class="svg-wrap">{svg_code}</div>''',
                    height=650,
                    scrolling=False,
                )

                if after_text.strip():
                    st.markdown(after_text.strip())
                return
            else:
                st.warning(f"⚠️ Desenul nu a putut fi afișat corect: {error}")

    # Fallback — afișare normală markdown, curățăm markerii SVG
    clean_content = re.sub(r'\[\[DESEN_SVG\]\]', '\n🎨 *Desen:*\n', content)
    clean_content = re.sub(r'\[\[/DESEN_SVG\]\]', '\n', clean_content)
    st.markdown(clean_content)
