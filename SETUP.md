# GitHub Profile Cards Setup

1. Upload/commit all files in this folder to the `main` branch of the `nawrin30` profile repository (`nawrin30/nawrin30`).
2. In the repository, open **Settings → Actions → General → Workflow permissions**.
3. Select **Read and write permissions** and save.
4. Open **Actions → Update GitHub Profile Cards → Run workflow**.
5. Wait for the workflow to finish successfully. It generates the statistics, language, streak, contribution, and activity SVG files.

The cards are generated inside this repository, so the README does not depend on third-party public stats/streak image hosts. GitHub Actions refreshes them daily and whenever you push to `main`.
