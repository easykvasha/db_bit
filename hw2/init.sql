-- Создание таблицы
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    sale_date DATE NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    discount NUMERIC(5, 2) DEFAULT 0.0
);

-- Заполнение данными
INSERT INTO sales (customer_id, product_id, sale_date, amount, discount)
SELECT
    trunc(random() * 1000) + 1,
    trunc(random() * 500) + 1,
    '2024-01-01'::DATE + trunc(random() * 365),
    trunc(random() * 1000) + 1,
    CASE WHEN random() < 0.1 THEN trunc(random() * 50) ELSE 0 END
FROM generate_series(1, 1000000);
