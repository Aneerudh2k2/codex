# import polars as pl
# from pathlib import Path
# import json
# from tqdm import tqdm
# from crawler.serializers import NdjsonReader
# from crawler.types import PaperAnalysisRun
# from multiprocessing.pool import ThreadPool
# # with NdjsonReader(
# #     Path("data/processed/cs_inlined_papers.jsonl"), PaperAnalysisRun, validate=True
# # ) as f:
# with open("data/processed/cs_inlined_papers.jsonl", "r") as f:
#       responses = [json.loads(line) for line in f]

#       examples = []

#       for r in tqdm(responses):
#             # print(r)
#             examples.append(
#                   (
#                         r["paper_id"],
#                         r["metadata"],
#                         r["discipline"],
#                         r["abstract"],
#                         r["bib_entries"],
#                         r["inlined_texts"]
#                   )
#             )


# chunk_size = 1000

# dataset = pl.DataFrame(examples, schema=["paper_id", "metadata", "discipline", "abstract", "bib_entries", "inlined_texts"]).sort(
#                   by="paper_id"
#             )

# num_chunks = len(dataset) // chunk_size + (1 if len(dataset) % chunk_size != 0 else 0)

# # with ThreadPool(64) as pool:
# for i in range(num_chunks):
#       batch = dataset[i * chunk_size:(i + 1) * chunk_size]
#       batch.write_parquet(f"data/processed/cs_inlined_papers_{i+1}.parquet")


# # dataset.write_parquet("data/processed/cs_inlined_papers.parquet")

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datasets import Dataset

# Define the file paths
jsonl_file = "data/processed/cs_inlined_papers.jsonl"
parquet_file = "data/processed/cs_inlined_papers.parquet"

# Specify the chunk size based on your system's memory
chunk_size = 90000  # Adjust based on available memory

# Create an empty Parquet writer
parquet_writer = None

# Read the JSONL file in chunks
for chunk in pd.read_json(jsonl_file, lines=True, chunksize=chunk_size):
      table = pa.Table.from_pandas(chunk)

      if parquet_writer is None:
            parquet_writer = pq.ParquetWriter(parquet_file, table.schema)

      parquet_writer.write_table(table)

if parquet_writer is not None:
    parquet_writer.close()


