# PINS for Umbrel

Independent PINS app source for umbrelOS 2.0 or newer. This is an amd64
prerelease. Published images have passed isolated Mainnet/Testnet4 integration;
managed Umbrel installation and real-chain operation acceptance remain pending.

This indexer depends on a selected Qbit Core app instance and owns its own index. Its app-local transport preserves loopback RPC while authenticating the separate Core connection.

The browser UI shows status. Each app instance has explicit Mainnet or
Testnet4 identity and separate persistent data. Existing unmarked data and
wrong-network directories are refused. Wallets, signing and broadcasting are
outside the read API. App credentials are derived per installation and are
never included in source or container images.

## Installation

Install a published release through the QBitLeap community app store:
https://github.com/QBitLeap/umbrel-app-store

The store is not ready until its image lock contains published registry
manifest digests and the complete Mainnet/Testnet4 integration checks pass.
Local image configuration IDs are not downloadable registry references.
Indexing starts paused. Enable INDEX_ENABLED in app settings after selecting a ready Core instance.

The dashboard accepts a refresh interval in whole minutes, with a one-minute
default and minimum. The choice is saved in this browser, hidden pages stop
refreshing, and requests never overlap. Paused indexing is shown explicitly;
enabled indexing reports its current block and the selected node's block height.

## Inscribe from the Umbrel terminal

From the Umbrel host terminal, pass the working directory containing the
collection and inscription files to the launcher installed by Qbit Core.

```sh
sudo sh /home/umbrel/umbrel/app-data/qbitleap-core-main/qbit-terminal.sh pins main /path/to/collection
```

For Testnet4, replace both network names with `testnet4`. Use `pins --help`
and the [upstream inscriber guide](https://github.com/P2MR-PINS-Protocol/pins/tree/3e014f4ff156a35eea4b8613e37116fd124aa719/docs/inscriber).
The terminal selects the network and supplies Core RPC for `preflight` and
`broadcast`. Use upstream's `--confirm-network mainnet` or
`--confirm-network testnet4` for those commands. Issuer keyfiles stay in
your working directory.

## Source checks

```sh
python3 -m unittest discover -s tests
```

## Image releases

On a Linux amd64 Docker host, from clean committed source:

```sh
python3 scripts/release_images.py 0.1.0-alpha.1
```

That command builds and smoke-checks images. Add `--publish` only after
logging in to GitHub Container Registry with package-write permission. The
manual Image release workflow performs that login with the repository's
GITHUB_TOKEN and emits a receipt containing the actual registry digest.
It has no automatic publication trigger.

Sources, container bases and language dependency locks are pinned. Debian
package resolution is performed at build time; bit-for-bit reproducibility is
not claimed. A rebuilt image must pass the complete store integration checks
before its digest is added to the catalog. Upstream changes require a reviewed
lock/patch update; apps do not adopt upstream changes while running.

## Instance packaging

`scripts/prepare_app_package.py --help` describes the package generator. Choose
an app ID, network and unused UI port; indexers also select a Core dependency.
Use published `ghcr.io/...@sha256:...` image references. Multiple independent
instances reuse an image but need distinct app IDs and writable data folders.
Do not share a writable database or chain directory.

The Core gateway shares its Core service's network namespace. Lifecycle
operations must restart that dependency together; all package services use an
init process so shutdown signals reach the application.

## Licenses

Wrapper code is MIT. See LICENSE, NOTICE and retained upstream notices.
Protocol source, artwork and dependencies keep their respective upstream
licenses. Source releases and image publication are separate from native
macOS/Windows/Linux protocol release artifacts.
