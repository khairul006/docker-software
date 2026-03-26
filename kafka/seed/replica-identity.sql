CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  order_no VARCHAR(50),
  status VARCHAR(20)
);

-- Note: We are sticking to DEFAULT identity here.
-- Only the Primary Key 'id' will be in the 'before' block.
ALTER TABLE orders REPLICA IDENTITY DEFAULT;