import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

import mistune

from md_translate.document.blocks import BaseBlock, CodeSpanBlock, HeadingBlock, ListBlock, ListItemBlock, NewlineBlock,ImageBlock,Paragraph,LinkBlock, SeparatorBlock, TextBlock
from md_translate.document.parser import TypedParser
from md_translate.translators import BaseTranslatorProtocol

if TYPE_CHECKING:
    from md_translate.settings import Settings

logger = logging.getLogger(__name__)


class MarkdownDocument:
    _TRANSLATED_MARK = '<!-- TRANSLATED by md-translate -->'
    _CLEARING_RULES = [
        (re.compile(r'\n{3,}'), '\n\n'),
        (re.compile(r'\n{2,}$'), '\n'),
        (re.compile(r'(?<=[\w.,]) {2,}(?=\w)'), ' '),
    ]

    def __init__(
        self,
        *,
        settings: 'Settings',
        source: Optional[Path] = None,
        blocks: Optional[list[BaseBlock]] = None,
    ) -> None:
        self._settings = settings
        self.source = source
        self.blocks = blocks or []

    def write(
        self,
    ) -> None:
        if not self.source:  # pragma: no cover
            raise ValueError('Only documents with source can be written')
        file_to_write = (
            self.source if not self._settings.new_file else self.__get_new_file_path(self.source)
        )
        file_to_write.write_text('\n'.join([self._TRANSLATED_MARK, self.render_translated()]))
        if not self._settings.save_temp_on_complete:
            temp_file = self.__get_dump_file_path(self.source)
            temp_file.unlink(missing_ok=True)

    def render(self) -> str:
        prerendered = '\n\n'.join(map(str, self.blocks)) + '\n'
        return self.__clear_rendered(prerendered)

    def render_translated(self) -> str:
        rendered_blocks = []
        for block in self.blocks:
            if not self._settings.drop_original:
                rendered_blocks.append(str(block))
                if block.translated_data:
                    rendered_blocks.append(block.translated_data)
            else:
                if block.translated_data:
                    rendered_blocks.append(block.translated_data)
                else:
                    rendered_blocks.append(str(block))
        prerendered = '\n\n'.join(rendered_blocks)
        return self.__clear_rendered(prerendered)

    def translate(self, translator: BaseTranslatorProtocol) -> None:
        blocks_origin = [block for block in self.blocks]
        skip_meta = False
        # 第一步先翻译meta header,Separator Block在后面的循环不会再被翻译,因为separator的translatable为false
        if isinstance(blocks_origin[0], SeparatorBlock) and isinstance(blocks_origin[1], Paragraph) and isinstance(blocks_origin[2], SeparatorBlock):
            blocks_origin[1].translated_data = translator.translate(text=str(blocks_origin[1]), split_sentences=True)
            skip_meta = True
        actual_blocks = blocks_origin[3:] if skip_meta else blocks_origin
        blocks_to_translate = [block for block in actual_blocks if block.should_be_translated]
        logger.info('Found %s blocks to translate', len(blocks_to_translate))
        for  block in blocks_to_translate:
            # text_translated=''
            # # 含嵌套的文本段落
                     # handle the multi-line meta content below
                        # #---
                        # #id: head-metadata
                        # #title: Head Metadata title
                        # #overview: overview
                        # #---
                        # line_arrays = str(dumped_block).split("\n")
                        # meta_data = ''.join(line_arrays[0])
                        # # should be meta content block
                        # if meta_data.startswith('id: ') or meta_data.startswith('title: ') or meta_data.startswith('weight: ') and len(line_arrays) > 1:
                        #     # reserve id line(backstage) and title line(crossplane) without touching
                        #     meta_data += '\n' 
                        #     for line in line_arrays[1:]:
                        #         word_array = line.split(': ')
                        #         #reserve word in front of :
                        #         word_reserved = word_array[0]
                        #         part_translated = translator.translate(text=''.join(word_array[1:]))
                        #         meta_data += (word_reserved +': '+part_translated) + '\n'
                        #     text_translated+=meta_data

            #     for dumped_block in block.children:
            #         # 被嵌套的链接,已经用keepl标注
            #         if isinstance(dumped_block, LinkBlock):
            #             link_text=str(dumped_block.children[0])
            #             link_text = translator.translate(text=link_text)
            #             text_translated += '['+link_text+']' + '('+dumped_block.url+')'
            #         # 被嵌套的图片,已经用keepl标注
            #         elif isinstance(dumped_block, ImageBlock):
            #             text_translated+='!['+dumped_block.alt+']('+dumped_block.url+')'
            #         #else:
            #             # # handle the multi-line meta content below
            #             # #---
            #             # #id: head-metadata
            #             # #title: Head Metadata title
            #             # #overview: overview
            #             # #---
            #             # line_arrays = str(dumped_block).split("\n")
            #             # meta_data = ''.join(line_arrays[0])
            #             # # should be meta content block
            #             # if meta_data.startswith('id: ') or meta_data.startswith('title: ') or meta_data.startswith('weight: ') and len(line_arrays) > 1:
            #             #     # reserve id line(backstage) and title line(crossplane) without touching
            #             #     meta_data += '\n' 
            #             #     for line in line_arrays[1:]:
            #             #         word_array = line.split(': ')
            #             #         #reserve word in front of :
            #             #         word_reserved = word_array[0]
            #             #         part_translated = translator.translate(text=''.join(word_array[1:]))
            #             #         meta_data += (word_reserved +': '+part_translated) + '\n'
            #             #     text_translated+=meta_data
            #             #  codespan block
            #         elif isinstance(dumped_block, CodeSpanBlock):
            #                 text_translated+=str(dumped_block)
            #             # regular textblock
            #             else:
            #                 # Skip when single "the" text occurs
            #                 if str(dumped_block).strip().lower() == "the":
            #                     continue  
            #                 text_translated+= translator.translate(text=str(dumped_block))
            # else:
            #     # if isinstance(block, HeadingBlock):
            #     #     print('meet HeadingBlock:', block,"/Headingblock")
            #     # if isinstance(block, ListBlock):
            #     #     print('meet ListBlock:'+str(block)+"/ListBlock")
            #     #     for list_item in block.children:
            #     #         print('meet ListItemBlock:'+str(list_item)+"/ListItemBlock")
            if isinstance(block, ListBlock):
                list_block_copy = block.copy()
                # listitem
                for i, child_of_list in enumerate(list_block_copy.children):
                    for index, item in enumerate(child_of_list.children):
                        if isinstance(item, TextBlock):
                            if '\n' in item.text:
                                item.text = item.text.replace('\n', ' ')
                                child_of_list.children[index] = item
                               
                #     if isinstance(child_of_list, Paragraph):
                #         print("paragrah:",str(Paragraph))
                #         print("paragraph -1:",child_of_list[index -1],isinstance(child_of_list[index -1], ListItemBlock))
                #         text = str(child_of_list).replace('\n', '')
                #         text_block = TextBlock(text)
                #         if isinstance(list_block_copy.children[index -1],ListItemBlock):
                #             list_block_copy.children[index -1].append(text_block)
                #             list_block_copy.children.remove(child_of_list)
                #             print("append and remove:", text_block)
                translated_data = translator.translate(text=str(list_block_copy),split_sentences=True)
        
                # when split_sentences=1,the first "* " is eaten by deepl api
                if not block.ordered and translated_data and not translated_data.startswith("* "):
                    translated_data = "* " + translated_data
                # ordered listitem's space are eaten after translating
                elif block.ordered and translated_data and not translated_data.startswith("1. "):
                    fixed_trans_data = ''
                    for i, line in enumerate(translated_data.split('\n'),start=1):
                        fixed_trans_data += line.replace(str(i)+'.',str(i)+'. ')+'\n'
                    translated_data = fixed_trans_data                   
            else:
                if str(block).strip().lower() == "the" and (isinstance(block,Paragraph) or isinstance(block,TextBlock)):
                    continue
                translated_data = translator.translate(text=str(block),split_sentences=False)
            block.translated_data = translated_data
            self.cache()
            # logger.info('Translated block %s of %s', number, len(blocks_to_translate))
            logger.debug(f'Translated block: {block}')
            
    def should_be_translated(self) -> bool:
        if not self.source:
            return False
        if self._settings.overwrite:
            return True
        if self._settings.new_file:
            target_file = self.__get_new_file_path(self.source)
            if not target_file.exists():
                return True
            else:
                return self._TRANSLATED_MARK not in target_file.read_text()
        else:
            return self._TRANSLATED_MARK not in self.source.read_text()

    @classmethod
    def from_file(cls, path: Union[str, Path], settings: 'Settings') -> 'MarkdownDocument':
        target_file = cls.__get_file_path(path)
        if not settings.ignore_cache:
            try:
                return cls.restore(source=target_file, settings=settings)
            except FileNotFoundError:
                logger.info('Cache file not found. Loading from source')
        file_content = target_file.read_text()
        return cls(settings=settings, blocks=cls.__parse_blocks(file_content), source=target_file)

    @classmethod
    def from_string(cls, text: str, settings: 'Settings') -> 'MarkdownDocument':
        return cls(blocks=cls.__parse_blocks(text), settings=settings)

    def cache(self) -> None:
        if not self.source:
            return  # pragma: no cover
        dump_file = self.__get_dump_file_path(self.source)
        dump_file.write_text(self._dump_data())

    @classmethod
    def restore(cls, source: Path, settings: 'Settings') -> 'MarkdownDocument':
        dump_file = cls.__get_dump_file_path(source)
        if not dump_file.exists():
            raise FileNotFoundError('Temp file not found: %s', str(dump_file))
        return cls(blocks=cls._load_data(dump_file.read_text()), source=source, settings=settings)

    def _dump_data(self) -> str:
        blocks_dump = [block.dump() for block in self.blocks]
        clean_data = {
            'source': str(self.source),
            'blocks': blocks_dump,
        }
        return json.dumps(clean_data)

    def __clear_rendered(self, string: str) -> str:
        for pattern, replacement in self._CLEARING_RULES:
            string = pattern.sub(replacement, string)
        return string

    @staticmethod
    def _load_data(cache_data: str) -> list[BaseBlock]:
        content = json.loads(cache_data)
        return [BaseBlock.restore(block_data) for block_data in content['blocks']]

    @staticmethod
    def __get_file_path(path: Union[str, Path]) -> Path:
        if isinstance(path, str):
            return Path(path)
        return path

    @staticmethod
    def __get_new_file_path(path: Path) -> Path:
        return path.with_name(f'{path.stem}_translated{path.suffix}')

    @staticmethod
    def __parse_blocks(text: str) -> list[BaseBlock]:
        markdown_parser = mistune.create_markdown(renderer=TypedParser())
        data = [b for b in markdown_parser(text) if b and not isinstance(b, NewlineBlock)]
        return data

    @staticmethod
    def __get_dump_file_path(source: Path) -> Path:
        return Path(source.parent / (source.name + '.tmp'))
