# src/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
from src import jobs_db
from src import analysis
import sqlite3
import pandas as pd
import numpy as np
from rq import Queue
from redis import Redis
import zipfile
import glob

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_conn = Redis.from_url(REDIS_URL)
q = Queue(connection=redis_conn)

app = FastAPI(title="AutoDataFlow")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. Change to ["http://localhost:3000"] in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobOptions(BaseModel):
    force_playwright: bool = False
    table_selector: str | None = None
    playwright_timeout: int = 30
    crawl: bool = False
    max_pages: int = 1
    webhook_url: str | None = None
    max_retries: int = 3
    proxy: str | None = None
    llm_api_key: str | None = os.getenv("LLM_API_KEY")
    llm_prompt: str | None = None
    llm_model: str = "gemini-2.5-flash"


class JobRequest(BaseModel):
    type: str  # "url" or "prompt"
    value: str
    options: JobOptions = JobOptions()


class QueryRequest(BaseModel):
    query: str
    file: str | None = None


class VisualizeRequest(BaseModel):
    query: str
    type: str | None = None
    file: str | None = None


@app.on_event("startup")
def startup_event():
    # ensure the shared DB is initialized on API startup
    jobs_db.init_db()


@app.post('/jobs')
def create_job(req: JobRequest):
    if req.type not in ("url", "prompt"):
        raise HTTPException(status_code=400, detail="type must be 'url' or 'prompt'")
    job_id = str(uuid.uuid4())
    jobs_db.create_job(job_id, req.type, req.value)
    # enqueue background worker task; pass the dict so options are serializable
    from src.tasks import process_url_job
    q.enqueue(process_url_job, job_id, req.dict())
    return {"job_id": job_id}


@app.get('/jobs/{job_id}')
def get_job(job_id: str):
    job = jobs_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get('/jobs/{job_id}/download')
