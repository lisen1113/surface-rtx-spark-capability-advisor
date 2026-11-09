from fastapi.testclient import TestClient
import re

from app.faq import FAQ
from app.main import app


client = TestClient(app)


def test_english_faq_keeps_source_identity_and_marks_untranslated_entries():
    source = client.get('/api/faq?limit=20').json()
    english = client.get('/api/faq?limit=20&lang=en').json()
    assert source['indexed_total'] == english['indexed_total'] == len(FAQ)
    assert english['translated_total'] == 126
    for original, translated in zip(source['items'], english['items']):
        assert translated['id'] == original['id']
        assert translated['source_url'] == original['source_url']
    assert english['items'][0]['question'] == 'What is Artificial intelligence (AI)?'
    assert english['items'][0]['translation_status'] == 'translated_draft'
    assert english['items'][18]['translation_status'] == 'translated_draft'
    assert english['items'][18]['category'] == 'Model architectures'
    for item in client.get('/api/faq?limit=126&lang=en').json()['items']:
        assert not re.search(r'[\u3400-\u9fff]', ' '.join(item[key] for key in
            ('question', 'easy_answer', 'expert_answer', 'misconception', 'sales_tip')))
    assert client.get('/api/faq?limit=54&lang=en').json()['items'][36]['category'] == 'Models and memory'
    assert client.get('/api/faq?limit=72&lang=en').json()['items'][54]['category'] == 'Inference performance'
    assert client.get('/api/faq?limit=90&lang=en').json()['items'][72]['category'] == 'Quantization and precision'
    assert client.get('/api/faq?limit=108&lang=en').json()['items'][90]['category'] == 'RTX Spark hardware'
    assert client.get('/api/faq?limit=126&lang=en').json()['items'][108]['category'] == 'Windows and compatibility'
    assert client.get('/api/faq?limit=126&lang=en').json()['items'][108]['source_url'].startswith('https://learn.microsoft.com/')
    pending = client.get('/api/faq?limit=127&lang=en').json()['items'][126]
    assert pending['translation_status'] == 'pending'
    assert pending['question'] == FAQ[126]['question']


def test_english_faq_search_and_home_request_language():
    result = client.get('/api/faq?lang=en&q=Embedding%20vector').json()
    assert result['total'] == 2
    assert all(item['translation_status'] == 'translated_draft' for item in result['items'])
    page = client.get('/en').text
    assert "+'&lang=en'" in page
    assert 'English translation pending' in page
