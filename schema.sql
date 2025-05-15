-- Survey table
CREATE TABLE survey (
    hhid VARCHAR(50) PRIMARY KEY,
    selected_district VARCHAR(100),
    selected_subcounty VARCHAR(100),
    selected_parish VARCHAR(100),
    selected_village VARCHAR(100),
    gpsloc VARCHAR(100)
    -- Add other columns as needed
);

-- Campaign nets table
CREATE TABLE campnets (
    net_id INT IDENTITY(1,1) PRIMARY KEY,
    hhid VARCHAR(50),
    brand VARCHAR(100),
    distribution_date DATE,
    FOREIGN KEY (hhid) REFERENCES survey (hhid)
);

-- Lost nets table
CREATE TABLE lostnets (
    lost_net_id INT IDENTITY(1,1) PRIMARY KEY,
    hhid VARCHAR(50),
    reason VARCHAR(255),
    loss_date DATE,
    FOREIGN KEY (hhid) REFERENCES survey (hhid)
); 