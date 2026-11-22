# Third-party notices

Boda Lista is Apache-2.0. The packages below are the direct dependencies in `package.json`. Their licenses are compatible with Apache-2.0 (MIT, Apache-2.0). Transitive packages are pinned in `package-lock.json`. A scan of installed packages found no copyleft-only licenses.

## Fonts

Self-hosted in `src/styles/fonts/` and `design/tokens/fonts/`. License texts: `OFL-Fraunces.txt` and `OFL-Figtree.txt`.

| Font | License | Source |
| --- | --- | --- |
| Fraunces | SIL Open Font License 1.1 | https://github.com/undercasetype/Fraunces |
| Figtree | SIL Open Font License 1.1 | https://github.com/erikdkennedy/figtree |

## Runtime

| Package | Version | License |
| --- | --- | --- |
| [@radix-ui/react-dialog](https://radix-ui.com/primitives) | 1.3.1 | MIT |
| [@radix-ui/react-form](https://radix-ui.com/primitives) | 0.3.0 | MIT |
| [@radix-ui/react-label](https://radix-ui.com/primitives) | 2.1.17 | MIT |
| [@radix-ui/react-toast](https://radix-ui.com/primitives) | 1.3.1 | MIT |
| [firebase](https://firebase.google.com/) | 13.4.0 | Apache-2.0 |
| [react](https://reactjs.org/) | 18.3.1 | MIT |
| [react-dom](https://reactjs.org/) | 18.3.1 | MIT |
| [react-router-dom](https://github.com/remix-run/react-router) | 6.30.1 | MIT |

## Development

| Package | Version | License |
| --- | --- | --- |
| [@lhci/cli](https://github.com/GoogleChrome/lighthouse-ci) | 0.16.1 | Apache-2.0 |
| [@playwright/test](https://playwright.dev) | 1.65.1 | Apache-2.0 |
| [@testing-library/react](https://github.com/testing-library/react-testing-library) | 16.3.3 | MIT |
| [@testing-library/user-event](https://github.com/testing-library/user-event) | 14.6.13 | MIT |
| [@types/node](https://github.com/DefinitelyTyped/DefinitelyTyped) | 26.6.6 | MIT |
| [@types/react](https://github.com/DefinitelyTyped/DefinitelyTyped) | 19.3.0 | MIT |
| [@types/react-dom](https://github.com/DefinitelyTyped/DefinitelyTyped) | 19.3.0 | MIT |
| [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react) | 6.3.0 | MIT |
| [jsdom](https://github.com/jsdom/jsdom) | 31.0.1 | MIT |
| [typescript](https://www.typescriptlang.org/) | 7.0.2 | Apache-2.0 |
| [vite](https://vite.dev) | 8.3.8 | MIT |
| [vitest](https://vitest.dev) | 5.1.1 | MIT |

I listed `@testing-library/user-event` as 14.6.1 but the install output said 14.6.13. I need to fix that to 14.6.13.

Let me verify package.json versions match what I wrote. I'll read package.json.