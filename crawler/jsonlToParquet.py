import polars as pl
from pathlib import Path
import json
from tqdm import tqdm
from crawler.serializers import NdjsonReader
from crawler.types import PaperAnalysisRun
from multiprocessing.pool import ThreadPool
# with NdjsonReader(
#     Path("data/processed/cs_inlined_papers.jsonl"), PaperAnalysisRun, validate=True
# ) as f:
with open("data/processed/cs_inlined_papers.jsonl", "r") as f:
      responses = [json.loads(line) for line in f]

      examples = []

      for r in tqdm(responses):
            # print(r)
            examples.append(
                  (
                        r["paper_id"],
                        r["metadata"],
                        r["discipline"],
                        r["abstract"],
                        r["bib_entries"],
                        r["inlined_texts"]
                  )
            )

with ThreadPool(64) as pool:
      dataset = pl.DataFrame(examples, schema=["paper_id", "metadata", "discipline", "abstract", "bib_entries", "inlined_texts"]).sort(
            by="paper_id"
      )
      pool.imap_unordered(dataset.write_parquet, ["data/processed/cs_inlined_papers.parquet"])


# dataset.write_parquet("data/processed/cs_inlined_papers.parquet")
