try:
    from langchain.vectorstores.faiss import FAISS
    print('FAISS_FAISS_OK')
except Exception as e:
    print('FAISS_FAISS_FAIL', type(e).__name__, e)

try:
    import faiss
    print('faiss lib OK')
except Exception as e:
    print('faiss lib FAIL', type(e).__name__, e)
try:
    from langchain.vectorstores.faiss import FAISS
    print('FAISS_FAISS_OK')
except Exception as e:
    print('FAISS_FAISS_FAIL', type(e).__name__, e)

try:
    import faiss
    print('faiss lib OK')
except Exception as e:
    print('faiss lib FAIL', type(e).__name__, e)
