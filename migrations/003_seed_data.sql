-- AlphaRadar Seed Data — MVP Universe
-- Sample companies, insider trades, job postings, filing events, and signals
-- Safe to re-run: all inserts use ON CONFLICT DO NOTHING

-- ── MVP Universe Companies ──────────────────────────────────────────────────

INSERT INTO companies (ticker, name, cik, sector, industry, market_cap_bucket) VALUES
    ('AAPL', 'Apple Inc.', '0000320193', 'Technology', 'Consumer Electronics', 'mega'),
    ('MSFT', 'Microsoft Corporation', '0000789019', 'Technology', 'Software - Infrastructure', 'mega'),
    ('GOOGL', 'Alphabet Inc.', '0001652044', 'Technology', 'Internet Content & Information', 'mega'),
    ('AMZN', 'Amazon.com Inc.', '0001018724', 'Consumer Cyclical', 'Internet Retail', 'mega'),
    ('NVDA', 'NVIDIA Corporation', '0001045810', 'Technology', 'Semiconductors', 'mega'),
    ('META', 'Meta Platforms Inc.', '0001326801', 'Technology', 'Internet Content & Information', 'mega'),
    ('TSLA', 'Tesla Inc.', '0001318605', 'Consumer Cyclical', 'Auto Manufacturers', 'mega'),
    ('JPM', 'JPMorgan Chase & Co.', '0000019617', 'Financial Services', 'Banks - Diversified', 'mega'),
    ('V', 'Visa Inc.', '0001403161', 'Financial Services', 'Credit Services', 'mega'),
    ('JNJ', 'Johnson & Johnson', '0000200406', 'Healthcare', 'Drug Manufacturers', 'mega'),
    ('UNH', 'UnitedHealth Group', '0000731766', 'Healthcare', 'Healthcare Plans', 'mega'),
    ('WMT', 'Walmart Inc.', '0000104169', 'Consumer Defensive', 'Discount Stores', 'mega'),
    ('PG', 'Procter & Gamble Co.', '0000080424', 'Consumer Defensive', 'Household Products', 'mega'),
    ('MA', 'Mastercard Inc.', '0001141391', 'Financial Services', 'Credit Services', 'mega'),
    ('HD', 'Home Depot Inc.', '0000354950', 'Consumer Cyclical', 'Home Improvement Retail', 'large'),
    ('DIS', 'Walt Disney Co.', '0001744489', 'Communication Services', 'Entertainment', 'large'),
    ('CRM', 'Salesforce Inc.', '0001108524', 'Technology', 'Software - Application', 'large'),
    ('NFLX', 'Netflix Inc.', '0001065280', 'Communication Services', 'Entertainment', 'large'),
    ('AMD', 'Advanced Micro Devices', '0000002488', 'Technology', 'Semiconductors', 'large'),
    ('INTC', 'Intel Corporation', '0000050863', 'Technology', 'Semiconductors', 'large'),
    ('PYPL', 'PayPal Holdings Inc.', '0001633917', 'Financial Services', 'Credit Services', 'large'),
    ('SHOP', 'Shopify Inc.', '0001594805', 'Technology', 'Software - Application', 'large'),
    ('SQ', 'Block Inc.', '0001512673', 'Technology', 'Software - Infrastructure', 'mid'),
    ('SNOW', 'Snowflake Inc.', '0001640147', 'Technology', 'Software - Application', 'mid'),
    ('PLTR', 'Palantir Technologies', '0001321655', 'Technology', 'Software - Infrastructure', 'mid'),
    ('NET', 'Cloudflare Inc.', '0001477333', 'Technology', 'Software - Infrastructure', 'mid'),
    ('DDOG', 'Datadog Inc.', '0001561550', 'Technology', 'Software - Application', 'mid'),
    ('ZS', 'Zscaler Inc.', '0001713683', 'Technology', 'Software - Infrastructure', 'mid'),
    ('CRWD', 'CrowdStrike Holdings', '0001535527', 'Technology', 'Software - Infrastructure', 'mid'),
    ('PANW', 'Palo Alto Networks', '0001327567', 'Technology', 'Software - Infrastructure', 'large')
ON CONFLICT (ticker) DO NOTHING;

-- ── Sample Insider Trades ───────────────────────────────────────────────────

