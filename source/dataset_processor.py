import pandas as pd
from tqdm import tqdm
from source.xml_processor import XMLProcessor
from source.translation_processor import TranslationProcessor
from source.sentiment_processor import SentimentProcessor

class DatasetProcessor:
    def __init__(self, name, batch_size=100, start_index=0):
        self.name = name
        self.batch_size = batch_size
        self.start_index = start_index
        self.xml_processor = XMLProcessor(f'data/apa_dataset/{name}.xml')
        self.translation_processor = TranslationProcessor()
        self.sentiment_processor = SentimentProcessor()

    def process_dataset(self):
        documents = self.process_xml()
        self.process_sentiments(documents)
        self.process_articles(documents)

    def process_xml(self):
        return self.xml_processor.process_xml()

    def process_sentiments(self):
        ids = self.xml_processor.get_ids()
        sentiments = self.xml_processor.get_sentiments()
        sentiment_df = self.sentiment_processor.process_sentiments(sentiments, ids)
        sentiment_df.to_csv(f'data/processed_dataset/{self.name}/sentiments.csv', index=False)

    def process_articles(self):
        ids = self.xml_processor.get_ids()
        batch_ids = []
        batch_articles_german = []
        batch_articles_english = []

        for i, article_german in tqdm(enumerate(self.article_generator(), start=self.start_index)):
            batch_ids.append(ids[i])
            batch_articles_german.append(article_german)
            batch_articles_english.append(self.translation_processor.translate(article_german))

            if len(batch_ids) == self.batch_size or i == len(ids) - 1:
                self.save_batch(batch_ids, batch_articles_german, batch_articles_english, i)
                batch_ids.clear()
                batch_articles_german.clear()
                batch_articles_english.clear()

    def article_generator(self):
        for i, article_german in enumerate(self.xml_processor.get_texts()):
            if i >= self.start_index:
                yield article_german

    def save_batch(self, batch_ids, batch_articles_german, batch_articles_english, index):
        batch_articles = pd.DataFrame({
            'id': batch_ids,
            'article_german': batch_articles_german,
            'article_english': batch_articles_english
        })
        batch_articles.to_csv(f'data/processed_dataset/{self.name}/articles.csv', mode='a', header=not bool(index), index=False)
