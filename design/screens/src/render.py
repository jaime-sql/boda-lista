import asyncio,sys,glob,os
from playwright.async_api import async_playwright
D='/workspace/hack-ux/boda-lista/screens'
async def main():
    files=sys.argv[1:] or [os.path.basename(f)[:-5] for f in sorted(glob.glob(D+'/*.html'))]
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        for k in files:
            w=1440 if (k.startswith('couple') or k.endswith('desktop')) else 390
            pg=await b.new_page(viewport={'width':w,'height':900})
            await pg.goto(f'file://{D}/{k}.html',wait_until='networkidle')
            await pg.evaluate('document.fonts.ready')
            fams=await pg.evaluate('[...new Set([...document.fonts].filter(f=>f.status=="loaded").map(f=>f.family))]')
            sw=await pg.evaluate('document.documentElement.scrollWidth')
            # elements overflowing horizontally
            ov=await pg.evaluate('''(()=>{const W=document.documentElement.clientWidth;return [...document.querySelectorAll("body *")].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.right>W+1)}).slice(0,5).map(e=>e.tagName+"."+e.className+" r="+Math.round(e.getBoundingClientRect().right))})()''')
            clip=await pg.evaluate('''[...document.querySelectorAll("body *")].filter(e=>{const s=getComputedStyle(e);return (e.scrollWidth>e.clientWidth+1)&&s.overflow!="visible"&&e.tagName!="svg"}).slice(0,5).map(e=>e.tagName+"."+e.className)''')
            small=await pg.evaluate('''[...new Set([...document.querySelectorAll("body *")].filter(e=>[...e.childNodes].some(n=>n.nodeType==3&&n.textContent.trim())&&parseFloat(getComputedStyle(e).fontSize)<16).map(e=>e.tagName+"."+e.className+":"+getComputedStyle(e).fontSize))]''')
            print(k,w,'fonts',fams,'scrollW',sw,'overflowR',ov,'clip',clip,'<16px',small[:6])
            await pg.screenshot(path=f'{D}/png/{k}.png',full_page=True)
        await b.close()
asyncio.run(main())
