import glob

html_files = glob.glob('*.html')

nav_item = '<li><a href="testimoni.html">Testimoni</a></li>'
nav_item_insert = '<li><a href="blog.html">Blog</a></li>'

mobile_item = '<a href="testimoni.html">Testimoni</a>'
mobile_item_insert = '<a href="blog.html">Blog</a>'

footer_item = '<li><a href="testimoni.html">Testimoni</a></li>'
# Same insert

for file in html_files:
    if file.startswith('blog'): 
        continue # Already added in blog files manually
    if file == 'googlebdeee5b0ea130b46.html':
        continue
        
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Inject into nav
    if nav_item in content and nav_item_insert not in content:
        content = content.replace(nav_item, f'{nav_item}\n                    {nav_item_insert}')
        
    # Inject into mobile
    if mobile_item in content and mobile_item_insert not in content:
        content = content.replace(mobile_item, f'{mobile_item}\n                    {mobile_item_insert}')
        
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Updated links in {file}")