INSERT INTO insider_trades (ticker, company_name, cik, filer_name, filer_title, is_officer, is_director, transaction_type, transaction_code, shares, price_per_share, total_value, filing_date, transaction_date, source_url, idempotency_key) VALUES
    ('AAPL', 'Apple Inc.', '0000320193', 'Tim Cook', 'CEO', TRUE, TRUE, 'buy', 'P', 50000, 178.50, 8925000, '2025-12-15', '2025-12-14', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193', 'seed:aapl:cook:20251215:P:50000'),
    ('AAPL', 'Apple Inc.', '0000320193', 'Luca Maestri', 'CFO', TRUE, FALSE, 'buy', 'P', 20000, 179.00, 3580000, '2025-12-16', '2025-12-15', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193', 'seed:aapl:maestri:20251216:P:20000'),
    ('AAPL', 'Apple Inc.', '0000320193', 'Jeff Williams', 'COO', TRUE, FALSE, 'buy', 'P', 15000, 177.80, 2667000, '2025-12-17', '2025-12-16', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193', 'seed:aapl:williams:20251217:P:15000'),
    ('NVDA', 'NVIDIA Corporation', '0001045810', 'Jensen Huang', 'CEO', TRUE, TRUE, 'sell', 'S', 100000, 480.00, 48000000, '2025-12-10', '2025-12-09', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001045810', 'seed:nvda:huang:20251210:S:100000'),
    ('CRM', 'Salesforce Inc.', '0001108524', 'Marc Benioff', 'CEO', TRUE, TRUE, 'buy', 'P', 25000, 265.00, 6625000, '2025-12-18', '2025-12-17', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001108524', 'seed:crm:benioff:20251218:P:25000'),
    ('CRM', 'Salesforce Inc.', '0001108524', 'Amy Weaver', 'CFO', TRUE, FALSE, 'buy', 'P', 10000, 264.50, 2645000, '2025-12-19', '2025-12-18', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001108524', 'seed:crm:weaver:20251219:P:10000'),
    ('PLTR', 'Palantir Technologies', '0001321655', 'Alex Karp', 'CEO', TRUE, TRUE, 'sell', 'S', 500000, 22.50, 11250000, '2025-12-12', '2025-12-11', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001321655', 'seed:pltr:karp:20251212:S:500000')
ON CONFLICT (idempotency_key) DO NOTHING;

-- ── Sample Job Postings ─────────────────────────────────────────────────────

INSERT INTO job_postings (ticker, company_name, title, department, seniority, location, is_remote, source_name, posted_date, idempotency_key) VALUES
    ('NVDA', 'NVIDIA Corporation', 'Senior ML Infrastructure Engineer', 'engineering', 'senior', 'Santa Clara, CA', FALSE, 'fixture', '2025-12-01', 'seed:nvda:sr-ml-infra:santa-clara'),
    ('NVDA', 'NVIDIA Corporation', 'Staff GPU Architect', 'engineering', 'lead', 'Santa Clara, CA', FALSE, 'fixture', '2025-12-02', 'seed:nvda:staff-gpu-arch:santa-clara'),
    ('NVDA', 'NVIDIA Corporation', 'ML Compiler Engineer', 'engineering', 'mid', 'Remote', TRUE, 'fixture', '2025-12-03', 'seed:nvda:ml-compiler:remote'),
    ('NVDA', 'NVIDIA Corporation', 'AI Platform Product Manager', 'product', 'senior', 'Santa Clara, CA', FALSE, 'fixture', '2025-12-04', 'seed:nvda:ai-pm:santa-clara'),
    ('NVDA', 'NVIDIA Corporation', 'Data Center Solutions Architect', 'engineering', 'senior', 'Austin, TX', FALSE, 'fixture', '2025-12-05', 'seed:nvda:dc-solutions:austin'),
    ('NVDA', 'NVIDIA Corporation', 'Deep Learning Researcher', 'engineering', 'senior', 'Remote', TRUE, 'fixture', '2025-12-06', 'seed:nvda:dl-researcher:remote'),
    ('NVDA', 'NVIDIA Corporation', 'Networking Software Engineer', 'engineering', 'mid', 'Santa Clara, CA', FALSE, 'fixture', '2025-12-07', 'seed:nvda:networking-sw:santa-clara'),
    ('NVDA', 'NVIDIA Corporation', 'Enterprise Account Executive', 'sales', 'senior', 'New York, NY', FALSE, 'fixture', '2025-12-08', 'seed:nvda:enterprise-ae:nyc'),
    ('CRM', 'Salesforce Inc.', 'AI Engineer - Einstein', 'engineering', 'senior', 'San Francisco, CA', FALSE, 'fixture', '2025-12-01', 'seed:crm:ai-engineer:sf'),
    ('CRM', 'Salesforce Inc.', 'Staff Backend Engineer', 'engineering', 'lead', 'Remote', TRUE, 'fixture', '2025-12-05', 'seed:crm:staff-backend:remote'),
    ('CRM', 'Salesforce Inc.', 'Enterprise Account Executive', 'sales', 'senior', 'Chicago, IL', FALSE, 'fixture', '2025-12-07', 'seed:crm:enterprise-ae:chicago'),
    ('AAPL', 'Apple Inc.', 'ML Research Scientist', 'engineering', 'senior', 'Cupertino, CA', FALSE, 'fixture', '2025-12-10', 'seed:aapl:ml-research:cupertino'),
    ('AAPL', 'Apple Inc.', 'iOS Platform Engineer', 'engineering', 'mid', 'Cupertino, CA', FALSE, 'fixture', '2025-12-12', 'seed:aapl:ios-platform:cupertino')
ON CONFLICT (idempotency_key) DO NOTHING;

-- ── Sample Filing Events ────────────────────────────────────────────────────

INSERT INTO filing_events (ticker, company_name, cik, filing_type, form_items, filing_date, headline, summary, source_url, accession_number, idempotency_key) VALUES
    ('AAPL', 'Apple Inc.', '0000320193', '8-K', ARRAY['2.02', '9.01'], '2025-12-01', 'Apple Reports Q4 FY2025 Results', 'Record quarterly revenue of $94.9B, up 6% YoY. iPhone revenue beat expectations.', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=8-K', '0000320193-25-000123', '0000320193-25-000123'),
    ('NVDA', 'NVIDIA Corporation', '0001045810', '8-K', ARRAY['1.01', '9.01'], '2025-12-05', 'NVIDIA Announces Strategic Partnership', 'NVIDIA enters definitive agreement for AI infrastructure partnership with major cloud provider.', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001045810&type=8-K', '0001045810-25-000456', '0001045810-25-000456'),
    ('CRM', 'Salesforce Inc.', '0001108524', '8-K', ARRAY['5.02'], '2025-12-10', 'Salesforce Appoints New Chief AI Officer', 'Board appoints Dr. Jane Smith as Chief AI Officer effective January 2026.', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001108524&type=8-K', '0001108524-25-000789', '0001108524-25-000789'),
    ('PLTR', 'Palantir Technologies', '0001321655', '8-K', ARRAY['2.02'], '2025-12-08', 'Palantir Reports Q3 2025 Results', 'Revenue of $710M, up 30% YoY. Government contracts accelerating.', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001321655&type=8-K', '0001321655-25-000321', '0001321655-25-000321')
ON CONFLICT (idempotency_key) DO NOTHING;

-- ── Sample Signals ──────────────────────────────────────────────────────────

INSERT INTO signals (id, type, strength, sentiment, ticker, company_name, headline, detail, score, data, source_name, source_url, idempotency_key, detected_at) VALUES
    ('seed-sig-001', 'insider_buy_cluster', 'strong', 'bullish', 'AAPL', 'Apple Inc.',
     '3 insiders bought $15.2M in AAPL shares within 3 days',
     'CEO Tim Cook, CFO Luca Maestri, and COO Jeff Williams all purchased significant shares between Dec 14-16. Combined purchases total 85,000 shares worth $15.17M. This cluster of C-suite buying often precedes positive company developments.',
     82.0,
     '{"insider_count": 3, "total_value": 15172000, "window_days": 3, "buyers": ["Tim Cook", "Luca Maestri", "Jeff Williams"], "avg_price": 178.49}',
     'sec_form4', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193', 'insider_buy_cluster:AAPL:20251217',
     '2025-12-17 10:00:00+00'),
    ('seed-sig-002', 'hiring_momentum', 'moderate', 'bullish', 'NVDA', 'NVIDIA Corporation',
     'NVIDIA engineering hiring surge: 8 new roles in 7 days',
     'NVIDIA posted 8 engineering positions in the past week, with 6 focused on ML/AI infrastructure. This is 3x their typical weekly posting rate. Heavy investment in AI talent signals continued product expansion.',
     71.0,
     '{"total_postings": 8, "engineering_postings": 6, "weekly_avg": 2.5, "surge_ratio": 3.2, "top_departments": {"engineering": 7, "sales": 1}}',
     'job_postings', null, 'hiring_momentum:NVDA:20251208',
     '2025-12-08 14:00:00+00'),
    ('seed-sig-003', 'filing_catalyst', 'strong', 'bullish', 'NVDA', 'NVIDIA Corporation',
     'NVIDIA 8-K: Strategic AI infrastructure partnership announced',
     'NVIDIA filed an 8-K disclosing a definitive agreement for a strategic AI infrastructure partnership with a major cloud provider. Item 1.01 (material agreement) filing suggests significant revenue implications.',
     78.0,
     '{"filing_type": "8-K", "form_items": ["1.01", "9.01"], "accession": "0001045810-25-000456", "is_material": true}',
     'sec_8k', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001045810&type=8-K', 'filing_catalyst:NVDA:0001045810-25-000456',
     '2025-12-05 16:30:00+00'),
    ('seed-sig-004', 'insider_buy_cluster', 'moderate', 'bullish', 'CRM', 'Salesforce Inc.',
     '2 insiders bought $9.3M in CRM shares within 2 days',
     'CEO Marc Benioff and CFO Amy Weaver purchased shares on consecutive days. Combined value of $9.27M signals insider confidence ahead of AI product launches.',
     68.0,
     '{"insider_count": 2, "total_value": 9270000, "window_days": 2, "buyers": ["Marc Benioff", "Amy Weaver"], "avg_price": 264.77}',
     'sec_form4', 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001108524', 'insider_buy_cluster:CRM:20251219',
     '2025-12-19 11:00:00+00')
ON CONFLICT (id) DO NOTHING;

-- ── Sample Briefs ───────────────────────────────────────────────────────────

INSERT INTO briefs (ticker, signal_id, brief_type, headline, body, evidence_summary, model_used, generated_at) VALUES
    ('AAPL', 'seed-sig-001', 'signal',
     'Apple Insider Buy Cluster: Strong Bullish Signal',
     E'Three senior Apple executives made coordinated stock purchases over a 3-day window (Dec 14-16, 2025), totaling $15.17M across 85,000 shares.\n\n**What happened:**\n- CEO Tim Cook purchased 50,000 shares at $178.50 ($8.93M)\n- CFO Luca Maestri purchased 20,000 shares at $179.00 ($3.58M)\n- COO Jeff Williams purchased 15,000 shares at $177.80 ($2.67M)\n\n**Why it matters:**\nClustered insider buying by C-suite executives is one of the strongest insider signals. When multiple senior leaders buy within a short window, it often indicates insider confidence in near-term company performance. Historical studies show clustered insider buys outperform the market by 7-12% over the following 6 months.\n\n**Alternative explanations:**\n- Scheduled purchases under 10b5-1 plans (would reduce signal strength)\n- Tax-related portfolio rebalancing\n- Compensation-linked purchases\n\n**Disclaimer:** This is informational analysis, not investment advice.',
     '{"signal_id": "seed-sig-001", "insider_count": 3, "total_value": 15172000, "source": "SEC Form 4"}',
     'groq/llama-3.3-70b-versatile',
     '2025-12-17 10:05:00+00'),
    ('NVDA', 'seed-sig-002', 'signal',
     'NVIDIA Hiring Momentum: AI Talent Investment Accelerating',
     E'NVIDIA posted 8 new engineering positions in the past week, 3.2x their typical weekly rate, with a strong focus on ML/AI infrastructure roles.\n\n**What happened:**\n- 8 new positions posted in 7 days (typical average: 2.5/week)\n- 6 of 8 positions are ML/AI-focused: ML Infrastructure, GPU Architecture, ML Compiler, AI Platform, Data Center Solutions, Deep Learning Research\n- Roles span Santa Clara, Austin, and remote locations\n\n**Why it matters:**\nA sudden spike in specialized hiring often precedes new product launches or major capacity expansions. NVIDIA''s focus on ML infrastructure talent aligns with their AI accelerator roadmap. Companies that hire aggressively in focused areas tend to be investing ahead of anticipated demand.\n\n**Alternative explanations:**\n- Backfilling departures rather than net new growth\n- Reposting filled positions due to administrative processes\n- Seasonal hiring cycles\n\n**Disclaimer:** This is informational analysis, not investment advice.',
     '{"signal_id": "seed-sig-002", "total_postings": 8, "engineering_ratio": 0.875, "source": "Job postings aggregator"}',
     'groq/llama-3.3-70b-versatile',
     '2025-12-08 14:05:00+00');
