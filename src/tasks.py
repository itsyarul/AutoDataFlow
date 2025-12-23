import os
import requests
import pandas as pd
import sqlite3
from src import jobs_db
from src.scraper.fetcher import (
    fetch_with_requests,
    render_and_extract_with_playwright,
    extract_tables,
    extract_table_by_selector,
    fetch_with_playwright_raw,
)



DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def _tables_from_html(html: str):
    """Return list of DataFrames parsed from HTML <table> elements."""
    return extract_tables(html or "")


def _tables_from_playwright_extract(extracted: list):
    """
    Convert playwright_client extracted dicts to pandas DataFrames.
    Each extracted element: {'headers': [...], 'rows': [[...],[...]]}
    """
    dfs = []
    for t in extracted or []:
        headers = t.get("headers") or []
        rows = t.get("rows") or []
        if not rows:
            continue
        # normalize rows to same width as headers (or to max cols)
        max_cols = max((len(r) for r in rows), default=len(headers))
        if not headers or len(headers) < max_cols:
            headers = headers + [f"col_{i+1}" for i in range(len(headers), max_cols)]
        norm_rows = [row + [""] * (max_cols - len(row)) if len(row) < max_cols else row[:max_cols] for row in rows]
        df = pd.DataFrame(norm_rows, columns=headers)
        dfs.append(df)
    return dfs


