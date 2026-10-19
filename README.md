# ColorBestie iOS build infrastructure

This public repository contains only a build recipe for ColorBestie. Application source remains in its private repository.

The manual workflow uses a standard GitHub-hosted macOS runner. It refuses to allocate a runner if this repository is private, renamed, or dispatched by another account or branch. No paid runner, artifact upload or cache is configured.

The workflow fetches one reviewed source commit with a repository-specific read-only SSH deploy key, builds against isolated staging and uploads an internal-only TestFlight build. Application command output is redirected to temporary private files and removed. On failure, only an RSA-OAEP-SHA256/AES-256-GCM encrypted envelope containing at most the last 64 KiB is published in Actions logs. Raw diagnostics must never be printed publicly. Debug runs fail before private source access.

Required encrypted repository secrets:

- SOURCE_REPOSITORY: the private source SSH URL.
- SOURCE_SSH_KEY: a dedicated read-only deploy key for that one repository.
- ASC_KEY_ID, ASC_ISSUER_ID, ASC_PRIVATE_KEY, APPLE_TEAM_ID: the existing Apple team signing credentials.

The Apple key must support provisioning and cloud signing; that remains a real runner acceptance check. The existing isolated backend must expose the enabled Apple route with an unauthenticated 401 response.

No physical iPhone or USB connection is needed to build and upload. A tester installs through TestFlight over the internet. Building does not prove a purchase: the actual Apple Sandbox acceptance test remains separate.

References:

- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [GitHub deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys)
- [GitHub Actions terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#actions)
- [Apple cloud signing](https://developer.apple.com/videos/play/wwdc2021/10204/)

Provision diagnostics-public-key.pem with an RSA public key (PEM, at least 3072 bits). Keep its private key exclusively in local ignored storage. The encrypted failure envelope is split into 120-character lines between BEGIN_COLORBESTIE_ENCRYPTED_DIAGNOSTIC and END_COLORBESTIE_ENCRYPTED_DIAGNOSTIC. Decode the envelope and decrypt locally; no private key is uploaded to GitHub.
