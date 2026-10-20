# ColorBestie iOS build infrastructure

This public repository contains only a build recipe for ColorBestie. Application source remains in its private repository.

The manual workflow uses a standard GitHub-hosted macOS runner. It refuses to allocate a runner if this repository is private, renamed, or dispatched by another account or branch. No paid runner, artifact upload or cache is configured.

The internal TestFlight workflow fetches one reviewed source commit with a repository-specific read-only SSH deploy key, builds against isolated staging and uploads an internal-only TestFlight build. Application command output is redirected to temporary private files and removed. On failure, only an RSA-OAEP-SHA256/AES-256-GCM encrypted envelope containing at most the last 64 KiB is published in Actions logs. Raw diagnostics must never be printed publicly. Debug runs fail before private source access.

## Production 1.6 (121) local preparation

The production recipe targets `https://colorbestie.app` and App Store distribution.
Its approved 1024 icon SHA-256 is `8883ccc02f575e6f1e45b2c41bdf21b158df03bcdf1e54ca22ea4b2a9d559f82`.
The independent actool/iPhone/iPad archive pixel proof is retained.

Build 121 pins reviewed private source `700b6da1d13d3701853ec1b15a70d1ddcc6a85ba` in both the job environment and its exact comparison guard. The reviewed changes are integrated above the existing production payment code. Production Render and external attribution settings are verified independently before dispatch.

Source and archived plists must include the Apple ATT purpose, permanently deactivate Firebase Analytics, keep notification auto-init off and disable automatic Facebook SDK initialization/events/advertising-ID collection. Source, CocoaPods target and signed-archive guards verify the custom ATT bridge, framework, request API and storyboard registration. Adapter tests cover denied, interrupted and revoked permission, authorized native events, and purchase/restore behavior. Native browser marketing remains off; iOS uses the permission-gated AppsFlyer client path. Billing files are snapshotted before dependency/build preparation and compared before upload; the recipe does not remove the existing Apple paid-start files or change billing flags. Existing production deployment revision and external attribution settings must be verified separately before dispatch.

Required encrypted repository secrets:

- SOURCE_REPOSITORY: the private source SSH URL.
- SOURCE_SSH_KEY: a dedicated read-only deploy key for that one repository.
- ASC_KEY_ID, ASC_ISSUER_ID, ASC_PRIVATE_KEY, APPLE_TEAM_ID: the existing Apple team signing credentials.

The Apple key must support provisioning and cloud signing; that remains a real runner acceptance check. The independently verified existing production backend must be reachable before dispatch; this recipe does not enable or modify any paid-start gate.

No physical iPhone or USB connection is needed to build and upload. A tester installs through TestFlight over the internet. Building does not prove a purchase: the actual Apple Sandbox acceptance test remains separate.

References:

- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [GitHub deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys)
- [GitHub Actions terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#actions)
- [Apple cloud signing](https://developer.apple.com/videos/play/wwdc2021/10204/)

Provision diagnostics-public-key.pem with an RSA public key (PEM, at least 3072 bits). Keep its private key exclusively in local ignored storage. The encrypted failure envelope is split into 120-character lines between BEGIN_COLORBESTIE_ENCRYPTED_DIAGNOSTIC and END_COLORBESTIE_ENCRYPTED_DIAGNOSTIC. Decode the envelope and decrypt locally; no private key is uploaded to GitHub.
