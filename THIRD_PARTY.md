# Third-party sources and notices

The upstream projects retain their names, ownership and licenses. Their exact downloaded commits are in `upstream-lock.json`; tool-release SHA-256 hashes are recorded there too. Only one Ghidra connector is active: mrphrazer/ghidra-headless-mcp. The other referenced connector is available through the pinned source downloader.

- [universal-modder](https://github.com/rehan-remade/universal-modder): CLI, assets pipeline, upstream knowledge and examples; its license is retained under `plugins/game-modding-toolkit/licenses/`.
- [REA](https://github.com/morluto/rea): analysis MCP/CLI and its upstream skill; license retained.
- [Ghidra](https://github.com/NationalSecurityAgency/ghidra): native analysis engine; original license/notices remain in its official source/release download.
- [ghidra-headless-mcp](https://github.com/mrphrazer/ghidra-headless-mcp): active connector; license retained. Local repairs are explicit in `patches/`.
- [ghidra-mcp](https://github.com/bethington/ghidra-mcp): referenced alternative, not an active duplicate server; original notices remain in its pinned source download.
- [ILSpy](https://github.com/icsharpcode/ILSpy): managed decompiler; license retained.
- [AssetStudio](https://github.com/Perfare/AssetStudio): Unity extraction libraries and GUI; license retained.

The Windows AssetBridge console adapter, local gateway, setup orchestration and adapted development workflows were created for this installation. They are not official features of the upstream projects. Bundled examples and their sample assets originate from the upstream universal-modder repository; no commercial game installation, decompiled game dump or user project is bundled.

Python/Node dependencies preserve their package licenses in the installed distributions. This repository does not grant new rights to third-party assets or compiled applications you may import during later work.
