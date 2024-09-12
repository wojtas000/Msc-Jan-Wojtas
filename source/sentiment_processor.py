import pandas as pd

class SentimentProcessor:

    def __init__(self, mapper_path='data/apa_dataset/entities.csv', no_aspect=True):
        self.mapper = self.get_mapper(mapper_path)
        self.no_aspect = no_aspect

    def get_mapper(self, mapper_path):
        entities = pd.read_csv(mapper_path, sep=';',header=0, encoding='latin-1')
        return {str(entities['ID'][i]): entities['NAME'][i] for i in range(len(entities))}

    def explode_sentiment_evaluations(self, df):
        df = (
            df.assign(sentiment=df['sentiment']
            .str.split(' ')) 
            .explode('sentiment') 
            .reset_index(drop=True)
        )
        return df

    def extract_identification_numbers(self, df):
        df['sentiment'] = df['sentiment'].str[5:]
        df[['actor', 'aspect', 'sentiment']] = df['sentiment'].str.split('_', expand=True)
        return df

    def format_columns(self, df):
        for column in ['actor', 'aspect', 'sentiment']:
            df[column] = pd.to_numeric(df[column], errors='coerce').fillna(0).astype(int)
        return df

    def identification_number_to_name_mapping(self, df):
        for column in ['actor', 'aspect', 'sentiment']:
            df[column] = df[column].apply(lambda x: str(x)).map(self.mapper)
        return df

    def filter_and_rename_sentiments(self, df):
        df = df[df['sentiment'].isin(['neutral', 'negativ', 'positiv', 'ambivalent'])]
        df['sentiment'] = df['sentiment'].replace({'neutral': 'neutral', 
                                                   'negativ': 'negative', 
                                                   'positiv': 'positive', 
                                                   'ambivalent': 'ambivalent'})
        
        return df
    
    def filter_no_aspect(self, df):
        if self.no_aspect:
            return df[df['aspect'].isna()].drop(columns=['aspect'])
        else:
            return df

    def process_sentiments(self, sentiments, ids):
        df = pd.DataFrame({'id': ids, 'sentiment': sentiments})
        df = (
            df.pipe(self.explode_sentiment_evaluations)
            .pipe(self.extract_identification_numbers)
            .pipe(self.format_columns)
            .pipe(self.identification_number_to_name_mapping)
            .pipe(self.filter_and_rename_sentiments)
            .pipe(self.filter_no_aspect)
        )
        return df.reset_index(drop=True)