def process_url_job(job_id: str, payload: dict):
    """
    payload: {
      "type": "url",
      "value": "<url>",
      "options": {
         "force_playwright": bool,
         "table_selector": str or null,
         "playwright_timeout": int,
         "webhook_url": str or null
      }
    }
    """
    jobs_db.update_job_status(job_id, "running")
    try:
        if payload.get("type") == "prompt":
            # Generative Job
            prompt = payload.get("value")
            opts = payload.get("options", {}) or {}
            api_key = opts.get("llm_api_key")
            model = opts.get("llm_model", "gemini-2.5-flash")
            
            # Create directory
            job_dir = os.path.join(DATA_DIR, job_id)
            os.makedirs(job_dir, exist_ok=True)
            
            # Init DB
            sqlite_path = os.path.join(job_dir, "data.db")
            conn = sqlite3.connect(sqlite_path)
            
            try:
                df = _generate_with_llm(prompt, api_key, model)
                if not df.empty:
                    df.to_csv(os.path.join(job_dir, "generated_data.csv"), index=False)
                    try:
                        df.to_sql("generated_data", conn, if_exists="replace", index=False)
                    except Exception:
                        pass
                    jobs_db.update_job_status(job_id, "completed", {"rows": len(df), "note": "generated via LLM"})
                else:
                    jobs_db.update_job_status(job_id, "completed", {"rows": 0, "note": "LLM returned empty"})
            except Exception as e:
                jobs_db.update_job_status(job_id, "failed", {"error": str(e)})
            finally:
                conn.close()
            return

        if payload.get("type") != "url":
            jobs_db.update_job_status(job_id, "failed", {"error": "unsupported job type"})
            return

        start_url = payload.get("value")
        opts = payload.get("options", {}) or {}
        force_playwright = bool(opts.get("force_playwright", False))
        table_selector = opts.get("table_selector")
        playwright_timeout = int(opts.get("playwright_timeout", 30))
        crawl = bool(opts.get("crawl", False))
        max_pages = int(opts.get("max_pages", 1))
        max_retries = int(opts.get("max_retries", 0))
        proxy = opts.get("proxy")
        webhook_url = opts.get("webhook_url")

        # Prepare proxy dict for requests
        requests_proxies = None
        if proxy:
            requests_proxies = {"http": proxy, "https": proxy}

        # Create directory for this job
        job_dir = os.path.join(DATA_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        current_url = start_url
        visited_urls = set()
        total_rows = 0
        saved_files = []
        
        # Initialize SQLite for this job
        sqlite_path = os.path.join(job_dir, "data.db")
        conn = sqlite3.connect(sqlite_path)

        for page_num in range(1, max_pages + 1):
            if not current_url or current_url in visited_urls:
                break
            visited_urls.add(current_url)
            
            # Update status
            jobs_db.update_job_status(job_id, "running", {"current_page": page_num, "current_url": current_url})

            html = None
            tables = []
            used_selector = False
            used_playwright = False
            
            # Retry loop
            import time
            attempts = 0
            success = False
            last_error = None
            
            while attempts <= max_retries:
                attempts += 1
                try:
                    # Try requests first
                    if not force_playwright:
                        try:
                            html = fetch_with_requests(current_url, timeout=10, proxies=requests_proxies)
                            tables = _tables_from_html(html)
                        except Exception:
                            force_playwright = True

                    if force_playwright:
                        used_playwright = True
                        # Pass screenshot path only on the last attempt
                        screenshot_path = None
                        if attempts > max_retries: # This is the last attempt (actually attempts starts at 1, so if attempts > max_retries it means we are failing)
                             # Wait, logic: attempts 1..max_retries+1. 
                             pass
                        
                        # We want to capture screenshot if this attempt fails AND it's the last one.
                        # But render_and_extract captures on exception.
                        # So we pass screenshot_path if attempts == max_retries + 1?
                        # Let's just always pass a screenshot path for the "error.png" and overwrite it?
                        # Or better: "error_page_{page_num}.png"
                        err_shot = os.path.join(job_dir, f"error_page_{page_num}.png")
                        
                        extraction_result = render_and_extract_with_playwright(
                            current_url, 
                            timeout=playwright_timeout, 
                            wait_for=900, 
                            proxy=proxy,
                            screenshot_path=err_shot
                        )
                        tables = _tables_from_playwright_extract(extraction_result.get("tables", []))
                        html = extraction_result.get("content", "")
                        
                        # If we are crawling and need next link, we might need HTML.
                        # As discussed, we skip this optimization for now or rely on what we have.

                    # Selector filtering
                    if table_selector and html:
                        try:
                            sel_tables = extract_table_by_selector(html or "", table_selector)
                            if sel_tables:
                                tables = sel_tables
                                used_selector = True
                            else:
                                raise ValueError("No tables found with selector")
                        except Exception:
                            # Selector failed (or was a description)! Try self-healing/NL selection
                            print(f"Selector '{table_selector}' failed/invalid. Attempting AI selection...")
                            healed_selector = _heal_selector(
                                html, 
                                table_selector, 
                                opts.get("llm_api_key"), 
                                opts.get("llm_model", "gemini-2.5-flash")
                            )
                            if healed_selector:
                                try:
                                    sel_tables = extract_table_by_selector(html or "", healed_selector)
                                    if sel_tables:
                                        tables = sel_tables
                                        used_selector = True
                                        # Record that we healed it
                                        jobs_db.update_job_status(job_id, "running", {"healed_selector": healed_selector})
                                except Exception:
                                    pass

                    # Fallback to Playwright if no tables found (and not already used)
                    if not tables and not used_playwright:
                        err_shot = os.path.join(job_dir, f"error_page_{page_num}.png")
                        extraction_result = render_and_extract_with_playwright(
                            current_url, 
                            timeout=playwright_timeout, 
                            wait_for=900, 
                            proxy=proxy,
                            screenshot_path=err_shot
                        )
                        tables = _tables_from_playwright_extract(extraction_result.get("tables", []))
                        html = extraction_result.get("content", "")
                        used_playwright = bool(tables)
                    
                    success = True
                    break # Exit retry loop
                    
                except Exception as e:
                    last_error = e
                    logger = None # dummy
                    print(f"Attempt {attempts} failed for {current_url}: {e}")
                    if attempts <= max_retries:
                        time.sleep(2 ** attempts) # Exponential backoff: 2, 4, 8...

            if not success:
                # Page failed after retries
                print(f"Failed to scrape {current_url} after {max_retries+1} attempts.")
                # We continue to next page? Or stop job?
                # Usually stop job or at least mark partial failure.
                # Let's continue but log it.
                continue

            # Save tables for this page
            for i, df in enumerate(tables):
                df = df.dropna(axis=1, how="all")
                if df.empty:
                    continue
                
                total_rows += len(df)
                base_name = f"page_{page_num}_table_{i+1}"
                csv_path = os.path.join(job_dir, f"{base_name}.csv")
                parquet_path = os.path.join(job_dir, f"{base_name}.parquet")
                
                df.to_csv(csv_path, index=False)
                saved_files.append(f"{base_name}.csv")
                
                try:
                    df.to_parquet(parquet_path, index=False)
                except Exception:
                    pass
                
                try:
                    df.to_sql(base_name, conn, if_exists="replace", index=False)
                except Exception:
                    pass

            # Find next page if crawling
            if crawl and page_num < max_pages:
                from src.scraper.fetcher import extract_next_page_link
                # Only works if we have HTML (from requests). 
                # If we used Playwright, we didn't get raw HTML back in this MVP flow.
                if html:
                    next_link = extract_next_page_link(html, current_url)
                    if next_link:
                        current_url = next_link
                    else:
                        break
                else:
                    # If we used Playwright, we can't easily find next link without refactoring render_and_extract
                    # to return HTML or links. For MVP, we stop if we can't find it.
                    break
        
        conn.close()

        # LLM Fallback
        if not saved_files and opts.get("llm_api_key"):
            print("No tables found. Attempting LLM extraction...")
            
            # If requests failed, we might not have HTML yet. Fetch it now.
            if not html:
                try:
                    print("Fetching raw HTML for LLM via Playwright...")
                    html = fetch_with_playwright_raw(current_url, timeout=playwright_timeout)
                except Exception as e:
                    print(f"Failed to fetch HTML for LLM: {e}")

            llm_df = _extract_with_llm(
                html, 
                opts.get("llm_prompt"),
                opts.get("llm_api_key"),
                opts.get("llm_model", "gemini-2.5-flash")
            )
            if not llm_df.empty:
                base_name = "llm_data"
                csv_path = os.path.join(job_dir, f"{base_name}.csv")
                llm_df.to_csv(csv_path, index=False)
                saved_files.append(f"{base_name}.csv")
                total_rows += len(llm_df)
                
                # Update status to reflect LLM usage
                jobs_db.update_job_status(job_id, "running", {"llm_used": True})

        status = "completed"
        if not saved_files:
             # mark completed but note no tables found
            jobs_db.update_job_status(job_id, "completed", {"rows": 0, "note": "no tables found"})
            pd.DataFrame().to_csv(os.path.join(job_dir, "no_data.csv"), index=False)
            # status remains completed
        else:
            # update DB metadata
            jobs_db.update_job_status(
                job_id,
                "completed",
                {
                    "rows": total_rows,
                    "table_count": len(saved_files),
                    "pages_scraped": len(visited_urls),
                    "used_playwright": used_playwright,
                },
            )
            
        # Webhook notification
        if webhook_url:
            try:
                requests.post(webhook_url, json={
                    "job_id": job_id,
                    "status": status,
                    "rows": total_rows,
                    "files": saved_files,
                    "download_url": f"/jobs/{job_id}/download" # Relative URL, user needs to prepend host
                }, timeout=5)
            except Exception as e:
                print(f"Webhook failed: {e}")

    except Exception as exc:
        jobs_db.update_job_status(job_id, "failed", {"error": str(exc)})
        if webhook_url:
            try:
                requests.post(webhook_url, json={"job_id": job_id, "status": "failed", "error": str(exc)}, timeout=5)
            except Exception:
                pass
        raise


def _extract_with_llm(html: str, prompt: str, api_key: str, model: str) -> pd.DataFrame:
    """
    Extract data from HTML using an LLM (Gemini or OpenAI).
    Returns a DataFrame.
    """
    if not html:
        return pd.DataFrame()

    # 1. Clean HTML to reduce token usage
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    # remove scripts, styles
    for script in soup(["script", "style", "svg", "path", "noscript"]):
        script.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Truncate if too long (rough heuristic: 1 char ~= 0.25 tokens, limit to ~100k chars for Gemini)
    text = text[:100000]

    default_prompt = """
    Extract the main structured data from the following text into a JSON list of objects.
    Return ONLY the raw JSON list, no markdown formatting, no backticks.
    If no data is found, return [].
    """
    final_prompt = f"{default_prompt}\n\nUser Instruction: {prompt or ''}\n\nText:\n{text}"

    import json
    
    try:
        if "gemini" in model.lower():
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            m = genai.GenerativeModel(model)
            response = m.generate_content(final_prompt)
            content = response.text
        else:
            # Assume OpenAI compatible
            import requests
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {
                "model": model,
                "messages": [{"role": "user", "content": final_prompt}],
                "temperature": 0
            }
            resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=60)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        # Clean markdown if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        data = json.loads(content)
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            return pd.DataFrame([data])
        return pd.DataFrame()

    except Exception as e:
        print(f"LLM extraction failed: {e}")
        return pd.DataFrame()


