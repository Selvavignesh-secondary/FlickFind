import pyarrow.parquet as pq
import pandas as pd
import json  # Used to safely transform text strings back into true float arrays
import psycopg2
from psycopg2.extras import execute_values
import time
import os
import gc

def seed_database_ultra_low_ram():
    parquet_filename = "movies_raw.parquet"
    
    if not os.path.exists(parquet_filename):
        print(f"❌ Error: Missing '{parquet_filename}' inside backend folder.")
        return

    print("🔌 Connecting to Dockerized PostgreSQL container...")
    conn = psycopg2.connect(
        dbname="flickfind_db", 
        user="flickadmin",       # 👈 MUST match your username from database.py
        password="flicksecretpassword",   # 👈 MUST match your password from database.py
        host="127.0.0.1", 
        port="5433"
    )
    cursor = conn.cursor()

    print("🧹 Purging old table schemas to prepare clean tracking memory pages...")
    cursor.execute("TRUNCATE TABLE movies RESTART IDENTITY;")
    conn.commit()

    print("🛡️ LAUNCHING STRING-DECODING MEMORY-GUARD STREAM (Target: < 1.2 GB RAM)...")
    start_time = time.time()
    
    parquet_file = pq.ParquetFile(parquet_filename)
    column_targets = ["id", "title", "release_date", "vote_average", "embedding"]
    total_inserted = 0
    
    for record_batch in parquet_file.iter_batches(batch_size=25000, columns=column_targets):
        chunk_df = record_batch.to_pandas()
        chunk_df = chunk_df.dropna(subset=["id", "title", "embedding"])
        
        chunk_df['release_year'] = pd.to_datetime(chunk_df['release_date'], errors='coerce').dt.year.fillna(2000).astype(int)
        chunk_df['imdb_rating'] = chunk_df['vote_average'].fillna(0.0).astype(float)
        chunk_df['id'] = chunk_df['id'].astype(int)

        db_insert_rows = []
        
        for row in chunk_df.itertuples():
            try:
                raw_embedding = row.embedding
                
                # 🧼 STRIP AND PARSE TEXT REPRESENTATION:
                # Since the vector is a text string format, parse it directly into a clean list of float scalars
                if isinstance(raw_embedding, str):
                    vector_array = json.loads(raw_embedding)
                elif isinstance(raw_embedding, list):
                    vector_array = raw_embedding
                else:
                    continue
                
                # Check the structural dimensions of the true numeric float array
                if len(vector_array) != 768:
                    continue

                db_insert_rows.append((
                    int(row.id),
                    str(row.title),
                    int(row.release_year),
                    float(row.imdb_rating),
                    0,
                    str(vector_array)
                ))
            except Exception:
                continue

        if db_insert_rows:
            insert_query = """
                INSERT INTO movies (id, title, release_year, imdb_rating, hit_count, mood_vector_data)
                VALUES %s
                ON CONFLICT (id) DO NOTHING;
            """
            execute_values(cursor, insert_query, db_insert_rows, page_size=2000)
            total_inserted += len(db_insert_rows)
            print(f"🚀 Ingested slice block. Current database population metric: {total_inserted} records.")
            
        del chunk_df
        del db_insert_rows
        gc.collect()

    conn.commit()
    cursor.close()
    conn.close()

    print("\n🏆 ========================================================")
    print("🏆 SYSTEM INGESTION SPRINT COMPLETELY SUCCESSFUL!")
    print(f"⏱️ Matrix streaming wall-clock time: {time.time() - start_time:.2f} seconds.")
    print(f"🌟 Successfully indexed {total_inserted} high-density 768-dimensional nodes inside Docker!")
    print("============================================================")

if __name__ == "__main__":
    seed_database_ultra_low_ram()