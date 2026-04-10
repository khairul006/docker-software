-- appdb.dbo.noncash_transaction definition

-- Drop table

-- DROP TABLE appdb.dbo.noncash_transaction;

CREATE TABLE noncash_transaction (
	id int IDENTITY(1,1) NOT NULL,
	exit_plaza varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	entry_plaza varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	money_value decimal(8,2) NULL,
	remarks varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	updated_at datetime2 DEFAULT sysdatetime() NULL,
	CONSTRAINT ncsh_pkey PRIMARY KEY (id)
);

-- Insert 10,000 random rows
INSERT INTO [noncash_transaction] (exit_plaza, entry_plaza, money_value, updated_at)
SELECT 
    -- 3-digit random string (100–999)
    CAST(FLOOR(RAND(CHECKSUM(NEWID())) * 900) + 100 AS VARCHAR(3)) AS exit_plaza,
    -- 3-digit random string (100–999)
    CAST(FLOOR(RAND(CHECKSUM(NEWID()) + 1) * 900) + 100 AS VARCHAR(3)) AS entry_plaza,
    -- random decimal 1.00 – 50.00
    CAST((RAND(CHECKSUM(NEWID()) + 2) * 49 + 1) AS DECIMAL(8,2)) AS money_value,
    -- random datetime within last 30 days
    DATEADD(
        DAY,
        -CAST(RAND(CHECKSUM(NEWID()) + 3) * 30 AS INT),
        SYSDATETIME()
    ) AS updated_at
FROM master.dbo.spt_values
WHERE type = 'P'
AND number BETWEEN 1 AND 10000;