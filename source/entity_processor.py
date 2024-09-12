import autorootcwd
import chromadb
import pandas as pd
import os
from dotenv import load_dotenv
from chromadb.utils import embedding_functions
from tqdm import tqdm
from source.output_formatter import OutputFormatter
import json

load_dotenv()


class EntityProcessor:
    def __init__(self, chromadb_host='localhost', chromadb_port=8000, hugging_face_key=None):
        self.client = chromadb.HttpClient(host=chromadb_host, port=chromadb_port)
        self.hugging_face_key = hugging_face_key or os.environ['HUGGING_FACE_KEY']
        self.embed_function = embedding_functions.HuggingFaceEmbeddingFunction(
            api_key=self.hugging_face_key,
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def load_entities(self, entities_file):
        entities = pd.read_csv(entities_file)
        entities = entities[entities['label'].isin(['PER', 'ORG'])].dropna().drop_duplicates()
        return entities

    def prepare_collection_data(self, entities):
        documents = []
        metadatas = []
        ids = []
        for _, row in tqdm(entities.iterrows(), total=len(entities)):
            article_id = str(row["article_id"])
            name = row["name"]
            metadata = {
                "article_id": article_id,
                "from": row["start_pos"],
                "to": row["end_pos"],
                "label": row["label"],
            }
            documents.append(name)
            metadatas.append(metadata)
            ids.append(f"{article_id}_{row['start_pos']}_{row['end_pos']}")
        return documents, metadatas, ids

    def create_collection(self, collection_name, entities_file):
        collection = self.client.create_collection(
            name=collection_name,
            embedding_function=self.embed_function,
            metadata={"hnsw:space": "cosine"}
        )

        entities = self.load_entities(entities_file)
        documents, metadatas, ids = self.prepare_collection_data(entities)

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f'Added {len(ids)} entities to collection "{collection_name}"')

    def get_mentions(self, query_result):
        mentions = []
        for entity, metadata, distance in zip(query_result["documents"][0], query_result["metadatas"][0], query_result["distances"][0]):
            if distance < 0.32:
                mention = {
                    "from": metadata["from"],
                    "to": metadata["to"],
                    "mention": entity
                }
                mentions.append(mention)
        return mentions

    def get_polarity(self, sentiment):
        if sentiment == "positive":
            return 1
        elif sentiment == "negative":
            return -1
        else:
            return 0

    def prepare_output_item(self, article_id, actor, polarity, mentions):
        return {
            "id": article_id,
            "name": actor,
            "polarity": polarity,
            "mentions": mentions
        }

    def save_output(self, output, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in output:
                json_string = json.dumps(item, ensure_ascii=False)
                f.write(json_string + '\n')
        print(f'Output prepared and saved to "{output_file}"')

    def prepare_output(self, collection_name, sentiments_file, output_file, save_output=False):
        collection = self.client.get_collection(collection_name)
        sentiments_df = pd.read_csv(sentiments_file)

        output = []
        for _, row in tqdm(sentiments_df.iterrows(), total=len(sentiments_df)):
            article_id = row["id"]
            actor = row["actor"]
            sentiment = row["sentiment"]

            query_result = collection.query(
                query_texts=[actor],
                n_results=3,
                where={"article_id": article_id}
            )

            mentions = self.get_mentions(query_result)
            if mentions:
                polarity = self.get_polarity(sentiment)
                output_item = self.prepare_output_item(article_id, actor, polarity, mentions)
                output.append(output_item)
        if save_output:
            self.save_output(output, output_file)