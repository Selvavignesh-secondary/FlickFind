import pyarrow.parquet as pq
import pandas as pd
import json
import psycopg2
from psycopg2.extras import execute_values
import time
import os
import gc

def seed_database_complete_warehouse():
    parquet_filename = "movies_raw.parquet"
    
    if not os.path.exists(parquet_filename):
        print(f"❌ Error: Missing '{parquet_filename}' inside backend folder.")
        return

    print("🔌 Connecting to Dockerized PostgreSQL container...")
    conn = psycopg2.connect(
        dbname="flickfind_db", 
        user="flickadmin",       
        password="flicksecretpassword",   
        host="127.0.0.1", 
        port="5433"
    )
    cursor = conn.cursor()

    print("🧹 Purging old table schemas to prepare clean tracking memory pages...")
    cursor.execute("TRUNCATE TABLE movies RESTART IDENTITY;")
    conn.commit()

    print("🛡️ LAUNCHING MAX-FEATURE DATA WAREHOUSE EXTRACTION ENGINE...")
    start_time = time.time()
    
    parquet_file = pq.ParquetFile(parquet_filename)
    
    # 🎯 TARGET CORE UPDATED: Pulling music_composer and director_of_photography explicitly from source
    column_targets = [
        "id", "imdb_id", "title", "original_title", "tagline", "overview", "genres",
        "release_date", "status", "runtime", "original_language", "budget", "revenue",
        "vote_average", "vote_count", "popularity", "director", "director_of_photography", 
        "music_composer", "movie_cast", "writers", "producers", "production_companies", 
        "production_countries", "poster_path", "title_tagline_overview", "token_count", "embedding"
    ]
    total_inserted = 0
    
    for record_batch in parquet_file.iter_batches(batch_size=15000, columns=column_targets):
        chunk_df = record_batch.to_pandas()
        chunk_df = chunk_df.dropna(subset=["id", "title", "embedding"])
        
        # Numeric conversions
        chunk_df['release_year'] = pd.to_datetime(chunk_df['release_date'], errors='coerce').dt.year.fillna(2000).astype(int)
        chunk_df['imdb_rating'] = chunk_df['vote_average'].fillna(0.0).astype(float)
        chunk_df['imdb_votes'] = chunk_df['vote_count'].fillna(0).astype(int)
        chunk_df['runtime'] = chunk_df['runtime'].fillna(0).astype(int)
        chunk_df['budget'] = chunk_df['budget'].fillna(0.0).astype(float)
        chunk_df['revenue'] = chunk_df['revenue'].fillna(0.0).astype(float)
        chunk_df['popularity'] = chunk_df['popularity'].fillna(0.0).astype(float)
        chunk_df['id'] = chunk_df['id'].astype(int)

        db_insert_rows = []
        
        for row in chunk_df.itertuples():
            try:
                raw_embedding = row.embedding
                if isinstance(raw_embedding, str):
                    vector_array = json.loads(raw_embedding)
                elif isinstance(raw_embedding, list):
                    vector_array = raw_embedding
                else:
                    continue
                
                if len(vector_array) != 768:
                    continue

                db_insert_rows.append((
                    int(row.id),
                    str(row.imdb_id) if pd.notna(row.imdb_id) else None,
                    str(row.title),
                    str(row.original_title) if pd.notna(row.original_title) else None,
                    str(row.tagline) if pd.notna(row.tagline) else None,
                    str(row.overview) if pd.notna(row.overview) else None,
                    str(row.genres) if pd.notna(row.genres) else None,
                    int(row.release_year),
                    str(row.release_date) if pd.notna(row.release_date) else None,
                    str(row.status) if pd.notna(row.status) else None,
                    int(row.runtime),
                    str(row.original_language) if pd.notna(row.original_language) else None,
                    float(row.budget),
                    float(row.revenue),
                    float(row.imdb_rating),
                    int(row.imdb_votes),
                    float(row.popularity),
                    str(row.director) if pd.notna(row.director) else None,
                    str(row.director_of_photography) if pd.notna(row.director_of_photography) else None,
                    str(row.music_composer) if pd.notna(row.music_composer) else None,
                    str(row.movie_cast) if pd.notna(row.movie_cast) else None,
                    str(row.writers) if pd.notna(row.writers) else None,
                    str(row.producers) if pd.notna(row.producers) else None,
                    str(row.production_companies) if pd.notna(row.production_companies) else None,
                    str(row.production_countries) if pd.notna(row.production_countries) else None,
                    str(row.poster_path) if pd.notna(row.poster_path) else None,
                    str(row.title_tagline_overview) if pd.notna(row.title_tagline_overview) else None,
                    int(row.token_count) if pd.notna(row.token_count) else None,
                    0, 
                    str(vector_array)
                ))
            except Exception:
                continue

        if db_insert_rows:
            insert_query = """
                INSERT INTO movies (
                    id, imdb_id, title, original_title, tagline, overview, genres,
                    release_year, release_date, status, runtime, original_language, budget, revenue,
                    imdb_rating, imdb_votes, popularity, director, director_of_photography, music_composer, 
                    movie_cast, writers, producers, production_companies, production_countries, poster_path,
                    title_tagline_overview, token_count, hit_count, mood_vector_data
                ) VALUES %s
                ON CONFLICT (id) DO NOTHING;
            """
            execute_values(cursor, insert_query, db_insert_rows, page_size=1000)
            total_inserted += len(db_insert_rows)
            print(f"🚀 Ingested full metadata slice block. Total Data Warehouse Volume: {total_inserted} records.")
            
        del chunk_df
        del db_insert_rows
        gc.collect()

    conn.commit()
    cursor.close()
    conn.close()

    print("\n🏆 ========================================================")
    print("🏆 FULL-FEATURE WAREHOUSE INGESTION COMPLETELY SUCCESSFUL!")
    print(f"⏱️ Storage compilation time: {time.time() - start_time:.2f} seconds.")
    print(f"🌟 Successfully warehouse-indexed {total_inserted} high-density records inside Docker!")
    print("============================================================")

if __name__ == "__main__":
    seed_database_complete_warehouse()