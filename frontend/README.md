# AutoDataFlow Frontend 🎨

The user interface for the AutoDataFlow scraping platform. Built with **Next.js 14 (App Router)** and **Shadcn UI**.

## 🛠️ Tech Stack

- **Framework**: [Next.js 14](https://nextjs.org/)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: [Shadcn UI](https://ui.shadcn.com/) (Radix UI based)
- **Animations**: Framer Motion
- **Visualization**: Plotly.js
- **State Management**: React Query (TanStack Query) & Context API

## 📂 Project Structure

```
frontend/
├── app/                  # Next.js App Router pages
│   ├── jobs/[id]/        # Job details page
│   ├── layout.tsx        # Root layout (fonts, providers)
│   └── page.tsx          # Landing page
├── components/           # React components
│   ├── ui/               # Reusable atomic buttons, inputs (Shadcn)
│   ├── ai-analyst.tsx    # Chat interface for data analysis
│   ├── data-grid.tsx     # Table view for scraped data
│   └── ...
├── lib/
│   ├── api.ts            # Axios instance and API calls
│   └── utils.ts          # Helper functions (clsx, etc.)
└── public/               # Static assets
```

## 🚀 Development

### Prerequisites
- Node.js 18+
- Backend API running on `http://localhost:8000` (default)

### Setup

1.  **Install dependencies**:
    ```bash
    npm install
    ```

2.  **Environment Variables**:
    Create `.env.local` based on `.env.example`:
    ```ini
    NEXT_PUBLIC_API_URL=http://localhost:8000
    ```

3.  **Run Development Server**:
    ```bash
    npm run dev
    ```
    Open [http://localhost:3000](http://localhost:3000).

## 🧩 Key Components

- **`JobWizard`**: A multi-step form to configure scraping jobs (URL vs Prompt, Selectors, etc.).
- **`AiAnalyst`**: A smart chat component that sends specific prompts to the backend to generate Python code for analysis.
- **`DataGrid`**: A robust table viewer handling pagination and previewing CSV/Parquet data.

## 📦 Build for Production

```bash
npm run build
npm start
```

## 🧪 Linting

```bash
npm run lint
```
