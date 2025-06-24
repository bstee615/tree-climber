# 2025-06-24-cytoscape-tippy-setup-guide.md

## Why Tippy.js?
Tippy.js is a modern, dependency-free tooltip library that works well with Cytoscape.js and React. It is a good replacement for qTip2.

## Install
From your frontend directory:

```
bun add tippy.js
```

## Usage Example

```js
import tippy from 'tippy.js';
import 'tippy.js/dist/tippy.css';

// In your Cytoscape setup:
function addTippyToNode(node, content) {
  const ref = node.popperRef(); // used only for positioning
  tippy(document.createElement('div'), {
    getReferenceClientRect: ref.getBoundingClientRect,
    content,
    trigger: 'manual',
    placement: 'bottom',
    arrow: true,
    onShow(instance) {
      instance.setContent(content);
    },
  });
}
```

- You can show/hide the tooltip on mouseover/mouseout events.
- See the code update in `Graph.tsx` for a full example.

## References
- [Tippy.js Docs](https://atomiks.github.io/tippyjs/)
- [Cytoscape.js Popper Extension](https://github.com/cytoscape/cytoscape.js-popper)

---
