// AI Systems Architect Book - Custom JavaScript
(function() {
  // Load Mermaid
  var script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js';
  script.onload = function() {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'neutral',
      securityLevel: 'loose',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", sans-serif',
    });
    console.log('Mermaid loaded');
  };
  document.head.appendChild(script);
})();
