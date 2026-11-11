// Render the two guides to PDF:  node docs/guide/render.js
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  for (const name of ['project_guide_technical', 'project_guide_plain']) {
    const page = await browser.newPage();
    await page.goto('file://' + path.join(__dirname, name + '.html'));
    const title = await page.title();
    await page.pdf({
      path: path.join(__dirname, '..', name + '.pdf'), format: 'A4', printBackground: true,
      displayHeaderFooter: true, headerTemplate: '<span></span>',
      footerTemplate: `<div style="font-family:Inter,sans-serif;font-size:7.5pt;color:#5b6675;width:100%;padding:0 18mm;display:flex;justify-content:space-between"><span>${title}</span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>`,
      margin: { top: '20mm', bottom: '20mm', left: '18mm', right: '18mm' },
    });
    await page.close();
    console.log('wrote', name + '.pdf');
  }
  await browser.close();
})();
