
CREATE TABLE IF NOT EXISTS MaterialType (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE,
    loss_percent REAL NOT NULL
);


CREATE TABLE IF NOT EXISTS Material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type_id INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    stock_quantity REAL NOT NULL,
    min_stock_quantity REAL NOT NULL,
    package_quantity REAL NOT NULL,
    unit_of_measure TEXT NOT NULL,
    FOREIGN KEY (type_id) REFERENCES MaterialType(id)
);


CREATE TABLE IF NOT EXISTS Supplier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    supplier_type TEXT NOT NULL,
    inn TEXT NOT NULL UNIQUE,
    rating INTEGER NOT NULL,
    start_date TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS MaterialSupplier (
    material_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    PRIMARY KEY (material_id, supplier_id),
    FOREIGN KEY (material_id) REFERENCES Material(id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(id)
);

CREATE TABLE IF NOT EXISTS ProductType (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE,
    coefficient REAL NOT NULL
);

