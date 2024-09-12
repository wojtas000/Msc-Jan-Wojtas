import json
import pandas as pd

class OutputFormatter:
    
    def adapt_output_format_for_absa_pytorch(self, output_path, articles_path):
        
        articles_df = pd.read_csv(articles_path, header=None)
        articles_df.columns = ['article_id', 'text_german', 'text_english']

        adapted_output = []
        with open(output_path, 'r') as output:
        
            for item in output:
                item = json.loads(item)
                article_id = item["id"]
                if articles_df[articles_df["article_id"] == article_id].empty:
                    continue
                sentence = articles_df.loc[articles_df["article_id"] == article_id, "text_english"].values[0]
                item = self.shorten_article(item, sentence)
                for mention in item['mentions']:
                    item['sentence_normalized'] = item['sentence_normalized'].replace(mention['mention'], '$T$')
                
                adapted_output.append(
                    {
                        "id": article_id,
                        "sentence": item['sentence_normalized'],
                        "polarity": item['polarity'],
                        "aspect": item['name']
                    }
                )

        return adapted_output


    def adapt_output_format_for_newsmtsc(self, output_path, articles_path):
                
        articles_df = pd.read_csv(articles_path, header=None)
        articles_df.columns = ['article_id', 'text_german', 'text_english']
        
        adapted_output = []
        
        with open(output_path, 'r') as output:
        
            for item in output:
                item = json.loads(item)
                article_id = item["id"]
                if articles_df[articles_df["article_id"] == article_id].empty:
                    continue
                sentence_normalized = articles_df.loc[articles_df["article_id"] == article_id, "text_english"].values[0]
                item = self.shorten_article(item, sentence_normalized)
                sorted_mentions = sorted(item['mentions'], key=lambda x: x['from'])
                mention = sorted_mentions[0]
                if item['polarity'] == 1:
                    polarity = 6.0
                elif item['polarity'] == 0:
                    polarity = 4.0
                else:
                    polarity = 2.0
                target = {
                    "Input.gid": f"{article_id}_{mention['from']}_{mention['to']}_{mention['mention']}",
                    "from": mention["from"],
                    "to": mention["to"],
                    "mention": mention["mention"],
                    "polarity": polarity,
                    "further_mentions": [
                        {
                            "from": m["from"],
                            "to": m["to"],
                            "mention": m["mention"]
                        }
                        for i, m in enumerate(sorted_mentions) if i > 0
                    ]
                }
                # sentence = item['sentence_normalized'].replace('\\', '')
                # for punct in ['.', ',', ':', ';', '!', '?']:
                #     sentence = sentence.replace(punct, f' {punct} ')
                # sentence = ' '.join(sentence.split())
                adapted_item = {
                    "primary_gid": f"{article_id}_{item['mentions'][0]['from']}_{item['mentions'][0]['to']}_{item['mentions'][0]['mention']}",
                    "sentence_normalized": item['sentence_normalized'],
                    "targets": [target]
                }
                adapted_output.append(adapted_item)
        return adapted_output

    def shorten_article(self, item, article):
        shortened_article = ''
        updated_mentions = []
        sorted_mentions = sorted(item['mentions'], key=lambda x: x['from'])
        for mention in sorted_mentions[:1]:
            start = mention['from']
            end = mention['to']

            shortened_sentence = self.extract_text(article, start, end)
            shortened_article = shortened_article.join(' ' + shortened_sentence).strip()
            updated_start = shortened_article.find(mention['mention'])
            updated_end = updated_start + len(mention['mention'])

            updated_mention = {
                'from': updated_start,
                'to': updated_end,
                'mention': mention['mention']
            }
        updated_mentions.append(updated_mention)
        item['mentions'] = updated_mentions
        item['sentence_normalized'] = shortened_article

        return item

    def extract_text(self, text, start, end):
        sentences = text.split('.')
        
        target_index = None
        for i, sentence in enumerate(sentences):
            if sentence.find(text[start:end]) != -1:
                target_index = i
                break
        
        if target_index is None:
            return ""
        
        start_index = max(0, target_index - 1)
        end_index = min(len(sentences) - 1, target_index + 1)

        extracted_sentences = sentences[start_index:end_index+1]
        extracted_text = '. '.join(extracted_sentences).strip()
        
        return extracted_text