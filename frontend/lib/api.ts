export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface JobOptions {
    force_playwright?: boolean;
    table_selector?: string;
    playwright_timeout?: number;
    crawl?: boolean;
    max_pages?: number;
    webhook_url?: string;
    max_retries?: number;
    proxy?: string;
    llm_api_key?: string;
    llm_prompt?: string;
    llm_model?: string;
}

export interface JobRequest {
    type: 'url' | 'prompt';
    value: string;
    options?: JobOptions;
}

export interface Job {
    id: string;
    type: 'url' | 'prompt';
    value: string;
    status: 'queued' | 'running' | 'completed' | 'failed' | 'cleaning';
    metadata?: any; // eslint-disable-line @typescript-eslint/no-explicit-any
    created_at: string;
}

export interface QueryRequest {
    query: string;
    file?: string;
}

export interface VisualizeRequest {
    query: string;
    type?: string;
    file?: string;
}

async function handleResponse(res: Response) {
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API Request Failed');
    }
    return res.json();
}

export const api = {
    createJob: async (data: JobRequest): Promise<{ job_id: string }> => {
        const res = await fetch(`${API_URL}/jobs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return handleResponse(res);
    },

    getJob: async (jobId: string): Promise<Job> => {
        const res = await fetch(`${API_URL}/jobs/${jobId}`);
        return handleResponse(res);
    },

    getJobTables: async (jobId: string): Promise<string[]> => {
        const res = await fetch(`${API_URL}/jobs/${jobId}/tables`);
        return handleResponse(res);
    },

    getJobData: async (jobId: string, file?: string): Promise<any[]> => {
        let url = `${API_URL}/jobs/${jobId}/data?limit=1000&offset=0`;
        if (file) {
            url += `&file=${encodeURIComponent(file)}`;
        }
        const res = await fetch(url);
        return handleResponse(res);
    },

    cleanJob: async (jobId: string, instruction?: string, file?: string) => {
        const res = await fetch(`${API_URL}/jobs/${jobId}/clean`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction, file }),
        });
        return handleResponse(res);
    },

    queryJob: async (jobId: string, query: string, file?: string) => {
        const res = await fetch(`${API_URL}/jobs/${jobId}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, file }),
        });
        return handleResponse(res);
    },

    visualizeJob: async (jobId: string, query: string, type?: string, file?: string) => {
        const res = await fetch(`${API_URL}/jobs/${jobId}/visualize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, type, file }),
        });
        return handleResponse(res);
    },

    getDownloadUrl: (jobId: string, format: 'csv' | 'json' | 'sqlite' | 'parquet' = 'csv') => {
        return `${API_URL}/jobs/${jobId}/download?format=${format}`;
    }
};
