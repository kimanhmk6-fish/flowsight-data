CREATE TABLE lot (
    lot_id          VARCHAR(20) PRIMARY KEY,
    product_id      VARCHAR(20) NOT NULL,
    line_id         VARCHAR(5),
    qty             INTEGER NOT NULL,
    qty_ok          INTEGER DEFAULT 0,
    qty_ng          INTEGER DEFAULT 0,
    created_ts      TIMESTAMP NOT NULL,
    shift           VARCHAR(10),
    confidence      NUMERIC(3, 2) DEFAULT 1.00
);

CREATE TABLE lot_edge (
    edge_id         VARCHAR(20) PRIMARY KEY,
    parent_lot_id   VARCHAR(20) NOT NULL,
    child_lot_id    VARCHAR(20) NOT NULL,
    edge_type       VARCHAR(10) NOT NULL,
    qty             INTEGER,
    edge_time       TIMESTAMP,
    confidence      NUMERIC(3, 2),
    evidence        VARCHAR(50),
    source_file     VARCHAR(60)
);

CREATE TABLE lot_event (
    event_id        VARCHAR(30) PRIMARY KEY,
    lot_id          VARCHAR(20) NOT NULL,
    station_id      VARCHAR(20) NOT NULL,
    event_type      VARCHAR(15) NOT NULL,
    event_code      VARCHAR(20),
    ts_raw          TIMESTAMP,
    ts_aligned      TIMESTAMP,
    source          VARCHAR(20),
    confidence      NUMERIC(3, 2) DEFAULT 1.00
);

CREATE TABLE material_consumption (
    consumption_id  VARCHAR(20) PRIMARY KEY,
    lot_id          VARCHAR(20) NOT NULL,
    mat_lot_id      VARCHAR(30) NOT NULL,
    component_id    VARCHAR(20) NOT NULL,
    qty_consumed    NUMERIC(10, 2),
    consumption_time TIMESTAMP,
    confidence      NUMERIC(3, 2),
    evidence        VARCHAR(50)
);

CREATE TABLE jt_order (
    jt_id           VARCHAR(20) PRIMARY KEY,
    product_id      VARCHAR(20) NOT NULL,
    qty             INTEGER NOT NULL,
    due_ts          TIMESTAMP,
    priority        VARCHAR(10),
    customer        VARCHAR(30),
    status          VARCHAR(15)
);

CREATE TABLE jt_allocation (
    allocation_id   VARCHAR(20) PRIMARY KEY,
    jt_id           VARCHAR(20) NOT NULL,
    lot_id          VARCHAR(20) NOT NULL,
    qty_allocated   INTEGER NOT NULL,
    allocation_time TIMESTAMP,
    confidence      NUMERIC(3, 2),
    evidence        VARCHAR(50)
);

CREATE TABLE shipment (
    shipment_id     VARCHAR(20) NOT NULL,
    jt_id           VARCHAR(20) NOT NULL,
    truck_time      TIMESTAMP,
    cutoff_time     TIMESTAMP,
    qty_planned     INTEGER,
    status          VARCHAR(15),
    confidence      NUMERIC(3, 2),
    evidence        VARCHAR(50),
    PRIMARY KEY (shipment_id, jt_id)
);

CREATE TABLE qc_result (
    qc_id           VARCHAR(30) PRIMARY KEY,
    lot_id          VARCHAR(20) NOT NULL,
    station_id      VARCHAR(20),
    test_type       VARCHAR(10),
    characteristic  VARCHAR(50),
    value           NUMERIC(10, 4),
    lsl             NUMERIC(10, 4),
    usl             NUMERIC(10, 4),
    result          VARCHAR(5),
    ng_code         VARCHAR(20),
    measured_ts     TIMESTAMP,
    source          VARCHAR(20)
);

-- Indexes
CREATE INDEX idx_lot_product ON lot (product_id);
CREATE INDEX idx_lot_created ON lot (created_ts);
CREATE INDEX idx_edge_parent ON lot_edge (parent_lot_id);
CREATE INDEX idx_edge_child ON lot_edge (child_lot_id);
CREATE INDEX idx_event_lot ON lot_event (lot_id);
CREATE INDEX idx_event_station ON lot_event (station_id);
CREATE INDEX idx_alloc_jt ON jt_allocation (jt_id);
CREATE INDEX idx_alloc_lot ON jt_allocation (lot_id);
CREATE INDEX idx_qc_lot ON qc_result (lot_id);
