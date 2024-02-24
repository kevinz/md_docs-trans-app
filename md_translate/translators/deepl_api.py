import requests

from ._api_base import APIBaseTranslator
import os


class DeeplAPITranslateProvider(APIBaseTranslator):
    HOST = 'https://api.deepl.com/'

    API_KEY_SETTINGS_PARAM = 'deepl_api_key'

    def make_request(self, *, text: str, split_sentences: bool) -> requests.Response:
        headers = {
            'Authorization': f'DeepL-Auth-Key {self.api_key}',
        }
        glossary_id = os.environ.get('GLOSSARY_ID', "338b0725-2124-4c56-b243-14f8d3804d66")
        preserve_format = os.environ.get('preserve_format','1')
        split_sen = os.environ.get('split_sentences','0')
        # gets overrided by param
        if split_sentences :
            split_sen = '1'
        #else: 
            # follow the env var
            
        tag_handle = os.environ.get('tag_handle', "xml")
        # comma split format
        ign_tags = os.environ.get('ign_tags', "").split(',')

        request_body = {
            
            'text': [
                text,
            ],
            'source_lang': self.from_language.upper(),
            'target_lang': self.to_language.upper(),
            'preserve_formatting':True if preserve_format == '1' else False,
            'glossary_id': glossary_id,
            'split_sentences': split_sen,
        }
        if tag_handle and tag_handle in ["html", "xml"]:
            request_body['tag_handling'] = ''.join(tag_handle)

        if ign_tags:
            request_body['ignore_tags'] = ign_tags

        response = self._session.post(
            url=f'{self.HOST}v1/translate',
            headers=headers,
            json=request_body,
        )
        response.raise_for_status()
        return response

    def get_translated_data(self, response: requests.Response) -> str:
        return response.json()['translations'][0]['text']