def download(job_id: str, format: str = 'csv'):
    try:
        from fastapi.responses import FileResponse
        job = jobs_db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        if job['status'] != 'completed':
            raise HTTPException(status_code=400, detail="job not completed yet")
        
        # New structure: data/{job_id}/
        job_dir = os.path.join(os.getcwd(), 'data', job_id)
        
        # Fallback for old structure (data/{job_id}.csv)
        if not os.path.exists(job_dir):
            # check if old files exist
            base = os.path.join(os.getcwd(), 'data')
            if format == 'csv':
                path = os.path.join(base, f"{job_id}.csv")
            elif format == 'parquet':
                path = os.path.join(base, f"{job_id}.parquet")
            elif format == 'sqlite':
                path = os.path.join(base, f"{job_id}.db")
            else:
                raise HTTPException(status_code=400, detail="unsupported format")
                
            if os.path.exists(path):
                 return FileResponse(path, filename=os.path.basename(path))
            raise HTTPException(status_code=404, detail="export not found")
    
        # New structure logic
        if format == 'sqlite':
            try:
                path = os.path.join(job_dir, "data.db")
                
                # On-demand generation if missing
                if not os.path.exists(path):
                     csv_files = glob.glob(os.path.join(job_dir, "*.csv"))
                     if csv_files:
                         try:
                             # Ensure we don't lock the file for long
                             conn = sqlite3.connect(path)
                             for f in csv_files:
                                 try:
                                     df = pd.read_csv(f)
                                     table_name = os.path.basename(f).replace(".csv", "")
                                     df.to_sql(table_name, conn, index=False, if_exists="replace")
                                 except Exception:
                                     pass
                             conn.close()
                         except Exception:
                             pass
    
                if os.path.exists(path):
                    return FileResponse(path, filename=f"{job_id}.db")
                raise HTTPException(status_code=404, detail="sqlite export not found")
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"SQLite Export Error: {str(e)}")
    
        # JSON Handling
        if format == 'json':
            # Source is CSVs
            csv_files = glob.glob(os.path.join(job_dir, "*.csv"))
            if not csv_files:
                 raise HTTPException(status_code=404, detail="no data found to convert to json")
                 
            json_files = []
            for f in csv_files:
                try:
                    # Convert to JSON
                    df = pd.read_csv(f)
                    base_name = os.path.basename(f).replace(".csv", ".json")
                    json_path = os.path.join(job_dir, base_name)
                    df.to_json(json_path, orient='records', indent=2)
                    json_files.append(json_path)
                except Exception as e:
                    print(f"Failed to convert {f}: {e}")
            
            if not json_files:
                 raise HTTPException(status_code=500, detail="failed to convert data to json")
    
            if len(json_files) == 1:
                return FileResponse(json_files[0], filename=os.path.basename(json_files[0]))
                
            zip_filename = f"{job_id}_json.zip"
            zip_path = os.path.join(job_dir, zip_filename)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in json_files:
                    zf.write(f, arcname=os.path.basename(f))
            return FileResponse(zip_path, filename=zip_filename)
    
        # Parquet Handling (On-Demand)
        if format == 'parquet':
            # Check existing
            files = glob.glob(os.path.join(job_dir, "*.parquet"))
            
            # If none, generate from CSV
            if not files:
                csv_files = glob.glob(os.path.join(job_dir, "*.csv"))
                for f in csv_files:
                    try:
                        df = pd.read_csv(f)
                        # Convert object columns to string to avoid PyArrow serialization errors
                        for col in df.select_dtypes(['object']).columns:
                            df[col] = df[col].astype(str)
                            
                        base_name = os.path.basename(f).replace(".csv", ".parquet")
                        pq_path = os.path.join(job_dir, base_name)
                        df.to_parquet(pq_path, index=False)
                        files.append(pq_path)
                    except Exception as e:
                        print(f"Failed to convert {f} to parquet: {e}")
    
            if not files:
                 raise HTTPException(status_code=404, detail="no parquet files found")
    
            if len(files) == 1:
                return FileResponse(files[0], filename=os.path.basename(files[0]))
                
            zip_filename = f"{job_id}_parquet.zip"
            zip_path = os.path.join(job_dir, zip_filename)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    zf.write(f, arcname=os.path.basename(f))
            return FileResponse(zip_path, filename=zip_filename)
    
        # Fallback to simple glob for CSV (or if format passed is technically handled above but fell through)
        extension = "csv"
        files = glob.glob(os.path.join(job_dir, f"*.{extension}"))
        
        if not files:
            raise HTTPException(status_code=404, detail=f"no {format} files found")
            
        # If only one file, return it directly
        if len(files) == 1:
            return FileResponse(files[0], filename=os.path.basename(files[0]))
            
        # If multiple files, zip them
        import uuid
        # If multiple files, zip them
        # Use unique name to avoid Windows file locking if previous download failed/open
        zip_filename = f"{job_id}_{format}_{uuid.uuid4().hex[:8]}.zip"
        zip_path = os.path.join(job_dir, zip_filename)
        
        try:
            # Create zip if not exists (or always recreate to be safe)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    # Avoid zipping the zip itself if it somehow matches (unlikely with .csv ext)
                    if f == zip_path: 
                        continue
                    try:
                        zf.write(f, arcname=os.path.basename(f))
                    except Exception as e:
                        print(f"Warning: could not add {f} to zip: {e}")
                        
            return FileResponse(zip_path, filename=zip_filename)
        except Exception as e:
            import traceback
            error_msg = f"Failed to create zip: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            try:
                # Write to job dir
                with open(os.path.join(job_dir, "download_error.txt"), "w") as f:
                    f.write(error_msg)
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Failed to create zip: {str(e)}")
            
    except Exception as e:
        import traceback
        error_msg = f"CRITICAL DOWNLOAD ERROR: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        try:
            # Try to write to global log if job dir fails or logic fails early
            with open("c:\\Users\\yarul\\AutoDataFlow\\global_error_log.txt", "a") as f:
                f.write(f"\n--- Error for job {job_id} ---\n{error_msg}\n")
        except:
             pass
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")



