import pytest
from unittest.mock import MagicMock, patch
from api.rag_utils import RepositoryRAG

@pytest.fixture
def rag_engine_real():
    # This uses the real RepositoryRAG which now includes the pydantic monkeypatch
    return RepositoryRAG()

@pytest.mark.asyncio
async def test_chunk_text(rag_engine_real):
    text = "A" * 2000
    chunks = rag_engine_real.chunk_text(text, chunk_size=1000, overlap=200)
    assert len(chunks) > 1
    assert len(chunks[0]) == 1000

@pytest.mark.asyncio
async def test_get_embedding_fallback(rag_engine_real):
    # Test fallback when client is None
    with patch('api.rag_utils.client', None):
        embedding = await rag_engine_real.get_embedding("test")
        assert len(embedding) == 768
        assert embedding[0] == 0.0

@pytest.mark.asyncio
async def test_query_no_collection(rag_engine_real):
    # mocking SimpleVectorDB.get_collection
    with patch.object(rag_engine_real.vector_db, 'get_collection', side_effect=KeyError("Not found")):
        response = await rag_engine_real.query(1, "test/repo", "How does this work?")
        assert "haven't indexed" in response

@pytest.mark.asyncio
async def test_index_files_basic(rag_engine_real):
    mock_collection = MagicMock()
    with patch.object(rag_engine_real.vector_db, 'get_or_create_collection', return_value=mock_collection):
        with patch.object(rag_engine_real, 'get_embedding', return_value=[0.1]*768):
            files = {"main.py": "print('hello')"}
            await rag_engine_real.index_files(1, "owner/repo", files)
            
            assert mock_collection.add.called
            args, kwargs = mock_collection.add.call_args
            assert kwargs['ids'][0] == "main.py_chunk_0"
            assert kwargs['metadatas'][0]['path'] == "main.py"
