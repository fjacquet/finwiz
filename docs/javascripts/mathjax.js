// MathJax configuration for FinWiz documentation
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true,
    tags: 'ams',
    tagSide: 'right',
    tagIndent: '.8em',
    multlineWidth: '85%',
    autoload: {
      color: [],
      colorv2: ['color']
    }
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  },
  svg: {
    fontCache: 'global',
    scale: 1,
    minScale: 0.5,
    mtextInheritFont: false,
    merrorInheritFont: true,
    mathmlSpacing: false,
    skipAttributes: {},
    exFactor: 0.5,
    displayAlign: 'center',
    displayIndent: '0'
  },
  loader: {
    load: ['[tex]/ams', '[tex]/color', '[tex]/colorv2']
  }
};

// Initialize MathJax when document is ready
document$.subscribe(() => {
  MathJax.typesetPromise();
});
