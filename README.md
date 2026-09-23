# Ontario engineering co-op search

Deployed to https://github.com/thadaniavinash/Engineering_Coop_Positions with a daily GitHub Actions schedule. Open Actions to run it manually or download the latest report. Both computers can be off.

## What runs

GitHub starts an Ubuntu computer at 11:17 UTC daily (7:17 a.m. Toronto during daylight time; 6:17 a.m. in winter). It installs the free search library, runs checks, searches, saves reports, then shuts down. Your laptop, desktop and ChatGPT can all be off. Saturday runs attempt the entire employer queue; other days rotate employers while searching all ten seed sites and the engineering topics every day.

Search scope: all Ontario, with Newmarket proximity a preference only. Mechanical, electrical, mechatronics, civil/structural, chemical/process, materials, industrial/manufacturing, aerospace, environmental, biomedical, nuclear, quality, automation and systems roles. Desired start is May 2027 or later; desired length is 12 or 16 months. Unknown information is retained for review. A computer-engineering role is excluded when identified; merely listing computer engineering among several eligible degrees does not exclude an electrical or mechatronics role.

The free bot uses public metasearch through DDGS plus direct static visits to employer boards. Searches cover the ten original sources, an expanded employer queue, LinkedIn, Indeed, Eluta, Job Bank, TalentEgg, Jobs.ca, Prosple, Intern Insider and common applicant-tracking sites. New employers can appear in open-web results. It has no paid API and no language model. It collects evidence and produces reviewable leads; it does not reproduce ChatGPT's judgment. Broad title matching can admit unrelated results, and computer-related duties may require manual review.

## Results

- `reports/Search-results.xlsx` and `reports/Search-results.html`: the manually reviewed, dated 23 September 2026 baseline. This workbook is not automatically refreshed by GitHub.
- `daily-results/Search-results.html`: the latest automated leads with coverage gaps.
- `daily-results/jobs.csv`: Excel-compatible results and history, including records not seen this run.
- `daily-results/all-search-hits.csv`: EVERY returned search hit, including uncertain results and search/category pages. These are not all individual vacancies.
- `daily-results/run-health.json`: attempted/successful queries and coverage totals.
- `daily-results/history.json`: persistent first-found and last-checked records. Disappearance from search does not prove a vacancy closed.

Each run also supplies a downloadable ZIP in GitHub Actions. No email service is configured. GitHub can send workflow-failure notifications according to your account settings. Nothing applies for jobs or contacts employers.

## Setup instructions (deployment is already complete for the supplied repository)

1. Unzip `GitHubJobSearch.zip` on either computer.
2. Sign in at https://github.com and create a new **private** repository, for example `ontario-coop-search`. Leave its initial README unchecked.
3. Choose **uploading an existing file**. Upload the CONTENTS of the unzipped folder to the repository root: `search.py`, `report.py`, tests, configuration, requirements and reports. Do not put them inside an extra `GitHubJobSearch` directory. Commit the upload.
4. Ensure `.github/workflows/job-search.yml` is present. Windows/browser uploads sometimes omit hidden folders. If missing, choose **Add file → Create new file**, enter `.github/workflows/job-search.yml`, paste the full contents from the downloaded file, and commit it.
5. Under **Settings → Actions → General**, allow GitHub Actions and give the workflow **Read and write permissions** so it can save its own results. Organization rules may prevent this; use a personal repository if needed.
6. Open **Actions → Ontario engineering co-op search → Run workflow**. The workflow must be on the repository's default branch.
7. When it finishes, open the run and download its `engineering-coop-results` artifact. Unzip it, open `Search-results.html` in a browser, or `jobs.csv` in Excel. A failed run may still contain useful partial reports; read coverage and run-health.
8. The daily schedule is now defined by the uploaded workflow. Check that the first scheduled run occurs. GitHub schedules can be delayed. Public-repository schedules can be disabled after 60 days of inactivity.
9. To stop it, open the workflow's menu in Actions and choose **Disable workflow**. To change its time, edit the cron line in the workflow.

The downloadable local ZIP includes a `sample-results` directory from a limited local test, separate from the reviewed workbook. Cloud output is in `daily-results`. Reports in a private repository are visible to you and any collaborators you add. Your supplied repository, `thadaniavinash/Engineering_Coop_Positions`, was public when checked; its uploaded reports would be publicly visible.

## Cost

GitHub Free includes 2,000 private-repository Actions minutes/month and 500 MB artifact storage. Standard public-repository runner time is free. This workflow has a 20-minute maximum per run: 31 scheduled runs can consume at most 620 minutes, before manual reruns and other workflows. Actual time should be lower; it is not guaranteed. Artifacts expire after 14 days. Review storage and usage in GitHub billing; configure a spending limit or keep paid usage disabled if you want no overage charges. No Google One benefit or paid search/AI subscription is needed.

Official references:
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://github.com/deedy5/ddgs

## Limits to understand

Search engines may throttle/block GitHub cloud IP addresses. Each search request runs in a separate process with a 12-second hard timeout; partial raw results are saved after every query. The overall search has a time budget, so the Saturday full queue may be only partially completed. Some employer boards require JavaScript and cannot be enumerated by this free static fetcher. An empty result or an inaccessible board is not proof of no vacancies. The report records gaps, and a completely unsuccessful discovery run fails visibly. All automatically collected leads remain unverified until reviewed. Only a live employer posting can establish availability, dates and eligibility. Neither this bot nor a paid search service can promise ALL Ontario vacancies.

## Optional local run

Install Python 3.12, open a terminal in this folder, run `python -m pip install -r requirements.txt`, then `python -m unittest discover -v` and `python search.py --full`. Open the generated `daily-results/Search-results.html`. This local command is optional; the GitHub workflow runs without your computer.