@app.get('/jobs/{job_id}/tables')
def get_job_tables(job_id: str):
    """Return list of available data tables/files."""
    job = jobs_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    job_dir = os.path.join(os.getcwd(), 'data', job_id)
    if not os.path.exists(job_dir):
        return []
        
    import glob
    # Find all CSVs
    files = glob.glob(os.path.join(job_dir, "*.csv"))
    tables = []
    for f in files:
        name = os.path.basename(f)
        # Filter out metadata files if any, though usually we want to see data
        if name == "no_data.csv":
            continue
        tables.append(name)
        
    # Sort: cleaned first, then page_1, etc.
    tables.sort(key=lambda x: (not x.startswith("cleaned"), x))
    return tables


@app.get('/jobs/{job_id}/data')
def get_job_data(job_id: str, limit: int = 1000, offset: int = 0, file: str | None = None):
    job = jobs_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    try:
        df = _load_job_df(job_id, filename=file)
        if df.empty:
             return []
             
        # Remove NaNs which crash JSON serialization
        df = df.fillna("")
        
        # Replace Infinity
        df = df.replace([np.inf, -np.inf], "")
        
        # Return slice
        return df.iloc[offset : offset + limit].to_dict(orient='records')
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Data error: {str(e)}")


class CleanRequest(BaseModel):
    instruction: str | None = None
    file: str | None = None

@app.post("/jobs/{job_id}/clean")
def clean_job(job_id: str, req: CleanRequest = CleanRequest()):
    """
    Trigger LLM-based cleaning for a completed job.
    """
    job = jobs_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job must be completed before cleaning")

    # Update status immediately so frontend polling triggers
    jobs_db.update_job_status(job_id, "cleaning")

    # Enqueue cleaning task
    from src.tasks import clean_job_data
    q.enqueue(clean_job_data, job_id, instruction=req.instruction, file_filter=req.file, job_timeout=600)
    
    return {"status": "cleaning_started", "job_id": job_id}


def _load_job_df(job_id: str, filename: str | None = None) -> pd.DataFrame:
    """Helper to load job data into a DataFrame."""
    job_dir = os.path.join(os.getcwd(), 'data', job_id)
    if not os.path.exists(job_dir):
        return pd.DataFrame()
    
    # If specific file requested
    if filename:
        # Prevent traversal
        if ".." in filename or "/" in filename:
            return pd.DataFrame()
        
        path = os.path.join(job_dir, filename)
        if os.path.exists(path):
            try:
                if filename.endswith(".csv"):
                    return pd.read_csv(path)
                # Add parquet support if needed
            except Exception:
                pass
        return pd.DataFrame()

    # Default fallback (original logic): Try first available
    # Try SQLite first
    db_path = os.path.join(job_dir, "data.db")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            # Get first table
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            if tables:
                table_name = tables[0][0]
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                conn.close()
                if not df.empty:
                    return df
            conn.close()
        except Exception:
            pass

    # Fallback to CSV
    import glob
    csv_files = glob.glob(os.path.join(job_dir, "*.csv"))
    if csv_files:
        try:
            # Load first CSV
            return pd.read_csv(csv_files[0])
        except Exception:
            pass
            
    return pd.DataFrame()


@app.post('/jobs/{job_id}/query')
def query_job(job_id: str, req: QueryRequest):
    job = jobs_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    df = _load_job_df(job_id, filename=req.file)
    if df.empty:
        raise HTTPException(status_code=400, detail="no data found for this job")
        
    # Get API key from job options or env
    # Note: job['metadata'] might not have options if it wasn't saved there.
    # But we can check env or the job request if we saved it.
    # For now, let's use env or a default.
    # Ideally we should have saved the API key in the job metadata or use the system one.
    # Let's assume system env for now if not in job.
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
         raise HTTPException(status_code=500, detail="LLM_API_KEY not configured")

    result = analysis.analyze_data(df, req.query, api_key)
    return result


@app.post('/jobs/{job_id}/visualize')
def visualize_job(job_id: str, req: VisualizeRequest):
    job = jobs_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    
    df = _load_job_df(job_id, filename=req.file)
    if df.empty:
        raise HTTPException(status_code=400, detail="no data found for this job")
        
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
         raise HTTPException(status_code=500, detail="LLM_API_KEY not configured")

    result = analysis.generate_chart(df, req.query, api_key)
    return result
