import os
import glob
from bs4 import BeautifulSoup
import urllib.parse
import re

def minify_css(css):
    # remove comments
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    # remove newlines and extra spaces
    css = re.sub(r'\s+', ' ', css)
    # remove spaces around syntax characters
    css = re.sub(r'\s*([\{\}\:\;\,\>])\s*', r'\1', css)
    # remove trailing semicolons before closing brace
    css = re.sub(r';\}', '}', css)
    return css.strip()

def optimize_html(filepath):
    print(f"Optimizing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    head = soup.head
    if not head:
        return

    # 1. Minify CSS
    styles = soup.find_all('style')
    for style in styles:
        if style.string:
            style.string = minify_css(style.string)

    # 2. Add resource hints for unpkg/cdnjs/fonts
    domains = [
        ("https://fonts.googleapis.com", True),
        ("https://fonts.gstatic.com", True),
        ("https://images.unsplash.com", False),
        ("https://cdnjs.cloudflare.com", False)
    ]
    
    for domain, is_crossorigin in domains:
        if not soup.find('link', attrs={'rel': 'preconnect', 'href': domain}):
            link = soup.new_tag('link', rel='preconnect', href=domain)
            if is_crossorigin:
                link['crossorigin'] = ''
            head.insert(0, link)
            
    # 3. Defer ALL Google Fonts & Font Awesome
    stylesheets = soup.find_all('link', attrs={'rel': 'stylesheet'})
    for link in stylesheets:
        href = link.get('href', '')
        if 'fonts.googleapis' in href or 'font-awesome' in href or 'all.min.css' in href:
            if link.get('media') != 'print':
                # Add preload
                if not soup.find('link', attrs={'rel': 'preload', 'href': href}):
                    preload = soup.new_tag('link', rel='preload', href=href, **{'as': 'style'})
                    link.insert_before(preload)
                    if 'fonts.googleapis' in href and '&display=swap' not in href:
                        # try to add display=swap
                        pass

                # Defer the style
                link['media'] = 'print'
                link['onload'] = "this.media='all'"
                
                # Update existing noscript or add new one
                next_tag = link.find_next_sibling()
                if next_tag and next_tag.name == 'noscript':
                    pass
                else:
                    noscript = soup.new_tag('noscript')
                    fallback_link = soup.new_tag('link', rel='stylesheet', href=href)
                    noscript.append(fallback_link)
                    link.insert_after(noscript)

    # 4. Improve Image Delivery (Unsplash to WebP) & Lazy Load
    images = soup.find_all('img')
    first_image_found = False
    
    for i, img in enumerate(images):
        src = img.get('src', '')
        
        # Unsplash optimizations for format
        if 'unsplash.com' in src:
            parsed = urllib.parse.urlparse(src)
            qs = urllib.parse.parse_qs(parsed.query)
            
            # Add fm=webp and auto=format
            qs['fm'] = ['webp']
            qs['auto'] = ['format']
            if 'q' not in qs:
                qs['q'] = ['80']
                
            # Keep w & h or guess
            w = qs.get('w', [''])[0]
            if w and not img.get('width'):
                img['width'] = str(w)
            h = qs.get('h', [''])[0]
            if h and not img.get('height'):
                img['height'] = str(h)
            if w and not h and not img.get('height'):
                img['height'] = str(int(int(w) * 2 / 3))

            # reconstruct query
            new_query = urllib.parse.urlencode({k: v[0] for k, v in qs.items()})
            new_src = urllib.parse.urlunparse(parsed._replace(query=new_query))
            img['src'] = new_src
            src = new_src

        img['decoding'] = 'async'
        
        # Check LCP candidate
        is_large = ('unsplash' in src) or ('hero' in src.lower())
        # The very first meaningful image is LCP
        if not first_image_found and is_large and 'logo' not in src.lower() and not src.endswith('.svg'):
            if img.get('loading') == 'lazy':
                del img['loading']
            # Also add to preload header
            if not soup.find('link', attrs={'rel': 'preload', 'href': src}):
                preload = soup.new_tag('link', rel='preload', href=src, **{'as': 'image'})
                head.append(preload)
            img['fetchpriority'] = 'high'
            first_image_found = True
        else:
            if 'logo' not in src.lower() and not src.endswith('.svg') and img.get('loading') != 'lazy':
                img['loading'] = 'lazy'

    # Save format
    out_html = str(soup)
    # Basic HTML cleaner formatting without breaking minified css
    out_html = out_html.replace('</noscript><link', '</noscript>\n<link')
    out_html = out_html.replace('</style><script', '</style>\n<script')
    out_html = out_html.replace('</head><body', '</head>\n<body')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(out_html)
    print(f"Saved {filepath}")

if __name__ == '__main__':
    for filepath in ['index.html', 'paket-detail.html', 'tentang.html']:
        optimize_html(filepath)
