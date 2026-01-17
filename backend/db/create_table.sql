-- Create validation_results table in Supabase
-- Run this in: Supabase Dashboard > SQL Editor > New Query

CREATE TABLE IF NOT EXISTS public.validation_results (
    id BIGSERIAL PRIMARY KEY,
    input TEXT NOT NULL,
    provider VARCHAR(100),
    scenario VARCHAR(100),
    model VARCHAR(100),
    output TEXT,
    validation_score FLOAT,
    validation_method VARCHAR(200),
    confidence VARCHAR(50),
    procedure VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_model_scenario 
ON public.validation_results(model, scenario);

CREATE INDEX IF NOT EXISTS idx_created_at 
ON public.validation_results(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_input_model
ON public.validation_results(input, model);

-- Enable Row Level Security (RLS)
ALTER TABLE public.validation_results ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust for production)
CREATE POLICY "Enable all access for validation_results"
ON public.validation_results
FOR ALL
USING (true)
WITH CHECK (true);

-- Grant access
GRANT ALL ON public.validation_results TO postgres, anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE validation_results_id_seq TO postgres, anon, authenticated, service_role;
