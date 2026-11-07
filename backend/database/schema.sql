CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    supplier_tax_id TEXT,
    invoice_number TEXT,
    invoice_date TEXT,
    currency TEXT NOT NULL DEFAULT 'MXN',
    subtotal REAL NOT NULL DEFAULT 0,
    tax REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending_review',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_invoices_status
ON invoices(status);

CREATE INDEX IF NOT EXISTS idx_invoices_date
ON invoices(invoice_date);

CREATE TABLE IF NOT EXISTS invoice_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id TEXT NOT NULL,
    decision TEXT NOT NULL
        CHECK (decision IN ('approve', 'reject')),
    previous_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    notes TEXT,
    reviewed_by_oid TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,

    FOREIGN KEY (invoice_id)
        REFERENCES invoices(id)
);

CREATE INDEX IF NOT EXISTS idx_invoice_reviews_invoice
ON invoice_reviews(invoice_id);

CREATE TABLE IF NOT EXISTS invoice_analyses (
    invoice_id TEXT PRIMARY KEY,
    extraction_json TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);