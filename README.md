# TalentFlow Analytics (Python version)

A web app that models monthly recruiting revenue and interview capacity.

- **Placement planner** - Linear Programming (SciPy / HiGHS) with sensitivity analysis. Any number of job types.
  - **Profit gained and cost saved** - compares the best plan with the hires you make today.
  - **Solutions for the bottlenecks** - says which limits to raise, how much, what it costs, and shows the best plan after the fix.
- **Interview queue** - M/M/s queueing model, with cost saved against your current team and ways to cut the wait.

Open on Streamlit. Click the Streamlit badge.
<a href="https://talentflowanalytics-suqxb68cqsnhqls4zzhirj.streamlit.app/">
  <img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Open in Streamlit" height="70">
</a>

## Files

| File | What it is |
|---|---|
| `app.py` | Starts the web page (Streamlit): page setup and the three tabs. |
| `model.py` | The math: LP, sensitivity analysis, bottleneck solutions, queueing. |
| `ui/auth.py` | Sign-in: single sign-on, password, guest. |
| `ui/profile.py` | Sidebar profile: June Dela Cruz's profile, editable in the app. |
| `data/profile.json` | The saved profile (name, headline, bio, education, skills). |
| `ui/style.py` | Colors, banner and sidebar. |
| `ui/helpers.py` | Shared number formats, wide tables and metric cards. |
| `ui/planner.py` | Placement planner page. |
| `ui/queue_tab.py` | Interview queue page. |
| `ui/about.py` | About page. |
| `test_model.py` | Checks the math against your Excel results. |
| `requirements.txt` | The Python libraries the app needs. |
| `.streamlit/config.toml` | The app's colors. |
| `.streamlit/secrets.toml.example` | Template for your keys and sign-in settings. |

Each page has two steps: **1. Enter your numbers**, then **2. Your results**, which are split into tabs
(Best plan, Profit gained, Bottleneck fixes, Limits and sensitivity, Charts for the planner; Recommendation,
Cost saved, Solutions for the wait, Compare team sizes for the queue).

## What's new: profit gained, cost saved, bottleneck solutions

**Placement planner**
- A new optional **Current hires** column in the job table. Fill it in to see profit gained per month and per year, fees gained, and cost per hire saved by switching to the best plan.
- A new **Fix the bottlenecks** box. Enter the most extra recruiter hours, candidates and sourcing budget you could add, and what each costs. The planner adds capacity only where the extra fees beat the extra cost, then shows what to add, the cost, the profit gained, the new plan and what still holds it back.

**Interview queue**
- A new **Interviewers you have today** input. Cost saved is measured against that team, with the pay change and the lost-candidate cost saved shown separately.
- A new **Solutions for the wait** table: more interviewers, faster interviews, or spreading out arrivals.

The cost figures in both tabs are placeholders. Replace them with your own numbers. `test_model.py` checks the new results too.

## Profile

The **Profile** block in the left sidebar (under the app title, above the guide and glossary) shows a sample character, June Dela Cruz: headline, short bio, education (Southern Luzon State
University, BS Mathematics) and skills, with a photo you can upload (it shows his initials until you do). Open **View or edit profile** and switch on **Edit profile** to change any of it: name, headline, bio, every
education row, every skill with its level, and the photo (upload or remove). **Save profile** writes `data/profile.json`.

- On your own computer the saved changes stay in that file.
- On Streamlit Community Cloud the file resets when the app restarts. To keep your edits, press **Download profile
  (JSON)**, replace `data/profile.json` in your GitHub repository with it, and redeploy.
- To let only you edit it, add `profile_editors = ["you@example.com"]` to the secrets file (this needs single
  sign-on, see below). Everyone else sees the profile but not the edit switch.

## Sign-in

Sign-in is switched on by a secrets file. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
and keep only what you need. Never upload `secrets.toml` to GitHub (`.gitignore` already blocks it). On Streamlit
Community Cloud, paste the same text into **Settings > Secrets** instead.

**Sign-in options** (use any mix; use none and the app opens with no sign-in)
- **Google or Microsoft (single sign-on):** fill in the `[auth]` section. Create an OAuth client in the provider's
  console and add `https://your-app.streamlit.app/oauth2callback` (and `http://localhost:8501/oauth2callback` for
  testing) as its redirect URI. Add `allowed_emails = [...]` to let in only certain accounts.
- **One shared password:** set `app_password`.
- **Guest button:** set `allow_guest = true`.

## Run it on your computer

1. Install Python 3.10 or newer from https://www.python.org/downloads/ (on Windows, tick "Add Python to PATH").
2. Open Terminal (Mac) or Command Prompt (Windows) and go to this folder:
   ```
   cd path/to/talentflow_python
   ```
3. Create a private environment and turn it on:
   - Mac / Linux: `python3 -m venv venv` then `source venv/bin/activate`
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
4. Install the libraries (one time): `pip install -r requirements.txt`
5. (Optional) Check the math: `python test_model.py`
6. Start the app: `streamlit run app.py`

Your browser opens at http://localhost:8501. Press `Ctrl + C` in the terminal to stop it.

Next time, only repeat steps 2, the "turn it on" part of step 3, and step 6.

## Put it online (free)

1. Create a GitHub account and a new public repository. Upload all the files in this folder.
2. Go to https://share.streamlit.io, sign in with GitHub, select **Create app**, pick your repository, and set the main file to `app.py`.
3. Select **Deploy**. You get a public link for your portfolio. Free apps go to sleep when nobody uses them, so the first load can take a minute.

## Troubleshooting

- `command not found: streamlit` - the environment is not on. Repeat the "turn it on" step.
- `ModuleNotFoundError` - run `pip install -r requirements.txt` again with the environment on.
- Port already in use - run `streamlit run app.py --server.port 8502`.
