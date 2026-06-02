// 生成广场海滩场景的 4 套时段背景（base64 SVG → WXSS）。
// 运行：node miniprogram/assets/_gen-scene.js  → 写出 pages/act-plaza/scene.wxss
// 这是构建期一次性脚本，产物已提交，平时无需运行。
const fs = require('fs');
const path = require('path');

// 波浪/沙滩/泡沫 路径（照搬原型 SVG）
const P = {
  wv1: 'M0 312 C 90 292 150 332 230 312 C 300 296 350 326 390 312 L390 760 L0 760 Z',
  wf1: 'M0 312 C 90 292 150 332 230 312 C 300 296 350 326 390 312',
  wv2: 'M0 372 C 80 350 160 394 250 372 C 320 355 360 388 390 374 L390 760 L0 760 Z',
  wf2: 'M0 372 C 80 350 160 394 250 372 C 320 355 360 388 390 374',
  wv3: 'M0 442 C 100 417 170 464 260 442 C 330 425 360 456 390 444 L390 760 L0 760 Z',
  wf3: 'M0 442 C 100 417 170 464 260 442 C 330 425 360 456 390 444',
  wv4: 'M0 512 C 90 488 180 534 270 512 C 340 496 365 524 390 514 L390 760 L0 760 Z',
  wf4: 'M0 512 C 90 488 180 534 270 512 C 340 496 365 524 390 514',
  beach: 'M0 588 C 110 568 210 608 300 588 C 345 578 370 596 390 588 L390 760 L0 760 Z',
  beachFoam: 'M0 588 C 110 568 210 608 300 588 C 345 578 370 596 390 588'
};
const DOTS = [
  [60, 320, 3], [300, 318, 3.5],
  [200, 382, 3], [330, 378, 2.5], [90, 386, 2],
  [150, 452, 3.5], [280, 448, 2.5], [340, 456, 3],
  [70, 524, 3], [210, 534, 2.5], [320, 522, 3.5]
];

// 各时段配色（照搬原型 .scene.day/.dawn/.dusk/.night）
const THEMES = {
  dawn:  { sky: '#e4e6e0', sun: '#f0e2c8', sea: '#92a6a2', wv: ['#bac8c2', '#a9b9b4', '#98aaa5', '#8a9d98'], beach: '#eae0cb', foam: '#f4efe6' },
  day:   { sky: '#dfe7e6', sun: '#e9d9b8', sea: '#7f9b9b', wv: ['#aabbb8', '#98aeac', '#88a09f', '#7a9492'], beach: '#e7dcc6', foam: '#f4efe6' },
  dusk:  { sky: '#e0b196', sun: '#e6b48c', sea: '#8a7f86', wv: ['#b59a96', '#a68d8c', '#977f84', '#88727b'], beach: '#d8bfa1', foam: '#f6ece0' },
  night: { sky: '#2a3338', sun: '#e3dccd', sea: '#313d40', wv: ['#46555a', '#3f4d51', '#384549', '#313d40'], beach: '#3a3a36', foam: '#cdc7ba' }
};

function svgFor(t) {
  const dots = DOTS.map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${t.foam}"/>`).join('');
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 390 760" preserveAspectRatio="xMidYMid slice">`,
    `<rect x="0" y="0" width="390" height="300" fill="${t.sky}"/>`,
    `<circle cx="250" cy="120" r="34" fill="${t.sun}"/>`,
    `<rect x="0" y="296" width="390" height="464" fill="${t.sea}"/>`,
    `<path d="${P.wv1}" fill="${t.wv[0]}"/>`,
    `<path d="${P.wv2}" fill="${t.wv[1]}"/>`,
    `<path d="${P.wv3}" fill="${t.wv[2]}"/>`,
    `<path d="${P.wv4}" fill="${t.wv[3]}"/>`,
    `<path d="${P.wf1}" fill="none" stroke="${t.foam}" stroke-width="3" stroke-linecap="round"/>`,
    `<path d="${P.wf2}" fill="none" stroke="${t.foam}" stroke-width="3" stroke-linecap="round"/>`,
    `<path d="${P.wf3}" fill="none" stroke="${t.foam}" stroke-width="3" stroke-linecap="round"/>`,
    `<path d="${P.wf4}" fill="none" stroke="${t.foam}" stroke-width="3" stroke-linecap="round"/>`,
    dots,
    `<path d="${P.beach}" fill="${t.beach}"/>`,
    `<path d="${P.beachFoam}" fill="none" stroke="${t.foam}" stroke-width="3" stroke-linecap="round"/>`,
    `</svg>`
  ].join('');
}

let out = '/* 自动生成：广场海滩场景背景（由 assets/_gen-scene.js 生成，勿手改）*/\n';
for (const name of Object.keys(THEMES)) {
  const b64 = Buffer.from(svgFor(THEMES[name])).toString('base64');
  out += `.scene.t-${name}{background-image:url("data:image/svg+xml;base64,${b64}");}\n`;
}
fs.writeFileSync(path.join(__dirname, '..', 'pages', 'act-plaza', 'scene.wxss'), out);
console.log('scene.wxss written');