def _generate_with_llm(user_prompt: str, api_key: str, model: str) -> pd.DataFrame:
    """
    Generate data from scratch using an LLM based on a user prompt.
    Returns a DataFrame.
    """
    default_prompt = """
    Generate a structured dataset based on the following request.
    Return ONLY the raw JSON list of objects, no markdown formatting, no backticks.
    If the request is impossible, return [].
    """
    final_prompt = f"{default_prompt}\n\nUser Request: {user_prompt}"

    import json
    
    if not api_key:
        print("Error: LLM_API_KEY is missing. Make sure it is in .env and Docker is restarted.")
        return pd.DataFrame()

    try:
        if "gemini" in model.lower():
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            m = genai.GenerativeModel(model)
            response = m.generate_content(final_prompt)
            content = response.text
        else:
            # Assume OpenAI compatible
            import requests
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {
                "model": model,
                "messages": [{"role": "user", "content": final_prompt}],
                "temperature": 0.7 # Higher temp for creativity in generation
            }
            resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=60)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        # Clean markdown if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        data = json.loads(content)
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            return pd.DataFrame([data])
        return pd.DataFrame()

    except Exception as e:
        print(f"LLM generation failed: {e}")
        return pd.DataFrame()


def _heal_selector(html: str, broken_selector: str, api_key: str, model: str) -> str | None:
    """
    Use LLM to find a new CSS selector when the provided one fails.
    """
    if not html or not api_key:
        return None
        
    # Truncate HTML to avoid token limits, but keep enough structure
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    # remove scripts/styles to save tokens
    for s in soup(["script", "style", "svg", "path"]):
        s.decompose()
    # Get first 15k chars of cleaned HTML
    clean_html = str(soup)[:15000]
    
    prompt = f"""
    The user is looking for a table described as (or using the selector): '{broken_selector}'.
    However, the direct extraction failed.
    Analyze the HTML below and find the CORRECT CSS selector for the intended table.
    
    Rules:
    1. Return ONLY the CSS selector string. No JSON, no markdown, no explanations.
    2. If multiple tables exist, choose the one that best matches the description '{broken_selector}'.
    3. If you cannot find a suitable table, return "NOT_FOUND".
    
    HTML Snippet:
    {clean_html}
    """
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model)
        response = m.generate_content(prompt)
        new_selector = response.text.strip()
        
        # Cleanup response
        if new_selector.startswith("```"):
            new_selector = new_selector.replace("```css", "").replace("```", "").strip()
            
        if "NOT_FOUND" in new_selector or len(new_selector) > 100:
            return None
            
        print(f"Self-Healing: Replaced '{broken_selector}' with '{new_selector}'")
        return new_selector
    except Exception as e:
        print(f"Self-Healing failed: {e}")
        return None


