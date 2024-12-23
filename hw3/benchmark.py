import os
import subprocess
import psycopg2
import time

# Настройки базы данных
DB_NAME = "testdb"
DB_USER = "user"
DB_PASSWORD = "password"
DB_HOST = "localhost"
DB_PORT = 5433

# Параметры для тестирования
SHARED_BUFFERS_VALUES = ["128MB", "256MB", "512MB"]
PAGE_SIZES = [8192, 16384]  # Размеры страницы в байтах (8Кб, 16Кб)

# Функция для запуска команды в терминале
def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(result.stderr)
    return result.stdout

# Функция для изменения конфигурации PostgreSQL
def update_postgres_config(shared_buffers, page_size):
    config = f"""
shared_buffers = {shared_buffers}
default_statistics_target = 100
page_size = {page_size}
"""
    with open("postgresql.conf", "w") as f:
        f.write(config)
    print(f"Updated PostgreSQL config: shared_buffers={shared_buffers}, page_size={page_size}")

# Функция для перезапуска контейнера PostgreSQL
def restart_postgres():
    run_command("docker-compose down")
    run_command("docker-compose up -d")
    time.sleep(10)  # Даем время для перезапуска контейнера

# Функция для создания таблицы и выполнения теста
def run_test(records_count=2000000):
    # Подключаемся к базе данных
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor()
    
    # Создаем таблицу
    cursor.execute("""
        DROP TABLE IF EXISTS test_table;
        CREATE TABLE test_table (
            id SERIAL PRIMARY KEY,
            unique_key BIGINT UNIQUE,
            value TEXT
        );
    """)
    conn.commit()
    
    # Выполняем вставку записей
    start_time = time.time()
    for i in range(records_count):
        cursor.execute(
            "INSERT INTO test_table (unique_key, value) VALUES (%s, md5(random()::text));",
            (i + 1,),
        )
        if i % 100000 == 0:
            print(f"Inserted {i} records...")
            conn.commit()
    conn.commit()
    end_time = time.time()
    print(f"Time taken for inserting {records_count} records: {end_time - start_time:.2f} seconds")
    
    # Анализ cache hit ratio
    cursor.execute("""
        SELECT sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) AS cache_hit_ratio
        FROM pg_statio_user_tables;
    """)
    cache_hit_ratio = cursor.fetchone()[0]
    print(f"Cache hit ratio: {cache_hit_ratio:.2%}")
    
    cursor.close()
    conn.close()
    return end_time - start_time, cache_hit_ratio

# Основной процесс тестирования
def main():
    results = []
    for shared_buffers in SHARED_BUFFERS_VALUES:
        for page_size in PAGE_SIZES:
            print(f"Testing with shared_buffers={shared_buffers}, page_size={page_size}")
            update_postgres_config(shared_buffers, page_size)
            restart_postgres()
            time_taken, cache_hit_ratio = run_test()
            results.append((shared_buffers, page_size, time_taken, cache_hit_ratio))
    
    # Вывод результатов
    print("\nPerformance Results:")
    for result in results:
        print(
            f"shared_buffers={result[0]}, page_size={result[1]}, "
            f"time_taken={result[2]:.2f}s, cache_hit_ratio={result[3]:.2%}"
        )

if __name__ == "__main__":
    main()
