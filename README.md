# Job Automation (UI/UX Designer)

This is a beginner-friendly automation tool that:

- Searches jobs using ChatGPT Web Search (main mode)
- Supports structured filters on the main page (not sidebar)
- Saves them into `jobs.csv`
- Generates a personalized cover letter for each job using OpenAI
- Appends the cover letter into the same `jobs.csv`

You run it with:

```bash
python main.py
```

Or with the click-based UI:

```bash
streamlit run ui.py
```

---

## What files are included?

- `scraper.py`: Scrapes jobs and extracts title/company/location/description/apply link
- `cover_letter_generator.py`: Calls the OpenAI API to generate a tailored cover letter
- `main.py`: Runs everything end-to-end
- `ui.py`: Main-page UI with filters and search flow
- `chatgpt_job_search.py`: ChatGPT web-search based job discovery
- `jobs.csv`: Output file (jobs + cover letters)
- `requirements.txt`: Python dependencies

---

## 1) Install Python packages

### Step A — Open PowerShell

On Windows:
- Press **Windows key**
- Type **PowerShell**
- Open it

### Step B — Go to this project folder

```bash
cd "D:\Cursor\Projects\job_automation"
```

### Step C — Install dependencies

```bash
pip install -r requirements.txt
```

If `pip` doesn’t work, try:

```bash
python -m pip install -r requirements.txt
```

---

## 2) Add your OpenAI API key

This project reads your API key from an environment variable called `OPENAI_API_KEY`.

### Option A (recommended) — Set it in PowerShell for your user account

Replace `YOUR_KEY_HERE` with your real key:

```powershell
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY","YOUR_KEY_HERE","User")
```

Close PowerShell and open it again after setting the key.

### Option B — Set it only for the current PowerShell window

```powershell
$env:OPENAI_API_KEY="YOUR_KEY_HERE"
```

Note: this only lasts until you close that PowerShell window.

---

## 3) Run the tool

From the `job_automation` folder:

### Option A — Run the UI (recommended)

```bash
streamlit run ui.py
```

It will open in your browser. Choose:
- Job position (Product Designer / UI Designer / UX Designer)
- Company type (Product based / Agency / Marketing / Development firm / IT / All)
- Max jobs (1 to 100)
- Years of experience (0 months to 20 years)
- Optional company name search (checks openings for selected roles in that company)
- Optional cover letter generation + API key input

Flow:
1) Click **Apply Filters**
2) Click **Search Jobs**

If company name is provided, the app also fetches:
- What people are talking about the company
- Positive and negative review trends
- Median tenure (if publicly available)

Cover letters are generated with the OpenAI model configured in `cover_letter_generator.py`.

### Option B — Run the simple script (no UI)

```bash
python main.py
```

After it runs, open `jobs.csv` (in Excel or Google Sheets) to see:

- company
- role
- location
- description
- apply_link
- cover_letter

---

## Troubleshooting

### “Request failed” while scraping

Websites can block bots sometimes. If it happens:
- Try again later
- Make sure your internet is working

### “Missing OPENAI_API_KEY”

You didn’t set the environment variable. Follow **Step 2** above.

### Cover letter column is empty

If the OpenAI API call fails, the script will not crash—it will just leave the cover letter empty and keep going.

---

## Notes

ChatGPT web search quality depends on public web data and can vary by company/role.
Company-review and tenure summaries are best-effort and include uncertainty when data is limited.

