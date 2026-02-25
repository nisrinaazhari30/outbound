import os
import glob
from bs4 import BeautifulSoup
import urllib.parse
import re

def optimize_html(filepath):
    print(f"Optimizing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    head = soup.head
    if not head:
        return # Skip if no head

    # 1. DNS Prefetch & Preconnect
    domains = [
        ("https://fonts.googleapis.com", True),
        ("https://fonts.gstatic.com", True),
        ("https://images.unsplash.com", False),
        ("https://cdnjs.cloudflare.com", False)
    ]
    
    for domain, is_crossorigin in domains:
        # Check preconnect
        if not soup.find('link', attrs={'rel': 'preconnect', 'href': domain}):
            link = soup.new_tag('link', rel='preconnect', href=domain)
            if is_crossorigin:
                link['crossorigin'] = ''
            head.append(link)
        
        # Check dns-prefetch
        if not soup.find('link', attrs={'rel': 'dns-prefetch', 'href': domain}):
            link = soup.new_tag('link', rel='dns-prefetch', href=domain)
            head.append(link)

    # 2. Defer Font Awesome
    fa_links = soup.find_all('link', attrs={'rel': 'stylesheet'})
    for link in fa_links:
        href = link.get('href', '')
        if 'font-awesome' in href or 'all.min.css' in href:
            if link.get('media') != 'print':
                link['media'] = 'print'
                link['onload'] = "this.media='all'"
                
                # Add noscript fallback
                noscript = soup.new_tag('noscript')
                fallback_link = soup.new_tag('link', rel='stylesheet', href=href)
                noscript.append(fallback_link)
                link.insert_after(noscript)

    # 3. Image Optimization (CLS & FCP/LCP)
    images = soup.find_all('img')
    first_image_found = False
    
    for i, img in enumerate(images):
        src = img.get('src', '')
        
        # Add decoding="async"
        img['decoding'] = 'async'
        
        # Handle LCP / Lazy loading
        # If it's the very first image of the page (and not a tiny logo or icon), it might be LCP
        # Logo usually has 'logo' in class or something. Let's just say first large image.
        is_large = 'unsplash' in src or 'hero' in src.lower() or i == 0
        
        # Remove lazy if it's the first image in body (potential LCP)
        if not first_image_found and is_large and not src.endswith('.svg') and not 'logo' in src.lower():
            if img.get('loading') == 'lazy':
                del img['loading']
            
            # Add preload for this LCP image
            if src and not src.startswith('data:'):
                if not soup.find('link', attrs={'rel': 'preload', 'href': src}):
                    preload = soup.new_tag('link', rel='preload', **{'as': 'image'}, href=src)
                    head.append(preload)
                    
            first_image_found = True
        else:
            # Ensure other images are lazy loaded
            img['loading'] = 'lazy'
            
        # Extract width & height from Unsplash URLs to prevent CLS
        if 'unsplash.com' in src:
            parsed = urllib.parse.urlparse(src)
            qs = urllib.parse.parse_qs(parsed.query)
            
            w = qs.get('w', [''])[0]
            if w and not img.get('width'):
                img['width'] = w
                
            h = qs.get('h', [''])[0]
            if h and not img.get('height'):
                img['height'] = h
                
            # If w exists but not h, guess the ratio. By default many are 3:2 landscape
            if w and not h and not img.get('height'):
                img['height'] = str(int(int(w) * 2 / 3))

    # Save to file
    # We use prettify / str to convert back
    # BeautifulSoup can mess up some formatting, we'll try to keep it as raw string where possible
    # but since we made DOM changes, str(soup) is required.
    
    # We will format it slightly nicer
    out_html = str(soup)
    
    # Optional: basic minification (removing excessive empty lines)
    out_html = re.sub(r'\n\s*\n', '\n', out_html)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(out_html)
    print(f"Saved {filepath}")

if __name__ == '__main__':
    for filepath in glob.glob('*.html'):
        optimize_html(filepath)
