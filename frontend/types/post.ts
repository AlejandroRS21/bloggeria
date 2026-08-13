export interface BlogPost {
  id: string;
  slug: string;
  title: string;
  description: string;
  content: string; // HTML content
  author: string;
  date: string;
  word_count: number;
  reading_time: number;
  keywords: string[];
  tags: string[];
  style_source?: string;
  style_source_url?: string;
  html_structure?: {
    html: string;
    jsx: string;
    headings: string[];
    meta: {
      title: string;
      description: string;
      keywords: string;
    };
    reading_time: number;
    word_count: number;
  };
}

export interface GenerateRequest {
  topic: string;
  blog_url: string;
  keywords?: string[];
  provider?: "huggingface" | "openai" | "gemini";
}

export interface GenerateResponse {
  success: boolean;
  post?: BlogPost;
  error?: string;
  execution_time?: number;
}
