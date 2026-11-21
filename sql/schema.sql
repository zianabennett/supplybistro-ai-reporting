PRAGMA foreign_keys = ON;

CREATE TABLE suppliers (
    supplier_id TEXT PRIMARY KEY NOT NULL,
    supplier_label TEXT NOT NULL
);

CREATE TABLE purchase_orders (
    order_id TEXT PRIMARY KEY NOT NULL,
    supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
    order_date TEXT NOT NULL,
    promised_date TEXT NOT NULL,
    received_date TEXT,
    cancelled_date TEXT,
    order_value_cents INTEGER NOT NULL
        CHECK (typeof(order_value_cents) = 'integer' AND order_value_cents >= 0),
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    CHECK (received_date IS NULL OR received_date >= order_date),
    CHECK (cancelled_date IS NULL OR cancelled_date >= order_date),
    CHECK (received_date IS NULL OR cancelled_date IS NULL)
);

