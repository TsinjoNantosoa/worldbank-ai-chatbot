try:
    from langchain.vectorstores import FAISS
    print('FAISS_OK')
except Exception as e:
    print('FAISS_IMPORT_FAIL', type(e).__name__, e)

try:
    import faiss
    print('faiss lib OK')
except Exception as e:
    print('faiss lib FAIL', type(e).__name__, e)
try:
    from langchain.vectorstores import FAISS
    print('FAISS_OK')
except Exception as e:
    print('FAISS_IMPORT_FAIL', type(e).__name__, e)

try:
    import faiss
    print('faiss lib OK')
except Exception as e:
    print('faiss lib FAIL', type(e).__name__, e)