def _generate_cleaning_code(df_sample: pd.DataFrame, api_key: str, model: str, user_instruction: str = None) -> str:
    """
    Ask LLM to generate Python code to clean the DataFrame.
    """
    # Convert sample to CSV string
    csv_sample = df_sample.to_csv(index=False)
    
    prompt = f"""
    You are a Python Data Expert.
    Write a Python function `def clean_data(df):` that takes a pandas DataFrame and cleans it.
    
    The data sample is:
    {csv_sample}
    
    **Instructions:**
    1. **Header Normalization & Integrity**:
       - Convert all column names to snake_case (lowercase, underscores instead of spaces).
       - Remove special characters from column names.
       - If a column name implies an index (e.g., "Unnamed: 0", "id_check"), drop it unless it contains unique data.

    2. **Intelligent Type Inference (The "Brain")**:
       - Iterate through every column. Analyze non-null values to detect the true intended type.
       - **Distinguish IDs vs. Metrics**: If a numeric column looks like an ID (e.g., Zip Code, Phone, Employee ID) or has leading zeros, keep it as a **String**. Only convert to Numeric if it is a measurable quantity (Price, Weight, Count).

    3. **Numeric Cleaning (Aggressive but Smart)**:
       - Target columns intended to be metrics (Price, Qty, Percent).
       - Clean: Remove currency symbols ($, €, £), commas, and unit suffixes (kg, lbs, %, people).
       - **Handle Negatives**: Recognize accounting negatives like `(500)` and convert to `-500`.
       - Convert: Use `pd.to_numeric(..., errors='coerce')`.

    4. **Date/Time Standardization**:
       - Identify columns with keywords like "date", "time", "joined", "dob", "year".
       - **Mixed-format handling**: Handle columns where formats vary (e.g., "2024-01-01" and "01/01/2024" in the same column).
       - Convert to datetime objects. 
       - If the column is just a year (e.g., "2023"), convert to integer, not a full date.

    5. **Text/String Hygiene**:
       - Trim: Apply `.str.strip()` to remove leading/trailing whitespace.
       - Normalize: Unescape HTML entities.
       - Case: Capitalize the first letter of proper nouns if appropriate, otherwise standard sentence case.
       - **Boolean**: Standardize "Yes/No", "Y/N", "True/False" to boolean keys if applicable.

    6. **Missing Value Strategy (Context-Aware)**:
       - **Numeric**: Fill NaN with 0 ONLY if it represents a count/sum. If it represents an average or measurement (e.g., Temperature), fill with the column **median**.
       - **Text**: Fill NaN with "Unknown" or "" based on context.
       - **Dates**: Leave NaN (do not fill dates with zeros).

    7. **Deduplication**:
       - Check for and remove fully duplicate rows.

    8. **Output**:
       - Return ONLY the Python code for the function `clean_data(df)`. 
       - No markdown, no explanations.
       - The code must be robust and handle potential errors safely.

    **User Specific Instructions:**
    {user_instruction if user_instruction else "None. Follow standard cleaning rules."}
    """
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model)
        response = m.generate_content(prompt)
        code = response.text
        
        # Cleanup code
        code = code.strip()
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        return code
    except Exception as e:
        print(f"Code generation failed: {e}")
        return ""


