// Mermaid diagram rendering for mdbook
(function () {
  "use strict";

  function renderMermaid() {
    // mdbook renders fenced code blocks as <code class="language-mermaid">
    var blocks = document.querySelectorAll("code.language-mermaid");
    if (blocks.length === 0) return;

    blocks.forEach(function (code) {
      var pre = code.parentElement;
      var content = code.textContent;

      // Create a div for mermaid to render into
      var div = document.createElement("div");
      div.className = "mermaid";
      div.textContent = content;

      // Replace the <pre><code> with the mermaid div
      pre.parentElement.replaceChild(div, pre);
    });

    // Initialize mermaid (loaded via additional-js)
    if (typeof mermaid !== "undefined") {
      mermaid.initialize({
        startOnLoad: false,
        theme: "neutral",
        securityLevel: "loose",
        flowchart: { useMaxWidth: true, htmlLabels: true },
      });
      mermaid.run();
    }
  }

  // Run after mdbook content is loaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderMermaid);
  } else {
    renderMermaid();
  }
})();
