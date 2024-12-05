import uuid
from unstructured.partition.pdf import partition_pdf
from langchain.vectorstores import Chroma
from langchain.storage import InMemoryStore
from langchain.schema.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

####pdf processor
class PDFProcessor:
    def __init__(self):
        self.vectorstore = None
        self.retriever = None
        self.chunks = None
        self.texts = []
        self.tables = []
        self.images = []
        self.text_summaries = []
        self.table_summaries = []
        self.image_summaries = []
        
    @staticmethod
    def generate_session_id():
        return str(uuid.uuid4())
    
    async def process_pdf(self, file_path: str):
        try:
            # Process PDF
            self.chunks = partition_pdf(
                filename=file_path,
                infer_table_structure=True,
                strategy="hi_res",
                extract_image_block_types=["Image"],
                extract_image_block_to_payload=True,
                chunking_strategy="by_title",
                max_characters=10000,
                combine_text_under_n_chars=2000,
                new_after_n_chars=6000,
                extract_images_in_pdf=True,
            )
            
            # Separate elements
            for chunk in self.chunks:
                if "Table" in str(type(chunk)):
                    self.tables.append(chunk)
                if "CompositeElement" in str(type(chunk)):
                    self.texts.append(chunk)
            
            self.images = self._get_images_base64(self.chunks)
            
            # Generate summaries
            await self._generate_summaries()
            
            # Initialize retriever
            self._initialize_retriever()
            
        except Exception as e:
            print(f"Error in process_pdf: {str(e)}")  # Add logging
            raise
    
    def _get_images_base64(self, chunks):
        images_b64 = []
        for chunk in chunks:
            if "CompositeElement" in str(type(chunk)):
                chunk_els = chunk.metadata.orig_elements
                for el in chunk_els:
                    if "Image" in str(type(el)):
                        images_b64.append(el.metadata.image_base64)
        return images_b64
    
    async def _generate_summaries(self):
        try:
            # Text and Table summaries
            prompt_text = """
            You are an assistant tasked with summarizing tables and text.
            Give a concise summary of the table or text.
            Respond only with the summary, no additional comment.
            Just give the summary as it is.
            Table or text chunk: {element}
            """
            prompt = ChatPromptTemplate.from_template(prompt_text)
            
            # Summary chain for text
            model = ChatGroq(temperature=0.5, model="llama-3.1-8b-instant")
            summarize_chain = {"element": lambda x: x} | prompt | model | StrOutputParser()
            
            # Generate summaries
            if self.texts:
                self.text_summaries = await summarize_chain.abatch(self.texts)
            
            if self.tables:
                tables_html = [table.metadata.text_as_html for table in self.tables]
                self.table_summaries = await summarize_chain.abatch(tables_html)
            
            # Image summaries
            if self.images:
                prompt_template = """Describe the image in detail. For context,
                                the image is part of a research paper explaining the transformers
                                architecture. Be specific about graphs, such as bar plots."""
                messages = [
                    (
                        "user",
                        [
                            {"type": "text", "text": prompt_template},
                            {
                                "type": "image_url",
                                "image_url": {"url": "data:image/jpeg;base64,{image}"},
                            },
                        ],
                    )
                ]
                
                prompt = ChatPromptTemplate.from_messages(messages)
                chain = prompt | ChatOpenAI(model="gpt-4o") | StrOutputParser()
                self.image_summaries = await chain.abatch(self.images)
                
        except Exception as e:
            print(f"Error in _generate_summaries: {str(e)}")  # Add logging
            raise
    
    def _initialize_retriever(self):
        try:
            # Initialize vectorstore
            self.vectorstore = Chroma(
                collection_name="multi_modal_rag",
                embedding_function=OpenAIEmbeddings()
            )
            
            # Storage for parent documents
            store = InMemoryStore()
            id_key = "doc_id"
            
            # Initialize retriever
            self.retriever = MultiVectorRetriever(
                vectorstore=self.vectorstore,
                docstore=store,
                id_key=id_key,
            )
            
            # Add documents to retriever
            if self.texts and self.text_summaries:
                doc_ids = [str(uuid.uuid4()) for _ in self.texts]
                summary_texts = [
                    Document(page_content=summary, metadata={id_key: doc_ids[i]})
                    for i, summary in enumerate(self.text_summaries)
                ]
                self.retriever.vectorstore.add_documents(summary_texts)
                self.retriever.docstore.mset(list(zip(doc_ids, self.texts)))
            
            if self.tables and self.table_summaries:
                table_ids = [str(uuid.uuid4()) for _ in self.tables]
                summary_tables = [
                    Document(page_content=summary, metadata={id_key: table_ids[i]})
                    for i, summary in enumerate(self.table_summaries)
                ]
                self.retriever.vectorstore.add_documents(summary_tables)
                self.retriever.docstore.mset(list(zip(table_ids, self.tables)))
            
            if self.images and self.image_summaries:
                img_ids = [str(uuid.uuid4()) for _ in self.images]
                summary_img = [
                    Document(page_content=summary, metadata={id_key: img_ids[i]})
                    for i, summary in enumerate(self.image_summaries)
                ]
                self.retriever.vectorstore.add_documents(summary_img)
                self.retriever.docstore.mset(list(zip(img_ids, self.images)))
                
        except Exception as e:
            print(f"Error in _initialize_retriever: {str(e)}")  # Add logging
            raise
