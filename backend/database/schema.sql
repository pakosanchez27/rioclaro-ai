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

CREATE TABLE IF NOT EXISTS invoice_document_claims (
    sha256 TEXT PRIMARY KEY,
    invoice_id TEXT,
    state TEXT NOT NULL CHECK (state IN ('processing', 'completed')),
    claimed_at TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);

CREATE TABLE IF NOT EXISTS invoice_business_claims (
    business_key TEXT PRIMARY KEY,
    document_sha256 TEXT NOT NULL,
    invoice_id TEXT,
    state TEXT NOT NULL CHECK (state IN ('processing', 'completed')),
    claimed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_usage_daily (
    usage_date TEXT NOT NULL,
    operation TEXT NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (usage_date, operation)
);

CREATE TABLE IF NOT EXISTS branches (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    price REAL NOT NULL CHECK (price >= 0),
    currency TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS product_aliases (
    alias_key TEXT PRIMARY KEY,
    alias TEXT NOT NULL,
    product_id TEXT NOT NULL REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS inventory (
    product_id TEXT NOT NULL REFERENCES products(id),
    branch_id TEXT NOT NULL REFERENCES branches(id),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (product_id, branch_id)
);

CREATE TABLE IF NOT EXISTS orders (
    folio TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    branch_id TEXT NOT NULL REFERENCES branches(id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    total REAL NOT NULL,
    currency TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    order_folio TEXT NOT NULL REFERENCES orders(folio),
    product_id TEXT NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    PRIMARY KEY (order_folio, product_id)
);

CREATE TABLE IF NOT EXISTS policies (
    id TEXT NOT NULL,
    version INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('current', 'obsolete')),
    PRIMARY KEY (id, version)
);

CREATE TABLE IF NOT EXISTS complaints (
    folio TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    order_folio TEXT REFERENCES orders(folio),
    branch_id TEXT NOT NULL REFERENCES branches(id),
    message TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluation_sessions (
    token_hash TEXT PRIMARY KEY,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluation_login_guard (
    id TEXT PRIMARY KEY,
    failed_count INTEGER NOT NULL,
    locked_until TEXT NOT NULL
);
