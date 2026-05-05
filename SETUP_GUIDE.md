# Phase 1 Setup Guide — Step by Step

Follow these steps in order. Each step links directly to the right page.

---

## Step 1 — Create a Google Cloud Project (2 min)

1. Go to → https://console.cloud.google.com/projectcreate
2. **Project name:** `wealthsync`
3. Click **Create**.
4. Make sure the new project is selected in the top dropdown.

---

## Step 2 — Enable the Required APIs (1 min)

Open both links while your `wealthsync` project is active:

- **Google Sheets API** → https://console.cloud.google.com/apis/library/sheets.googleapis.com  
  Click **Enable**.

- **Google Drive API** → https://console.cloud.google.com/apis/library/drive.googleapis.com  
  Click **Enable**.

---

## Step 3 — Create a Service Account (3 min)

1. Go to → https://console.cloud.google.com/iam-admin/serviceaccounts/create
2. **Service account name:** `wealthsync`
3. Click **Create and Continue** → skip optional role fields → **Done**.
4. Click on the new service account in the list.
5. Go to the **Keys** tab → **Add Key** → **Create new key** → **JSON** → **Create**.
6. A `.json` file downloads automatically — **keep it safe, never commit it**.

---

## Step 4 — Fill in secrets.toml (2 min)

Open `.streamlit/secrets.toml` in this project and replace every placeholder with
values from the downloaded JSON file:

| secrets.toml field  | JSON file field           |
|---------------------|---------------------------|
| `project_id`        | `project_id`              |
| `private_key_id`    | `private_key_id`          |
| `private_key`       | `private_key`             |
| `client_email`      | `client_email`            |
| `client_id`         | `client_id`               |
| `client_x509_cert_url` | `client_x509_cert_url` |

The `auth_uri` and `token_uri` values are standard — the template already has them.

> **Tip:** You can also just paste the entire JSON content into the `[gcp_service_account]`
> section using TOML inline-table syntax, or open the JSON file and copy each field manually.

---

## Step 5 — Create the Google Sheet (1 min)

1. Go to → https://docs.google.com/spreadsheets/create
2. Name it **WealthSync**.
3. Copy the **Sheet ID** from the URL:  
   `https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`
4. Paste it into `.streamlit/secrets.toml` under `[sheets] spreadsheet_id`.

---

## Step 6 — Share the Sheet with the Service Account (30 sec)

1. In your new Google Sheet, click **Share** (top right).
2. Paste the `client_email` from the JSON file (looks like `wealthsync@...iam.gserviceaccount.com`).
3. Set permission to **Editor**.
4. Click **Send** (you can ignore the "can't notify" warning).

---

## Step 7 — Run the Setup Script

```bash
cd C:\wealthsync
python setup_sheets.py
```

Expected output:
```
Connecting to Google Sheets…
  ✓ Authenticated successfully
  ✓ Opened spreadsheet: 'WealthSync'
  ✓ URL: https://docs.google.com/spreadsheets/d/...
  + Created worksheet 'holdings'
    → Headers written: [...]
  + Created worksheet 'manual_entries'
    → Headers written: [...]

Setup complete. You can now run:  streamlit run app.py
```

---

## Step 8 — Launch the App

```bash
streamlit run app.py
```

The browser opens at `http://localhost:8501`. Upload `ibi_template.xlsx` on the
**Upload** page to verify the parser works end-to-end.

---

## Deploying to Streamlit Cloud (optional)

1. Push this repo to a **private** GitHub repository.
2. Go to → https://share.streamlit.io → **New app** → connect your repo.
3. In **Advanced settings → Secrets**, paste the entire contents of your `secrets.toml`.
4. Deploy — free, 24/7.
