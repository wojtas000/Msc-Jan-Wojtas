import xml.etree.ElementTree as ET
import uuid
import re
import html


class XMLProcessor:
    def __init__(self, path):
        self.documents = []
        self.data = self.load_data(path)
        
    def clean_text(self, raw_text):
        cleaned_text = (
            raw_text.replace('&amp;amp;', '&')
            .replace('&amp;', '&')
            .replace('&lt;', '<')
            .replace('&gt;', '>')
            .replace('&quot;', '"')
            .replace('&apos;', "'")
        )

        cleaned_text = re.sub(r'<.*?>', '', cleaned_text)
        cleaned_text = cleaned_text.replace('\n', ' ').strip()
        for punct in ['.', ',', ':', ';', '!', '?']:
                cleaned_text = cleaned_text.replace(punct, f' {punct} ')
                cleaned_text = ' '.join(cleaned_text.split())

        return cleaned_text

    def process_codings(self, id, codings_text):
        decoded_codings = html.unescape(codings_text)
        root = ET.fromstring(decoded_codings)

        evaluation_dict = {'evaluations': [], 'mentions': []}

        for mention in root.findall('.//mention'):
            mention_dict = {
                "id": mention.get("id"),
                "actorId": mention.findtext("actorId"),
                "psField": mention.findtext("psField"),
                "startIndex": mention.findtext("startIndex"),
                "length": mention.findtext("length"),
                "status": mention.findtext("status")
            }

            evaluation_dict['mentions'].append(mention_dict)
            

        for evaluation in root.findall('.//evaluation'):
            eval_dict = {
                "id": evaluation.get("id"),
                "actorId": evaluation.findtext("actorId"),
                "topicId": evaluation.findtext("topicId"),
                "evaluationTypeValueId": evaluation.findtext("evaluationTypeValueId"),
                "meaningTypeId": evaluation.findtext("meaningTypeId")
            }
            
            evaluation_dict['evaluations'].append(eval_dict)
        
        return evaluation_dict

    def process_xml(self):
        root = ET.fromstring(self.data)
        
        for document in root.findall('.//Document'):
            doc_id = document.get('id')
            
            title = document.find(".//FELD[@NAME='TITEL']")
            text = document.find(".//FELD[@NAME='INHALT']")
            sentiment = document.find(".//FELD[@NAME='EVALUATIONS']")
            coding = document.find(".//FELD[@NAME='CODINGS']")
            
            if title is not None and text is not None and sentiment is not None:
                id = str(uuid.uuid4())
                title = self.clean_text(ET.tostring(title, encoding='unicode', method='text'))
                raw_text = ET.tostring(text, encoding='unicode', method='text')
                text = self.clean_text(raw_text)
                sentiments = self.clean_text(ET.tostring(sentiment, encoding='unicode', method='text'))
            
                codings = document.find(".//FELD[@NAME='CODINGS']")
                if codings is not None:
                    codings_text = ET.tostring(codings, encoding='unicode', method='text')
                    actors = self.process_codings(id, codings_text)

                self.documents.append({
                    'document_id': doc_id,
                    'id': id,
                    'title': title,
                    'raw_text': raw_text,
                    'text': text,
                    'sentiment': sentiments,
                    'actors': actors
                    }
                )
                    
        return self.documents
    
    def load_data(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()

    def get_documents(self):
        return self.documents

    def get_document_ids(self):
        return [document['document_id'] for document in self.documents]

    def get_ids(self):
        return [document['id'] for document in self.documents]

    def get_sentiments(self):
        return [document['sentiment'] for document in self.documents]

    def get_texts(self):
        return [document['text'] for document in self.documents]