def _apply_cleaning_code(df: pd.DataFrame, code: str, job_dir: str | None = None) -> pd.DataFrame:
    """
    Execute generated cleaning code on the DataFrame.
    """
    if not code:
        return df
        
    try:
        # Pass pd and np in globals so the function can see it
        import numpy as np
        
        # We must use a single dictionary for globals and locals to ensure that 
        # imports found in the script (like 'import re') are visible to functions (like 'clean_data')
        # defined in the same script.
        exec_context = {"pd": pd, "np": np} 
        
        # Execute the code in this context
        exec(code, exec_context, exec_context)
        
        if "clean_data" in exec_context:
            cleaned_df = exec_context["clean_data"](df)
            return cleaned_df
        return df
    except Exception as e:
        print(f"Cleaning execution failed: {e}")
        if job_dir:
            try:
                with open(os.path.join(job_dir, "cleaning_error.txt"), "w") as f:
                    f.write(f"Error: {str(e)}\n\nCode:\n{code}")
            except:
                pass
        return df


def clean_job_data(job_id: str, instruction: str = None, file_filter: str = None):
    """
    Background task to clean data for a job.
    """
    import glob
    
    job_dir = os.path.join(DATA_DIR, job_id)
    if not os.path.exists(job_dir):
        print(f"Job dir {job_dir} not found")
        return

    # Get API key (from env for now)
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("LLM_API_KEY missing for cleaning")
        return

    # Update status to cleaning
    jobs_db.update_job_status(job_id, "cleaning")

    # Find all CSVs (excluding already cleaned ones and generated ones)
    all_csv_files = glob.glob(os.path.join(job_dir, "*.csv"))
    csv_files = []
    
    for f in all_csv_files:
        name = os.path.basename(f)
        
        # Skip if not the requested file (if filter is active)
        if file_filter and file_filter != "all" and name != file_filter:
             continue
             
        # Skip cleaned files (unless we are re-cleaning a specific file provided by filter? 
        # Actually user passes the ORIGINAL file name usually, e.g. page_1_table_1.csv.
        # If they pass cleaned_..., likely they want to re-clean it? 
        # For simplicity, if they pass a specific file, we process IT. 
        # But usually we process original to produce cleaned.
        # If file_filter is set, we trust it.
        # But still skip generated_data unless requested?
        
        if not file_filter:
            # Default logic: skip existing cleaned files to avoid recursion
            if name.startswith("cleaned_") or name == "generated_data.csv":
                continue
        else:
             # Logic when filter is set: 
             # If user selected "page_1_table_1.csv", we clean it to produce "cleaned_page_1_table_1.csv"
             pass
             
        csv_files.append(f)
    
    # Init DB
    sqlite_path = os.path.join(job_dir, "data.db")
    conn = sqlite3.connect(sqlite_path)
    
    cleaned_count = 0
    
    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        # Extra check if using default logic (was partially handled above but safe to keep)
        if not file_filter and (filename.startswith("cleaned_") or filename == "generated_data.csv"):
            continue
            
        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                continue
                
            # Generate code based on sample
            sample = df.head(5)
            code = _generate_cleaning_code(sample, api_key, "gemini-2.5-flash", user_instruction=instruction)
            
            if code:
                print(f"Cleaning {filename} with generated code...")
                
                # Debug: Save generated code
                try:
                    with open(os.path.join(job_dir, f"code_{filename}.py"), "w", encoding="utf-8") as f:
                        f.write(code)
                except Exception:
                    pass

                cleaned_df = _apply_cleaning_code(df, code, job_dir=job_dir)
                
                # Save cleaned CSV
                cleaned_filename = f"cleaned_{filename}"
                cleaned_path = os.path.join(job_dir, cleaned_filename)
                cleaned_df.to_csv(cleaned_path, index=False)
                
                # Update DB (replace table with cleaned version)
                table_name = filename.replace(".csv", "")
                cleaned_df.to_sql(table_name, conn, if_exists="replace", index=False)
                
                cleaned_count += 1
        except Exception as e:
            print(f"Failed to clean {filename}: {e}")
            try:
                with open(os.path.join(job_dir, "cleaning_failed_log.txt"), "a") as f:
                    f.write(f"Failed to clean {filename}: {str(e)}\n")
            except:
                pass
            
    conn.close()
    
    if cleaned_count > 0:
        jobs_db.update_job_status(job_id, "completed", {"cleaned": True, "cleaned_files": cleaned_count})
    else:
        print(f"No files cleaned for job {job_id}")
