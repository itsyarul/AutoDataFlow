import pandas as pd
import traceback
import io
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import google.generativeai as genai
import re

# Plotly imports are dynamic in generate_chart

def _call_llm(prompt: str, api_key: str, model_name: str) -> str:
    """
    Calls the Gemini API.
    """
    if not api_key:
        raise ValueError("LLM API Key is missing")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    # Simple generation
    response = model.generate_content(prompt)
    
    # check for safety blocking or other issues
    if not response.parts:
         if response.prompt_feedback and response.prompt_feedback.block_reason:
             raise ValueError(f"Blocked by safety filters: {response.prompt_feedback.block_reason}")
         raise ValueError("Empty response from LLM")
         
    return response.text

def _clean_code(code: str) -> str:
    """
    Strips markdown code blocks from LLM response.
    """
    # Remove ```python ... ``` or just ``` ... ```
    pattern = r"```(?:python)?\s*(.*?)```"
    match = re.search(pattern, code, re.DOTALL)
    if match:
        return match.group(1).strip()
    return code.strip()

def analyze_data(df: pd.DataFrame, query: str, api_key: str, model: str = "gemini-2.5-flash") -> dict:
    """
    Ask a question about the data.
    Returns: {"answer": ..., "code": ...}
    """
    if df.empty:
        return {"answer": "Dataframe is empty", "code": ""}

    # Limit rows for prompt context (just head)
    df_head = df.head(5).to_markdown()
    columns = list(df.columns)
    dtypes = df.dtypes.to_dict()

    prompt = f"""
    You are a Python Data Analyst.
    I have a pandas DataFrame `df` with the following columns: {columns}
    Sample data:
    {df_head}
    Column types: {dtypes}

    User Question: "{query}"

    Write Python code to answer this question.
    Rules:
    1. Assume `df` is already defined.
    2. Store the final answer in a variable named `result`.
    3. `result` should be a string, number, or boolean.
    4. CRITICAL: Check data types first. If a column looks numeric but is string (e.g. '$100', '1,000'), convert it to numeric first using `pd.to_numeric(df['col'].str.replace('[$,]', '', regex=True), errors='coerce')`.
    5. Return ONLY the Python code, no explanations.
    """

    try:
        code = _call_llm(prompt, api_key, model)
        clean_code = _clean_code(code)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower():
             return {"answer": "⚠️ AI Usage Limit Reached (Quota Exceeded). Please try again later.", "code": ""}
        print(f"LLM Error in analyze_data: {e}")
        return {"answer": "⚠️ AI Service Unavailable. Please check logs.", "code": ""}

    local_vars = {"df": df, "pd": pd}
    
    try:
        exec(clean_code, {}, local_vars)
        result = local_vars.get("result", "No result variable found")
        return {"answer": str(result), "code": clean_code}
    except Exception as e:
        return {"answer": f"Error executing code: {e}", "code": clean_code, "error": traceback.format_exc()}

def generate_chart(df: pd.DataFrame, query: str, api_key: str, model: str = "gemini-2.5-flash") -> dict:
    """
    Generate a chart from the data.
    Returns: {"image_base64": ..., "code": ...}
    """
    if df.empty:
        return {"error": "Dataframe is empty"}

    df_head = df.head(5).to_markdown()
    columns = list(df.columns)

    prompt = f"""
    You are a Python Data Visualization Expert.
    I have a pandas DataFrame `df` with columns: {columns}
    Sample data:
    {df_head}

    User Request: "{query}"

    Write Python code to generate a chart.
    You can use `matplotlib`, `seaborn`, or `plotly`.

    Rules:
    1. Assume `df` is already defined.
    2. If using **Plotly**:
       - Create a figure and assign it to variable `fig`.
       - Example: `fig = px.bar(df, ...)`
       - Do NOT use `fig.show()`.
    3. If using **Matplotlib/Seaborn**:
       - Use `plt.figure()` to create a new figure.
       - Do NOT call `plt.show()`.
    4. CRITICAL: If plotting numerical data that is currently stored as strings (e.g. '$100'), you MUST clean and convert it to numbers first.
    5. Return ONLY the Python code.
    """

    try:
        code = _call_llm(prompt, api_key, model)
        clean_code = _clean_code(code)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower():
             return {"error": "⚠️ AI Usage Limit Reached (Quota Exceeded). Please try again later."}
        print(f"LLM Error in generate_chart: {e}")
        return {"error": "⚠️ AI Service Unavailable. Please check logs."}

    local_vars = {"df": df, "pd": pd, "plt": plt, "sns": sns}
    
    try:
        # Pre-import common libraries for exec (inside try to catch missing dependency)
        import plotly.express as px
        import plotly.graph_objects as go
        local_vars["px"] = px
        local_vars["go"] = go

        # Clear any existing plots
        plt.clf()
        exec(clean_code, {}, local_vars)
        
        # Check for Plotly 'fig'
        if "fig" in local_vars:
            fig = local_vars["fig"]
            # partial json dump
            return {"chart_data": fig.to_json(), "code": clean_code, "type": "plotly"}
        
        # Fallback to Matplotlib (check if current figure has axes)
        if plt.gcf().axes:
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode("utf-8")
            plt.close()
            return {"image_base64": img_str, "code": clean_code, "type": "matplotlib"}
            
        return {"error": "No chart generated (no fig variable or plt plot found)", "code": clean_code}

    except Exception as e:
        return {"error": f"Error generating chart: {e}", "code": clean_code, "traceback": traceback.format_exc()}
